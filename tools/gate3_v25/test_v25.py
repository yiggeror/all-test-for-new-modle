import hashlib
import tempfile
import unittest
from pathlib import Path
from assemble import Plan
from reproduce import gate25_inputs,restore_scene,mux_command,root,rgb_locks
from audio_lock import RELEASE_BYTES,COUNT,RELEASE_SHA256

class Version25Boundaries(unittest.TestCase):
 def test_manifest_selects_exact_17_numbered_round19_parts(self):
    _,m=gate25_inputs(root())
    self.assertEqual([len(m[s]['parts']) for s in ('spring','summer','autumn','winter')],[1,8,2,6])
 def test_modified_numbered_part_is_refused_and_no_partial_leak(self):
    with tempfile.TemporaryDirectory() as t:
        p=Path(t); r=p/'lossless_parts/spring';r.mkdir(parents=True)
        (r/'part-00.bin').write_bytes(b'bad')
        k=hashlib.sha256(b'new').hexdigest()
        item=dict(output='spring_loop.mp4',bytes=3,sha256=k,parts=[dict(path='lossless_parts/spring/part-00.bin',bytes=3,sha256=k)])
        with self.assertRaises(ValueError):restore_scene(p,'spring',item,p/'out')
        self.assertEqual(list((p/'out').iterdir()),[])
 def test_visual_locks_are_complete_and_contiguous(self):
    d=rgb_locks()
    pts=[i for row in d['domains'].values() for i in range(row['frames_inclusive'][0],row['frames_inclusive'][1]+1)]
    self.assertEqual(pts,list(range(5917)))
    for k in ('summer','winter'):
        self.assertEqual(d['domains'][k]['rgb_sha256'],d['domains'][k]['prior_rgb_sha256'])
    self.assertEqual(Plan((1440,2880,4320)).tail_begin,5802)
 def test_muxe_uses_prior_release_audio_only_and_no_audio_reencode(self):
    c=mux_command('picture.mp4','v24.mp4','out.mp4')
    self.assertEqual([c[j+1] for j,k in enumerate(c) if k=='-map'],['0:v:0','1:a:0'])
    self.assertIn('copy',c);self.assertNotIn('-shortest',c);self.assertNotIn('aac',c)
    self.assertEqual(RELEASE_BYTES,132852726);self.assertEqual(COUNT,9247)
    self.assertEqual(RELEASE_SHA256,'a9870ce471487b76b68c93eb779a075182e5d1b28b3e18d145aae99f480d0687')
