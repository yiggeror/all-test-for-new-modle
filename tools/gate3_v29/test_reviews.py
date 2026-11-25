import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import json
from fractions import Fraction

from review_exports import EXCERPTS, DETAILS, HEROES, media_clock, showinfo_frames, clip_rate_args


class ReviewSourceTests(unittest.TestCase):
    def test_honest_media_clock_and_names(self):
        self.assertEqual(media_clock(0), '00:00:00.000')
        self.assertEqual(media_clock(1440), '00:00:48.000')
        self.assertEqual(media_clock(5916), '00:03:17.200')
        self.assertEqual(HEROES, {'spring':120,'summer':1534,'autumn':3005,'winter':4456})
        self.assertEqual({(s,n) for s,n,*_ in DETAILS}, {('spring','street'),('spring','yard'),('summer','street'),('winter','street')})
        for _,a,b in EXCERPTS:
            self.assertLess(a,b)
            self.assertLessEqual(b,5917)

    def test_ffmpeg_retains_selected_source_pts(self):
        ff=subprocess.run(['ffmpeg','-hide_banner','-nostdin','-f','lavfi','-i','testsrc2=size=16x16:rate=30:duration=1',
            '-vf',"select='eq(n,3)+eq(n,17)',showinfo",'-f','null','-'],capture_output=True,text=True,check=True)
        tick,records=showinfo_frames(ff.stderr)
        self.assertEqual([Fraction(p)*tick for p,_ in records], [Fraction(3,30),Fraction(17,30)])
        self.assertNotEqual(records[0][1],records[1][1])

    def test_mp4_trim_preserves_last_frame_duration(self):
        with TemporaryDirectory() as td:
            out=Path(td)/'fps.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=32x32:rate=30:duration=1',
               '-vf','trim=start_frame=8:end_frame=30,setpts=PTS-STARTPTS','-an','-c:v','libx264','-threads','1',
               *clip_rate_args(),'-movie_timescale','48000',str(out)],check=True)
            v,=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(out)]))['streams']
            self.assertEqual([v['nb_frames'],v['avg_frame_rate'],Fraction(v['duration_ts'])*Fraction(v['time_base'])],
                             ['22','30/1',Fraction(22,30)])

    def test_showinfo_missing_timestamps_not_silently_accepted(self):
        with self.assertRaises(ValueError):
            showinfo_frames('has no actual packet timing')


if __name__=='__main__':
    unittest.main()
