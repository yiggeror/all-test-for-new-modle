"""Round 33 timeline/input contract. Run from clean checkout with unittest discover."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from io import BytesIO

import numpy as np

from assemble import DOMAINS, ENCODE_ARGS, FRAME_LIMIT, PLAN, compose, rgb_locks
from audio_lock import RELEASE_SHA256, RELEASE_URL, download_release
from reproduce import gate29_inputs, restore_scene, MASTER, mux_command


class PictureTimeline(unittest.TestCase):
    def test_exact_frames_and_overlap(self):
        self.assertEqual(FRAME_LIMIT, 5917)
        self.assertEqual(PLAN.centers, (1440, 2880, 4320))
        self.assertEqual(PLAN.intervals, ((1410, 1470), (2850, 2910), (4290, 4350)))
        self.assertEqual(PLAN.origins, (0, 1410, 2850, 4290))
        for n, (first, last) in enumerate(PLAN.intervals):
            _, start, _ = PLAN.at(first)
            phase, middle, _ = PLAN.at(first + 30)
            _, end, _ = PLAN.at(last)
            self.assertEqual(phase[n + 1], 30)
            self.assertEqual((start[n], middle[n], middle[n + 1], end[n + 1]), (1, .5, .5, 1))

    def test_black_to_scene_and_tail_to_black(self):
        self.assertEqual(PLAN.tail_begin, 5802)
        self.assertEqual([PLAN.at(i)[2] for i in (0, 45, 5802, 5916)], [0, 1, 1, 0])
        raw = np.broadcast_to(np.full((180, 320, 3), 160, np.uint8), (330, 180, 320, 3))
        a = (raw,) * 4
        self.assertTrue((compose(PLAN, a, 0) == 0).all())
        self.assertTrue((compose(PLAN, a, 45) == 160).all())
        self.assertTrue((compose(PLAN, a, 5916) == 0).all())

    def test_linear_light_midpoint_not_code_value_average(self):
        a = tuple(np.broadcast_to(np.full((180, 320, 3), c, np.uint8), (330, 180, 320, 3)) for c in (0, 255, 0, 255))
        self.assertTrue((compose(PLAN, a, 1440) == 188).all())

    def test_autumn_is_exactly_the_signed_unblended_domain(self):
        self.assertEqual(DOMAINS['autumn'], (2910, 4290))
        ref = '60273e5639377f2beb915787cf65d5ae66f9302b2647b1813812473a0f5bfb09'
        lock = rgb_locks()['domains']['autumn']
        self.assertEqual((lock['rgb_sha256'], lock['prior_rgb_sha256']), (ref, ref))
        self.assertEqual(lock['native_changed_pixels_summed'], 0)

    def test_encoder_contract(self):
        self.assertEqual(ENCODE_ARGS[ENCODE_ARGS.index('-profile:v') + 1], 'high')
        self.assertEqual(ENCODE_ARGS[ENCODE_ARGS.index('-crf') + 1], '14')
        self.assertEqual(ENCODE_ARGS[ENCODE_ARGS.index('-colorspace') + 1], 'bt709')
        self.assertIn('1920:1080:flags=neighbor', ENCODE_ARGS[ENCODE_ARGS.index('-vf')+1])
        self.assertIn('+faststart', ENCODE_ARGS)


class Sources(unittest.TestCase):
    def test_accepts_only_signed_manifest_and_exact_count(self):
        root = Path(__file__).resolve().parents[2]
        _, manifest = gate29_inputs(root)
        self.assertEqual([len(manifest[s]['parts']) for s in ('spring','summer','autumn','winter')], [1,8,1,6])

    def test_rejects_rehashed_proxy_or_missing_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            pp = root / 'previews' / 'gate_2_9' / 'lossless_parts'
            pp.mkdir(parents=True)
            (pp / 'MANIFEST.json').write_text(json.dumps({'spring': {'output': 'spring_not_approved.mp4'}}))
            with self.assertRaisesRegex(ValueError, 'Round 33'):
                gate29_inputs(root)

    def test_corrupted_part_fails_without_leaving_a_complete_file(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            wrong = root / 'lossless_parts' / 'spring' / 'part-00.bin'
            wrong.parent.mkdir(parents=True)
            wrong.write_bytes(b'bad')
            m = {'output': 'spring_loop.mp4', 'parts': [{'path': 'lossless_parts/spring/part-00.bin', 'bytes': 3, 'sha256': '0'*64}]}
            with self.assertRaisesRegex(ValueError, 'SHA-256'):
                restore_scene(root, 'spring', m, root / 'out')
            self.assertFalse((root / 'out' / 'spring_loop.mp4').exists())

    def test_transient_download_retries_without_leaving_a_partial_asset(self):
        class PartialResponse(BytesIO):
            def read(self, *args):
                if not self.tell():
                    return super().read(1)
                raise ConnectionResetError('lost connection after first byte')
        class RecoveringSession:
            def __init__(self):
                self.attempts=iter((PartialResponse(b"oops"), BytesIO(b"abc")))
            def open(self, request, timeout):
                if request.full_url != RELEASE_URL or timeout > 60:
                    raise AssertionError('unexpected source URL or unbounded timeout')
                return next(self.attempts)
        with tempfile.TemporaryDirectory() as td, patch('audio_lock.RELEASE_BYTES',3), patch('audio_lock.sleep'):
            path=Path(td)/'release.mp4'
            download_release(path,opener=RecoveringSession())
            self.assertEqual(path.read_bytes(), b'abc')
            self.assertFalse(path.with_suffix('.download').exists())

    def test_release_and_mux_are_audio_only_copy_from_v28(self):
        self.assertTrue(RELEASE_URL.endswith('/v2.8-rainroji-lofi-1080p/Rainroji_Lofi_V2.8_1080p.mp4'))
        self.assertEqual(RELEASE_SHA256, '515b5185225f2c8c27ec7906dc5d77de112f9f943d76d9a6a7017abb59502cc9')
        self.assertEqual(MASTER, 'Rainroji_Lofi_V2.9_1080p.mp4')
        cmd = mux_command(Path('assembled.mp4'), Path('official.mp4'), Path(MASTER))
        self.assertEqual([cmd[i+1] for i,k in enumerate(cmd) if k=='-map'], ['0:v:0','1:a:0'])
        self.assertEqual(cmd[cmd.index('-c:a')+1], 'copy')


if __name__ == '__main__':
    unittest.main()
