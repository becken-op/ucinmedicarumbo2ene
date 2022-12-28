# -*- coding: utf-8 -*-

from odoo import fields, models


class MailActivityType(models.Model):
    _inherit = 'mail.activity.type'

    use_geolocation = fields.Boolean(
        string='Use Geolocation',
        default=False,
        help="If marked, this type of activities are going to be able to check in geolocation.")

    # restrict_by_distance = fields.Boolean(
    #     string='Restrict by Distance',
    #     default=False,
    #     help="If marked, this type of activities are going to be restrict the distance between the user and the requesting partner.")