#!/usr/bin/env python3
"""Create deterministic release assets, checksum manifest and provenance."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path


SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
VERSION_RE = re.compile(r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_source_archive(repository: str, source_sha: str, destination: Path) -> str:
    """Download the exact codeload archive addressed by ``source_sha``."""
    url = f"https://codeload.github.com/{repository}/tar.gz/{source_sha}"
    request = urllib.request.Request(url, headers={"User-Agent": "development-process-harness"})
    with urllib.request.urlopen(request, timeout=60) as response, destination.open("wb") as stream:
        stream.write(response.read())
    return url


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, help="GitHub owner/repository")
    parser.add_argument("--version", required=True, help="release SemVer without the v prefix")
    parser.add_argument("--source-sha", required=True, help="exact 40-character commit SHA")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    if not VERSION_RE.fullmatch(args.version):
        parser.error("version must be SemVer MAJOR.MINOR.PATCH")
    if not SHA_RE.fullmatch(args.source_sha):
        parser.error("source-sha must be a full 40-character git SHA")
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", args.repository):
        parser.error("repository must be owner/repository")

    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    archive = output_dir / f"development-process-harness-v{args.version}.source.tar.gz"
    try:
        archive_url = download_source_archive(args.repository, args.source_sha, archive)
    except (OSError, urllib.error.URLError) as exc:
        print(f"release-assets: cannot download codeload archive: {exc}", file=sys.stderr)
        return 1

    # Fail closed if GitHub returned an HTML/error payload instead of a gzip
    # archive. This also prevents publishing an accidentally named error page.
    try:
        with tarfile.open(archive, mode="r:gz"):
            pass
    except (OSError, tarfile.TarError) as exc:
        print(f"release-assets: codeload archive is not a valid gzip tarball: {exc}", file=sys.stderr)
        return 1

    assets = sorted(path for path in output_dir.iterdir() if path.is_file() and path.name not in {
        "SHA256SUMS", "RELEASE-PROVENANCE.json"
    })
    if not assets:
        print("release-assets: no release assets found", file=sys.stderr)
        return 1
    checksums = "".join(f"{sha256(path)}  {path.name}\n" for path in assets)
    (output_dir / "SHA256SUMS").write_text(checksums, encoding="utf-8")
    provenance = {
        "schema_version": 1,
        "package": "development-process-harness",
        "version": args.version,
        "source": {
            "repository": f"https://github.com/{args.repository}",
            "commit_sha": args.source_sha.lower(),
            "codeload_url": archive_url,
            "codeload_sha256": sha256(archive),
        },
        "assets": [
            {"name": path.name, "sha256": sha256(path)}
            for path in assets
        ],
        "checksum_manifest": "SHA256SUMS",
    }
    (output_dir / "RELEASE-PROVENANCE.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"release-assets: wrote {len(assets)} assets, SHA256SUMS and RELEASE-PROVENANCE.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
