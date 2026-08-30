"""Small stdlib-only checks shared by consumer repositories."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def context(root: Path) -> list[str]:
    path = root / ".specify" / "feature.json"
    if not path.is_file():
        return ["missing .specify/feature.json; feature selection by mtime is forbidden"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid feature pointer: {exc}"]
    errors = []
    for key in ("feature_directory", "feature_id", "owner", "risk_lane", "owned_paths"):
        if not data.get(key):
            errors.append(f"missing context field: {key}")
    if not re.fullmatch(r"specs/\d{3,}-[a-z0-9][a-z0-9-]*", str(data.get("feature_directory", ""))):
        errors.append("feature_directory must be specs/NNN-slug")
    for item in data.get("owned_paths", []):
        path_item = Path(str(item))
        if path_item.is_absolute() or ".." in path_item.parts:
            errors.append("owned_paths must be relative")
    return errors


def fragments(root: Path) -> list[str]:
    directory = root / "changes" / "unreleased"
    errors: list[str] = []
    seen: set[str] = set()
    for path in sorted(directory.glob("F*.yaml")) if directory.is_dir() else []:
        text = path.read_text(encoding="utf-8", errors="ignore")
        match = re.search(r"^feature_id:\s*(\d{3,})\s*$", text, re.MULTILINE)
        if not match:
            errors.append(f"{path}: missing numeric feature_id")
            continue
        feature = match.group(1)
        if feature in seen:
            errors.append(f"{path}: duplicate feature_id {feature}")
        seen.add(feature)
        if path.stem != f"F{feature}":
            errors.append(f"{path}: filename must match feature_id")
        if not re.search(r"^summary:\s*.+[А-Яа-яЁё]", text, re.MULTILINE):
            errors.append(f"{path}: summary must be non-empty and Russian")
        for key in ("schema_version:", "category:", "issue:", "tasks:", "compatibility:", "release_notes:"):
            if key not in text:
                errors.append(f"{path}: missing {key}")
        if re.search(r"/Users/|/home/|BEGIN PRIVATE KEY|sk-[A-Za-z0-9]|signed-url|raw audio|transcript text", text, re.I):
            errors.append(f"{path}: forbidden secret/private content")
    return errors


def legacy(spec: Path) -> list[str]:
    try:
        text = spec.read_text(encoding="utf-8")
    except OSError as exc:
        return [str(exc)]
    match = re.search(r"^## Legacy Impact\s*$([\s\S]*)", text, re.MULTILINE)
    if not match:
        return [f"{spec}: missing Legacy Impact"]
    section = match.group(1)
    if not re.search(r"\b(remove|retain-with-exception|untouched)\b", section):
        return [f"{spec}: Legacy Impact classification is invalid"]
    if "retain-with-exception" in section and any(token not in section.lower() for token in ("owner", "expiry", "trigger", "retirement task")):
        return [f"{spec}: compatibility exception needs owner, expiry, trigger and retirement task"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--spec", type=Path)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    errors = context(root) + fragments(root)
    if args.spec:
        errors += legacy(args.spec.resolve())
    if errors:
        for error in errors:
            print(f"harness-check: ERROR: {error}", file=sys.stderr)
        return 1
    print("harness-check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
