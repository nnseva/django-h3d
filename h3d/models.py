"""
Mixin defining model with H3 index
"""
import functools
import logging
import operator

import h3

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from h3d import h3d


logger = logging.getLogger(__name__)


class H3DModel(models.Model):
    """Mixin to be used in H3 indexed models"""

    #: Field where we can find the geography point as defined in the GeoDjango
    POINT_FIELD = None

    #: Fields pair where we can find latitude and longitude fields,
    #  either POINT_FIELD, or LATLON_FIELDS should be defined
    LATLON_FIELDS = ()

    #: whether to ignore a special value of (0, 0)
    IGNORE_COORDINATE_ZERO = True

    h3d = models.BigIntegerField(
        null=True, blank=True, db_index=True, editable=False,
        verbose_name=_('H3D'),
        help_text=_('H3 distilled index of the last (15th) level, can be used for range-based search')
    )

    def get_latlon(self):
        """
        Get the lat/lon values pair, or (None, None) of the instance

        :returns: (lat, lon) pair, or (None, None)
        :rtype: Tuple[Optional[float], Optional[float]]
        """
        lat, lon = None, None
        if self.POINT_FIELD:
            point = getattr(self, self.POINT_FIELD)
            if point:
                lat, lon = point.y, point.x
        elif self.LATLON_FIELDS and len(self.LATLON_FIELDS) >= 2:
            lat_field, lon_field = self.LATLON_FIELDS[:2]
            lat, lon = getattr(self, lat_field), getattr(self, lon_field)
        else:
            logger.error('Either POINT_FIELD, or pair of LATLON_FIELDS should determine source of coordinates')

        if lat == 0 and lon == 0:
            if self.IGNORE_COORDINATE_ZERO:
                lat, lon = None, None
        return lat, lon

    @classmethod
    def calc_h3d(cls, lat, lon, res):
        """
        Calculate h3 distilled index for given parameters

        :param lat: Latitude
        :type lat: float
        :param lon: Longiture
        :type lon: float
        :param res: resolution (level, depth) of H3 index, 0-15
        :type res: int
        :returns: h3 distilled index
        :rtype: int
        """
        return h3d.h3s_to_h3d(h3.geo_to_h3(lat, lon, res))

    def get_h3d(self, res):
        """
        Get h3 distilled index for current (probably not saved) values of coordinates

        :param res: resolution (level, depth) of H3 index, 0-15
        :type res: int
        :returns: h3 distilled index
        :rtype: int
        """
        lat, lon = self.get_latlon()
        if lat is not None and lon is not None:
            return self.calc_h3d(lat, lon, res)

    @classmethod
    def filter_h3d_around(cls, lat, lon, res, k_distance=1, queryset=None):
        """
        Filter all instances with the same h3 cell, or in cells around it

        :param lat: latitude
        :param lon: longitude
        :param res: resolution (level, depth) of the index where to find
        :param k_distance: max distance in hexagon cells from the cell containing the start point
            0 for the containing cell only,
            1 for the containing cell and cells immediately around,
            etc.
        :param queryset: the queryset to search in, None means cls.objects.all()
        """
        cells = h3.compact(h3.k_ring(h3.geo_to_h3(lat, lon, res), k_distance))
        d_cells = [h3d.h3s_to_h3d(c) for c in cells]
        filters = [models.Q(h3d__range=h3d.h3d_range(c)) for c in d_cells]
        if not queryset:
            queryset = cls.objects.all()
        return queryset.filter(functools.reduce(operator.or_, filters))

    class Meta:
        abstract = True


@receiver(pre_save)
def h3d_pre_save(sender, instance, raw, using, update_fields, **kw):
    """Synchronize H3 index"""
    if not issubclass(sender, H3DModel):
        return
    instance.h3d = instance.get_h3d(h3d.H3_MAX_RES)
