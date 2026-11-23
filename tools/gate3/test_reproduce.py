from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import reproduce


class ReproduceTests(unittest.TestCase):
    def test_repo_root_is_anchored_to_script_not_callers_cwd(self):
        self.assertEqual(reproduce.checkout_root() / "tools/gate3", Path(reproduce.__file__).resolve().parent)

    def test_mux_stream_copy_with_sample_accurate_timescale(self):
        cmd = reproduce.mux_command(Path("v.mp4"), Path("a.m4a"), Path("out.mp4"))
        self.assertEqual(cmd[cmd.index("-c")+1], "copy")
        self.assertEqual(cmd[cmd.index("-movie_timescale")+1], "48000")
        self.assertEqual(cmd[cmd.index("-metadata")+1], "creation_time=2026-11-23T00:00:00Z")
        self.assertNotIn("-shortest", cmd)

    def test_tail_fade_matches_frozen_reviewed_picture(self):
        cmd = reproduce.picture_args(Path('native'), Path('picture.mp4'), Path('qa'))
        tail_frames = int(cmd[cmd.index('--tail-frames')+1])
        self.assertEqual(5917-1-tail_frames, 5802)  # 193.4 s, approved optical and sonic tail.

    def test_existing_bad_output_is_rejected_and_not_replaced(self):
        with TemporaryDirectory() as d:
            p = Path(d)/"master.mp4"
            p.write_bytes(b"original content")
            with self.assertRaisesRegex(ValueError, "已经存在"):
                reproduce.check_existing_master(p)
            self.assertEqual(p.read_bytes(), b"original content")

    def test_review_package_rejects_nonfaststart_container(self):
        def box(tag):
            return b"\x00\x00\x00\x08"+tag
        with TemporaryDirectory() as d:
            p = Path(d)/"misordered.mp4"
            p.write_bytes(box(b"ftyp")+box(b"mdat")+box(b"moov"))
            with self.assertRaisesRegex(ValueError, "faststart"):
                reproduce.verify_faststart(p)


if __name__ == "__main__":
    unittest.main()
