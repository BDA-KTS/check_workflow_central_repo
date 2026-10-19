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

from util.reporting_functions.py import *

import resource


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









    

    


    




def load_ml_artifacts():
    model = joblib.load(ML_PATH/"model.joblib")
    vectorizer = joblib.load(ML_PATH/ "vectorizer.joblib")
    mlb = joblib.load(ML_PATH / "mlb.joblib")
    return model, vectorizer, mlb

def predict_labels_with_probability(path: Path ,threshold: float = 0.5):
    result = {'ifpassed': False, 'messages': [], 'warnings': [], 'errors': []}
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
        result['messages'] = [f"Predicted labels: {', '.join(predicted) if predicted else 'none'}", f"Probability: {round(probability_map[predicted[0]] * 100, 2)}%"]
    else:
        result['messages'] = ["No labels predicted with probability above threshold."]
    result['ifpassed'] = True
    return result

#def summary(checklists):
    #if any(not checklist.passed for checklist in checklists):
    #    passed = False
    #    errors.append("Major Flaws, Error in at least one Check")
    #    error_labels.append("Critical")
    #elif  any(checklist.warnings for checklist in checklists) and passed:
    #    warnings.append("Passed but with warnings")
    #    error_labels.append("Warning")
    #else:
    #    messages.append("Passed perfectly")
    #return CheckResult("Summary", passed, messages, warnings, errors, [],[],error_labels)



