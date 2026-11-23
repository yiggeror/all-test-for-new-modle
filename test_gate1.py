import unittest

import numpy as np

try:
    from gate1 import camera_signature, grid, upscale1080
except ModuleNotFoundError as error:
    if error.name != "gate1":
        raise
    camera_signature = grid = upscale1080 = None


class PreviewContract(unittest.TestCase):
    def test_exact_native_grids_for_1080p(self):
        self.assertIsNotNone(grid, "The Gate 1 native-grid contract is missing")
        self.assertEqual(grid(320), (320, 180, 6))
        self.assertEqual(grid(384), (384, 216, 5))
        for denied_width in (480, 640, 321, 0):
            with self.subTest(denied_width=denied_width), self.assertRaises(ValueError):
                grid(denied_width)

    def test_1080p_blocks_preserve_each_native_pixel(self):
        self.assertIsNotNone(upscale1080, "The exact nearest-neighbour upscaler is missing")
        for w, h, scale in ((320, 180, 6), (384, 216, 5)):
            source = np.random.default_rng(121).integers(0, 256, (h, w, 3), dtype=np.uint8)
            target = upscale1080(source)
            self.assertEqual(target.shape, (1080, 1920, 3))
            self.assertEqual(target.dtype, source.dtype)
            for y in range(scale):
                for x in range(scale):
                    self.assertTrue(np.array_equal(source, target[y::scale, x::scale]))

    def test_camera_signature_ignores_grid_but_catches_viewport_drift(self):
        self.assertIsNotNone(camera_signature, "The paired camera check is missing")
        from engine.render import Camera
        a = Camera((0, 2, 10), (0, 2, 0), fov=40, W=320, H=180)
        b = Camera((0, 2, 10), (0, 2, 0), fov=40, W=384, H=216)
        moved = Camera((1, 2, 10), (0, 2, 0), fov=40, W=384, H=216)
        wide = Camera((0, 2, 10), (0, 2, 0), fov=44, W=384, H=216)
        self.assertTrue(np.allclose(camera_signature(a), camera_signature(b)))
        self.assertFalse(np.allclose(camera_signature(a), camera_signature(moved)))
        self.assertFalse(np.allclose(camera_signature(a), camera_signature(wide)))


if __name__ == "__main__":
    unittest.main()
