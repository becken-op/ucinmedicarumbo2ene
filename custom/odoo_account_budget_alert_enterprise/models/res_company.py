# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    budget_warning_percentage = fields.Float(
        string='Warning Percentage',
        default=85.0,
        help="Show Warning if Budget Planned Amount has reached this percentage.")