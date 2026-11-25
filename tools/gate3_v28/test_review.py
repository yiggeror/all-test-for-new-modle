import unittest
import numpy as np
from review_cues import CUE_DETAIL,WINTER_ORIGIN,WINTER_FOLEY_PHASES
from review_exports import audio_check,REVIEW_START,REVIEW_FRAMES,X,Y,CW,CH,SAMPLE_START,SAMPLE_STOP

class ReviewCuts(unittest.TestCase):
    def test_crop_carries_full_approved_window_and_precise_seek(self):
        self.assertEqual((X,Y,CW,CH),(1452,588,192,144))
        self.assertEqual(REVIEW_START,4384)
        self.assertEqual(REVIEW_FRAMES,330)
        self.assertEqual(SAMPLE_START,7014400)
        self.assertEqual(SAMPLE_STOP-SAMPLE_START,528000)
        self.assertEqual(CUE_DETAIL['winter_first_film_foley_frames'],[4446,4459])
    def test_audio_synchrony_guard_rejects_deliberate_shift(self):
        reference=np.random.default_rng(38).normal(size=REVIEW_FRAMES*1600)
        same=audio_check(reference.copy(),reference)
        self.assertTrue(all(x['lag_in_samples']==0 and x['correlation']>.999999 for x in same))
        with self.assertRaisesRegex(ValueError,'does not correlate'):
            audio_check(np.roll(reference,92),reference)
if __name__=='__main__':unittest.main()
