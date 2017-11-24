from unittest import TestCase

import math

import numpy as np

from mantidimaging.core.reconstruct import cor_tilt


class CorTiltTest(TestCase):

    def test_cors_to_tilt_angle(self):
        theta = cor_tilt.cors_to_tilt_angle(10, 1)
        self.assertAlmostEqual(theta, math.pi / 4)

    def test_tilt_angle_to_cors(self):
        theta = math.pi / 4
        slices = np.linspace(0, 100, 20)
        cors = cor_tilt.tilt_angle_to_cors(theta, 50, slices)
        self.assertAlmostEqual(cors[0], 50.0)
        self.assertAlmostEqual(cors[-1], 150.0)