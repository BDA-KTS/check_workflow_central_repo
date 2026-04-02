#!/usr/bin/env python3

import json
import re
import html
from pathlib import Path
from urllib.parse import quote

import requests


METHODS_PATH = Path("methods.json")
TUTORIALS_PATH = Path("tutorials.json")
OUTPUT_PATH = Path("training_data.jsonl")


def load_entries(methods_path: Path, tutorials_path: Path):
    with methods_path.open("r", encoding="utf-8") as f:
        methods_data = json.load(f)

    with tutorials_path.open("r", encoding="utf-8") as f:
        tutorials_data = json.load(f)

    entries = []

    for entry in methods_data.get("software_source_codes", []):
        entries.append(("methods.json", "software_source_codes", entry))

    for entry in methods_data.get("tutorials", []):
        entries.append(("methods.json", "tutorials", entry))

    for entry in tutorials_data.get("tutorials", []):
        entries.append(("tutorials.json", "tutorials", entry))

    return entries


def deduplicate_entries(entries):
    seen = set()
    unique_entries = []

    for source_file, source_section, entry in entries:
        key = (
            entry.get("id"),
            entry.get("name"),
            entry.get("code_repository"),
            entry.get("git_reference"),
            entry.get("supplement_source"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique_entries.append((source_file, source_section, entry))

    return unique_entries


def normalize_labels(entry):
    labels = entry.get("top_level_tasks") or []
    labels = [str(label).strip() for label in labels if str(label).strip()]
    return list(dict.fromkeys(labels))


def extract_repo_path(code_repository: str) -> str:
    if "github.com/" not in code_repository:
        raise ValueError(f"Not a GitHub URL: {code_repository}")

    repo_path = code_repository.rstrip("/").split("github.com/", 1)[1]
    if repo_path.endswith(".git"):
        repo_path = repo_path[:-4]

    parts = [p for p in repo_path.split("/") if p]
    if len(parts) < 2:
        raise ValueError(f"Could not extract owner/repo from: {code_repository}")

    return f"{parts[0]}/{parts[1]}"


def build_raw_github_url(code_repository: str, git_reference: str, supplement_source: str) -> str:
    repo_path = extract_repo_path(code_repository)
    file_path = quote(supplement_source.lstrip("/"), safe="/")
    return f"https://raw.githubusercontent.com/{repo_path}/{git_reference}/{file_path}"


def download_text(url: str, timeout: int = 30) -> str:
    response = requests.get(
        url,
        timeout=timeout,
        headers={"User-Agent": "methodshub-training-data-builder/1.0"},
    )
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    return response.text


def strip_front_matter(text: str) -> str:
    return re.sub(r"(?s)\A---\n.*?\n---\n", "", text)


def strip_markdown(text: str) -> str:
    text = strip_front_matter(text)
    text = html.unescape(text)

    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)   # fenced code
    text = re.sub(r"`[^`]*`", " ", text)                      # inline code
    text = re.sub(r"!\[.*?\]\(.*?\)", " ", text)              # images
    text = re.sub(r"\[([^\]]+)\]\((.*?)\)", r"\1", text)      # links -> label
    text = re.sub(r"<[^>]+>", " ", text)                      # html tags
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)  # headings
    text = re.sub(r"[*_~]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


def extract_text_from_ipynb(content: str) -> str:
    notebook = json.loads(content)
    parts = []

    for cell in notebook.get("cells", []):
        if cell.get("cell_type") in {"markdown", "raw"}:
            source = cell.get("source", "")
            if isinstance(source, list):
                source = "".join(source)
            parts.append(str(source))

    return strip_markdown("\n\n".join(parts))


def extract_text_from_content(content: str, filename: str) -> str:
    suffix = Path(filename).suffix.lower()

    if suffix == ".ipynb":
        return extract_text_from_ipynb(content)

    return strip_markdown(content)


def build_training_data(entries):
    dataset = []

    for source_file, source_section, entry in entries:
        name = entry.get("name", "<unknown>")
        code_repository = entry.get("code_repository")
        git_reference = entry.get("git_reference")
        supplement_source = entry.get("supplement_source")
        labels = normalize_labels(entry)

        if not code_repository or not git_reference or not supplement_source:
            print(f"Skipping {name}: missing repository metadata")
            continue

        if not labels:
            print(f"Skipping {name}: no top_level_tasks")
            continue

        try:
            raw_url = build_raw_github_url(code_repository, git_reference, supplement_source)
            content = download_text(raw_url)
            text = extract_text_from_content(content, supplement_source)

            if not text.strip():
                print(f"Skipping {name}: extracted text is empty")
                continue

            dataset.append({
                "source_file": source_file,
                "source_section": source_section,
                "id": entry.get("id"),
                "name": name,
                "code_repository": code_repository,
                "git_reference": git_reference,
                "supplement_source": supplement_source,
                "raw_url": raw_url,
                "labels": labels,
                "text": text,
            })

            print(f"Added: {name}")

        except Exception as e:
            print(f"Skipping {name}: {e}")

    return dataset


def save_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    entries = load_entries(METHODS_PATH, TUTORIALS_PATH)
    entries = deduplicate_entries(entries)

    dataset = build_training_data(entries)
    save_jsonl(OUTPUT_PATH, dataset)

    print(f"\nBuilt {len(dataset)} training examples")
    print(f"Saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()