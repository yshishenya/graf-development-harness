"""Portable event identity and metadata-only CI receipt contracts."""
from __future__ import annotations

import datetime as dt
import re
from typing import Any

_SHA = re.compile(r"^[0-9a-fA-F]{40}$")
_SAFE = re.compile(r"^[A-Za-z0-9._:-]{1,160}$")
_KEY = re.compile(r"^[A-Za-z0-9._:/-]{1,512}$")
_GROUP_ID = re.compile(r"^[A-Za-z0-9._:-]{1,256}$")
_DIGEST = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
_UTC_RFC3339 = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|\+00:00)$"
)
_EVENTS = {"pull_request", "merge_group", "workflow_dispatch"}
_STATUSES = {"passed", "failed", "cancelled", "superseded", "stale", "ambiguous"}
_DECISIONS = {"pending", "approved", "rejected", "blocked"}
_FEATURE_ID = re.compile(r"^(?:F)?[0-9]{3,}$")


class IdentityError(ValueError):
    """Raised when an event cannot be resolved without guessing."""


def _sha(value: Any, field: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not _SHA.fullmatch(value):
        raise IdentityError(f"{field} must be a full 40-character SHA")
    return value.lower()


def _same(left: Any, right: Any, field: str) -> Any:
    if left is not None and right is not None and left != right:
        raise IdentityError(f"conflicting values for {field}")
    return left if left is not None else right


def _positive(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise IdentityError(f"{field} must be a positive integer")
    return value


def resolve_event_identity(
    event: dict[str, Any],
    event_name: str | None = None,
    *,
    merge_group_id: str | None = None,
    pull_request_numbers: list[int] | None = None,
) -> dict[str, Any]:
    """Resolve PR, merge-group, or manual GitHub payloads fail-closed."""
    if not isinstance(event, dict):
        raise IdentityError("unsupported or malformed event")
    payload_name = event.get("event_name")
    if payload_name is not None and (not isinstance(payload_name, str) or not payload_name.strip()):
        raise IdentityError("event.event_name must be a non-empty string when present")
    if event_name and payload_name and event_name != payload_name:
        raise IdentityError("event_name argument conflicts with event.event_name")
    name = event_name or str(payload_name or "").strip()
    if name not in _EVENTS:
        raise IdentityError("unsupported or malformed event")
    if name == "pull_request":
        pull = event.get("pull_request")
        if not isinstance(pull, dict) or not isinstance(pull.get("head"), dict) or not isinstance(pull.get("base"), dict):
            raise IdentityError("pull_request head and base payloads are required")
        number = _positive(_same(event.get("number"), pull.get("number"), "pull_request.number"), "pull_request.number")
        return {
            "schema_version": 1,
            "event_name": name,
            "target_sha": _sha(pull["head"].get("sha"), "pull_request.head.sha"),
            "base_sha": _sha(pull["base"].get("sha"), "pull_request.base.sha"),
            "pull_request_numbers": [number],
            "merge_group_id": None,
            "concurrency_key": f"pr-{number}",
        }
    if name == "merge_group":
        group = event.get("merge_group")
        if group is None:
            group = {}
        if not isinstance(group, dict):
            raise IdentityError("merge_group payload must be an object")
        target = _sha(_same(event.get("head_sha"), group.get("head_sha"), "merge_group.head_sha"), "merge_group.head_sha")
        base = _sha(_same(event.get("base_sha"), group.get("base_sha"), "merge_group.base_sha"), "merge_group.base_sha")
        group_id = _same(
            _same(
                _same(event.get("id"), event.get("merge_group_id"), "merge_group.id"),
                group.get("id"),
                "merge_group.id",
            ),
            merge_group_id,
            "merge_group.id",
        )
        if not isinstance(group_id, str) or not _GROUP_ID.fullmatch(group_id):
            raise IdentityError("merge_group.id is required and must be safe")
        root_rows, nested_rows = event.get("pull_requests"), group.get("pull_requests")
        if root_rows is not None and nested_rows is not None and root_rows != nested_rows:
            raise IdentityError("conflicting values for merge_group.pull_requests")
        rows = root_rows if root_rows is not None else nested_rows
        root_numbers, nested_numbers = event.get("pull_request_numbers"), group.get("pull_request_numbers")
        if pull_request_numbers is not None:
            if root_numbers is not None and root_numbers != pull_request_numbers:
                raise IdentityError("conflicting values for merge_group.pull_request_numbers")
            if nested_numbers is not None and nested_numbers != pull_request_numbers:
                raise IdentityError("conflicting values for merge_group.pull_request_numbers")
            root_numbers = pull_request_numbers
        if root_numbers is not None and nested_numbers is not None and root_numbers != nested_numbers:
            raise IdentityError("conflicting values for merge_group.pull_request_numbers")
        rows = rows if rows is not None else (root_numbers if root_numbers is not None else nested_numbers)
        if not isinstance(rows, list) or not rows:
            raise IdentityError("merge_group.pull_requests mapping is required")
        numbers = [_positive(row.get("number") if isinstance(row, dict) else row, "merge_group.pull_requests.number") for row in rows]
        if len(numbers) != len(set(numbers)):
            raise IdentityError("merge_group.pull_requests contains duplicate PR numbers")
        explicit_numbers = root_numbers if root_numbers is not None else nested_numbers
        if explicit_numbers is not None:
            if not isinstance(explicit_numbers, list):
                raise IdentityError("merge_group.pull_request_numbers must be a list")
            normalized_explicit = [_positive(number, "merge_group.pull_request_numbers") for number in explicit_numbers]
            if normalized_explicit != numbers:
                raise IdentityError("conflicting merge_group PR mappings")
        return {"schema_version": 1, "event_name": name, "target_sha": target, "base_sha": base,
                "pull_request_numbers": numbers, "merge_group_id": group_id,
                "concurrency_key": f"merge-group-{group_id}"}
    inputs = event.get("inputs")
    if not isinstance(inputs, dict):
        raise IdentityError("workflow_dispatch.inputs is required")
    target = _same(inputs.get("target_sha"), inputs.get("requested_sha"), "workflow_dispatch target SHA")
    target_sha = _sha(target, "workflow_dispatch target SHA")
    return {"schema_version": 1, "event_name": name, "target_sha": target_sha,
            "base_sha": None, "pull_request_numbers": [], "merge_group_id": None,
            "concurrency_key": f"manual-{target_sha}"}


def ci_receipt(data: Any) -> list[str]:
    """Validate a metadata-only receipt and reject stale terminal states."""
    if not isinstance(data, dict):
        return ["receipt must be a JSON object"]
    errors: list[str] = []
    required = ("schema_version", "status", "event_name", "workflow", "run_id", "run_attempt",
                "workflow_url", "target_sha", "base_sha", "pull_request_numbers", "merge_group_id",
                "requested_sha", "observed_sha_start", "observed_sha_end", "final_cleanliness",
                "local_evidence_digest", "started_at", "finished_at")
    allowed = set(required) | {"reason", "final_cleanliness_reason", "conclusion", "concurrency_key", "cancellation_state", "supersession_state"}
    errors.extend(f"unsupported receipt field: {key}" for key in sorted(set(data) - allowed))
    errors.extend(f"missing {key}" for key in required if key not in data)
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    status, event = data.get("status"), data.get("event_name")
    if not isinstance(status, str) or status not in _STATUSES:
        errors.append("invalid status")
    if not isinstance(event, str) or event not in _EVENTS:
        errors.append("invalid event_name")
    for key in ("workflow", "run_id"):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip() or not _SAFE.fullmatch(value):
            errors.append(f"invalid {key}")
    workflow_url = data.get("workflow_url")
    if not isinstance(workflow_url, str) or not re.fullmatch(r"https://[^\s/]+(?:/[^\s]*)?", workflow_url):
        errors.append("invalid workflow_url")
    attempt = data.get("run_attempt")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        errors.append("run_attempt must be a positive integer")
    for key in ("target_sha", "requested_sha", "observed_sha_start", "observed_sha_end"):
        if not isinstance(data.get(key), str) or not _SHA.fullmatch(data[key]):
            errors.append(f"{key} must be a full 40-character SHA")
    base = data.get("base_sha")
    if base is not None and (not isinstance(base, str) or not _SHA.fullmatch(base)):
        errors.append("base_sha must be null or a full 40-character SHA")
    if event in {"pull_request", "merge_group"} and (not isinstance(base, str) or not _SHA.fullmatch(base)):
        errors.append("base_sha is required for PR and merge_group events")
    pull_numbers = data.get("pull_request_numbers")
    if not isinstance(pull_numbers, list) or any(isinstance(x, bool) or not isinstance(x, int) or x < 1 for x in pull_numbers) or len(set(pull_numbers)) != len(pull_numbers):
        errors.append("pull_request_numbers must contain unique positive integers")
    elif event == "pull_request" and len(pull_numbers) != 1:
        errors.append("pull_request events require exactly one pull request number")
    elif event == "merge_group" and not pull_numbers:
        errors.append("merge_group events require a complete PR mapping")
    group_id = data.get("merge_group_id")
    if event == "merge_group" and (not isinstance(group_id, str) or not _GROUP_ID.fullmatch(group_id)):
        errors.append("merge_group_id is required for merge_group events")
    elif group_id is not None and (not isinstance(group_id, str) or not _SAFE.fullmatch(group_id)):
        errors.append("merge_group_id is invalid")
    elif event != "merge_group" and group_id is not None:
        errors.append("merge_group_id is only valid for merge_group events")
    digest = data.get("local_evidence_digest")
    if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
        errors.append("local_evidence_digest must be sha256:<64 hex>")
    cleanliness = data.get("final_cleanliness")
    if not isinstance(cleanliness, str) or cleanliness not in {"pass", "fail", "stale", "ambiguous"}:
        errors.append("invalid final_cleanliness")
    sha_values = [data.get(key).lower() for key in ("target_sha", "requested_sha", "observed_sha_start", "observed_sha_end")
                  if isinstance(data.get(key), str) and _SHA.fullmatch(data[key])]
    if len(sha_values) == 4 and len(set(sha_values)) != 1:
        errors.append("target and observed SHAs must match")
    if event == "workflow_dispatch":
        if base is not None:
            errors.append("workflow_dispatch base_sha must be null")
        if pull_numbers != []:
            errors.append("workflow_dispatch events cannot contain pull request numbers")
    if status == "passed" and cleanliness != "pass":
        errors.append("passed receipt requires final_cleanliness=pass")
    reason = data.get("reason")
    if reason is not None and (not isinstance(reason, str) or not 0 < len(reason.strip()) <= 1024):
        errors.append("reason must be a non-empty string of at most 1024 characters")
    if status != "passed" and not isinstance(reason, str):
        errors.append("non-passed receipt requires reason")
    final_reason = data.get("final_cleanliness_reason")
    if final_reason is not None and (not isinstance(final_reason, str) or not 0 < len(final_reason.strip()) <= 512):
        errors.append("final_cleanliness_reason must be a non-empty string of at most 512 characters")
    if data.get("conclusion") is not None and data.get("conclusion") != status:
        errors.append("conclusion must match status")
    concurrency = data.get("concurrency_key")
    if concurrency is not None and (not isinstance(concurrency, str) or not _KEY.fullmatch(concurrency)):
        errors.append("invalid concurrency_key")
    cancellation_state = data.get("cancellation_state")
    if cancellation_state is not None and (not isinstance(cancellation_state, str) or cancellation_state not in {"none", "cancelled"}):
        errors.append("invalid cancellation_state")
    supersession_state = data.get("supersession_state")
    if supersession_state is not None and (not isinstance(supersession_state, str) or supersession_state not in {"none", "superseded"}):
        errors.append("invalid supersession_state")
    if status == "cancelled" and cancellation_state != "cancelled":
        errors.append("cancelled receipt requires cancellation_state=cancelled")
    if status == "superseded" and supersession_state != "superseded":
        errors.append("superseded receipt requires supersession_state=superseded")
    if status == "passed" and cancellation_state == "cancelled":
        errors.append("passed receipt cannot have cancellation_state=cancelled")
    if status == "passed" and supersession_state == "superseded":
        errors.append("passed receipt cannot have supersession_state=superseded")
    timestamps: dict[str, dt.datetime] = {}
    for key in ("started_at", "finished_at"):
        value = data.get(key)
        try:
            parsed = (
                dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
                if isinstance(value, str) and _UTC_RFC3339.fullmatch(value)
                else None
            )
            if parsed is None or parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
                raise ValueError
            timestamps[key] = parsed
        except ValueError:
            errors.append(f"{key} must be UTC RFC3339")
    if len(timestamps) == 2 and timestamps["finished_at"] <= timestamps["started_at"]:
        errors.append("finished_at must be after started_at")

    def scan(value: Any, path: str = "receipt") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if re.search(r"(?:raw[_ -]?audio|raw[_ -]?transcript|transcript[_ -]?text|private[_ -]?meeting)", str(key), re.IGNORECASE):
                    errors.append(f"receipt contains forbidden sensitive field: {path}.{key}")
                scan(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                scan(child, f"{path}[{index}]")
        elif isinstance(value, str) and (
            re.search(r"/(?:Users|home|private/var|Volumes)/", value, re.IGNORECASE)
            or ("BEGIN " + "PRIVATE KEY") in value
            or "signed-url" in value.lower()
            or re.search(r"\b(?:raw[_ -]?audio|raw[_ -]?transcript|transcript[_ -]?text|private[_ -]?meeting(?: content)?)\b", value, re.IGNORECASE)
            or re.search(r"\b(?:api[_-]?key|secret|password|token|cookie)\s*[:=]\s*[^\s,;]{1,}", value, re.IGNORECASE)
            or re.search(r"(?:authorization\s*:\s*)?bearer\s+[^\s,;]{1,}", value, re.IGNORECASE)
        ):
            errors.append(f"receipt contains private content in {path}")
    scan(data)
    return errors


def release_train(data: Any) -> list[str]:
    """Validate a frozen release-train manifest and its receipt lineage."""
    if not isinstance(data, dict):
        return ["release train must be a JSON object"]
    required = ("schema_version", "train_id", "source_sha", "base_sha", "synthetic_merge_sha", "post_merge_sha",
                "included_prs", "feature_ids", "merge_group_ids", "pr_receipts",
                "merge_group_receipts", "changelog_digest", "authoritative_full_ci_receipt",
                "decision", "rollback_target")
    allowed = set(required)
    errors = [f"unsupported release train field: {key}" for key in sorted(set(data) - allowed)]
    errors.extend(f"missing {key}" for key in required if key not in data)
    if data.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    train_id = data.get("train_id")
    if not isinstance(train_id, str) or not _KEY.fullmatch(train_id):
        errors.append("train_id must be a safe non-empty string")
    source = data.get("source_sha")
    base = data.get("base_sha")
    for key, value in (("source_sha", source), ("base_sha", base)):
        if not isinstance(value, str) or not _SHA.fullmatch(value):
            errors.append(f"{key} must be a full 40-character SHA")
    synthetic = data.get("synthetic_merge_sha")
    if synthetic is not None and (not isinstance(synthetic, str) or not _SHA.fullmatch(synthetic)):
        errors.append("synthetic_merge_sha must be null or a full 40-character SHA")
    post_merge = data.get("post_merge_sha")
    if post_merge is not None and (not isinstance(post_merge, str) or not _SHA.fullmatch(post_merge)):
        errors.append("post_merge_sha must be null or a full 40-character SHA")

    def unique_positive_list(key: str) -> list[int] | None:
        value = data.get(key)
        if not isinstance(value, list) or not value or any(
            isinstance(item, bool) or not isinstance(item, int) or item < 1 for item in value
        ) or len(set(value)) != len(value):
            errors.append(f"{key} must contain unique positive integers")
            return None
        return value

    included_prs = unique_positive_list("included_prs")

    def unique_strings(key: str, pattern: re.Pattern[str], *, non_empty: bool = True) -> list[str] | None:
        value = data.get(key)
        if not isinstance(value, list) or (non_empty and not value) or any(
            not isinstance(item, str) or not pattern.fullmatch(item) for item in value
        ) or len(set(value)) != len(value):
            errors.append(f"{key} must contain unique safe strings")
            return None
        return value

    feature_ids = unique_strings("feature_ids", _FEATURE_ID)
    merge_group_ids = unique_strings("merge_group_ids", _GROUP_ID, non_empty=False)
    def validate_lineage(
        key: str,
        expected_event: str,
        expected_ids: list[int] | list[str] | None,
        expected_target: str | None,
    ) -> None:
        receipts = data.get(key)
        if not isinstance(receipts, list):
            errors.append(f"{key} must be a JSON array")
            return
        observed_ids: list[int | str] = []
        for index, receipt in enumerate(receipts):
            receipt_errors = ci_receipt(receipt)
            errors.extend(f"{key}[{index}]: {error}" for error in receipt_errors)
            if isinstance(receipt, dict) and receipt.get("event_name") != expected_event:
                errors.append(f"{key}[{index}] event_name must be {expected_event}")
            if isinstance(receipt, dict) and expected_event == "pull_request":
                numbers = receipt.get("pull_request_numbers")
                if (
                    isinstance(numbers, list)
                    and len(numbers) == 1
                    and isinstance(numbers[0], int)
                    and not isinstance(numbers[0], bool)
                ):
                    observed_ids.append(numbers[0])
                else:
                    errors.append(f"{key}[{index}] must identify exactly one pull request")
            elif isinstance(receipt, dict) and expected_event == "merge_group":
                group_id = receipt.get("merge_group_id")
                if isinstance(group_id, str) and _GROUP_ID.fullmatch(group_id):
                    observed_ids.append(group_id)
                else:
                    errors.append(f"{key}[{index}] must identify one valid merge group")
            if isinstance(receipt, dict) and expected_target is not None:
                target = receipt.get("target_sha")
                if isinstance(target, str) and _SHA.fullmatch(target) and target.lower() != expected_target.lower():
                    errors.append(f"{key}[{index}] target_sha must match its release-train target SHA")
        if expected_ids is not None:
            expected_set = set(expected_ids)
            observed_set = set(observed_ids)
            if len(observed_ids) != len(observed_set):
                errors.append(f"{key} must contain at most one receipt per declared identity")
            if observed_set - expected_set:
                errors.append(f"{key} contains identities not declared by the release train")
            if expected_set - observed_set:
                errors.append(f"{key} must cover every declared identity")

    source_target = source if isinstance(source, str) and _SHA.fullmatch(source) else None
    synthetic_target = synthetic if isinstance(synthetic, str) and _SHA.fullmatch(synthetic) else None
    post_merge_target = post_merge if isinstance(post_merge, str) and _SHA.fullmatch(post_merge) else None
    authoritative_target = synthetic_target or post_merge_target or source_target
    validate_lineage("pr_receipts", "pull_request", included_prs, source_target)
    validate_lineage("merge_group_receipts", "merge_group", merge_group_ids, synthetic_target)
    authoritative = data.get("authoritative_full_ci_receipt")
    if authoritative is not None:
        receipt_errors = ci_receipt(authoritative)
        errors.extend(f"authoritative_full_ci_receipt: {error}" for error in receipt_errors)
        if isinstance(authoritative, dict) and authoritative.get("status") != "passed":
            errors.append("authoritative_full_ci_receipt must be passed")
        if isinstance(authoritative, dict) and authoritative_target is not None:
            target = authoritative.get("target_sha")
            if isinstance(target, str) and _SHA.fullmatch(target) and target.lower() != authoritative_target.lower():
                errors.append("authoritative_full_ci_receipt target_sha must match its release-train target SHA")
    digest = data.get("changelog_digest")
    if not isinstance(digest, str) or not _DIGEST.fullmatch(digest):
        errors.append("changelog_digest must be sha256:<64 hex>")
    decision = data.get("decision")
    if not isinstance(decision, str) or decision not in _DECISIONS:
        errors.append("invalid decision")
    if decision == "approved" and not isinstance(authoritative, dict):
        errors.append("approved release train requires authoritative_full_ci_receipt")
    rollback = data.get("rollback_target")
    if not isinstance(rollback, str) or not _KEY.fullmatch(rollback):
        errors.append("rollback_target must be a safe non-empty string")
    if merge_group_ids is not None and merge_group_ids and synthetic is None:
        errors.append("merge_group_ids require synthetic_merge_sha")
    return errors


def self_test() -> None:
    """Run dependency-free contract checks used by the package smoke test."""
    sha = "a" * 40
    identity = resolve_event_identity({"event_name": "merge_group", "merge_group": {
        "head_sha": sha, "base_sha": "b" * 40, "id": "mg-1", "pull_requests": [{"number": 7}]
    }})
    assert identity["concurrency_key"] == "merge-group-mg-1"
    native_identity = resolve_event_identity(
        {"event_name": "merge_group", "merge_group": {"head_sha": sha, "base_sha": "b" * 40}},
        merge_group_id="mg-native",
        pull_request_numbers=[7, 8],
    )
    assert native_identity["pull_request_numbers"] == [7, 8]
    assert native_identity["merge_group_id"] == "mg-native"
    try:
        resolve_event_identity(
            {"event_name": "merge_group", "merge_group": {"head_sha": sha, "base_sha": "b" * 40}},
            merge_group_id="x" * 257,
            pull_request_numbers=[7],
        )
    except IdentityError:
        pass
    else:
        raise AssertionError("oversized merge-group id must be rejected")
    good = {
        "schema_version": 1, "status": "passed", "event_name": "pull_request", "workflow": "governance", "run_id": "run-1", "run_attempt": 1,
        "workflow_url": "https://github.com/example/project/actions/runs/1", "target_sha": sha, "base_sha": "b" * 40, "pull_request_numbers": [1], "merge_group_id": None,
        "requested_sha": sha, "observed_sha_start": sha, "observed_sha_end": sha, "final_cleanliness": "pass", "local_evidence_digest": "sha256:" + "c" * 64,
        "started_at": "2026-01-01T00:00:00Z", "finished_at": "2026-01-01T00:01:00Z",
        "concurrency_key": "pr-1",
    }
    assert ci_receipt(good) == []
    assert ci_receipt({**good, "observed_sha_end": "d" * 40})
    assert ci_receipt({**good, "started_at": "2026-W01-1T00:00:00Z"})
    assert ci_receipt({**good, "cancellation_state": "cancelled"})
    assert ci_receipt({**good, "supersession_state": "superseded"})
    train = {
        "schema_version": 1, "train_id": "train-example", "source_sha": sha, "base_sha": "b" * 40,
        "synthetic_merge_sha": None, "post_merge_sha": None, "included_prs": [1], "feature_ids": ["001"],
        "merge_group_ids": [], "pr_receipts": [good], "merge_group_receipts": [],
        "changelog_digest": "sha256:" + "c" * 64, "authoritative_full_ci_receipt": None,
        "decision": "pending", "rollback_target": "previous-successful-release",
    }
    assert release_train(train) == []
    assert release_train({**train, "included_prs": [1, 2]})
    assert release_train({**train, "decision": "approved"})
    two_pr_train = {
        **train,
        "included_prs": [1, 2],
        "feature_ids": ["001"],
        "pr_receipts": [good, {**good, "pull_request_numbers": [2], "concurrency_key": "pr-2"}],
    }
    assert release_train(two_pr_train) == []
    synthetic = "c" * 40
    merge_receipt = {
        **good,
        "event_name": "merge_group",
        "target_sha": synthetic,
        "requested_sha": synthetic,
        "observed_sha_start": synthetic,
        "observed_sha_end": synthetic,
        "pull_request_numbers": [7],
        "merge_group_id": "mg-1",
        "concurrency_key": "merge-group-mg-1",
    }
    authoritative = {
        **good,
        "event_name": "workflow_dispatch",
        "target_sha": synthetic,
        "requested_sha": synthetic,
        "observed_sha_start": synthetic,
        "observed_sha_end": synthetic,
        "base_sha": None,
        "pull_request_numbers": [],
        "merge_group_id": None,
        "concurrency_key": "manual-" + synthetic,
    }
    synthetic_train = {
        **train,
        "synthetic_merge_sha": synthetic,
        "post_merge_sha": "d" * 40,
        "merge_group_ids": ["mg-1"],
        "merge_group_receipts": [merge_receipt],
        "authoritative_full_ci_receipt": authoritative,
        "decision": "approved",
    }
    assert release_train(synthetic_train) == []
    assert release_train({**synthetic_train, "merge_group_receipts": []})
    assert release_train({**synthetic_train, "authoritative_full_ci_receipt": {**authoritative, "target_sha": sha}})
    malformed = {**good, "target_sha": {}}
    assert ci_receipt(malformed)
