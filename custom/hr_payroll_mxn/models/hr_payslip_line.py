# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.addons import decimal_precision as dp


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    taxable_amount = fields.Float(digits=dp.get_precision('Payroll'))
    excent_amount =  fields.Float(digits=dp.get_precision('Payroll'), compute="_excent_amount")


    # @api.multi
    def _excent_amount(self):
    	for rec in self:
    		rec.excent_amount = rec.amount-rec.taxable_amount
