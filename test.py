import os
from pathlib import Path
import json

localvariable1=os.environ.get("REPO_FULL_NAME")
print(localvariable1)

event_path = os.environ.get("GITHUB_EVENT_PATH")

if not event_path:
    raise RuntimeError("GITHUB_EVENT_PATH ist nicht gesetzt")

with open(event_path, "r") as f:
    event = json.load(f)

client_payload = event.get("client_payload", {})

rank = client_payload.get("rank")

print("Client Payload:", client_payload)
print("Rank:", rank)

def tree(path: Path, prefix=""):
    contents = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
    for i, item in enumerate(contents):
        is_last = i == len(contents) - 1
        connector = "└── " if is_last else "├── "
        print(prefix + connector + item.name)

        if item.is_dir():
            extension = "    " if is_last else "│   "
            tree(item, prefix + extension)

parent_dir = Path.cwd().parent

print(parent_dir)
tree(parent_dir)
