from pathlib import Path

pathway = Path("./Testproject")
required_files = ["LICENSE", "README.md", "CITATION.cff", ""]
missing_files = [fname for fname in required_files if not (pathway / fname).is_file()]
for fname in missing_files:
    print(fname)
if len(missing_files) == 0:
    print("All required files are present.")
def missingfiles(required_files):
    for fname in required_files:

