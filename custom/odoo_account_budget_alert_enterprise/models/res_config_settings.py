# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    budget_warning_percentage = fields.Float(
        string='Warning Percentage',
        related='company_id.budget_warning_percentage',
        readonly=False,
        help="Show Warning if Budget Planned Amount has reached this percentage.")
