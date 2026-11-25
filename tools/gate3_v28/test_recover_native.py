import hashlib
from pathlib import Path
import unittest

import numpy as np

from recover_native import (
    FRAME_BYTES, HEIGHT, LUMA_BYTES, WIDTH, CHROMA_BYTES,
    build_palette, decode_native_frame, load_fingerprints, require_hash,
)


class RecoverNativeTests(unittest.TestCase):
    def test_sampling_distinct_grid_cells_and_chroma_planes(self):
        black = [16, 128, 128, 0, 0, 0]
        color = [98, 142, 181, 185, 65, 121]
        palette = build_palette([black, color])
        # Literal Y / Cb / Cr sample sentinels, not generated from the recovery function.
        data = np.empty(FRAME_BYTES, dtype=np.uint8)
        data[:LUMA_BYTES] = 16
        data[LUMA_BYTES:] = 128
        data.reshape(-1)[(1 * 6 + 3) * WIDTH + (2 * 6 + 3)] = 98
        data[LUMA_BYTES + (1 * 3 + 1) * (WIDTH // 2) + (2 * 3 + 1)] = 142
        data[LUMA_BYTES + CHROMA_BYTES + (1 * 3 + 1) * (WIDTH // 2) + (2 * 3 + 1)] = 181
        result = decode_native_frame(data.tobytes(), palette)
        self.assertEqual((180, 320, 3), result.shape)
        self.assertEqual([185, 65, 121], result[1, 2].tolist())
        self.assertEqual([0, 0, 0], result[1, 1].tolist())
        self.assertEqual(371, int(result.sum()))

    def test_unknown_decoded_color_is_not_approximated(self):
        data = bytes([17]) * LUMA_BYTES + bytes([128]) * (2 * CHROMA_BYTES)
        with self.assertRaisesRegex(ValueError, r"17, 128, 128"):
            decode_native_frame(data, build_palette([[16, 128, 128, 0, 0, 0]]))

    def test_truncated_plane_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "frame"):
            decode_native_frame(b"\0" * (FRAME_BYTES - 1), build_palette([[16, 128, 128, 0, 0, 0]]))

    def test_yuv_collision_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "collision"):
            build_palette([[16, 128, 128, 0, 0, 0], [16, 128, 128, 1, 0, 0]])

    def test_detect_tamper_before_loading_table(self):
        anchor = Path(__file__).resolve().with_name("native_fingerprints.json")
        fingerprints = load_fingerprints(anchor)
        self.assertEqual({"spring", "summer", "autumn", "winter"}, set(fingerprints))
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            require_hash(anchor, hashlib.sha256(b"tampered file").hexdigest(), "test")


if __name__ == "__main__":
    unittest.main()
