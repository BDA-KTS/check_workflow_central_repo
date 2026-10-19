import html
import os
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
import joblib
import nbformat
from pathlib import Path
from typing import Set, List, Counter
from licensename import from_text
from datetime import datetime
import time
from config import Settings
from jsons.Json_PreCooking import strip_markdown

import resource

def get_file_extensions(path: Path) -> Set[str]:
    #Get all file extensions in the given directory recursively.
    return {path.suffix for path in path.rglob("*") if path.is_file()}

def get_event_data() -> tuple:
    #Load event data from GITHUB_EVENT_PATH.
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
    readme_name = payload.get("readme")
    if not readme_name:
        print("Error: readme missing in payload.")
        sys.exit(1)
    return full_name, readme_name

def get_needed_files(suffixes: Set[str]) -> Set[str]:
    required_for_binder = set()
    suffixes_lower = {s.casefold() for s in suffixes}
    if ".py" in suffixes_lower:
        required_for_binder.add("requirements.txt")
    if ".r" in suffixes_lower:
        required_for_binder.add("runtime.txt")      
    if '.yml' in suffixes_lower:
        required_for_binder.add('environment.yml')
    return required_for_binder

def get_files(path: Path):
    root_files =[]
    extended_files=[]
    for binder_directory in BINDER_DIRS:
        if not (path / binder_directory).is_dir():
            continue
        for f in (path/ binder_directory).iterdir():
            if f.parent == path:
                root_files.append(f.name)
            extended_files.append(f.name)
    return root_files , extended_files

def check_for_files(repo_requirements,required_binder,root_files,extended_files):
    match = next((f for f in extended_files if f.casefold().split(".")[0] == "postbuild"), None)
    if match is not None and not any(f for f in root_files if f.casefold().split(".")[0] == "postbuild" ):
        extended_files.remove(match)
        root_files.append("postbuild")
    
    formal_files = check_for_formal_files(repo_requirements, root_files)
    binder_files=check_for_binder_files(required_binder,extended_files)
    
    result = {'ifpassed': False, 'messages': [], 'warnings': [], 'errors': []}
    
    result['ifpassed'] = formal_files['ifpassed'] and binder_files['ifpassed']
    result['messages'] = formal_files['messages'] + binder_files['messages']
    result['warnings'] = formal_files['warnings'] + binder_files['warnings']
    result['errors'] = formal_files['errors'] + binder_files['errors']
    #result['messages'] = formal_files.statuses + binder_files.statuses
    #warning_labels=formal_files.warning_labels + binder_files.warning_labels
    #error_labels=formal_files.error_labels + binder_files.error_labels
    if result['ifpassed']:
        result['messages'].append("All required documents found")
    return result

def get_language_version(path: Path):
    ENVIRONMENT_PATTERNS = {
        "Python": {
            "environment.yml": r"python\s*=\s*[\"']?([0-9]+(?:\.[0-9]+){0,2})",
            "runtime.txt": r"python[-=]?([0-9]+(?:\.[0-9]+){0,2})",
            "pyproject.toml": r"requires-python\s*=\s*[\"']([^\"']+)[\"']",
            "setup.py": r"python_requires\s*=\s*[\"']([^\"']+)[\"']",
            "setup.cfg": r"python_requires\s*=\s*([^\n]+)",
        },
        "R": {
            "DESCRIPTION": r"R\s*\(>=\s*([0-9]+(?:\.[0-9]+){0,2})\)",
            "renv.lock": r'"R"\s*:\s*\{[^}]*"Version"\s*:\s*"([0-9]+(?:\.[0-9]+){0,2})"',
            "environment.yml": r"r-base\s*=\s*[\"']?([0-9]+(?:\.[0-9]+){0,2})",
        },
    }

    for language, patterns in ENVIRONMENT_PATTERNS.items():
        for filename, pattern in patterns.items():
            file_path = path / filename

            if not file_path.exists():
                continue

            text = file_path.read_text(encoding="utf-8")
            match = re.search(pattern, text, re.IGNORECASE)

            if match:
                return {'ifpassed': True, 'messages': f"{language} version: "f"{match.group(1)} (from {filename})", 'warnings': [], 'errors': []} 
    return {'ifpassed': False, 'messages': [], 'warnings': ['Python/R version is not specified for the method'], 'errors': []}

