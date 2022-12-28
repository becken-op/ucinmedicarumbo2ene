# -*- coding: utf-8 -*-
from odoo import models, fields, api, exceptions, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    bant_warning_percentage = fields.Float(
        string='Warning Percentage',
        default=40.0,
        help="If any Opportunity is less than this percentage, a warning is going to be created.")

    bant_warning_user_ids = fields.Many2many(
        comodel_name='res.users',
        relation='bant_warning_user_res_company_rel',
        column1='user_id',
        column2='company_id',
        string="Warning Users",
        help='Define the users who are going to receive the warning.')
