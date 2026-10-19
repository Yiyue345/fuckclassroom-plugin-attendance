from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.package_wxscan import bundle, stage, verify
from native import load_native_extension, platform_key


class NativePackageTests(unittest.TestCase):
    def test_stages_wheel_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wheels = root / "wheels"
            wheels.mkdir()
            with zipfile.ZipFile(wheels / "wxscan-test.whl", "w") as archive:
                archive.writestr("fuckclassroom_wxscan.abi3.so", b"test-native-code")
            staged = root / "artifacts" / "wxscan-linux-x86_64"
            stage(wheels, "linux-x86_64", staged)
            native = root / "native"
            bundle(root / "artifacts", native, ["linux-x86_64"])
            verify(native, ["linux-x86_64"])

            manifest = json.loads((native / "_manifest.json").read_text())
            self.assertEqual(manifest["schema_version"], 1)
            entry = manifest["platforms"]["linux-x86_64"]
            target = native / entry["file"]
            self.assertEqual(target.read_bytes(), b"test-native-code")
            target.write_bytes(b"tampered")
            with self.assertRaisesRegex(ValueError, "checksum"):
                verify(native, ["linux-x86_64"])

    def test_does_not_import_host_level_wxscan_if_plugin_has_no_bundle(self):
        if not (Path("native") / "_manifest.json").exists():
            with self.assertRaises(ImportError):
                load_native_extension()

    def test_platform_name_normalization(self):
        from unittest.mock import patch

        with patch("native.platform.system", return_value="Darwin"), patch(
            "native.platform.machine", return_value="arm64"
        ):
            self.assertEqual(platform_key(), "macos-aarch64")


if __name__ == "__main__":
    unittest.main()
