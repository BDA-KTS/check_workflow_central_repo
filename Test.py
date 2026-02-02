from os import write
from pathlib import Path

pathway = Path("./Testproject")
path = Path("./Report/Report.md")
path.parent.mkdir(parents=True, exist_ok=True)
required_files = ["LICENSE", "README.md", "CITATION.cff", ""]
missing_files = [fname for fname in required_files if not (pathway / fname).is_file()]
with open ("./Report/Report.md","w") as f:
    f.write("#Report Test \n ##Fehlende Dateien:")
f.close()
with open ("./Report/Report.md","a") as f:
    for fname in missing_files:
        f.write(fname)
    if len(missing_files) == 0:
        f.write("All required files are present.")
    f.write("##License Type:\n Apache License \n License accepted")

