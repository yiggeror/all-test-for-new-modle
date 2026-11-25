import unittest
import math
from importlib.util import find_spec
import numpy as np

class PictureCuts(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(find_spec('assemble'), 'native edit decision module not built yet')
        import assemble
        self.a=assemble
        self.p=assemble.Plan((1440,2880,4320),60,45,114,5917)
    def test_cadence_entire_film_four_cycles(self):
        self.p.validate()
        for f in range(1,self.p.frames):
            e=self.p.at(f)
            h=self.p.at(f-1)
            self.assertAlmostEqual(e[1].sum(),1,places=8)
            for j in range(4):
                if h[1][j]>0 and e[1][j]>0:
                    self.assertEqual((e[0][j]-h[0][j])%330,1)
    def test_cut_windows_centers_and_endpoints(self):
        for i,c in enumerate(self.p.centers):
            lo,hi=self.p.intervals[i]
            self.assertEqual(hi-lo,60)
            self.assertEqual(self.p.at(lo)[1][i],1)
            self.assertEqual(self.p.at(lo)[1][i+1],0)
            self.assertEqual(self.p.at(c)[1][i],.5)
            self.assertEqual(self.p.at(c)[1][i+1],.5)
            self.assertEqual(self.p.at(hi)[1][i+1],1)
    def test_open_close_exact_black_without_paused_phase(self):
        self.assertEqual(self.p.at(0)[2],0)
        self.assertEqual(self.p.at(45)[2],1)
        self.assertEqual(self.p.at(5916)[2],0)
        self.assertGreater(self.p.at(5915)[2],0)
        self.assertEqual(self.p.at(5916)[0][3],(self.p.at(5915)[0][3]+1)%330)
    def test_all_opaque_unchanged_resampling_neighbour(self):
        a=self.a
        frames=[np.full((330,180,320,3),color,np.uint8) for color in (255,44,112,2)]
        original=a.compose(self.p,frames,120)
        self.assertEqual(original.shape,(180,320,3))
        self.assertTrue(np.equal(original,255).all())
        self.assertTrue(np.equal(a.compose(self.p,frames,0),0).all())
        actual=a.compose(self.p,frames,1440); self.assertGreater(actual.mean(),187)
        self.assertLess(actual.mean(),195)
    def test_invalid_schedule(self):
        with self.assertRaises(ValueError):self.a.Plan((10,20,30),60,45,114,5917).validate()

if __name__=='__main__':unittest.main()
