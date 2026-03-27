import os
import json
import subprocess
import sys
from dataclasses import dataclass, field

import nbformat
from pathlib import Path
from typing import Set, List, Counter
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

@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    statuses: List[str] = field(default_factory=list)

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
        sys.exit(1)
    readme_name = payload.get("readme") or "README.md"
    return full_name, readme_name


def get_needed_files(suffixes: Set[str]) -> Set[str]:
    required_for_binder = set()
    suffixes_lower = {s.casefold() for s in suffixes}

    if ".py" in suffixes_lower:
        required_for_binder.add("requirements.txt")

    if ".r" in suffixes_lower:
        required_for_binder.add("install.R")
        required_for_binder.add("runtime.txt")

    return required_for_binder


def check_for_formal_files():
    passed=False
    messages=[]
    warnings=[]
    statuses=[]
    repo_files = [p.stem for p in TEST_PATH.iterdir() if p.is_file()]
    repo_scaffold = sorted([f.casefold() for f in repo_files])

    required = {r.casefold() for r in set(REPO_REQUIREMENTS)}
    repo_scaffold=[f for f in repo_scaffold if f in required]
    if "license" in repo_scaffold:
        statuses.append("license")
    counter=Counter(repo_scaffold)
    duplicates=[f for f, count in counter.items() if count <1]
    if duplicates:
        for f in duplicates:
            warnings.append(f"Warning: {f} is duplicated.")
    missing = required - set(repo_scaffold)
    if missing:
        for item in missing:
            messages.append(f"Missing required files: {item}")
            messages.append(f"For further information see: {REPO_REQUIREMENTS[item]}")
    else:
        messages.append("All required files found")
        passed=True
    return CheckResult("Formal Files", passed, messages, warnings, statuses)


def check_for_binder_files(required_binder):
    passed=False
    messages=[]
    warnings=[]
    statuses=[]
    found_files = []
    for binder_directory in BINDER_DIRS:
        if not (TEST_PATH / binder_directory).is_dir():
            continue
        for f in (TEST_PATH / binder_directory).iterdir():
            found_files.append(f.name)
    if "environment.yml" in found_files:
        passed=True
        messages.append("Found required file: environment.yml")
        messages.append("All required binder files found")
    found_files = sorted([f in found_files for f in required_binder])
    counter=Counter(found_files)
    duplicates=[f for f, count in counter.items() if count <1]
    if duplicates:
        for f in duplicates:
            warnings.append(f"Warning: {f} is duplicated.")
    for f in found_files:
            messages.append(f"Found required file: {f}")
    if found_files == required_binder:
        if passed:
            warnings.append("Multiple binder configs found")
        else:
            passed=True
            messages.append("All required binder files found")
    return CheckResult("Binder Files", passed, messages, warnings,statuses)

def license_check():
    passed=False
    messages=[]
    warnings=[]
    license_files = [
        f for f in TEST_PATH.iterdir()
        if f.is_file() and f.name.casefold().startswith("license")
    ]
    licenses = []
    for f in license_files:
        try:
            license_text = f.read_text(encoding="utf-8")
            license_name = from_text(license_text)
            licenses.append(license_name)
        except Exception as e:
            warnings.append(f"License file could not be read or parsed: Error {e}")
    if len(licenses) > 1:
        warnings.append(" Too many licenses found, try choosing just one ")
    if len(licenses) == 1:
        if licenses[0] in FREE_LICENSES:
            passed=True
            messages.append(f"Found {licenses[0]} License, License accepted ")
        else:
            messages.append(f"Found {licenses[0]} License denied ")

    return CheckResult("License Check",passed,messages,warnings,[])


def convert_readme_md(readme_path: Path) :
    """Analyze the README for required titles and subtitles."""
    warnings=[]
    if not readme_path.exists():
        warnings.append(f"Readme check failed: {readme_path} not found")
        return warnings
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
        warnings.append(f"Readme check failed: Error reading file ({e})")
        return warnings
    return check_readme(titles, subtitles, warnings)

