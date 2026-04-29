import json
from collections import Counter
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd

REQUIRED_COLUMNS = {
    "owner",
    "repo",
    "name",
    "passed",
    "warning_labels",
    "error_labels",
    "Workflow Duration",
}

PLOT_DIR = Path("plots")


def load_jsonl(path: Path) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {exc}") from exc

    if not rows:
        raise ValueError("The JSONL file is empty.")

    df = pd.DataFrame(rows)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
    return df


def parse_duration_to_seconds(duration: str) -> int:
    minutes, seconds = duration.split(":")
    return int(minutes) * 60 + int(seconds)


def _save_show(path: str) -> None:
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(PLOT_DIR / path, dpi=300, bbox_inches="tight")
    plt.show()
    plt.close()


def _plot_passed(df: pd.DataFrame, title: str, filename: str) -> None:
    counts = df["passed"].value_counts().sort_index()
    total = counts.sum()

    ax = counts.plot(kind="bar", color=["tab:red", "tab:green"])
    ax.set(title=title, xlabel="Passed", ylabel="Count")
    ax.set_xticklabels(["False", "True"], rotation=0)
    ymax = counts.max() if len(counts) else 0

    for i, count in enumerate(counts):
        ax.text(
            i,
            count + 0.02 * ymax,
            f"{count}\n({count / total * 100:.1f}%)",
            ha="center",
            va="bottom",
        )

    ax.set_ylim(0, ymax * 1.3 if ymax else 1)
    _save_show(filename)


def _has_any(labels) -> bool:
    return isinstance(labels, list) and len(labels) > 0

def _has_label(labels, target: str) -> bool:
    return isinstance(labels, list) and target in labels

def _summary_label_state_plot(df: pd.DataFrame, title: str, filename: str):
    if df.empty:
        plt.figure(figsize=(8, 4))
        plt.title(title)
        plt.text(
            0.5,
            0.5,
            "No data available",
            ha="center",
            va="center",
            transform=plt.gca().transAxes,
        )
        plt.xticks([])
        plt.yticks([])
        _save_show(filename)
        return

    error_labels = df["error_labels"]

    categories = {
        "No Error": error_labels.apply(lambda labels: not labels).sum(),
        "Warning": error_labels.apply(lambda labels: _has_label(labels, "Warning")).sum(),
        "Error": error_labels.apply(lambda labels: _has_label(labels, "Critical")).sum(),
    }

    plt.figure(figsize=(8, 5))
    ax = plt.gca()
    bars = ax.bar(
        categories.keys(),
        categories.values(),
        color=["tab:green", "tab:orange", "tab:red"],
    )
    ax.set(title=title, xlabel="Category", ylabel="Count")

    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h,
            str(int(h)),
            ha="center",
            va="bottom",
        )

    _save_show(filename)

def _label_state_plot(df: pd.DataFrame, title: str, filename: str) -> None:
    warning_has = df["warning_labels"].apply(_has_any)
    error_has = df["error_labels"].apply(_has_any)

    categories = {
        "No warnings / No errors": ((~warning_has) & (~error_has)).sum(),
        "Warnings only": (warning_has & (~error_has)).sum(),
        "Errors only": ((~warning_has) & error_has).sum(),
        "Warnings + Errors": (warning_has & error_has).sum(),
    }

    plt.figure(figsize=(10, 5))
    ax = plt.gca()
    bars = ax.bar(
        categories.keys(),
        categories.values(),
        color=["tab:green", "tab:orange", "tab:red", "tab:purple"],
    )
    ax.set(title=title, xlabel="Category", ylabel="Count")
    plt.xticks(rotation=20, ha="right")

    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h,
            str(int(h)),
            ha="center",
            va="bottom",
        )

    _save_show(filename)


def _flatten_labels(df: pd.DataFrame, column: str) -> list:
    labels: list = []
    for item in df[column].dropna():
        if isinstance(item, list):
            labels.extend(item)
    return labels


def _plot_labels(
    df: pd.DataFrame,
    column: str,
    title: str,
    color: str,
    filename: str,
    empty_msg: str,
) -> None:
    labels = _flatten_labels(df, column)
    if not labels:
        print(empty_msg)
        return

    counts = dict(sorted(Counter(labels).items(), key=lambda x: x[1], reverse=True))
    plt.figure(figsize=(10, 5))
    plt.bar(counts.keys(), counts.values(), color=color)
    plt.title(title)
    plt.xlabel(
        column.replace("_", " ").title()[:-1] if column.endswith("s") else column.title()
    )
    plt.ylabel("Count")
    plt.xticks(rotation=30, ha="right")

    for i, v in enumerate(counts.values()):
        plt.text(i, v + 0.05, str(v), ha="center", va="bottom")

    _save_show(filename)


def get_binder_after_filecheck(df: pd.DataFrame) -> pd.DataFrame:
    df_filecheck_passed = df[
        (df["name"] == "File Check") & (df["passed"] == True)
    ][["owner", "repo"]].drop_duplicates()

    df_binder = df[df["name"] == "Binder Test"].copy()

    binder_after_filecheck = df_binder.merge(
        df_filecheck_passed,
        on=["owner", "repo"],
        how="inner",
    )
    return binder_after_filecheck


