# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    geolocation_maximum_distance_meters = fields.Integer(
        string='Maximum distance in meters',
        related='company_id.geolocation_maximum_distance_meters',
        readonly=False,
        help="Maximum distance in meters accepted to mark as done activities between the Salesvendor and the Customer Location.")
