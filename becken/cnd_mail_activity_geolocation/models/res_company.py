# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    geolocation_maximum_distance_meters = fields.Integer(
        string='Maximum distance in meters',
        default=100,
        help="Maximum distance in meters accepted to make check in activities between the Salesvendor and the Customer Location.")
