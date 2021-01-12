"""
Test model with H3 index
"""
import functools
import logging
import operator

import h3

from django.db import models
from django.contrib.gis.db import models as gmodels
from django.utils.translation import ugettext_lazy as _

from h3d.models import H3DModel


logger = logging.getLogger(__name__)


class TestSimpleModel(H3DModel):
    LATLON_FIELDS = ('lat', 'lon')

    lat = models.FloatField(
        blank=True, null=True,
        verbose_name=_('Latitude'),
        help_text=_('Coordinates')
    )
    lon = models.FloatField(
        blank=True, null=True,
        verbose_name=_('Longitude'),
        help_text=_('Coordinates')
    )
    text = models.TextField(
        blank=True, null=True,
        verbose_name=_('Text'),
        help_text=_('Content')
    )

    def __str__(self):
        return self.text or ('<%s %s>' % (self.lat, self.lon))

    class Meta:
        verbose_name = _('Test Simple Model')
        verbose_name_plural = _('Test Simple Models')


class TestGeoModel(H3DModel, gmodels.Model):
    POINT_FIELD = ('point')

    point = gmodels.PointField(
        blank=True, null=True,
        verbose_name=_('Point'),
        help_text=_('Coordinates')
    )
    text = models.TextField(
        blank=True, null=True,
        verbose_name=_('Text'),
        help_text=_('Content')
    )

    def __str__(self):
        return self.text or ('<%s %s>' % self.get_latlon())

    class Meta:
        verbose_name = _('Test GEO Model')
        verbose_name_plural = _('Test GEO Models')
