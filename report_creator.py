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

with open(os.environ["GITHUB_EVENT_PATH"], "r", encoding="utf-8") as payload_file:
    payload = json.load(payload_file)

event_type = payload.get("action")
client_payload = payload.get("client_payload", {})
# Gets the configuration from the config.py file
TEST_PATH = Settings.TEST_PATH
CENTRAL_PATH = Settings.CENTRAL_PATH
OUTPUT_PATH = Path(Settings.OUTPUT_PATH[event_type])
REPORT_PATH = Settings.REPORT_PATH
AGGREGATION_PATH = Settings.AGGREGATION_PATH
NECESSARY_SUBTITLES = Settings.NECESSARY_SUBTITLES
FREE_LICENSES = Settings.FREE_LICENSES
REPO_REQUIREMENTS = Settings.REPO_REQUIREMENTS
BINDER_DIRS = Settings.BINDER_DIRS
ML_PATH = Settings.ML_PATH
report = []


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    messages: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    statuses: List[str] = field(default_factory=list)
    warning_labels: List[str] = field(default_factory=list)
    error_labels:  List[str] = field(default_factory=list)

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
    passed=formal_files.passed and binder_files.passed
    messages=formal_files.messages + binder_files.messages
    warnings=formal_files.warnings + binder_files.warnings
    errors=formal_files.errors + binder_files.errors
    statuses=formal_files.statuses + binder_files.statuses
    warning_labels=formal_files.warning_labels + binder_files.warning_labels
    error_labels=formal_files.error_labels + binder_files.error_labels
    if passed:
        messages.append("All required files found")
    return CheckResult("Documentation",passed=passed,messages=messages,warnings=warnings,errors=errors,statuses=statuses,warning_labels=warning_labels,error_labels=error_labels)

def get_language_version(path: Path) -> CheckResult:
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
                return CheckResult(
                    f"Programming Language",
                    True,
                    [
                        f"{language} version: "
                        f"{match.group(1)} (from {filename})"
                    ],
                    [],
                    [],
                    [],
                    [],
                    [],
                )

    return CheckResult(
        "Programming Language",
        True,
        [],
        ["Python/R version is not explicitly specified in the repository."],
        [],
        [],
        [],
        [],
    )
    
def check_for_formal_files(repo_requirements, root_files):
    passed = False
    messages = []
    warnings = []
    errors = []
    statuses = []
    warning_labels = []
    error_labels = []

    repo_sorted = sorted(
        [f.casefold().split(".")[0] for f in root_files]
    )
    required = {r.casefold() for r in repo_requirements}

    repo_sorted = [f for f in repo_sorted if f in required]

    # Found files
    if repo_sorted:
        messages.append(
            f"Found: {', '.join(repo_sorted)}"
        )
    #else:
        #messages.append("Found: —")

    # License status
    if "license" in repo_sorted:
        statuses.append("license")

    # Duplicate files
    counter = Counter(repo_sorted)
    duplicates = [f for f, count in counter.items() if count > 1]

    if duplicates:
        warnings.append(
            f"Duplicated: {', '.join(sorted(duplicates))}"
        )
        for f in duplicates:
            warning_labels.append(f)

    # Missing files
    missing = required - set(repo_sorted)

    if missing:
        errors.append(
            f"Missing: {', '.join(sorted(missing))}"
        )

        for item in sorted(missing):
            errors.append(
                f"[{item}]({REPO_REQUIREMENTS[item]})"
            )
            error_labels.append(item)
    else:
        #errors.append("Missing: —")
        passed = True

    #if not duplicates:
        #warnings.append("Duplicated: —")

    return CheckResult(
        "Mandatory Files",
        passed,
        messages,
        warnings,
        errors,
        statuses,
        warning_labels,
        error_labels
    )

