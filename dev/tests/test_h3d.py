"""Module to test H3 Distilled base utility"""
import json
import random
from unittest import mock

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

import h3
from h3d import h3d
from tests import models as test_models

class Test(TestCase):
    """Test"""

    def test_001_utility(self):
        """Test utility functions working"""
        for i in range(15000):
            lat = -90 + random.random() * 180
            lon = -180 + random.random() * 360
            res = i % 16
            s = h3.geo_to_h3(lat, lon, res)
            d = h3d.h3s_to_h3d(s)
            s1 = h3d.h3d_to_h3s(d)
            self.assertEqual(s, s1)  # conversion is reversible
            dmin, dmax = h3d.h3d_range(d)
            self.assertEqual(dmax, d)
            if res > 0:
                p = h3d.h3d_parent(d)
                pmin, pmax = h3d.h3d_range(d, res - 1)
                self.assertEqual(pmax, p)
                self.assertLessEqual(d, pmax)
                self.assertGreaterEqual(d, pmin)

    def test_002_simple_model(self):
        """Test simple model working"""
        for i in range(1500):
            lat = -10 + random.random() * 20
            lon = -20 + random.random() * 40
            test_models.TestSimpleModel.objects.create(lat=lat, lon=lon, text='Point %s %s' % (lat, lon))

        for inst in test_models.TestSimpleModel.objects.all():
            self.assertNotNull(inst.h3d)
            self.assertEqual(inst.h3d, inst.get_h3d(15))

        for i in range(1500):
            lat = -10 + random.random() * 20
            lon = -20 + random.random() * 40
            res = (i % 15) + 1

            k_ring = h3.k_ring(h3.geo_to_h3(lat, lon, res))
            instances = set(test_models.TestSimpleModel.filter_h3d_around(lat, lon, res, k_distance=1))
            if instances:
                compared = set([])
                for c in k_ring:
                    clat, clon = h3.h3_to_geo(c)
                    compared.update(set(test_models.TestSimpleModel.filter_h3d_around(clat, clon, res, k_distance=0)))
                self.assertEqual(instances, compared)

    def test_003_geo_model(self):
        """Test geo model working"""
        for i in range(1500):
            lat = -10 + random.random() * 20
            lon = -20 + random.random() * 40
            test_models.TestGeoModel.objects.create(point=json.dumps({'type': 'Point', 'coordinates':[lon, lat]}), text='Point %s %s' % (lat, lon))

        for inst in test_models.TestSimpleModel.objects.all():
            self.assertNotNull(inst.h3d)
            self.assertEqual(inst.h3d, inst.get_h3d(15))
