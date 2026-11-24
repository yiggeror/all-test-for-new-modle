import tempfile
import unittest
from pathlib import Path

import assemble
import audio_lock
import reproduce


class Gate31Tests(unittest.TestCase):
    def test_approved_linear_light_curve_and_tail_geometry(self):
        p=assemble.Plan(reproduce.CENTERS,tail=reproduce.TAIL)
        p.validate()
        self.assertEqual(p.origins,(0,1410,2850,4290))
        self.assertEqual(p.tail_begin,5802)
        wave=(0.,.15625,.5,.84375,1.)
        for j,(lo,hi) in enumerate(p.intervals):
            self.assertEqual(tuple(float(p.at(i)[1][j+1]) for i in range(lo,hi+1,15)),wave)
        self.assertEqual(p.at(0)[2],0)
        self.assertEqual(p.at(45)[2],1)
        self.assertEqual(p.at(5916)[2],0)

    def test_mux_preserves_priming_and_timings(self):
        cmd=reproduce.mux_command(Path('vision.mp4'),Path('v2_audio.mp4'),Path('final.mp4'))
        self.assertIn('1:a:0',cmd)
        self.assertEqual(cmd[cmd.index('-movie_timescale')+1],'48000')
        self.assertEqual(cmd[cmd.index('-c')+1],'copy')
        for option in ('-shortest','-ss','-avoid_negative_ts','-itsoffset'):
            self.assertNotIn(option,cmd)

    def test_non_release_cache_rejected_unchanged(self):
        with tempfile.TemporaryDirectory() as path:
            f=Path(path)/'wrong.mp4';f.write_bytes(b'wrong version')
            with self.assertRaisesRegex(ValueError,'不是已签收'):
                audio_lock.acquire(Path(path)/'never-written.mp4',f)
            self.assertEqual(f.read_bytes(),b'wrong version')

    def test_altered_local_split_manifest_refused(self):
        with tempfile.TemporaryDirectory() as path:
            root=Path(path)
            data=root/'previews/gate_2_1/lossless_parts'
            tool=root/'previews/gate_2_1/tools'
            data.mkdir(parents=True);tool.mkdir()
            (data/'MANIFEST.json').write_text('{}\n')
            (tool/'restore_lossless.py').write_text('raise RuntimeError("must not start")')
            with self.assertRaisesRegex(ValueError,'不是 Round 7'):
                reproduce.gate21_inputs(root)


if __name__=='__main__':unittest.main()