def check_for_binder_files(required_binder,extended_files):
    passed=False
    messages=[]
    warnings=[]
    errors=[]
    statuses=[]
    warning_labels=[]
    error_labels=[]
    found_files = extended_files
    output = ""
    if "environment.yml" in found_files:
        passed=True
        messages.append("Found required file: environment.yml")
        
    found_files = sorted([f for f in found_files if f in required_binder])
    counter=Counter(found_files)
    duplicates=[f for f, count in counter.items() if count > 1]
    if duplicates:
        for f in duplicates:
            warnings.append(f"Warning: {f} is duplicated.")
            warning_labels.append(f"{f}")
    for f in found_files:
            messages.append(f"Found required file: {f}")
    if set(required_binder).issubset(set(found_files)):
        if passed:
            warnings.append("Multiple binder configs found")
            warning_labels.append("Multiple Setups")
        else:
            passed=True
    else:
        missing = set(required_binder) - set(found_files)
        if missing:
            for item in missing:
                errors.append(f"Missing required files: {item}")
                error_labels.append(f"{item}")
        messages.append("Missing required files")
    if passed:
        statuses.append("binder")
    return CheckResult("Working Environment", passed, messages, warnings, errors, statuses, warning_labels, error_labels)

def license_check():
    passed=False
    messages=[]
    warnings=[]
    errors=[]
    statuses=[]
    warning_labels=[]
    error_labels=[]
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
            errors.append(f"License file could not be read or parsed: Error {e}")
            error_labels.append(f"Loading")
    licenses = [license_ for license_ in licenses if license_ is not None]
    if len(licenses) > 1:
        errors.append("More than one license files found")
        error_labels.append("Multiple")
    elif len(licenses) == 1:
        if licenses[0] in FREE_LICENSES:
            passed=True
            messages.append(f"Found {licenses[0]} License, License accepted ")
        else:
            errors.append(f"Found {licenses[0]} License denied ")
            error_labels.append(f"{licenses[0]}")
    else:
        errors.append("No valid License found.")
        error_labels.append("None")

    return CheckResult("License",passed,messages,warnings,errors,statuses,warning_labels,error_labels)


def convert_readme_md(readme_path: Path) :
    """Analyze the README for required titles and subtitles."""
    errors=[]
    error_labels=[]
    if not readme_path.exists():
        errors.append(f"Readme check failed: {readme_path} not found")
        error_labels.append("Path")
        return check_readme([],[],errors, error_labels)
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
        errors.append(f"Readme check failed: Error reading file ({e})")
        error_labels.append("Loading")
        return check_readme([],[],errors, error_labels)
    return check_readme(titles, subtitles, errors, error_labels)

def convert_readme_ipynb(readme_path: Path)  :
    errors = []
    error_labels=[]
    if not readme_path.exists():
        errors.append(f"Readme check failed: {readme_path} not found")
        error_labels.append("Path")
        return check_readme([],[],errors, error_labels)
    try:
        nb=nbformat.read(readme_path, as_version=4)
    except Exception as e:
        errors.append(f"Readme check failed: Error reading file ({e})")
        error_labels.append("Loading")
        return check_readme([],[],errors, error_labels)
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
    return check_readme(titles, subtitles, errors, error_labels)

def check_readme(titles,subtitles, error, error_labels) -> CheckResult:
    passed=True
    message=[]
    warnings=[]
    errors=error
    statuses=[]
    waring_labels=[]
    error_labels = error_labels
    if len(titles) < 1:
        passed=False
        errors.append("No title found but one is required.")
        error_labels.append("No Title")
    elif len(titles) == 1:
        message.append("Found one title: Accepted")
    else:
        passed=False
        errors.append(f"Found too many titles: Count: {len(titles)}")
        error_labels.append("Multiple Titles")
    if len(subtitles) < 1:
        passed=False
        errors.append("No subtitle found but one is required.")
        error_labels.append("Subtitles")
    missing = set(NECESSARY_SUBTITLES) - set(subtitles)
    for subtitle in subtitles:
        message.append(f"Found subtitle: {subtitle}")
    for item in missing:
        passed = False
        error.append(f"Missing subtitles: {item}")
        error.append(f"For further information see: {NECESSARY_SUBTITLES[item]}")
        error_labels.append(f"{item}")
    if len(subtitles) != len(set(subtitles)):
        warnings.append("Warning: Some subtitles are duplicated.")
        waring_labels.append("Duplicated")
    return CheckResult("Readme Check",passed,message,warnings,errors,statuses, waring_labels,error_labels)

