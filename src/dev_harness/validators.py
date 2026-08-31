"""Small stdlib-only checks shared by consumer repositories."""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
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


def package_consistency(package_root: Path) -> list[str]:
    """Check the three user-visible package version declarations."""
    errors: list[str] = []
    try:
        version_file = (package_root / "VERSION").read_text(encoding="utf-8").strip()
        pyproject = (package_root / "pyproject.toml").read_text(encoding="utf-8")
        init = (package_root / "src" / "dev_harness" / "__init__.py").read_text(encoding="utf-8")
    except OSError as exc:
        return [f"package metadata is incomplete: {exc}"]
    project_match = re.search(r'^version\s*=\s*"([^"]+)"\s*$', pyproject, re.MULTILINE)
    runtime_match = re.search(r'^__version__\s*=\s*"([^"]+)"\s*$', init, re.MULTILINE)
    if not project_match or not runtime_match:
        return ["package metadata must declare version in pyproject.toml and __init__.py"]
    declared = {version_file, project_match.group(1), runtime_match.group(1)}
    if len(declared) != 1:
        errors.append("package version mismatch: " + ", ".join(sorted(declared)))
    if not re.fullmatch(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)", version_file):
        errors.append("VERSION must use SemVer MAJOR.MINOR.PATCH")
    return errors


def package_safety(package_root: Path) -> list[str]:
    """Reject secrets, private paths and generated artifacts before publishing."""
    errors: list[str] = []
    forbidden = re.compile(
        r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|(?:api[_-]?key|secret|password|bearer)\s*[:=]|"
        r"/(?:Users|home|private/var|Volumes)/[^\s/]+/[^\s]+",
        re.IGNORECASE,
    )
    for path in sorted(package_root.rglob("*")):
        relative = path.relative_to(package_root)
        if path.is_symlink():
            errors.append(f"symlink is not publishable: {relative}")
            continue
        if path.is_dir() or ".git" in path.parts:
            continue
        # The scanner's own pattern literals are policy text, not credentials.
        if relative == Path("src/dev_harness/validators.py"):
            continue
        if path.suffix in {".pyc", ".pyo"} or ".egg-info" in path.parts or path.name in {".DS_Store"}:
            errors.append(f"generated artifact is not publishable: {relative}")
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            errors.append(f"cannot read package file {relative}: {exc}")
            continue
        if b"\x00" in data:
            errors.append(f"binary file is not publishable: {relative}")
            continue
        if forbidden.search(data.decode("utf-8", errors="ignore")):
            errors.append(f"forbidden secret/private content: {relative}")
    return errors


def self_test() -> int:
    with tempfile.TemporaryDirectory(prefix="development-harness-") as directory:
        root = Path(directory)
        (root / ".specify").mkdir()
        (root / "specs/001-example").mkdir(parents=True)
        (root / "specs/001-example/spec.md").write_text(
            "# Example\n\n## Legacy Impact\n\nClassification: untouched\n", encoding="utf-8"
        )
        (root / ".specify/feature.json").write_text(
            json.dumps({"feature_directory": "specs/001-example", "feature_id": "001", "owner": "test", "risk_lane": "low", "owned_paths": ["specs/001-example"]}),
            encoding="utf-8",
        )
        assert context(root) == []
        assert legacy(root / "specs/001-example/spec.md") == []
    print("harness-check: self-test OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, nargs="?", default=Path.cwd())
    parser.add_argument("--spec", type=Path)
    parser.add_argument("--package-root", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    root = args.root.resolve()
    errors = context(root) + fragments(root)
    if args.spec:
        errors += legacy(args.spec.resolve())
    if args.package_root:
        package_root = args.package_root.resolve()
        errors += package_consistency(package_root) + package_safety(package_root)
    if errors:
        for error in errors:
            print(f"harness-check: ERROR: {error}", file=sys.stderr)
        return 1
    print("harness-check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
