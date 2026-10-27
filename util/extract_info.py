import html
import os
import json
import re
import sys
import nbformat
from pathlib import Path
import time
from typing import Set, List, Counter
from jsons.Json_PreCooking import strip_markdown

from config import Settings
TEST_PATH = Settings.TEST_PATH
BINDER_DIRS = Settings.BINDER_DIRS

def get_file_extensions() -> Set[str]:
    #Get all file extensions in the given directory recursively.
    return {TEST_PATH.suffix for TEST_PATH in TEST_PATH.rglob("*") if TEST_PATH.is_file()}

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
    if '.yml' in suffixes_lower:
        required_for_binder.add('environment.yml')
    return required_for_binder

def get_files():
    root_files =[]
    extended_files=[]
    for binder_directory in BINDER_DIRS:
        if not (TEST_PATH / binder_directory).is_dir():
            continue
        for f in (TEST_PATH/ binder_directory).iterdir():
            if f.parent == TEST_PATH:
                root_files.append(f.name)
            extended_files.append(f.name)
    return root_files , extended_files


def convert_readme_md(readme_path: Path, NECESSARY_SUBTITLES) :
    """Analyze the README for required titles and subtitles."""
    result = {'ifpassed': False, 'messages': [], 'warnings': [], 'errors': []}

    if not readme_path.exists():
        result['errors'].append(f"Readme check failed: {readme_path} not found")
        return result
    h1 = []
    h2 = []
    try:
        with open(readme_path, encoding="utf-8") as f:
            content = f.read()
            h1_headings = re.findall(r"(?m)^#(?!#)\s+.*$", content)
            h1_headings = [h1[2:].strip() for h1 in h1_headings]
            h2_headings = re.findall(r"(?m)^\s*##(?!#)\s+.*$", content)
            h2_headings = [h2[3:].strip() for h2 in h2_headings]
            h3_plus_headings = re.findall(r"(?m)^\s*#{3,6}\s+.*$", content)
            if h1_headings: #line.startswith("# "):
                #titles.append(line[2:].strip())
                h1.append(h1_headings)
            elif h2_headings:
                h2.append(h2_headings)
            if h3_plus_headings:
                result["errors"].append(h3_plus_headings)
    except Exception as e:
        result['errors'].append(f"Readme check failed: Error reading file ({e})")
        return result
    return check_readme(h1, h2, result, NECESSARY_SUBTITLES)

def convert_readme_ipynb(readme_path: Path, NECESSARY_SUBTITLES):
    result = {'ifpassed': False, 'messages': [], 'warnings': [], 'errors':[]}

    if not readme_path.exists():
        result['errors'].append(f"Readme check failed: {readme_path} not found")
        return result
    try:
        nb=nbformat.read(readme_path, as_version=4)
    except Exception as e:
        result['errors'].append(f"Readme check failed: Error reading file ({e})")
        return result
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
    return check_readme(titles, subtitles, result, NECESSARY_SUBTITLES)

def check_readme(titles,subtitles, result, NECESSARY_SUBTITLES):
    if len(titles) < 1:
        result['ifpassed'] = False
        result['errors'].append("Method title not defined.")
    elif len(titles) == 1:
        result['messages'].append("Method title accepted.")
    else:
        result['ifpassed'] = False
        result['errors'].append(f"Method has {len(titles)}, i.e., more than 1 title cases.")
    if len(subtitles) < 1:
        result['ifpassed'] = False
        result['errors'].append("Method README has no section headings defined.")
    missing = set(NECESSARY_SUBTITLES) - set(subtitles)
    for subtitle in subtitles:
        result['messages'].append(f"{subtitle}")
    for item in missing:
        result['ifpassed'] = False
        result['errors'].append(f"Method README has {item} section heading missing, {NECESSARY_SUBTITLES[item]}")

    if len(subtitles) != len(set(subtitles)):
        result['warnings'].append("Method README has duplicate section headings.")
    
    return result


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

