import os
import json
from pathlib import Path
from typing import Set, List, Counter
from datetime import datetime
import time
from config import Settings

from util.review_functions import *
from util.extract_info import *
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


badge_reuse = ["![Reusability](https://img.shields.io/badge/Reusable-green)", "![Reusability](https://img.shields.io/badge/Reusability-partially%20reusable-yellow)", "![Reusability](https://img.shields.io/badge/Reusability-not%20reusable-orange)"]
badge_trans = ["![Transparency](https://img.shields.io/badge/full%20documentation-green)", "![Transparency](https://img.shields.io/badge/inconsistent%20formatting-yellow)", "![Transparency](https://img.shields.io/badge/incomplete%20documentation-orange)"]
badge_repro = ["![Reproducibility](https://img.shields.io/badge/single%20click%20reproducible-green)", "![Reproducibility](https://img.shields.io/badge/partially%20reproducible%20code-yellow)", "![Reproducibility](https://img.shields.io/badge/not%20single%20click%20reproducible-orange)"]


def summary(checklists, f):
    f.write("## Summary \n")
    f.write("| Category | Level attained | Guidelines reference | \n")
    f.write("| --- | --- | \n")
    # Reusability and attribution    
    if checklists['license']['ifpassed'] and 'citation' in checklists['files']['messages']:
        f.write(f"| Reusability and attribution | {badge_reuse[0]} | | \n")
    elif checklists['license']['warnings']:
        f.write(f"| Reusability and attribution | {badge_reuse[1]} |  multiple license files found, [for more ...](#license) | \n")
    else:
        f.write(f"| Reusability and attribution | {badge_reuse[2]} |")   
        if checklists['license']['errors'] and 'citation' not in checklists['files']['messages']:
            f.write(f"| No or invalid license, [for more ...](#license) <br> Citation file not found [for more ...](#documentation) | \n")
        if checklists['license']['errors'] and 'citation' in checklists['files']['messages']:
            f.write(f"| No or invalid license, [for more ...](#license) | \n")
        if not checklists['license']['errors'] and 'citation' not in checklists['files']['messages']:
            f.write(f"| Citation file not found [for more ...](#documentation) | \n")
    # transparency
    if checklists['readme']['ifpassed'] and checklists['files']['ifpassed']:
        f.write(f"| Transparency | {badge_trans[0]} | | \n")
    elif checklists['readme']['warnings'] or checklists['files']['warnings']:
        f.write(f"| Transparency | {badge_trans[1]} | ")
        if checklists['readme']['warnings'] and checklists['files']['warnings']:
            f.write(f" Duplicate files, [for more ...](#documentation) <br> README sections duplicates for formating issue, [for more ...](#readme) | \n")
        if checklists['readme']['warnings'] and not checklists['files']['warnings']:
            f.write(f" README sections duplicates for formating issue, [for more ...](#readme) | \n")
        if not checklists['readme']['warnings'] and checklists['files']['warnings']:
            f.write(f" Duplicate files, [for more ...](#documentation) | \n")
    else:
        f.write(f"| Transparency | {badge_trans[2]} | ")
        if checklists['readme']['errors'] and checklists['files']['errors']:
            f.write(f" Missing mandatory files, [for more ...](#documentation) <br> README missing mandatory sections, [for more ...](#readme) | \n")
        if checklists['readme']['errors'] and not checklists['files']['errors']:
            f.write(f" README missing mandatory sections, [for more ...](#readme) | \n")
        if not checklists['readme']['warnings'] and checklists['files']['warnings']:
            f.write(f" Missing mandatory files, [for more ...](#documentation) | \n")
        #computational reproduciiblity
        if checklists['repo2docker']['ifpassed'] and checklists['language']['ifpassed']:
            f.write(f"| Computational reproducibility | {badge_repro[0]} | | \n")
        elif checklists['repo2docker']['warnings'] or checklists['language']['warnings']:
            f.write(f"| Computational reproducibility | {badge_repro[1]} | ")
            if checklists['repo2docker']['warnings'] and checklists['language']['warnings']:
                f.write(f" Binder files missing, [for more ...](#documentation) <br> programming language version not specified, [for more ...](#programming-language)  | \n")
            if checklists['repo2docker']['warnings'] and not checklists['language']['warnings']:
                f.write(f" Repo2docker failed, [for more ...](#repo2docker) | \n")
            if not checklists['repo2docker']['warnings'] and checklists['language']['warnings']:
                f.write(f" programming language version not specified, [for more ...](#programming-language) | \n")
        elif checklists['repo2docker']['errors']:
            f.write(f"| Computational reproducibility | {badge_repro[2]} |  Repo2docker failed, [for more ...](#repo2docker)  | \n")
        
        if checklists['sustainability']['ifpassed']:
            f.write("| Resource consumption | | \n")
            for message in checklists['sustainability']['messages']:
                key, value = message.split(':')
                f.write(f"| | {key} | {value} | \n")
        else:
            f.write("|  | Resource consumption could not be computed due to Repo2docker failure | | \n")
        f.write("\n\n")


