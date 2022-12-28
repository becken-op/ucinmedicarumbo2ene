# -*- coding: utf-8 -*-
from odoo import fields, models


class Lead(models.Model):
    _inherit = 'crm.lead'

    tradename = fields.Char(string="Tradename", store=True, related='partner_id.tradename')
