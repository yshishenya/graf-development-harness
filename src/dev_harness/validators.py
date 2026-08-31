"""Small stdlib-only checks shared by consumer repositories."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Optional


def context(root: Path) -> list[str]:
    path = root / ".specify" / "feature.json"
    if not path.is_file():
        return ["missing .specify/feature.json; feature selection by mtime is forbidden"]
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid feature pointer: {exc}"]
    if not isinstance(data, dict):
        return ["invalid feature pointer: expected a JSON object"]
    errors = []
    for key in (
        "feature_directory", "feature_id", "branch", "source_sha", "owner",
        "risk_lane", "owned_paths",
    ):
        if not data.get(key):
            errors.append(f"missing context field: {key}")
    feature_directory = str(data.get("feature_directory", ""))
    directory_match = re.fullmatch(r"specs/(\d{3,})-[a-z0-9][a-z0-9-]*", feature_directory)
    if not directory_match:
        errors.append("feature_directory must be specs/NNN-slug")
    else:
        if str(data.get("feature_id", "")) != directory_match.group(1):
            errors.append("feature_id must match feature_directory")
        candidate = (root / feature_directory).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            errors.append("feature_directory must remain inside the consumer root")
        else:
            if not candidate.is_dir() or not (candidate / "spec.md").is_file():
                errors.append("feature_directory and spec.md must exist")
    branch = data.get("branch")
    source_sha = data.get("source_sha")
    if branch and (not isinstance(branch, str) or not branch.strip()):
        errors.append("branch must be a non-empty string")
    if source_sha and (not isinstance(source_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", source_sha, re.IGNORECASE)):
        errors.append("source_sha must be a full 40-character git SHA")
    # A standalone sample fixture may not have its own .git directory. Real
    # consumer roots do, and their pointer must describe the checkout actually
    # being used; no timestamp or newest-directory fallback is permitted.
    if (root / ".git").exists() and isinstance(branch, str) and branch.strip() and isinstance(source_sha, str) and re.fullmatch(r"[0-9a-f]{40}", source_sha, re.IGNORECASE):
        try:
            current_branch = subprocess.check_output(
                ["git", "-C", str(root), "branch", "--show-current"], text=True, stderr=subprocess.DEVNULL
            ).strip()
            current_sha = subprocess.check_output(
                ["git", "-C", str(root), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
            ).strip()
        except (OSError, subprocess.CalledProcessError) as exc:
            errors.append(f"cannot verify current checkout: {exc}")
        else:
            if not current_branch:
                errors.append("checkout must have an active branch")
            elif current_branch != branch:
                errors.append(f"branch mismatch: pointer={branch!r}, checkout={current_branch!r}")
            if current_sha.lower() != source_sha.lower():
                errors.append("source_sha does not match current HEAD; refresh context before changing files")
    owned_paths = data.get("owned_paths", [])
    if not isinstance(owned_paths, list):
        return errors + ["owned_paths must be a JSON array"]
    for item in owned_paths:
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
        if not re.search(r"^summary:\s*\S", text, re.MULTILINE):
            errors.append(f"{path}: summary must be non-empty")
        for key in ("schema_version:", "category:", "issue:", "tasks:", "compatibility:", "release_notes:"):
            if not re.search(r"^" + re.escape(key), text, re.MULTILINE):
                errors.append(f"{path}: missing {key}")
        forbidden_literals = (
            r"/(?:Users|home)/|"
            "BEGIN " + r"PRIVATE KEY|sk-[A-Za-z0-9]|signed-url|raw audio|transcript text"
        )
        if re.search(forbidden_literals, text, re.I):
            errors.append(f"{path}: forbidden secret/private content")
    return errors


def legacy(spec: Path) -> list[str]:
    try:
        text = spec.read_text(encoding="utf-8")
    except OSError as exc:
        return [str(exc)]
    match = re.search(r"^## Legacy Impact\s*$([\s\S]*?)(?=^## |\Z)", text, re.MULTILINE)
    if not match:
        return [f"{spec}: missing Legacy Impact"]
    section = match.group(1)
    classifications = re.findall(
        r"^[ \t]*(?:[-*][ \t]*)?(?:\*\*)?classification(?:\*\*)?[ \t]*:[ \t]*[`']?(remove|retain-with-exception|untouched)[`']?(?:[ \t]*;[ \t]*.*)?$",
        section,
        re.IGNORECASE | re.MULTILINE,
    )
    if len(classifications) != 1:
        return [f"{spec}: Legacy Impact classification is invalid"]
    if classifications[0].lower() == "retain-with-exception":
        for token in ("owner", "expiry", "trigger", "retirement task"):
            field = re.search(
                rf"^[ \t]*(?:[-*][ \t]*)?(?:\*\*)?{re.escape(token)}(?:\*\*)?[ \t]*:[ \t]*(\S.*)$",
                section,
                re.IGNORECASE | re.MULTILINE,
            )
            if not field:
                return [f"{spec}: compatibility exception needs owner, expiry, trigger and retirement task"]
            if token == "expiry":
                value = field.group(1).strip().strip("`'\"")
                try:
                    expiry = dt.date.fromisoformat(value)
                except ValueError:
                    return [f"{spec}: compatibility exception needs an ISO expiry date"]
                if expiry < dt.date.today():
                    return [f"{spec}: expired legacy exception {value}"]
    return []


_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
_DIGEST_RE = re.compile(r"^(?:sha256:)?[0-9a-fA-F]{64}$")
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9._:-]+$")
_ARTIFACT_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
_CI_LANES = {"focused", "fast", "full"}
_CI_STATUSES = {"passed", "failed", "stale", "cancelled", "ambiguous"}
_STALE_CI_STATUSES = {"failed", "stale", "cancelled", "ambiguous"}
_UTC_TIMESTAMP_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]00:00)$"
)


def _utc_timestamp(data: dict[str, Any], key: str, errors: list[str]) -> Optional[dt.datetime]:
    value = _non_empty_string(data, key, errors)
    if value is None or not _UTC_TIMESTAMP_RE.fullmatch(value):
        if value is not None:
            errors.append(f"{key} must be an RFC3339 UTC timestamp")
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{key} must be an RFC3339 UTC timestamp")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        errors.append(f"{key} must be an RFC3339 UTC timestamp")
        return None
    return parsed


def _non_empty_string(data: dict[str, Any], key: str, errors: list[str]) -> Optional[str]:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        errors.append(f"missing or invalid {key}")
        return None
    return value


def _sha(data: dict[str, Any], key: str, errors: list[str]) -> Optional[str]:
    value = _non_empty_string(data, key, errors)
    if value is not None and not _SHA_RE.fullmatch(value):
        errors.append(f"invalid {key}: expected 40 hexadecimal characters")
    return value


def _string_list(
    data: dict[str, Any], key: str, errors: list[str], *, non_empty: bool = False
) -> Optional[list[str]]:
    value = data.get(key)
    if not isinstance(value, list) or (non_empty and not value) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        errors.append(f"missing or invalid {key}: expected a list of non-empty strings")
        return None
    return value


def _artifact_digests(data: dict[str, Any], errors: list[str]) -> None:
    value = data.get("artifact_digests")
    if not isinstance(value, dict) or not value:
        errors.append("missing or invalid artifact_digests: expected a non-empty object")
        return
    for name, digest in value.items():
        if not isinstance(name, str) or not _ARTIFACT_NAME_RE.fullmatch(name):
            errors.append("artifact_digests contains an invalid artifact name")
        elif not isinstance(digest, str) or not _DIGEST_RE.fullmatch(digest):
            errors.append(f"invalid artifact digest for {name!r}")


def _source_revision_identity(
    data: dict[str, Any], observed_end: Optional[str], errors: list[str]
) -> None:
    """Bind the optional source-revision digest to the observed SHA.

    ``source-revision`` is an identity assertion, not an artifact digest.  If
    a producer emits it, accepting a value for a different revision would
    make otherwise stale evidence look current.  Actual release artifacts
    remain producer-specific and may be represented by additional entries.
    """
    digests = data.get("artifact_digests")
    if not isinstance(digests, dict) or "source-revision" not in digests or not observed_end:
        return
    digest = digests["source-revision"]
    if not isinstance(digest, str) or not _DIGEST_RE.fullmatch(digest):
        return
    if not _SHA_RE.fullmatch(observed_end):
        return
    expected = "sha256:" + hashlib.sha256(observed_end.encode("ascii")).hexdigest()
    normalized = digest if digest.lower().startswith("sha256:") else "sha256:" + digest
    if normalized.lower() != expected:
        errors.append("source-revision artifact digest does not match observed end SHA")


def ci_evidence(data: Any) -> list[str]:
    """Validate metadata-only CI evidence bound to one exact source SHA.

    Relational checks (for example, all observed SHAs matching the requested
    SHA) intentionally live here rather than only in JSON Schema.
    """
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["evidence must be a JSON object"]

    run_id = _non_empty_string(data, "run_id", errors)
    if run_id is not None and not _SAFE_ID_RE.fullmatch(run_id):
        errors.append("invalid run_id")
    lane = _non_empty_string(data, "lane", errors)
    if lane is not None and lane not in _CI_LANES:
        errors.append(f"invalid lane {lane!r}")

    requested = _sha(data, "requested_sha", errors)
    observed_start = _sha(data, "observed_sha_start", errors)
    observed_end = _sha(data, "observed_sha_end", errors)
    if requested and observed_start and requested.lower() != observed_start.lower():
        errors.append("requested/observed start SHA mismatch: evidence is stale")
    if requested and observed_end and requested.lower() != observed_end.lower():
        errors.append("requested/observed end SHA mismatch: evidence is stale")
    if observed_start and observed_end and observed_start.lower() != observed_end.lower():
        errors.append("observed start/end SHA mismatch: run changed during execution")

    status = _non_empty_string(data, "status", errors)
    if status is not None and status not in _CI_STATUSES:
        errors.append(f"invalid status {status!r}")
    if status in _STALE_CI_STATUSES:
        errors.append(f"status {status} cannot be release evidence")
    if status != "passed":
        _non_empty_string(data, "reason", errors)

    started_at = _utc_timestamp(data, "started_at", errors)
    finished_at = _utc_timestamp(data, "finished_at", errors)
    if started_at is not None and finished_at is not None and finished_at <= started_at:
        errors.append("finished_at must be after started_at")
    _string_list(data, "commands", errors, non_empty=True)
    skipped_gates = _string_list(data, "skipped_gates", errors)
    _non_empty_string(data, "scope", errors)
    _artifact_digests(data, errors)
    _source_revision_identity(data, observed_end, errors)

    component_shas = data.get("component_shas")
    if lane == "full" and (not isinstance(component_shas, dict) or not component_shas):
        errors.append("full evidence requires a non-empty component_shas object")
    if component_shas is not None:
        if not isinstance(component_shas, dict) or not component_shas:
            errors.append("component_shas must be a non-empty object when present")
        elif requested:
            for component, component_sha in component_shas.items():
                if not isinstance(component, str) or not isinstance(component_sha, str):
                    errors.append("component_shas contains an invalid entry")
                elif not _SHA_RE.fullmatch(component_sha):
                    errors.append(f"invalid component SHA for {component!r}")
                elif component_sha.lower() != requested.lower():
                    errors.append(f"component SHA mismatch for {component!r}")

    if lane == "full":
        candidate_id = _non_empty_string(data, "candidate_id", errors)
        if candidate_id is not None and not _SAFE_ID_RE.fullmatch(candidate_id):
            errors.append("invalid candidate_id")
        if data.get("authoritative_full") is not True:
            errors.append("full evidence requires authoritative_full=true")
        if skipped_gates == []:
            pass
        elif skipped_gates is not None:
            errors.append("authoritative full evidence cannot skip gates")

    if "authoritative_full" in data and not isinstance(data["authoritative_full"], bool):
        errors.append("authoritative_full must be boolean")
    return errors


_PR_REQUIRED_SECTIONS = (
    "## Feature identity",
    "## Как проверено",
    "## Risk / validation lane",
    "## Issues",
    "## Legacy Impact",
    "## Перед merge",
)


def pr_metadata(body: Any, feature_id: str) -> list[str]:
    """Validate the machine-checkable metadata contract in a pull request."""
    if not isinstance(body, str):
        return ["PR body must be a string"]
    errors: list[str] = []
    sections: dict[str, str] = {}
    for heading in _PR_REQUIRED_SECTIONS:
        match = re.search(
            rf"^\s*{re.escape(heading)}\s*$([\s\S]*?)(?=^\s*##\s|\Z)",
            body,
            re.MULTILINE,
        )
        if not match:
            errors.append(f"missing PR section: {heading}")
        else:
            section = match.group(1).strip()
            sections[heading] = section
            if not section:
                errors.append(f"empty PR section: {heading}")
    lane_section = sections.get("## Risk / validation lane", "")
    lane = re.search(r"(?im)^\s*[-*]?\s*Lane\s*:\s*`?([A-Za-z][A-Za-z0-9_-]*)`?\s*$", lane_section)
    if not lane or lane.group(1).lower() in {"tbd", "todo", "unknown", "placeholder"}:
        errors.append("Risk / validation lane requires a concrete Lane")
    verification_section = sections.get("## Как проверено", "")
    has_command = bool(re.search(r"`[^`\n]+`", verification_section))
    has_result = bool(re.search(r"\b(?:pass(?:ed)?|fail(?:ed)?|not[ -]?run|blocked)\b", verification_section, re.IGNORECASE))
    if not has_command or not has_result:
        errors.append("Как проверено requires command and result evidence")
    marker = re.search(r"Feature ID:\s*`?F?(\d{3,})", body)
    if not marker:
        errors.append("Feature ID is required in PR body")
    elif marker.group(1) != str(feature_id):
        errors.append(f"Feature ID mismatch: expected {feature_id}, got {marker.group(1)}")
    if not re.search(r"Umbrella issue:\s*`?#\d+", body):
        errors.append("umbrella issue is required")
    if not re.search(r"Exact source SHA[^\n]*\b([0-9a-fA-F]{40})\b", body):
        errors.append("exact source SHA evidence is required")
    if not re.search(r"Spec task IDs:\s*`?T\d{3,}", body):
        errors.append("at least one Spec task ID is required")
    if not any(token in body for token in ("Refs #", "Part of #", "Fixes #", "Closes #", "Resolves #")):
        errors.append("at least one explicit issue linkage keyword is required")
    if not re.search(r"Classification:\s*`(?:remove|retain-with-exception|untouched)`", body):
        errors.append("Legacy Impact classification is required")
    return errors


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
    private_material = re.compile(
        r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY|"
        r"/(?:Users|home|private/var|Volumes)/[^\s/]+/[^\s]+",
        re.IGNORECASE,
    )
    credential_assignment = re.compile(
        r"\b(?:api[_-]?key|secret|password|bearer)\s*[:=]\s*['\"]?"
        r"[A-Za-z0-9][A-Za-z0-9_./+=:-]{7,}",
        re.IGNORECASE,
    )
    for path in sorted(package_root.rglob("*")):
        relative = path.relative_to(package_root)
        if path.is_symlink():
            errors.append(f"symlink is not publishable: {relative}")
            continue
        if path.is_dir() or ".git" in path.parts:
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
        text = data.decode("utf-8", errors="ignore")
        if private_material.search(text) or credential_assignment.search(text):
            errors.append(f"forbidden secret/private content: {relative}")
    return errors


def self_test() -> int:
    sha = "a" * 40
    digest = "sha256:" + "b" * 64
    good_evidence = {
        "run_id": "run-1",
        "lane": "full",
        "requested_sha": sha,
        "observed_sha_start": sha,
        "observed_sha_end": sha,
        "status": "passed",
        "started_at": "2026-08-31T00:00:00Z",
        "finished_at": "2026-08-31T00:01:00Z",
        "commands": ["ci --full"],
        "artifact_digests": {"full-log": digest},
        "skipped_gates": [],
        "scope": "release candidate",
        "candidate_id": "rc-20260831T000000Z-aaaaaaaaaaaa",
        "authoritative_full": True,
        "component_shas": {"backend": sha, "frontend": sha},
    }
    assert ci_evidence(good_evidence) == []
    stale_evidence = dict(good_evidence, observed_sha_end="b" * 40)
    assert any("mismatch" in error for error in ci_evidence(stale_evidence))
    failed_evidence = dict(good_evidence, status="ambiguous", reason="runner interrupted")
    assert any("cannot be release" in error for error in ci_evidence(failed_evidence))

    good_pr = (
        "## Feature identity\nFeature ID: `F216`\nUmbrella issue: `#6090`\nSpec task IDs: `T042`\n"
        "\n## Как проверено\n- `ci --fast`: passed\n- Exact source SHA: " + sha + "\n"
        "\n## Risk / validation lane\n- Lane: significant-feature\n"
        "\n## Issues\n- Refs #6090\n"
        "\n## Legacy Impact\n- Classification: `untouched`\n"
        "\n## Перед merge\n- evidence recorded\n"
    )
    assert pr_metadata(good_pr, "216") == []
    assert any("Feature ID mismatch" in error for error in pr_metadata(good_pr.replace("F216", "F215"), "216"))
    assert any("missing PR section" in error for error in pr_metadata(good_pr.replace("## Issues", "## Links"), "216"))
    empty_quality = good_pr.replace("## Как проверено\n- `ci --fast`: passed", "## Как проверено\n").replace(
        "## Risk / validation lane\n- Lane: significant-feature", "## Risk / validation lane\n- Lane: TBD"
    )
    assert any("command and result evidence" in error for error in pr_metadata(empty_quality, "216"))
    assert any("concrete Lane" in error for error in pr_metadata(empty_quality, "216"))

    with tempfile.TemporaryDirectory(prefix="development-harness-") as directory:
        root = Path(directory)
        (root / ".specify").mkdir()
        (root / "specs/001-example").mkdir(parents=True)
        (root / "specs/001-example/spec.md").write_text(
            "# Example\n\n## Legacy Impact\n\nClassification: untouched\n", encoding="utf-8"
        )
        (root / ".specify/feature.json").write_text(
            json.dumps(
                {
                    "feature_directory": "specs/001-example",
                    "feature_id": "001",
                    "branch": "test/001-example",
                    "source_sha": "a" * 40,
                    "owner": "test",
                    "risk_lane": "low",
                    "owned_paths": ["specs/001-example"],
                }
            ),
            encoding="utf-8",
        )
        assert context(root) == []
        assert legacy(root / "specs/001-example/spec.md") == []
        (root / "specs/001-example/spec.md").write_text(
            "# Example\n\n## Legacy Impact\n\n- Classification: `untouched`; no legacy surface is changed.\n",
            encoding="utf-8",
        )
        assert legacy(root / "specs/001-example/spec.md") == []
        (root / "specs/001-example/spec.md").write_text(
            "# Example\n\n## Legacy Impact\n\n"
            "Classification: retain-with-exception\n"
            "owner: platform\nexpiry: 2099-12-31\ntrigger: migration complete\n"
            "retirement task: T999\n",
            encoding="utf-8",
        )
        assert legacy(root / "specs/001-example/spec.md") == []
        (root / "specs/001-example/spec.md").write_text(
            "# Example\n\n## Legacy Impact\n\n"
            "Classification: retain-with-exception\n"
            "owner: platform\nexpiry: yesterday\ntrigger: migration complete\n"
            "retirement task: T999\n",
            encoding="utf-8",
        )
        assert any("ISO expiry date" in error for error in legacy(root / "specs/001-example/spec.md"))
        package = root / "package"
        (package / "src/dev_harness").mkdir(parents=True)
        (package / "src/dev_harness/validators.py").write_text(
            "pass" + "word = \"" + "x" * 24 + "\"\n", encoding="utf-8"
        )
        assert package_safety(package)
        documentation = package / "README.md"
        documentation.write_text("api" + '_key = "RealCredential123456"\n', encoding="utf-8")
        assert package_safety(package)
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
    package_root = args.package_root.resolve() if args.package_root else None
    # A package-root scan is intentionally runnable from the standalone
    # harness checkout, which has no consumer project's .specify pointer.
    # Keep context/fragment checks when a caller explicitly supplies a
    # separate consumer root or a spec.
    scan_only = package_root is not None and args.spec is None and root == package_root
    errors = [] if scan_only else context(root) + fragments(root)
    if args.spec:
        errors += legacy(args.spec.resolve())
    if args.package_root:
        assert package_root is not None
        errors += package_consistency(package_root) + package_safety(package_root)
    if errors:
        for error in errors:
            print(f"harness-check: ERROR: {error}", file=sys.stderr)
        return 1
    print("harness-check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