def repo2dockertest():
    """Simulate a repo2docker build to verify Binder compatibility."""
    passed=False
    message=[]
    warnings=[]
    errors=[]
    statuses=[]
    warning_labels=[]
    error_labels=[]

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
            errors.append("Repo2Docker build failed.")
            errors.append(" Repo2Docker Output:")
            combined_output = "".join(
                part for part in [result.stdout, result.stderr] if part
            )
            errors.append(combined_output[-4000:] + "")
            error_labels.append("repo2docker")

    except FileNotFoundError:
        errors.append("Repo2Docker test failed: repo2docker is not installed in the environment.")

    except Exception as e:
        errors.append(f"Repo2Docker test failed with unexpected error: {e}")
    return CheckResult("Binder Test",passed,message,warnings,errors,statuses,warning_labels,error_labels)

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

def load_ml_artifacts():
    model = joblib.load(ML_PATH/"model.joblib")
    vectorizer = joblib.load(ML_PATH/ "vectorizer.joblib")
    mlb = joblib.load(ML_PATH / "mlb.joblib")
    return model, vectorizer, mlb

def predict_labels_with_probability(path: Path ,threshold: float = 0.5):
    text = extract_text_from_content(path)
    model, vectorizer, mlb = load_ml_artifacts()
    vec = vectorizer.transform([text])
    probs = model.predict_proba(vec)[0]
    probability_map = {
        label: float(prob)
        for label, prob in zip(mlb.classes_, probs)
    }

    predicted = [
        label for label, prob in probability_map.items()
        if prob >= threshold
    ]
    if predicted:
        predicted.sort(key=lambda label: probability_map[label], reverse=True)
        messages = [f"Predicted labels: {', '.join(predicted) if predicted else 'none'}",
                    f"Probability: {round(probability_map[predicted[0]] * 100, 2)}%"]
    else:
        messages = ["No labels predicted with probability above threshold."]
    return CheckResult(
        name="Taxonomy",
        passed=True,
        messages=messages,
        warnings=[],
        errors=[],
        statuses=[],
        warning_labels=[],
        error_labels=[]
    )



def summary(checklists: list[CheckResult]):
    messages = []
    warnings = []
    errors = []
    error_labels = []
    passed = True
    if any(not checklist.passed for checklist in checklists):
        passed = False
        errors.append("Major Flaws, Error in at least one Check")
        error_labels.append("Critical")
    elif  any(checklist.warnings for checklist in checklists) and passed:
        warnings.append("Passed but with warnings")
        error_labels.append("Warning")
    else:
        messages.append("Passed perfectly")
    return CheckResult("Summary", passed, messages, warnings, errors, [],[],error_labels)