def plot_summary_passed(df_summary):
    _plot_passed(df_summary, "How many Workflows passed?", "plotsummary_passed.png")


def plot_filecheck_passed(df_filecheck):
    _plot_passed(df_filecheck, "File Check: Passed vs Failed", "filecheck_passed.png")


def plot_licensecheck_passed(df_licensecheck):
    _plot_passed(
        df_licensecheck,
        "License Check: Passed vs Failed",
        "licensecheck_passed.png",
    )


def plot_readmecheck_passed(df_readmecheck):
    _plot_passed(df_readmecheck, "Readme Check: Passed vs Failed", "readme_passed.png")


def plot_bindertest_passed(df_bindertest):
    _plot_passed(
        df_bindertest,
        "Binder Test: Passed vs Failed (only repos with passed File Check)",
        "bindertest_passed.png",
    )


def plot_summary_label_states(df_summary):
    _summary_label_state_plot(df_summary, "Summary label states", "plotsummary_label_states.png")


def plot_filecheck_label_states(df_filecheck):
    _label_state_plot(df_filecheck, "File Check: Label States", "filecheck_label_state.png")


def plot_licensecheck_label_states(df_licensecheck):
    _label_state_plot(
        df_licensecheck,
        "License Check: Label States",
        "licensecheck_label_states.png",
    )


def plot_readmecheck_label_states(df_readmecheck):
    _label_state_plot(
        df_readmecheck,
        "Readme Check: Label States",
        "readme_label_states.png",
    )


def plot_warning_labels(df_filecheck):
    _plot_labels(
        df_filecheck,
        "warning_labels",
        "Warning Labels in File Check",
        "tab:orange",
        "filecheck_warning_labels.png",
        "No warning labels found.",
    )


def plot_error_labels(df_filecheck):
    _plot_labels(
        df_filecheck,
        "error_labels",
        "Error Labels in File Check",
        "tab:red",
        "filecheck_error_labels.png",
        "No error labels found.",
    )


def plot_licensecheck_warning_labels(df_licensecheck):
    _plot_labels(
        df_licensecheck,
        "warning_labels",
        "License Check: Warning Labels",
        "tab:orange",
        "licensecheck_warning_labels.png",
        "No warning labels found for License Check.",
    )


def plot_licensecheck_error_labels(df_licensecheck):
    _plot_labels(
        df_licensecheck,
        "error_labels",
        "License Check: Error Labels",
        "tab:red",
        "licensecheck_error_labels.png",
        "No error labels found for License Check.",
    )


def plot_readmecheck_warning_labels(df_readmecheck):
    _plot_labels(
        df_readmecheck,
        "warning_labels",
        "Readme Check: Warning Labels",
        "tab:orange",
        "readme_warning_labels.png",
        "No warning labels found for Readme Check.",
    )


def plot_readmecheck_error_labels(df_readmecheck):
    _plot_labels(
        df_readmecheck,
        "error_labels",
        "Readme Check: Error Labels",
        "tab:red",
        "readme_error_labels.png",
        "No error labels found for Readme Check.",
    )


def plot_summary_duration(df: pd.DataFrame):
    df_summary = df[df["name"] == "Summary"].copy()
    df_summary["duration_seconds"] = df_summary["Workflow Duration"].apply(
        parse_duration_to_seconds
    )

    plt.figure(figsize=(8, 5))
    plt.hist(
        df_summary["duration_seconds"],
        bins=10,
        color="tab:blue",
        edgecolor="black",
    )
    plt.title("Workflow Duration from Summary")
    plt.xlabel("Duration (seconds)")
    plt.ylabel("Number of repos")
    _save_show("average_duration.png")


def average_time(df: pd.DataFrame):
    df_time = df[df["name"] == "Binder Test"].copy()
    df_time = df_time[df_time["passed"] == True]
    df_time["duration_seconds"] = df_time["Workflow Duration"].apply(
        parse_duration_to_seconds
    )
    return round(df_time["duration_seconds"].mean(), 0)


