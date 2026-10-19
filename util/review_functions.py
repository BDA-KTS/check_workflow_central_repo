import subprocess
import sys
from typing import Set, List, Counter
from licensename import from_text
import time
import resource
from pathlib import Path

def check_for_formal_files(repo_requirements, root_files):
    repo_sorted = sorted([f.casefold().split(".")[0] for f in root_files])
    required = {r.casefold() for r in repo_requirements}

    repo_sorted = [f for f in repo_sorted if f in required]

    result = {'ifpassed': False, 'messages': [], 'warnings': [], 'errors': []}
    # Found files
    if repo_sorted:
        result['messages'].append(f"{', '.join(repo_sorted)}")

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


def license_check(TEST_PATH, FREE_LICENSES):
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
        result['warning'].append("More than one license files found")

    elif len(licenses) == 1:
        if licenses[0] in FREE_LICENSES:
            result['ifpassed'] = True
            result['messages'].append(f"License {licenses[0]} accepted as an open license")
        else:
            result['errors'].append(f"License {licenses[0]} not accepted as an open license")
    else:
        result['errors'].append("No valid License found")
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



