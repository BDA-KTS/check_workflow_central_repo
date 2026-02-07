from pathlib import Path

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
