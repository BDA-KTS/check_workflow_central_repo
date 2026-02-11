import os
import csv
import json
from pathlib import Path
from licensename import from_text

# Client Payload: {'readme': 'README.md', 'repo_hash': '1ddf824b50bc6d159d1e1d6037d17419f32c2694', 'repository_full_name': 'owner/repo'}
event_path = os.environ.get("GITHUB_EVENT_PATH")
with open(event_path, "r") as payload:
    event_data = json.load(payload)

full_name = (
    event_data
    .get("client_payload", {})
    .get("repository_full_name")
)
readme=(
    event_data
    .get("client_payload", {})
    .get("readme")
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
    required_in_repo = {"citation.cff", "LICENSE", "postBuild"}
    required_for_binder = set()
    suffixes = {s.casefold() for s in suffixes}

    if ".py" in suffixes:
        required_for_binder |= {"requirements.txt"}

    if ".r" in suffixes:
        required_for_binder |= {"install.r", "runtime.txt"}
    print(required_for_binder)
    return required_in_repo, required_for_binder


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


def check_readme(readme):
    necessary_subtitles=["Description","Use Cases","Input Data","Output Data","Hardware Requirements","Environment Setup","How to Use","Technical Details","Contact Details"]
    titles = []
    subtitles = []
    return_string = ""

    with open(readme, encoding="utf-8") as f:
        for line in f:
            if line.startswith("# "):
                titles.append(line[2:].strip())
            elif line.startswith("## "):
                subtitles.append(line[3:].strip())
    if len(titles) ==1:
        return_string += "\n Found one title: Accepted\n"
    elif len(titles) < 1:
        return_string += "\n Found no titles: Denied\n"
    else:
        return_string += f"\n Found to many titles: Anzahl: {len(titles)} \n"
    missing = set(necessary_subtitles) - set(subtitles)

    if not missing:
        return_string+="All necessary subtitles exists \n"
    else:
        for s in missing:
            return_string+=f"Missing subtitle: {s} \n"

    return return_string

# existing_files = {p.name.lower() for p in testpath.iterdir() if p.is_file()}

def check_and_write_required_files(repo_files, binder_files):
    return_string = ""

    # --- Repo-Dateien direkt in testpath ---
    found_repo_files = {
        p.name
        for p in testpath.iterdir()
        if p.is_file()
    }

    missing_repo = repo_files - found_repo_files

    if missing_repo:
        return_string += "Repo – es fehlen:\n"
        return_string += "\n".join(f"- {f}" for f in sorted(missing_repo)) + "\n"
    else:
        return_string += "Repo – everything found\n"

    # --- Binder-Dateien: mehrere mögliche Orte ---
    binder_dirs = {
        testpath,
        testpath / "binder",
        testpath / "./binder",
    }

    found_binder = set()

    for fname in binder_files:
        for base in binder_dirs:
            if (base / fname).is_file():
                found_binder.add(fname)
                break  # einmal gefunden reicht

    missing_binder = binder_files - found_binder

    if missing_binder:
        return_string += "Binder – es fehlen:\n"
        return_string += "\n".join(f"- {b}" for b in sorted(missing_binder)) + "\n"
    else:
        return_string += "Binder – everything found\n"

    return return_string

make_title()
file_suffix = get_file_extensions(testpath)
required_repo, required_binder = get_needed_files(file_suffix)

with open(report_file, "a") as f:
    f.write("## Checking required files\n")
    f.write(check_and_write_required_files(required_repo, required_binder))
    #    for fname in required_files:
    #        if fname.lower() not in existing_files:
    #            f.write(f"- {fname} is not present\n")
    #        else:
    #            f.write(f"- {fname} is present\n")
    if "license" in existing_files:
        f.write("\n ## Checking License: \n ")
        f.write(check_and_write_license())
    f.write("## Checking Readme \n ")
    f.write(check_readme(readme))
