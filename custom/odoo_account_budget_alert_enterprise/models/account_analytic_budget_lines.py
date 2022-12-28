# -*- coding: utf-8 -*-
from odoo import models, fields, api


class CrossoveredBudgetLines(models.Model):

	_inherit = 'crossovered.budget.lines'
	
	custom_configuration_state = fields.Selection([
        ('stop', 'Stop / Restrict'),
        ('warn', 'Warn Message'),
        ('warn_stop', 'Warn Message and Stop / Restrict'),
        ('ignore', 'Ignore'),],
        string="Alert Type",
        default='warn',
    )