def check_for_formal_files(repo_requirements, root_files):
    repo_sorted = sorted([f.casefold().split(".")[0] for f in root_files])
    required = {r.casefold() for r in repo_requirements}

    repo_sorted = [f for f in repo_sorted if f in required]

    result = {'ifpassed': False, 'messages': [], 'warnings': [], 'errors': []}
    # Found files
    if repo_sorted:
        result['messages'].append(f"{', '.join(repo_sorted)}")
    #else:
        #messages.append("Found: —")

    # License status
    flag = False
    for file in repo_sorted:
        if "license" in file:
            result['messages'].append('license:' + file)
            flag = True
    if not flag:
        result['errors'].append('A valid open license not found')

    # Duplicate files
    counter = Counter(repo_sorted)
    duplicates = [f for f, count in counter.items() if count > 1]

    if duplicates:
        result['warnings'].append(f"Duplicated: {', '.join(sorted(duplicates))}")

    # Missing files
    missing = required - set(repo_sorted)

    if missing:
        result['errors'].append(f"Missing: {', '.join(sorted(missing))}")

        for item in sorted(missing):
            result['errors'].append(f"[{item}]({REPO_REQUIREMENTS[item]})")
    else:
        #errors.append("Missing: —")
        result['ifpassed'] = True

    #if not duplicates:
        #warnings.append("Duplicated: —")

    return result

def check_for_binder_files(required_binder,extended_files):
    found_files = extended_files
    result = {'ifpassed': False, 'messages': [], 'warnings': [], 'errors': []}
    output = ""
    if "environment.yml" in found_files:
        result['ifpassed'] = True
        result['messages'].append("environment.yml")
        
    found_files = sorted([f for f in found_files if f in required_binder])
    counter=Counter(found_files)
    duplicates = [f for f, count in counter.items() if count > 1]
    if duplicates:
        for f in duplicates:
            result['warnings'].append(f"File {f} is duplicated.")
    for f in found_files:
            result['messages'].append(f"{f}")
    if set(required_binder).issubset(set(found_files)):
        if result['ifpassed']:
            result['warnings'].append("Multiple binder configs found.")
        else:
            result['ifpassed'] = True
    else:
        missing = set(required_binder) - set(found_files)
        if missing:
            for item in missing:
                result['errors'].append(f"Missing required files: {item}")
        result['messages'].append("Missing required files")
    if result['ifpassed']:
        result['messages'].append("binder")
    return result

def license_check():
    result = {'ifpassed': False, 'messages':[], 'warnings':[], 'errors':[]}
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
            result['errors'].append(f"License file could not be read or parsed: Error {e}")

    licenses = [license_ for license_ in licenses if license_ is not None]
    if len(licenses) > 1:
        result['errors'].append("More than one license files found")

    elif len(licenses) == 1:
        if licenses[0] in FREE_LICENSES:
            result['ifpassed'] = True
            result['messages'].append(f"License {licenses[0]} accepted.")
        else:
            result['errors'].append(f"License {licenses[0]} not accepted.")
    else:
        result['errors'].append("No valid License found.")

    return result

def convert_readme_md(readme_path: Path) :
    """Analyze the README for required titles and subtitles."""
    result = {'ifpassed': False, 'messages': [], 'warnings': [], 'errors': []}

    if not readme_path.exists():
        result['errors'].append(f"Readme check failed: {readme_path} not found")
        return result
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
        result['errors'].append(f"Readme check failed: Error reading file ({e})")
        return result
    return check_readme(titles, subtitles, result)

def convert_readme_ipynb(readme_path: Path)  :
    result = {'ifpassed': False, 'messages': [], 'warnings': [], 'errors':[]}

    if not readme_path.exists():
        result['errors'].append(f"Readme check failed: {readme_path} not found")
        return result
    try:
        nb=nbformat.read(readme_path, as_version=4)
    except Exception as e:
        result['errors'].append(f"Readme check failed: Error reading file ({e})")
        return result
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
    return check_readme(titles, subtitles, result)