def write_report(checklists, report_file, owner, repo, elapsed_time):
    with open(report_file, "w", encoding="utf-8") as f:
        total_seconds = int(elapsed_time.total_seconds())
        minutes, seconds = divmod(total_seconds, 60)
        f.write(f"# Report: [{owner} / {repo}](https://github.com/{owner}/{repo})\n\n" f"<small>created on {time.strftime('%Y-%m-%d %H:%M:%S')}, \n Review time: {minutes}:{seconds:02d} (min/sec)\n\n")
        
        summary(checklists, f)
             
        
        f.write("# Detailed Report \n\n")
        
        label = [" ✅ **Information:**", " ⚠️ **Warnings:**", " ⛔ **Errors:**"]
        
        # Reusability and attribution
        f.write("## Reusability and attribution \n\n")
        f.write("The method is reusable if supported by a valid open-source licence and has citation metadata provided in supported CITATION.cff file. \n")
        f.write("### License \n\n")
        for item in checklists['license']['errors']:
            f.write(f"- {label[2]} {item} (to fix this issue, please consult the [Openness criteria in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/README.md#openness-criteria)) \n")
        for item in checklists['license']['warnings']:
            f.write(f"- {label[1]} {item} (to fix this issue, please consult the [Openness criteria in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/README.md#openness-criteria)) \n")
        for item in checklists['license']['messages']:
            f.write(f"- {label[0]} {item} \n")
        f.write('\n\n')
        f.write("### Citation \n\n")
        if 'citation' in checklists['files']['messages']:
            f.write("Citation.cff file accepted \n")
        else:
            f.write("No valid Citation.cff file found, please consult the [documentation quality criteria in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/README.md#documentation-quality-criteria) \n")
        
        #Transparency
        f.write("## Transparency \n\n")
        f.write("The method is fully transparent when it has all required documents and has README as per template. \n")
        f.write(f"### Documentation \n\n")
        for item in checklists['files']['errors']:
            if 'license' not in item or 'citation' not in item:
                f.write(f"- {label[2]} {item}, please consult the [documentation quality criteria in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/README.md#documentation-quality-criteria) \n")
        for item in checklists['files']['warnings']:
            if 'license' not in item or 'citation' not in item:
                f.write(f"- {label[1]} {item}, please consult the [documentation quality criteria in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/README.md#documentation-quality-criteria) \n")
        for item in checklists['files']['messages']:
            if 'license' not in item or 'citation' not in item:
                f.write(f"- {label[0]} {item}, please consult the [documentation quality criteria in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/README.md#documentation-quality-criteria) \n")
        f.write('\n\n')
        # README template
        f.write(f"### README  \n\n")
        for item in checklists['readme']['errors']:
            f.write(f"- {label[2]} {item}, please consult the [README template in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md?plain=1) \n")
        for item in checklists['readme']['warnings']:
            f.write(f"- {label[1]} {item}, please consult the [README template in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md?plain=1) \n")
        for item in checklists['readme']['messages']:
            f.write(f"- {label[0]} {item}, please consult the [README template in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/method/template.md?plain=1) \n")
        f.write('\n\n')
        # Computational reproducibility
        f.write("## Computational reproducibility \n\n")
        f.write("Computational reproducibility is supported if repo2docker successfully builds the execution environment and the programming language version is explicitly specified in the repository’s configuration files. \n")
        # Repo2docker
        f.write(f"### Repo2docker \n\n")
        for item in checklists['repo2docker']['errors']:
            f.write(f"- {label[2]} {item}, please consult the [binder environment in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/README.md#binder-environment) \n")
        for item in checklists['repo2docker']['warnings']:
            f.write(f"- {label[1]} {item}, please consult the [binder environment in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/README.md#binder-environment) \n")
        for item in checklists['repo2docker']['messages']:
            f.write(f"- {label[0]} {item}, please consult the [binder environment in guidelines](https://github.com/GESIS-Methods-Hub/guidelines/blob/v0/README.md#binder-environment) \n")
        f.write('\n\n')
        # programming language
        f.write(f"### Programming Language \n\n")
        for item in checklists['language']['errors']:
            f.write(f"- {label[2]} {item} \n")
        for item in checklists['language']['warnings']:
            f.write(f"- {label[1]} {item} \n")
        for item in checklists['language']['messages']:
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
    root_files, extended_files=get_files(TEST_PATH, BINDER_DIRS)

    # License check
    #if 'license' in root_files or 'license' in extended_files:
    checklists['license'] = license_check(TEST_PATH, FREE_LICENSES)
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
        checklists['readme'] = convert_readme_ipynb(readme_path, NECESSARY_SUBTITLES)
    elif readme_path.suffix == ".md":
        checklists['readme'] = convert_readme_md(readme_path, NECESSARY_SUBTITLES)
    elif readme_path.suffix == ".qmd":
        checklists['readme'] = convert_readme_md(readme_path, NECESSARY_SUBTITLES)
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
