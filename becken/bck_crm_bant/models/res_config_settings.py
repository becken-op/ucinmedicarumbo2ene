# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    bant_warning_percentage = fields.Float(
        string='Warning Percentage',
        related='company_id.bant_warning_percentage',
        readonly=False,
        help="If any Opportunity is less than this percentage, a warning is going to be created.")

    bant_warning_user_ids = fields.Many2many(
        comodel_name='res.users',
        related='company_id.bant_warning_user_ids',
        readonly=False,
        string="Warning Users",
        help='Define the users who are going to receive the warning.')
