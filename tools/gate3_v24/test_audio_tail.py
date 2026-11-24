import unittest
import math
import numpy as np
from audio_tail import weather_gain, apply_weather_delta, recover_f32_gain, zero_verified_black_pcm

class TailGuards(unittest.TestCase):
    def test_exact_join_and_8db_plateau_and_fade(self):
        s = np.array([8_879_999, 8_880_000, 8_880_001, 9_225_599, 9_225_600,
                      9_336_000, 9_400_800, 9_465_599, 9_465_600, 9_467_199])
        a = weather_gain(s)
        self.assertAlmostEqual(float(a[1]), 10**(-5.3/20), places=7)
        self.assertAlmostEqual(float(a[2]), float(a[1]), places=7)
        self.assertAlmostEqual(float(a[4]/a[1]), 10**(8/20), places=6)
        self.assertAlmostEqual(float(a[5]), float(a[4]), places=6)
        self.assertAlmostEqual(float(a[6]/a[4]), .5, places=6)
        self.assertLess(float(a[7]), 1e-8)
        np.testing.assert_array_equal(a[-2:], [0,0])

    def test_tail_delta_never_rescales_prefix_or_removes_other_sound(self):
        b = np.array([[.105,.202],[.325,.407],[.505,.607],[.701,.803]], dtype='f4')
        old, new = np.array([[.1,.2],[.3,.2]], dtype='f4'), np.array([[.1,.2],[.6,.5]], dtype='f4')
        got = apply_weather_delta(b, old, new, start=2)
        np.testing.assert_array_equal(got[:3], b[:3])
        np.testing.assert_allclose(got[3], [1.001,1.103],atol=1e-7)
        np.testing.assert_array_equal(b, np.array([[.105,.202],[.325,.407],[.505,.607],[.701,.803]], dtype='f4'))

    def test_recovers_original_single_precision_stem_calibration(self):
        r = np.random.default_rng(914)
        x = r.uniform(-.24,.23,8500).astype('f4')
        scale = np.float32(.99383544921875)
        self.assertEqual(recover_f32_gain(x, x*scale), scale)
        y = x*scale
        y[10] += .0005
        with self.assertRaises(ValueError):
            recover_f32_gain(x,y)

    def test_only_flush_eq_subnormals_after_blackout(self):
        x=np.array([[1.54e-43,-1.54e-43],[0.,0.]],dtype='f4')
        self.assertAlmostEqual(zero_verified_black_pcm(x),1.54e-43,delta=2e-45)
        np.testing.assert_array_equal(x,[[0,0],[0,0]])
        with self.assertRaises(ValueError):
            zero_verified_black_pcm(np.array([[0.,1e-10]],dtype='f4'))

if __name__ == '__main__':
    unittest.main()
