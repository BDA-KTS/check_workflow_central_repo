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
from jsons.Json_PreCooking import strip_markdown

with open(os.environ["GITHUB_EVENT_PATH"], "r", encoding="utf-8") as payload_file:
    payload = json.load(payload_file)

event_type = payload.get("action")
client_payload = payload.get("client_payload", {})
print(event_type)
if event_type == "report_creator":
    from config import Settings
elif event_type == "report_creator_tester":
    from config import PublicSettings


# Gets the configuration from the config.py file
TEST_PATH = Settings.TEST_PATH
CENTRAL_PATH = Settings.CENTRAL_PATH
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
    readme_name = payload.get("readme") or "README.md"
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
    print(f"Root files are: {root_files}")
    print(f"Extended files are: {extended_files}")
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
    return CheckResult("File Check",passed=passed,messages=messages,warnings=warnings,errors=errors,statuses=statuses,warning_labels=warning_labels,error_labels=error_labels)

def check_for_formal_files(repo_requirements,root_files):
    passed=False
    messages=[]
    warnings=[]
    errors=[]
    statuses=[]
    warning_labels=[]
    error_labels=[]
    repo_sorted = sorted([f.casefold().split(".")[0] for f in root_files])
    required = {r.casefold() for r in repo_requirements}

    repo_sorted= [f for f in repo_sorted if f in required]

    for f in repo_sorted:
        messages.append(f"Found required file: {f}")
    if "license" in repo_sorted:
        statuses.append("license")
    counter=Counter(repo_sorted)
    duplicates=[f for f, count in counter.items() if count > 1]
    if duplicates:
        for f in duplicates:
            warnings.append(f"Warning: {f} is duplicated.")
            warning_labels.append(f"{f}")
    missing = required - set(repo_sorted)
    if missing:
        for item in missing:
            errors.append(f"Missing required files: {item}")
            errors.append(f"For further information see: {REPO_REQUIREMENTS[item]}")
            error_labels.append(f"{item}")
        messages.append("Missing required files")
    else:
        passed=True
    return CheckResult("Formal Files", passed, messages, warnings, errors, statuses,warning_labels,error_labels)


def check_for_binder_files(required_binder,extended_files):
    passed=False
    messages=[]
    warnings=[]
    errors=[]
    statuses=[]
    warning_labels=[]
    error_labels=[]
    found_files = extended_files
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
    return CheckResult("Binder Files", passed, messages, warnings, errors, statuses, warning_labels, error_labels)

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
        errors.append(" Too many licenses found, try choosing just one ")
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

    return CheckResult("License Check",passed,messages,warnings,errors,statuses,warning_labels,error_labels)


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
        message.append(f"Found too many titles: Count: {len(titles)}")
        error_labels.append("Multiple Titles")
    if len(subtitles) < 1:
        passed=False
        errors.append("No subtitle found but one is required.")
        error_labels.append("Subtitles")
    missing = set(NECESSARY_SUBTITLES) - set(subtitles)
    for subtitle in subtitles:
        message.append(f"Found subtitle: {subtitle}")
    for item in missing:
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
    vectorizer = joblib.load(ML_PATH/ "models/vectorizer.joblib")
    mlb = joblib.load(ML_PATH / "models/mlb.joblib")
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
        name="Taxonomie",
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
        f.write(f"# Report for {owner} of {repo}\n\n")
        f.write("## Report generated at {}\n\n".format(time.strftime("%Y-%m-%d %H:%M:%S")))
        f.write(f"## Link to the repository: [GitHub Repository](https://github.com/{owner}/{repo})")
        for checklist in checklists:
            f.write("## {}\n\n".format(checklist.name))
            if checklist.errors:
                f.write("### Errors ⛔ \n\n")
                f.write("<br>".join(checklist.errors))
                f.write("\n\n")
            if checklist.warnings:
                f.write("### Warnings ⚠️ \n\n")
                f.write("<br>".join(checklist.warnings))
                f.write("\n\n")
            if checklist.messages:
                f.write("### Information ✅ \n\n")
                f.write("<br>".join(checklist.messages))
                f.write("\n\n")
        total_seconds = int(elapsed_time.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        f.write("#### Duration \n\n")
        f.write(f"Time to complete {minutes} min {seconds} sec\n\n")

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
    report_dir = REPORT_PATH / owner
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"{repo}.md"

    aggregated_dir = AGGREGATION_PATH / owner
    aggregated_dir.mkdir(parents=True, exist_ok=True)
    aggregated = aggregated_dir / f"{repo}.jsonl"
    # File presence checks
    suffixes = get_file_extensions(TEST_PATH)
    required_binder = get_needed_files(suffixes)
    root_files, extended_files=get_files(TEST_PATH)
    checklists.append(check_for_files(REPO_REQUIREMENTS,required_binder,root_files,extended_files))

    # License check
    if any("license" in result.statuses for result in checklists):
        checklists.append(license_check())
    else:
        checklists.append(CheckResult("License Check",False,[],[],["License Check failed, no license file found"],[],[],["No license"]))
    # Readme check
    readme_path = TEST_PATH / readme_name
    if readme_path.suffix == ".ipynb":
        checklists.append(convert_readme_ipynb(readme_path))
    elif readme_path.suffix == ".md":
        checklists.append(convert_readme_md(readme_path))
    elif readme_path.suffix == ".qmd":
        checklists.append(convert_readme_md(readme_path))
    else:
        checklists.append(CheckResult("Readme Check",False,[],[],["Readme check failed: Format not yet supported"],[],[],[]))

    # Simulate Repo2Docker 2
    if any("binder" in result.statuses for result in checklists):
        checklists.append(repo2dockertest())
    else:
        checklists.append(CheckResult("Binder Test",False,[],[],["Binder test skipped: Binder files not found or not valid"],[],[],[]))
    checklists.insert(0,summary(checklists))
    checklists.append(predict_labels_with_probability(readme_path))
    time_end = datetime.now()
    elapsed_time = time_end - time_start
    # Write the report
    write_report(checklists, report_file,owner,repo, elapsed_time)
    write_macro(checklists, aggregated, owner, repo, elapsed_time)


if __name__ == "__main__":
    main()