def convert_readme_ipynb(readme_path: Path):
    warnings = []
    if not readme_path.exists():
        warnings.append(f"Readme check failed: {readme_path} not found")
        return warnings
    try:
        nb=nbformat.read(readme_path, as_version=4)
    except Exception as e:
        warnings.append(f"Readme check failed: Error reading file ({e})")
        return warnings
    titles = []
    subtitles = []
    for cell in nb.cells:
        if cell.cell_type == "markdown":
            text= cell.source
            for line in text.splitlines():
                line=line.strip()
                if line.startswith("# "):
                    titles.append(line[2:].strip())
                elif line.startswith("## "):
                    subtitles.append(line[3:].strip())
    return check_readme(titles, subtitles, warnings)

def check_readme(titles,subtitles, warning):
    passed=True
    message=[]
    warnings=warning
    statuses=[]
    if len(titles) == 1:
        message.append("Found one title: Accepted")
    elif len(titles) < 1:
        passed=False
        message.append("Found no titles: Denied")
    else:
        message.append(f"Found too many titles: Count: {len(titles)}")
    missing = set(NECESSARY_SUBTITLES) - set(subtitles)
    for subtitle in subtitles:
        message.append(f"Found subtitle: {subtitle}")
    for item in missing:
        message.append(f"Missing subtitles: {item}")
        message.append(f"For further information see: {NECESSARY_SUBTITLES[item]}")
    if len(subtitles) == len(set(subtitles)):
        warnings.append("Warning: Some subtitles are duplicated.")
    return CheckResult("Readme Check",passed,message,warnings,statuses)

def repo2dockertest():
    """Simulate a repo2docker build to verify Binder compatibility."""
    passed=False
    message=[]

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
            message.append("Repo2Docker build successful. Binder environment is valid.")
            passed=True
        else:
            message.append("Repo2Docker build failed.")
            message.append(" Repo2Docker Output:")
            combined_output = "".join(
                part for part in [result.stdout, result.stderr] if part
            )
            message.append(combined_output[-4000:] + "")

    except FileNotFoundError:
        message.append("Repo2Docker test failed: repo2docker is not installed in the environment.")

    except Exception as e:
        message.append(f"Repo2Docker test failed with unexpected error: {e}")
    return CheckResult("Binder Test",passed,message,[],[])


def write_report(checklists, report_file, owner, repo):
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(f"# Report for {owner} of {repo}\n\n")
        f.write("## Report generated at {}\n\n".format(time.strftime("%Y-%m-%d %H:%M:%S")))
        for checklist in checklists:
            f.write("## {}\n\n".format(checklist.name))
            f.write("<br>".join(checklist.messages))
            f.write("<br>".join(checklist.warnings))
            f.write("\n\n")


def main():
    checklists: list[CheckResult] = []
    full_name, readme_name = get_event_data()
    owner, repo = full_name.split("/", 1)
    report_dir = CENTRAL_PATH / "report" / owner
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"{repo}.md"

    # Start building the report content
    #messages.append(f"# Report for {owner} of {repo}\n\n")
    #messages.append(f"## Report generated at {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    # File presence checks
    suffixes = get_file_extensions(TEST_PATH)
    required_binder = get_needed_files(suffixes)
    checklists.append(check_for_formal_files())
    checklists.append(check_for_binder_files(required_binder))

    # License check
    if any(results.statuses == "license" for results in checklists):
        license_check()

    # Readme check
    readme_path = TEST_PATH / readme_name
    if readme_path.suffix == ".ipynb":
        checklists.append(convert_readme_ipynb(readme_path))
    elif readme_path.suffix == ".md":
        checklists.append(convert_readme_md(readme_path))
    else:
        checklists.append(CheckResult("Readme Check",False,["Readme check failed: Format not yet supported"],[""],[""]))

    # Simulate Repo2Docker
    if any(results.name == "Binder Files" and results.passed for results in checklists):
        repo2dockertest()
    else:
        checklists.append(CheckResult("Binder Test",False,["Binder test skipped: Binder files not found or not valid"],[""],[""]))

    # Write the report
    write_report(checklists, report_file,owner,repo)


if __name__ == "__main__":
    main()