def check_readme(titles,subtitles, result):
    if len(titles) < 1:
        result['ifpassed'] = False
        result['errors'].append("Method title not defined.")
    elif len(titles) == 1:
        result['message'].append("Method title accepted.")
    else:
        result['ifpassed'] = False
        result['errors'].append(f"Method has {len(titles)}, i.e., more than 1 title cases.")
    if len(subtitles) < 1:
        result['ifpassed'] = False
        result['errors'].append("Method README has no section headings defined.")
    missing = set(NECESSARY_SUBTITLES) - set(subtitles)
    for subtitle in subtitles:
        result['messages'].append(f"{subtitle}")
    for item in missing:
        result['ifpassed'] = False
        reslt['errors'].append(f"Method README has {item} section heading missing, {NECESSARY_SUBTITLES[item]}")

    if len(subtitles) != len(set(subtitles)):
        result['warnings'].append("Method README has duplicate section headings.")
    
    return result

def repo2dockertest():
    """Simulate a repo2docker build to verify Binder compatibility."""
    result = {'ifpassed': False, 'messages': [], 'warnings': [], 'errors': []}

    try:
        output = subprocess.run(["repo2docker", "--no-run", "--debug", str(TEST_PATH)], capture_output=True, text=True, check=False, )

        if output.returncode == 0:
            result['messages'].append("Repo2Docker build successful. Binder environment is valid.")
            result['ifpassed'] = True
        else:
            result['errors'].append("Repo2Docker build failed.")
            combined_output = "".join(
                part for part in [result.stdout, result.stderr] if part
            )
            result['errors'].append(combined_output[-4000:] + "")

    except FileNotFoundError:
        result['errors'].append("Repo2Docker test failed: repo2docker is not installed in the environment.")

    except Exception as e:
        result['errors'].append(f"Repo2Docker test failed with unexpected error: {e}")
    return result

def repo2dockertest_sustainability():
    """Build the repository and report basic sustainability metrics."""
    result = {'ifpassed': False, 'messages': [], 'warnings': [], 'errors': []}
    start_time = time.perf_counter()

    try:
        process = subprocess.run(["repo2docker", "--no-run", str(TEST_PATH), ], capture_output=True, text=True, check=False, )

        execution_time = time.perf_counter() - start_time

        # Peak memory usage of this Python process (not necessarily Docker).
        peak_ram = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # Linux reports KiB; macOS reports bytes
        peak_ram_mib = peak_ram / (1024 if sys.platform == "linux" else 1024**2)

        if process.returncode == 0:
            result['ifpassed'] = True
            result['messages'].append("Repo2Docker build successful.")
            result['messages'].append("Environment validation: PASS")
        else:
            result['errors'].append("Repo2Docker build failed.")
            result['errors'].append(result.stderr[-2000:])
            error_labels.append("repo2docker")
            result['messages'].append("Environment validation: FAIL")

        result['messages'].extend([f"Build time: {execution_time:.2f} seconds", f"Peak RAM usage: {peak_ram_mib:.2f} MiB", "CPU utilization: ?", "Energy consumption: ?", "CO₂ emissions: ?", ])

    except FileNotFoundError:
        result['errors'].append("repo2docker is not installed.")
        result['messages'].append("Environment validation: FAIL")

    except Exception as e:
        result['errors'].append(f"Unexpected error: {e}")
        result['messages'].append("Environment validation: FAIL")

    return result

def strip_markdown(text: str) -> str:
    text = html.unescape(text)

    # Remove YAML front matter
    text = re.sub(r"(?s)\A---\n.*?\n---\n", "", text)

    # Remove fenced and inline code
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"`[^`]*`", " ", text)

    # Remove images and convert links to their label
    text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)
    text = re.sub(r"\[([^\]]+)\]\((.*?)\)", r"\1", text)

    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove markdown headings and blockquotes
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s{0,3}>\s?", "", text, flags=re.MULTILINE)

    # Remove list markers
    text = re.sub(r"^\s{0,3}[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"^\s{0,3}\d+\.\s+", "", text, flags=re.MULTILINE)

    # Remove emphasis markers
    text = re.sub(r"[*_~]+", " ", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text

def extract_text_from_content(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix == ".ipynb":
        with open(path, "r", encoding="utf-8") as f:
            notebook = json.load(f)

        parts = []
        for cell in notebook.get("cells", []):
            if cell.get("cell_type") in {"markdown", "raw"}:
                source = cell.get("source", "")
                if isinstance(source, list):
                    source = "".join(source)
                parts.append(str(source))
        return strip_markdown("\n\n".join(parts))

    with open(path, "r", encoding="utf-8") as f:
        return strip_markdown(f.read())


