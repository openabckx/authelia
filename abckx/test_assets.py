"""Check the official brand assets without requiring a live external website."""
import hashlib
import pathlib
import struct
import unittest

ASSETS = pathlib.Path(__file__).resolve().parent / "assets"


class BrandAssets(unittest.TestCase):
    def test_wallpaper_is_test_input_only_not_a_shipped_brand_asset(self):
        self.assertFalse((ASSETS / "background.png").exists())
        fixture = ASSETS.parent / "testdata" / "background.png"
        self.assertEqual((1280, 720), struct.unpack(">II", fixture.read_bytes()[16:24]))
        dockerfile = (ASSETS.parent / "Dockerfile").read_text()
        runtime_stage = dockerfile.split("FROM authelia/base:", 1)[1]
        self.assertNotIn("testdata", runtime_stage)
        self.assertIn("COPY abckx/assets/ /abckx/assets/", runtime_stage)

    def test_logo_is_the_official_touch_icon(self):
        logo = (ASSETS / "logo.png").read_bytes()
        self.assertEqual(b"\x89PNG\r\n\x1a\n", logo[:8])
        self.assertEqual((180, 180), struct.unpack(">II", logo[16:24]))
        self.assertEqual("5d82f6ef5d2406fe3465e6e4f28386a95e403da185174c39c21f9374b113e90b",
                         hashlib.sha256(logo).hexdigest())

    def test_favicon_is_the_official_multi_resolution_icon(self):
        favicon = (ASSETS / "favicon.ico").read_bytes()
        self.assertEqual((0, 1, 4), struct.unpack("<HHH", favicon[:6]))
        self.assertEqual("e692fb7a30e029a06bafeaa193eb42f921d40cd200e9cd1cf5040e18c0ad7045",
                         hashlib.sha256(favicon).hexdigest())


if __name__ == "__main__":
    unittest.main()