def write_report(checklists, report_file, owner, repo, elapsed_time):
    with open(report_file, "w", encoding="utf-8") as f:
        total_seconds = int(elapsed_time.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        f.write(
            f"# Report: [{owner} / {repo}](https://github.com/{owner}/{repo})\n\n"
            f"<small>created on {time.strftime('%Y-%m-%d %H:%M:%S')}, taking {minutes}:{seconds:02d} (min/sec)\n\n"
        )

        #f.write("[![Report Creator](https://github.com/BDA-KTS/check_workflow_central_repo/actions/workflows/test_workflow.yml/badge.svg)](https://github.com/BDA-KTS/check_workflow_central_repo/actions/workflows/test_workflow.yml)\n\n")

        #[![Report Creator](https://github.com/BDA-KTS/check_workflow_central_repo/actions/workflows/test_workflow.yml/badge.svg)](https://github.com/BDA-KTS/check_workflow_central_repo/actions/workflows/test_workflow.yml)
        #f.write("## Report generated at {}\n\n".format(time.strftime("%Y-%m-%d %H:%M:%S")))
        #f.write(f"## Link to the repository: [GitHub Repository](https://github.com/{owner}/{repo})\n\n")
        
        
        #f.write(f"### Working Environment:", f"{env}", f"{required_binder}", f"{root_files}", f"{extended_files}")
    
        for checklist in checklists:
            f.write("### {}\n\n".format(checklist.name))
        
            if checklist.errors:
                f.write(f"**⛔ Errors:** {checklist.errors}\n\n")

            if checklist.warnings:
                f.write(f"**⚠️ Warnings:** {checklist.warnings}\n\n")

            if checklist.messages:
                f.write(f"**✅ Information:** {checklist.messages}\n\n")


def write_macro(checklists, report_file, owner, repo, elapsed_time):
    total_seconds = int(elapsed_time.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    times = f"{minutes}:{seconds:02d}"

    with open(report_file, "w", encoding="utf-8") as f:
        for checklist in checklists:
            entry = {
                "owner": owner,
                "repo": repo,
                "name": checklist.name,
                "passed": checklist.passed,
                "warning_labels": checklist.warning_labels,
                "error_labels": checklist.error_labels,
                "Workflow Duration": times,
            }
            f.write(json.dumps(entry) + "\n")

def main():
    time_start = datetime.now()
    checklists: list[CheckResult] = []
    full_name, readme_name = get_event_data()
    owner, repo = full_name.split("/", 1)
    report_dir = OUTPUT_PATH / REPORT_PATH / owner
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"{repo}.md"

    aggregated_dir = OUTPUT_PATH / AGGREGATION_PATH / owner
    aggregated_dir.mkdir(parents=True, exist_ok=True)
    aggregated = aggregated_dir / f"{repo}.jsonl"
    # File presence checks
    suffixes = get_file_extensions(TEST_PATH)
    required_binder = get_needed_files(suffixes)
    root_files, extended_files=get_files(TEST_PATH)

    # License check
    if any("license" in result.statuses for result in checklists):
        checklists.append(license_check())
    else:
        checklists.append(CheckResult("License",False,[],[],["License Check failed, no license file found"],[],[],["No license"]))
    # Working language
    checklists.append(get_language_version(TEST_PATH))
    # Binder environment
    checklists.append(check_for_files(REPO_REQUIREMENTS,required_binder,root_files,extended_files))
     # Simulate Repo2Docker 2
    if any("binder" in result.statuses for result in checklists):
        checklists.append(repo2dockertest())
    else:
        checklists.append(CheckResult("Binder Test",False,[],[],["Binder test skipped: Binder files not found or not valid"],[],[],[]))

    
    # Readme check
    readme_path = TEST_PATH / readme_name
    if readme_path.suffix == ".ipynb":
        checklists.append(convert_readme_ipynb(readme_path))
    elif readme_path.suffix == ".md":
        checklists.append(convert_readme_md(readme_path))
    elif readme_path.suffix == ".qmd":
        checklists.append(convert_readme_md(readme_path))
    else:
        checklists.append(CheckResult("README",False,[],[],["Readme check failed: Format not yet supported"],[],[],[]))

    #checklists.insert(0,summary(checklists))
    #checklists.append(predict_labels_with_probability(readme_path))
    time_end = datetime.now()
    elapsed_time = time_end - time_start
    # Write the report
    write_report(checklists, report_file,owner,repo, elapsed_time)
    write_macro(checklists, aggregated, owner, repo, elapsed_time)


if __name__ == "__main__":
    main()
