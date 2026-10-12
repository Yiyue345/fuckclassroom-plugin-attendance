"""Stage wxscan PyO3 wheels and bundle platform-specific native libraries.

Usage:
  package_wxscan.py stage --wheels dist --platform windows-x86_64 --output staged
  package_wxscan.py bundle --artifacts artifacts --native native --require linux-x86_64 windows-x86_64
  package_wxscan.py verify --native native --require linux-x86_64 windows-x86_64
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile

PLATFORM_RE = re.compile(r"^(?:linux|windows|macos)-(?:x86_64|aarch64)$")
MODULE_PREFIX = "fuckclassroom_wxscan."


def _is_extension(name: str, key: str) -> bool:
    if not name.startswith(MODULE_PREFIX):
        return False
    return name.endswith(".pyd") if key.startswith("windows-") else name.endswith(".so")


def stage(wheels: Path, key: str, output: Path) -> Path:
    if not PLATFORM_RE.fullmatch(key):
        raise ValueError(f"Unsupported native platform key: {key}")
    paths = sorted(wheels.glob("*.whl"))
    if len(paths) != 1:
        raise ValueError(f"Expected one built wheel in {wheels}; found {len(paths)}")
    with zipfile.ZipFile(paths[0]) as archive:
        candidates = [
            name for name in archive.namelist()
            if _is_extension(Path(name).name, key) and not name.endswith("/")
        ]
        if len(candidates) != 1:
            raise ValueError(f"Expected one wxscan extension in wheel: {candidates}")
        output.mkdir(parents=True, exist_ok=True)
        target = output / Path(candidates[0]).name
        target.write_bytes(archive.read(candidates[0]))
    print(f"Staged {key}: {target.name}, {target.stat().st_size} bytes")
    return target


def _entry(native: Path, key: str) -> dict[str, str | int]:
    if not PLATFORM_RE.fullmatch(key):
        raise ValueError(f"Invalid platform key: {key}")
    directory = native / key
    binaries = [
        path for path in directory.iterdir()
        if path.is_file() and _is_extension(path.name, key)
    ] if directory.is_dir() else []
    if len(binaries) != 1:
        raise ValueError(f"Expected one native binary for {key}; found {len(binaries)}")
    binary = binaries[0]
    return {
        "file": f"{key}/{binary.name}",
        "sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
        "size": binary.stat().st_size,
    }


def bundle(artifacts: Path, native: Path, required: list[str]) -> None:
    if not required:
        raise ValueError("A release must declare at least one target platform")
    for key in required:
        if not PLATFORM_RE.fullmatch(key):
            raise ValueError(f"Invalid platform key: {key}")
        source_dir = artifacts / f"wxscan-{key}"
        candidates = [
            path for path in source_dir.iterdir()
            if path.is_file() and _is_extension(path.name, key)
        ] if source_dir.is_dir() else []
        if len(candidates) != 1:
            raise ValueError(f"Missing or duplicate compiled wxscan binaries for {key}")
        target_dir = native / key
        target_dir.mkdir(parents=True, exist_ok=True)
        for stale in target_dir.iterdir():
            if stale.is_file():
                stale.unlink()
        shutil.copy2(candidates[0], target_dir / candidates[0].name)
    manifest = {
        "schema_version": 1,
        "platforms": {key: _entry(native, key) for key in sorted(set(required))},
    }
    (native / "_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    verify(native, required)
    print(f"Bundled {len(required)} wxscan platforms")


def verify(native: Path, required: list[str] | None = None) -> None:
    manifest_path = native / "_manifest.json"
    if not manifest_path.exists():
        if required:
            raise ValueError("Release is missing native/_manifest.json")
        if any(native.rglob("*.so")) or any(native.rglob("*.pyd")):
            raise ValueError("Untracked native binary without a manifest")
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("platforms"), dict):
        raise ValueError("Invalid wxscan native manifest")
    platforms = manifest["platforms"]
    for key in required or []:
        if key not in platforms:
            raise ValueError(f"Native manifest is missing {key}")
    for key, recorded in platforms.items():
        if not PLATFORM_RE.fullmatch(key) or not isinstance(recorded, dict):
            raise ValueError(f"Invalid wxscan native entry: {key}")
        current = _entry(native, key)
        if current != recorded:
            raise ValueError(f"wxscan native checksum or path mismatch: {key}")
    if not platforms:
        raise ValueError("Native manifest has no platforms")
    if sorted(str(p.relative_to(native)) for p in native.rglob("*.so") if p.is_file()) + sorted(
        str(p.relative_to(native)) for p in native.rglob("*.pyd") if p.is_file()
    ) != sorted(str(entry["file"]) for entry in platforms.values()):
        raise ValueError("Native directory has untracked binary files")
    print(f"Validated {len(platforms)} wxscan native binaries")


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_subparsers(dest="mode", required=True)
    stage_parser = modes.add_parser("stage")
    stage_parser.add_argument("--wheels", type=Path, required=True)
    stage_parser.add_argument("--platform", required=True)
    stage_parser.add_argument("--output", type=Path, required=True)
    for mode in ("bundle", "verify"):
        sub = modes.add_parser(mode)
        sub.add_argument("--native", type=Path, required=True)
        sub.add_argument("--require", nargs="*", default=[])
        if mode == "bundle":
            sub.add_argument("--artifacts", type=Path, required=True)
    args = parser.parse_args()
    if args.mode == "stage":
        stage(args.wheels, args.platform, args.output)
    elif args.mode == "bundle":
        bundle(args.artifacts, args.native, args.require)
    else:
        verify(args.native, args.require)


if __name__ == "__main__":
    main()