def make_report(df: pd.DataFrame, binder_after_filecheck: pd.DataFrame):
    report = [
        "# Strategic Overview\n\n",
        "## Summary Results\n\n",
        f"The total number of workflows is {(len(df)/6)}.\n\n",
        f"The average workflow duration for successful workflows is {average_time(df)} seconds.\n\n",
    ]

    df_summary = df[df["name"] == "Summary"].copy()
    report.append('\n\n<img src="../plots/plotsummary_passed.png" width="600">\n\n')
    for _, row in df_summary.iterrows():
        if not row["passed"]:
            report.append(
                f"The workflow [{row['owner']}/{row['repo']}](../report/{row['owner']}/{row['repo']}.md) failed.\n\n"
            )

    report.append('\n\n<img src="../plots/plotsummary_label_states.png" width="600">\n\n')
    for _, row in df_summary.iterrows():
        if row["warning_labels"]:
            report.append(
                f"The workflow [{row['owner']}/{row['repo']}](../report/{row['owner']}/{row['repo']}.md) has warnings.\n\n"
            )

    report.append("## File Check Results\n\n")
    report.append('\n\n<img src="../plots/filecheck_passed.png" width="600">\n\n')
    df_filecheck = df[df["name"] == "File Check"].copy()
    for _, row in df_filecheck.iterrows():
        if not row["passed"]:
            report.append(
                f"The workflow [{row['owner']}/{row['repo']}](../report/{row['owner']}/{row['repo']}.md) failed.\n\n"
            )
    report.append("The following files are missing in the File Check:\n\n")
    report.append('\n\n<img src="../plots/filecheck_error_labels.png" width="600">\n\n')
    report.append("<br>")
    report.append('\n\n<img src="../plots/filecheck_label_state.png" width="600">\n\n')
    for _, row in df_filecheck.iterrows():
        if row["warning_labels"]:
            report.append(
                f"The workflow [{row['owner']}/{row['repo']}](../report/{row['owner']}/{row['repo']}.md) has warnings.\n\n"
            )

    report.append("\n\n")
    report.append("## License Check Results\n\n")
    report.append('\n\n<img src="../plots/licensecheck_passed.png" width="600">\n\n')
    df_license = df[df["name"] == "License Check"].copy()
    for _, row in df_license.iterrows():
        if not row["passed"]:
            report.append(
                f"The workflow [{row['owner']}/{row['repo']}](../report/{row['owner']}/{row['repo']}.md) failed.\n\n"
            )
    report.append("Most Common Errors:\n\n")
    report.append('\n\n<img src="../plots/licensecheck_error_labels.png" width="600">\n\n')
    report.append("<br>")
    report.append('\n\n<img src="../plots/licensecheck_label_states.png" width="600">\n\n')
    for _, row in df_license.iterrows():
        if row["warning_labels"]:
            report.append(
                f"The workflow [{row['owner']}/{row['repo']}](../report/{row['owner']}/{row['repo']}.md) has warnings.\n\n"
            )

    report.append("## Readme Check Results\n\n")
    report.append('\n\n<img src="../plots/readme_passed.png" width="600">\n\n')
    df_readme = df[df["name"] == "Readme Check"].copy()
    for _, row in df_readme.iterrows():
        if not row["passed"]:
            report.append(
                f"The workflow [{row['owner']}/{row['repo']}](../report/{row['owner']}/{row['repo']}.md) failed.\n\n"
            )
    report.append("Most Common Errors:\n\n")
    report.append('\n\n<img src="../plots/readme_error_labels.png" width="600">\n\n')
    report.append("Most Common Warnings:\n\n")
    report.append('\n\n<img src="../plots/readme_warning_labels.png" width="600">\n\n')
    report.append("<br>")
    report.append('\n\n<img src="../plots/readme_label_states.png" width="600">\n\n')
    for _, row in df_readme.iterrows():
        if row["warning_labels"]:
            report.append(
                f"The workflow [{row['owner']}/{row['repo']}](../report/{row['owner']}/{row['repo']}.md) has warnings.\n\n"
            )

    report.append("## Binder Test Results\n\n")
    report.append('\n\n<img src="../plots/bindertest_passed.png" width="600">\n\n')
    for _, row in binder_after_filecheck.iterrows():
        if not row["passed"]:
            report.append(
                f"The workflow [{row['owner']}/{row['repo']}](../report/{row['owner']}/{row['repo']}.md) failed.\n\n"
            )

    return report


def save_report(report, path: Path):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("".join(report))
    except Exception as e:
        print(f"Error saving report to {path}: {e}")


df = load_jsonl(Path("report_jsonl/merged.jsonl"))

sections = {
    "Summary": df[df["name"] == "Summary"],
    "File Check": df[df["name"] == "File Check"],
    "License Check": df[df["name"] == "License Check"],
    "Readme Check": df[df["name"] == "Readme Check"],
    "Binder Test": df[df["name"] == "Binder Test"],
}

binder_after_filecheck = get_binder_after_filecheck(df)

plot_summary_passed(sections["Summary"])
plot_summary_label_states(sections["Summary"])

plot_filecheck_passed(sections["File Check"])
plot_filecheck_label_states(sections["File Check"])
plot_warning_labels(sections["File Check"])
plot_error_labels(sections["File Check"])

plot_licensecheck_passed(sections["License Check"])
plot_licensecheck_label_states(sections["License Check"])
plot_licensecheck_warning_labels(sections["License Check"])
plot_licensecheck_error_labels(sections["License Check"])

plot_readmecheck_passed(sections["Readme Check"])
plot_readmecheck_label_states(sections["Readme Check"])
plot_readmecheck_warning_labels(sections["Readme Check"])
plot_readmecheck_error_labels(sections["Readme Check"])

plot_bindertest_passed(binder_after_filecheck)
plot_summary_duration(df)

report = make_report(df, binder_after_filecheck)

overview_dir = Path("overview")
overview_dir.mkdir(parents=True, exist_ok=True)
save_report(report, Path("overview/overview.md"))