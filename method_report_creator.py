import os
import csv
import json
from pathlib import Path
from licensename import from_text

event_path = os.environ.get("GITHUB_EVENT_PATH")
with open(event_path, "r") as payload:
    event_data = json.load(payload)
    payload.close()
full_name = event_data.get("repository_url")


owner, repo = full_name.split("/", 1)

report_file = Path("central", "report", owner, f"{repo}.md")
testpath = Path("testee")
path = Path("central.report")



def make_title():
    splitter=full_name("/")
    with open ("report_path","w") as fx:
        fx.write(f"#Report of  {splitter[0]}")
    fx.close()

def get_file_extensions(directory_path):
    extensions = set()

    # Loop through all files in the given directory
    for filename in os.listdir(directory_path):
        if os.path.isfile(os.path.join(directory_path, filename)):
            # Split the filename to get the extension
            ext = os.path.splitext(filename)[1]
            extensions.add(ext)

    return extensions

def get_needed_files(suffix):
    required={"citation.cff","license"}
    if ".py" in suffix:
        required.add("requirements.txt")
        required.add("postBuild")
    if ".R" in suffix:
        required.add("install.R")
        required.add("runtime.txt")
        required.add("postBuild")
    return required

def check_and_write_license(file):
    license_name = from_text(testee/license)
    with open(central/free_licenses.csv) as csvf:
        reader = csv.reader(csvf)
        if license_name in reader:
            file.write(f"License accepted: Found {license_name}")
        else:
            file.write(f"License denied: Found {license_name}")
        #TO DO Match read input with license_name and return either license_name, "accepted" or license_name, "Denied"

make_title()
file_suffix = get_file_extensions(testpath)
required_files = get_needed_files(file_suffix)

missing_files = [fname for fname in required_files if not (testpath / fname).is_file()]


with open (report_file,"a") as f:
    for fname in missing_files:
        f.write(fname)
    if len(missing_files) == 0:
        f.write("All required files are present.")

if "license" not in missing_files:
    check_and_write_license(f)
