"""Load the optional wxscan binary shipped with the Attendance plugin.

The application host does not own or install this native dependency. If this
platform is unsupported or the bundled binary is invalid, scanner.py falls
back to OpenCV.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import platform
from pathlib import Path
import sys


def platform_key() -> str:
    system = platform.system().lower()
    if system == "darwin":
        system = "macos"
    machine = platform.machine().lower()
    if machine in {"amd64", "x86_64", "x64"}:
        machine = "x86_64"
    elif machine in {"arm64", "aarch64"}:
        machine = "aarch64"
    return f"{system}-{machine}"


def load_native_extension():
    """Import only an integrity-checked extension from this plugin directory."""
    native_dir = Path(__file__).resolve().parent
    manifest_path = native_dir / "_manifest.json"
    if not manifest_path.is_file():
        raise ImportError("Attendance release has no bundled wxscan native extension")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1:
        raise ImportError("Unsupported Attendance native manifest")
    item = manifest.get("platforms", {}).get(platform_key())
    if not isinstance(item, dict):
        raise ImportError(f"wxscan native extension unavailable for {platform_key()}")

    relative = item.get("file")
    digest = item.get("sha256")
    if not isinstance(relative, str) or not isinstance(digest, str):
        raise ImportError("Invalid wxscan native manifest entry")
    binary = (native_dir / relative).resolve()
    if native_dir.resolve() not in binary.parents or not binary.name.startswith("fuckclassroom_wxscan."):
        raise ImportError("Invalid wxscan binary path")
    if binary.suffix not in {".so", ".pyd"} or not binary.is_file():
        raise ImportError("Missing wxscan native binary")
    if hashlib.sha256(binary.read_bytes()).hexdigest() != digest:
        raise ImportError("wxscan native binary checksum mismatch")

    name = f"{__name__}.fuckclassroom_wxscan"
    cached = sys.modules.get(name)
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(name, binary)
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load packaged wxscan native binary")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module
