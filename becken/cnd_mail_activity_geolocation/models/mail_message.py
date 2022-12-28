# -*- coding: utf-8 -*-

from odoo import fields, models
import math
from odoo.tools.misc import clean_context


class Message(models.Model):
    _inherit = 'mail.message'

    check_in_latitude = fields.Float(
        "Check-in Latitude", digits="Geo Location", readonly=True,
    )
    check_in_longitude = fields.Float(
        "Check-in Longitude", digits="Geo Location", readonly=True,
    )
    check_in_date = fields.Datetime(
        "Check-in Date", readonly=True,
    )
    use_geolocation = fields.Boolean(
        string='Use Geolocation',
        related='mail_activity_type_id.use_geolocation',
        help="If marked, this type of activities are going to be able to check in geolocation.")

    def distance(self, origin, destination):
        """
        Calculate the Haversine distance.

        Parameters
        ----------
        origin : tuple of float
            (lat, long)
        destination : tuple of float
            (lat, long)

        Returns
        -------
        distance_in_km : float

        Examples
        --------
        >>> origin = (48.1372, 11.5756)  # Munich
        >>> destination = (52.5186, 13.4083)  # Berlin
        >>> round(distance(origin, destination), 1)
        504.2
        """
        lat1, lon1 = origin
        lat2, lon2 = destination
        radius = 6371  # km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) * math.sin(dlon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = radius * c

        return d
