import unittest

import numpy as np

from recover_native import hold_indices, verify_frozen_holds


class ApprovedSourceHolds(unittest.TestCase):
    def test_detect_cyclic_neighbor_hold_not_recent_anywhere(self):
        a = np.array([1, 2, 2, 3, 1], dtype='uint8').reshape(5, 1, 1, 1)
        self.assertEqual(hold_indices(a), (0, 2))
        self.assertEqual(verify_frozen_holds('spring', a, [0, 2]), (0, 2))

    def test_same_count_wrong_phase_refused(self):
        a = np.array([1, 2, 2, 1], dtype='uint8').reshape(4, 1, 1, 1)
        with self.assertRaisesRegex(ValueError, 'hold indices mismatch'):
            verify_frozen_holds('spring', a, [0, 3])

    def test_identical_approved_phases_preserved_as_independent_frames(self):
        a = np.array([1, 1, 2, 3], dtype='uint8').reshape(4, 1, 1, 1)
        indices = verify_frozen_holds('spring', a, [1])
        self.assertEqual(indices, (1,))
        self.assertEqual(len(a), 4)
        self.assertEqual(a[:, 0, 0, 0].tolist(), [1, 1, 2, 3])