def write_report(checklists, report_file, owner, repo, elapsed_time):
    with open(report_file, "w", encoding="utf-8") as f:
        total_seconds = int(elapsed_time.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        f.write(f"# Report: [{owner} / {repo}](https://github.com/{owner}/{repo})\n\n" f"<small>created on {time.strftime('%Y-%m-%d %H:%M:%S')}, \n Review time: {minutes}:{seconds:02d} (min/sec)\n\n")

        #f.write("[![Report Creator](https://github.com/BDA-KTS/check_workflow_central_repo/actions/workflows/test_workflow.yml/badge.svg)](https://github.com/BDA-KTS/check_workflow_central_repo/actions/workflows/test_workflow.yml)\n\n")

        #[![Report Creator](https://github.com/BDA-KTS/check_workflow_central_repo/actions/workflows/test_workflow.yml/badge.svg)](https://github.com/BDA-KTS/check_workflow_central_repo/actions/workflows/test_workflow.yml)
        #f.write("## Report generated at {}\n\n".format(time.strftime("%Y-%m-%d %H:%M:%S")))
        #f.write(f"## Link to the repository: [GitHub Repository](https://github.com/{owner}/{repo})\n\n")
        
        
        #f.write(f"### Working Environment:", f"{env}", f"{required_binder}", f"{root_files}", f"{extended_files}")

        badge_reuse = ["![Reusability](https://img.shields.io/badge/Reusable-green)", "![Reusability](https://img.shields.io/badge/Reusability-partially%20reusable-yellow)", "![Reusability](https://img.shields.io/badge/Reusability-not%20reusable-orange)"]
        badge_trans = ["![Transparency](https://img.shields.io/badge/full%20documentation-green)", "![Transparency](https://img.shields.io/badge/inconsistent%20formatting-yellow)", "![Transparency](https://img.shields.io/badge/incomplete%20documentation-orange)"]
        badge_repro = ["![Reproducibility](https://img.shields.io/badge/single%20click%20reproducible-green)", "![Reproducibility](https://img.shields.io/badge/partially%20reproducible%20code-yellow)", "![Reproducibility](https://img.shields.io/badge/not%20single%20click%20reproducible-orange)"]
        
        #others = ["![Python](https://img.shields.io/badge/Python-supported-yellow)", "![R](https://img.shields.io/badge/R-supported-yellow)", "![Python](https://img.shields.io/badge/Python-supported-green)", "![R](https://img.shields.io/badge/R-supported-green)","![Python](https://img.shields.io/badge/Python-supported-orange)", "![R](https://img.shields.io/badge/R-supported-orange)"]

        f.write("## Summary \n")
        f.write("| Category | Level attained | \n")
        f.write("| --- | --- | \n")
        if checklists['license']['ifpassed']:
             f.write(f"| Reusability and attribution | {badge_reuse[0]} | \n")
        elif checklists['license']['warnings'] or 'citation' not in checklists['files']['messages']:
            f.write(f"| Reusability and attribution | {badge_reuse[1]} | \n")
        else:
            f.write(f"| Reusability and attribution | {badge_reuse[2]} |\n")

        if checklists['readme']['ifpassed'] and checklists['files']['ifpassed']:
            f.write(f"| Transparency | {badge_trans[0]} | \n")
        elif checklists['readme']['warnings'] or checklists['files']['warnings']:
            f.write(f"| Transparency | {badge_trans[1]} | \n")
        else:
            f.write(f"| Transparency | {badge_trans[2]} | \n")
        
        if checklists['repo2docker']['ifpassed'] and checklists['language']['ifpassed']:
            f.write(f"| Computational reproducibility | {badge_repro[0]} | \n")
        elif checklists['repo2docker']['warnings'] or checklists['language']['warnings']:
            f.write(f"| Computational reproducibility | {badge_repro[1]} | \n")
        else:
            f.write(f"| Computational reproducibility | {badge_repro[2]} | \n")
        
        if checklists['sustainability']['ifpassed']:
            f.write("| Resource consumption | | \n")
            for message in checklists['sustainability']['messages']:
                f.write(f"| | {message} | \n")
        else:
            f.write("|  | Resource consumption could not be computed due to Repo2docker failure | \n")
        f.write("\n\n")
        
        f.write("## Detailed Report \n\n")
        
        label = [" ✅ **Information:**", " ⚠️ **Warnings:**", " ⛔ **Errors:**"]
        
        # License
        f.write("### License \n\n")
        for item in checklists['license']['errors']:
            f.write(f"- {label[2]} {item} \n")
        for item in checklists['license']['warnings']:
            f.write(f"- {label[1]} {item} \n")
        for item in checklists['license']['messages']:
            f.write(f"- {label[0]} {item} \n")
        f.write('\n\n')
        
        # Programming language
        f.write(f"### Programming Language \n\n")
        for item in checklists['language']['errors']:
            f.write(f"- {label[2]} {item} \n")
        for item in checklists['language']['warnings']:
            f.write(f"- {label[1]} {item} \n")
        for item in checklists['language']['messages']:
            f.write(f"- {label[0]} {item} \n")
        f.write('\n\n')

        # Documentation
        f.write(f"### Documentation \n\n")
        for item in checklists['files']['errors']:
            f.write(f"- {label[2]} {item} \n")
        for item in checklists['files']['warnings']:
            f.write(f"- {label[1]} {item} \n")
        for item in checklists['files']['messages']:
            f.write(f"- {label[0]} {item} \n")
        f.write('\n\n')

        # README template
        f.write(f"### README  \n\n")
        for item in checklists['readme']['errors']:
            f.write(f"- {label[2]} {item} \n")
        for item in checklists['readme']['warnings']:
            f.write(f"- {label[1]} {item} \n")
        for item in checklists['readme']['messages']:
            f.write(f"- {label[0]} {item} \n")
        f.write('\n\n')

        # Repo2docker
        f.write(f"### Repo2docker \n\n")
        for item in checklists['repo2docker']['errors']:
            f.write(f"- {label[2]} {item} \n")
        for item in checklists['repo2docker']['warnings']:
            f.write(f"- {label[1]} {item} \n")
        for item in checklists['repo2docker']['messages']:
            f.write(f"- {label[0]} {item} \n")
        f.write('\n\n')
        
        
def write_macro(checklists, report_file, owner, repo, elapsed_time):
    total_seconds = int(elapsed_time.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    times = f"{minutes}:{seconds:02d}"

    #with open(report_file, "w", encoding="utf-8") as f:
    #    for name, checklist in checklists.items():
    #        entry = {"owner": owner, "repo": repo, "name": name, "passed": checklist.ifpassed, "warnings": checklist.warnings, "errors": checklist.errors, "Workflow Duration": times, }
    #        f.write(json.dumps(entry) + "\n")

def main():
    time_start = datetime.now()
    #checklists: list[CheckResult] = []
    checklists = {}
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
    #if 'license' in root_files or 'license' in extended_files:
    checklists['license'] = license_check()
    #else:
    #    checklists['license'] = {'ifpassed': False, 'messages': [], 'warnings': [], 'errors': ["License Check failed, no license file found"]}
    # Working language
    checklists['language'] = get_language_version(TEST_PATH)
    # Binder environment
    checklists['files'] = check_for_files(REPO_REQUIREMENTS,required_binder,root_files,extended_files)
     # Simulate Repo2Docker 2
    #if "binder" in checklists['files'].messages:
    checklists['repo2docker'] = repo2dockertest()
    #else:
    #checklists['repo2docker'] = {'ifpassed': False, 'messages': [], 'warnings': [], 'messages': ["Binder test skipped: Binder files not found or not valid"]}

    
    # Readme check
    readme_path = TEST_PATH / readme_name
    if readme_path.suffix == ".ipynb":
        checklists['readme'] = convert_readme_ipynb(readme_path)
    elif readme_path.suffix == ".md":
        checklists['readme'] = convert_readme_md(readme_path)
    elif readme_path.suffix == ".qmd":
        checklists['readme'] = convert_readme_md(readme_path)
    else:
        checklists['readme'] = {'ifpassed': False, 'messages': [], 'warnings': [], 'errors': ["Readme check failed: Format not yet supported"]}

    #sutainability
    checklists['sustainability'] = repo2dockertest_sustainability()

    #checklists.insert(0,summary(checklists))
    #checklists.append(predict_labels_with_probability(readme_path))
    time_end = datetime.now()
    elapsed_time = time_end - time_start
    # Write the report
    write_report(checklists, report_file,owner,repo, elapsed_time)
    write_macro(checklists, aggregated, owner, repo, elapsed_time)


if __name__ == "__main__":
    main()
