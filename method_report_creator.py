import os
import csv
import json
from pathlib import Path
from licensename import from_text

#Client Payload: {'readme': 'README.md', 'repo_hash': '1ddf824b50bc6d159d1e1d6037d17419f32c2694', 'repository_url': 'owner/repo'}
event_path = os.environ.get("GITHUB_EVENT_PATH")
with open(event_path, "r") as payload:
    event_data = json.load(payload)

full_name = (
    event_data
    .get("client_payload", {})
    .get("repository_url")
)


owner, repo = full_name.split("/", 1)

report_file = Path("central", "report", owner, f"{repo}.md")
testpath = Path("testee")



def make_title():
    with open(report_file, "w") as fx:
        fx.write(f"# Report for {owner} of {repo} \n\n")

def get_file_extensions(directory_path):
    extensions = set()
    for path in Path(directory_path).rglob("*"):
        if path.is_file():
            extensions.add(path.suffix)
    return extensions

def get_needed_files(suffixes):
    required = {"citation.cff", "LICENSE"}

    suffixes = {s.casefold() for s in suffixes}

    if ".py" in suffixes:
        required |= {"requirements.txt", "postBuild"}

    if ".r" in suffixes:
        required |= {"install.r", "runtime.txt", "postBuild"}
    print(required)
    return required

def check_and_write_license():
    license_text = (testpath / "LICENSE").read_text(encoding="utf-8")
    license_name = from_text(license_text)
    print(f"\n{license_name} \n")
    with open(Path("central") / "free_licenses.csv") as csvf:
        reader = csv.reader(csvf)
        licenses = {row[0] for row in reader if row}
        if license_name in licenses:
            return f"License accepted: Found {license_name}\n"
        else:
            return f"License denied: Found {license_name}\n"

make_title()
file_suffix = get_file_extensions(testpath)
required_files = get_needed_files(file_suffix)

# Get all files in testpath (case-insensitive names)
existing_files = {p.name.lower() for p in testpath.iterdir() if p.is_file()}

# Check which required files are missing
#missing_files = []
#for fname in required_files:
#    if fname.lower() not in existing_files:
#        missing_files.append(fname)


with open (report_file,"a") as f:
    f.write("## Checking required files\n")
    for fname in required_files:
        if fname.lower() not in existing_files:
            f.write(f"- {fname} is not present\n")
        else:
            f.write(f"- {fname} is present\n")
 #    for fname in missing_files:
#       f.write(f"- Missing: {fname}\n")
    if all(fname.lower() in existing_files for fname in required_files):
        f.write("All required files are present.\n")
    if "license" in existing_files:
        f.write("\n ##Checking License: \n")
        f.write(check_and_write_license())
