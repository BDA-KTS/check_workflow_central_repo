import os
import csv
from pathlib import Path
from licensename import from_text

repo_hash= os.environ.get('REPO_HASH')
testpath = Path("testee")
path = Path("central.report")


def get_needed_files():
    return {"citation.cff","license","readme.md"}


required_files = get_needed_files()

def check_and_write_license():
    license_name = from_text(testee/license)
    with open(central/free_licenses.csv) as csv:



missing_files = [fname for fname in required_files if not (pathway / fname).is_file()]

with open ("./Report/Report.md","w") as f:
    f.write("#Report Test \n ##Fehlende Dateien:")
f.close()
with open ("./Report/Report.md","a") as f:
    for fname in missing_files:
        f.write(fname)
    if len(missing_files) == 0:
        f.write("All required files are present.")

if "license" not in missing_files:
    check_and_write_license()
