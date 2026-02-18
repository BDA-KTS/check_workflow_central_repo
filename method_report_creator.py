import os
import csv
import json
import sys
from pathlib import Path
from typing import Set, Tuple, List, Optional
from licensename import from_text

# Configuration
TEST_PATH = Path("testee")
CENTRAL_PATH = Path("central")
FREE_LICENSES_PATH = CENTRAL_PATH / "free_licenses.csv"
NECESSARY_SUBTITLES = [
    "Description", "Use Cases", "Input Data", "Output Data",
    "Hardware Requirements", "Environment Setup", "How to Use",
    "Technical Details", "Contact Details"
]


def get_event_data() -> dict:
    """Load event data from GITHUB_EVENT_PATH."""
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        print("Error: GITHUB_EVENT_PATH not set.")
        sys.exit(1)
    
    try:
        with open(event_path, "r") as payload:
            return json.load(payload)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading event data: {e}")
        sys.exit(1)


def get_file_extensions(directory_path: Path) -> Set[str]:
    """Get all file extensions in the given directory recursively."""
    return {path.suffix for path in directory_path.rglob("*") if path.is_file()}


def get_needed_files(suffixes: Set[str]) -> Tuple[Set[str], Set[str]]:
    """Determine required files based on file extensions found in the repo."""
    required_in_repo = {"citation.cff", "license", "postbuild"}
    required_for_binder = set()
    suffixes_lower = {s.casefold() for s in suffixes}

    if ".py" in suffixes_lower:
        required_for_binder.add("requirements.txt")

    if ".r" in suffixes_lower:
        required_for_binder.update({"install.r", "runtime.txt"})
    
    return required_in_repo, required_for_binder


def check_license() -> str:
    """Check if the license in the repo is accepted based on free_licenses.csv."""
    license_file = TEST_PATH / "LICENSE"
    if not license_file.exists():
        # Try lowercase just in case, though usually it's uppercase
        license_file = TEST_PATH / "license"
        if not license_file.exists():
            return "License denied: LICENSE file not found\n"

    try:
        license_text = license_file.read_text(encoding="utf-8")
        license_name = from_text(license_text)
    except Exception as e:
        return f"License check failed: Could not read or parse LICENSE file ({e})\n"

    if not FREE_LICENSES_PATH.exists():
        return f"License check failed: {FREE_LICENSES_PATH} not found\n"

    try:
        with open(FREE_LICENSES_PATH, "r", encoding="utf-8") as csvf:
            reader = csv.reader(csvf)
            allowed_licenses = {row[0] for row in reader if row}
        
        if license_name in allowed_licenses:
            return f"License accepted: Found {license_name}\n"
        else:
            return f"License denied: Found {license_name}\n"
    except Exception as e:
        return f"License check failed: Error reading free_licenses.csv ({e})\n"


def check_readme(readme_filename: str) -> str:
    """Analyze the README for required titles and subtitles."""
    readme_path = TEST_PATH / readme_filename
    if not readme_path.exists():
        return f"Readme check failed: {readme_filename} not found\n"

    titles = []
    subtitles = []
    report_lines = []

    try:
        with open(readme_path, encoding="utf-8") as f:
            for line in f:
                if line.startswith("# "):
                    titles.append(line[2:].strip())
                elif line.startswith("## "):
                    subtitles.append(line[3:].strip())
    except Exception as e:
        return f"Readme check failed: Error reading file ({e})\n"

    if len(titles) == 1:
        report_lines.append("Found one title: Accepted")
    elif len(titles) < 1:
        report_lines.append("Found no titles: Denied")
    else:
        report_lines.append(f"Found too many titles: Count: {len(titles)}")

    missing = set(NECESSARY_SUBTITLES) - set(subtitles)
    if not missing:
        report_lines.append("All necessary subtitles exist")
    else:
        for s in sorted(missing):
            report_lines.append(f"Missing subtitle: {s}")
#Newline
    return "\n".join(report_lines) + "\n"


def check_required_files(repo_files: Set[str], binder_files: Set[str]) -> Tuple[str, Set[str]]:
    """Check for presence of required repository and Binder files."""
    report_lines = []

    # Check Repo-specific files in root
    found_repo_files = {p.name.lower() for p in TEST_PATH.iterdir() if p.is_file()}
    missing_repo = repo_files - found_repo_files

    if missing_repo:
        report_lines.append("Repo – not found:")
        report_lines.extend(f"- {f}" for f in sorted(missing_repo))
    else:
        report_lines.append("Repo – everything found")

    report_lines.append("") # Spacer

    # Check Binder-specific files in various locations
    binder_dirs = [TEST_PATH, TEST_PATH / "binder"]
    found_binder = set()

    for fname in binder_files:
        for base in binder_dirs:
            if (base / fname).is_file():
                found_binder.add(fname)
                break

    missing_binder = binder_files - found_binder

    if missing_binder:
        report_lines.append("Binder – not found:")
        report_lines.extend(f"- {b}" for b in sorted(missing_binder))
    else:
        report_lines.append("Binder – everything found")

    return "\n".join(report_lines) + "\n", missing_repo


def main():
    event_data = get_event_data()
    payload = event_data.get("client_payload", {})
    full_name = payload.get("repository_full_name")
    readme_name = payload.get("readme", "README.md")

    if not full_name:
        print("Error: repository_full_name missing in payload.")
        sys.exit(1)

    owner, repo = full_name.split("/", 1)
    report_dir = CENTRAL_PATH / "report" / owner
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"{repo}.md"

    # Start building the report content
    report_content = [f"# Report for {owner} of {repo}\n"]

    # File presence checks
    report_content.append("## Checking required files\n")
    suffixes = get_file_extensions(TEST_PATH)
    required_repo, required_binder = get_needed_files(suffixes)
    
    file_check_text, missing_repo_files = check_required_files(required_repo, required_binder)
    report_content.append(file_check_text)

    # License check
    if "license" not in missing_repo_files:
        report_content.append("## Checking License\n")
        report_content.append(check_license())

    # Readme check
    report_content.append("\n## Checking Readme\n")
    report_content.append(check_readme(readme_name))

    # Write the report
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(report_content))
    
    print(f"Report generated: {report_file}")


if __name__ == "__main__":
    main()
