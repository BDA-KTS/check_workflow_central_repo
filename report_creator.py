import os
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Set
from licensename import from_text
from config import Settings
import time

TEST_PATH = Settings.TEST_PATH
CENTRAL_PATH = Settings.CENTRAL_PATH
NECESSARY_SUBTITLES = Settings.NECESSARY_SUBTITLES
FREE_LICENSES = Settings.FREE_LICENSES
REPO_REQUIREMENTS = Settings.REPO_REQUIREMENTS
BINDER_DIRS = Settings.BINDER_DIRS
report = []
license_flag = False
binder_ready_flag = False


def report_creator(report_text: str) -> None:
    report.append(report_text)


def get_file_extensions(path: Path) -> Set[str]:
    """Get all file extensions in the given directory recursively."""
    return {path.suffix for path in path.rglob("*") if path.is_file()}


def get_event_data() -> tuple:
    """Load event data from GITHUB_EVENT_PATH."""
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        print("Error: GITHUB_EVENT_PATH not set.")
        sys.exit(1)

    try:
        with open(event_path, "r") as payload_file:
            payload = json.load(payload_file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading event data: {e}")
        sys.exit(1)
    if not payload:
        print("Error: No payload found in the event.")
        sys.exit(1)
    payload = payload.get("client_payload", {})
    full_name = payload.get("repository_full_name")
    if not full_name:
        print("Error: repository_full_name missing in payload.")
    readme_name = payload.get("readme") or "README.md"
    return full_name, readme_name


def get_needed_files(suffixes: Set[str]) -> Set[str]:
    required_for_binder = set()
    suffixes_lower = {s.casefold() for s in suffixes}

    if ".py" in suffixes_lower:
        required_for_binder.add("requirements.txt")

    if ".r" in suffixes_lower:
        required_for_binder.add("install.r")
        required_for_binder.add("runtime.txt")

    if ".conda" in suffixes_lower:
        required_for_binder.add("environment.yml")

    return required_for_binder


def check_for_formal_files():
    global license_flag
    repo_files = [p.stem for p in TEST_PATH.iterdir() if p.is_file()]
    repo_scaffold = sorted([f.casefold() for f in repo_files])

    required = {r.casefold() for r in REPO_REQUIREMENTS}

    for found in repo_scaffold:
        if found in required:
            report_creator(f"Found required file: {found} \n")
        if found == "license":
            license_flag = True

    for missing in required:
        if missing not in repo_scaffold:
            report_creator(f"Missing required file: {missing} \n")

    duplicates = {
        name for name, count in Counter(repo_scaffold).items() if count > 1
    }
    if not duplicates:
        report_creator("No duplicate files found.\n")
    else:
        if any(required.intersection(duplicates)):
            report_creator(
                "Warning: Some required files are duplicated.\n"
            )


def check_for_binder_files(required_binder):
    global binder_ready_flag
    found_files = []
    for dir in BINDER_DIRS:
        if not (TEST_PATH / dir).is_dir():
            continue
        for f in (TEST_PATH / dir).iterdir():
            found_files.append(f.name)
        for f in found_files:
            if f in required_binder:
                report_creator(f"Found required file: {f} in {dir} \n")
        for f in required_binder:
            if f not in found_files:
                report_creator(f"Missing required file: {f} in {dir} \n")
        if required_binder.issubset(found_files):
            binder_ready_flag = True
            report_creator(f"All Binder Files found \n")
        duplicates = {
            name for name, count in Counter(found_files).items() if count > 1
        }
        if not duplicates:
            report_creator("No duplicate files found.\n")
        else:
            if any(required_binder.intersection(duplicates)):
                report_creator(
                    "Warning: Some required files are duplicated.\n"
                )


def license_check():
    license_files = [
        f for f in TEST_PATH.iterdir()
        if f.is_file() and f.name.casefold().startswith("license")
    ]
    print(license_files)
    licenses = []
    report_creator("## Checking License: \n\n")
    for f in license_files:
        try:
            license_text = f.read_text(encoding="utf-8")
            license_name = from_text(license_text)
            licenses.append(license_name)
            print(license_name)
        except Exception as e:
            return report_creator(f"License check failed: Could not read or parse LICENSE file ({e})\n")
    if len(licenses) > 1:
        report_creator(" Too many licenses found, try choosing just one \n")
    if len(licenses) == 1:
        if licenses[0] in FREE_LICENSES:
            report_creator(f"Found {licenses[0]} License, License accepted \n")
        else:
            report_creator(f"Found {licenses[0]} License denied \n")
    return None


def check_readme(readme_filename: str) -> None:
    """Analyze the README for required titles and subtitles."""
    report_creator("## Checking Readme: \n\n")
    readme_path = TEST_PATH / readme_filename
    if not readme_path.exists():
        report_creator(f"Readme check failed: {readme_filename} not found\n")
        return
    titles = []
    subtitles = []
    try:
        with open(readme_path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("# "):
                    titles.append(line[2:].strip())
                elif line.startswith("## "):
                    subtitles.append(line[3:].strip())
    except Exception as e:
        report_creator(f"Readme check failed: Error reading file ({e})\n")
        return
    if len(titles) == 1:
        report_creator("Found one title: Accepted\n")
    elif len(titles) < 1:
        report_creator("Found no titles: Denied\n")
    else:
        report_creator(f"Found too many titles: Count: {len(titles)}\n")
    missing = set(NECESSARY_SUBTITLES) - set(subtitles)
    for subtitle in subtitles:
        report_creator(f"Found subtitle: {subtitle}\n")
    if not missing:
        report_creator("All necessary subtitles exist\n")
    else:
        for s in sorted(missing):
            report_creator(f"Missing subtitle: {s}\n")


def repo2dockertest():
    """Simulate a repo2docker build to verify Binder compatibility."""
    report_creator("## Testing repository with repo2docker\n\n")

    try:
        result = subprocess.run(
            [
                "repo2docker",
                "--no-run",
                "--debug",
                str(TEST_PATH)
            ],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode == 0:
            report_creator("Repo2Docker build successful. Binder environment is valid.\n")
        else:
            report_creator("Repo2Docker build failed.\n")
            report_creator(" Repo2Docker Output:\n")
            report_creator("```text\n")
            combined_output = "\\n".join(
                part for part in [result.stdout, result.stderr] if part
            )
            report_creator(combined_output[-4000:] + "\\n")
            report_creator("```\n")

    except FileNotFoundError:
        report_creator("Repo2Docker test failed: repo2docker is not installed in the environment.\n")

    except Exception as e:
        report_creator(f"Repo2Docker test failed with unexpected error: {e}\n")


def main():
    full_name, readme_name = get_event_data()
    owner, repo = full_name.split("/", 1)
    report_dir = CENTRAL_PATH / "report" / owner
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"{repo}.md"

    # Start building the report content
    report_creator(f"# Report for {owner} of {repo}\n\n")
    report_creator(f"## Report generated at {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    # File presence checks
    report_creator("## Checking for required files\n\n")
    suffixes = get_file_extensions(TEST_PATH)
    required_binder = get_needed_files(suffixes)
    check_for_formal_files()
    check_for_binder_files(required_binder)

    # License check
    if license_flag:
        license_check()
    else:
        report_creator("## Can't check license, no license file found.\n\n")

    # Readme check
    check_readme(readme_name)

    # Simulate Repo2Docker
    if binder_ready_flag:
        repo2dockertest()
    else:
        report_creator("## Can't check binder, no or wrong binder files found.\n\n")

    # Write the report
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("".join(report))


if __name__ == "__main__":
    main()
