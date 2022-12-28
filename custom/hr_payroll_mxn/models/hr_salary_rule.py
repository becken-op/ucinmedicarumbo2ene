# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError, except_orm
from odoo.tools.safe_eval import safe_eval
import xmlrpc.client
import logging
from lxml.objectify import fromstring
import base64
from datetime import datetime, timedelta
import requests



legend = '''
# Available variables:
#----------------------
# payslip: object containing the payslips
# employee: hr.employee object
# contract: hr.contract object
# rules: object containing the rules code (previously computed)
# categories: object containing the computed salary rule categories
# (sum of amount of all rules belonging to that category).
# worked_days: object containing the computed worked days
# inputs: object containing the computed inputs
# smgvdf: float object containing the current Minimal Wage

# Note: returned value have to be set in the variable 'result'

result = rules.NET > categories.NET * 0.10'''

tax_select_options = [
    ('none', 'Never'),
    ('always', 'Always'),
    ('python', 'Python Expression'),
]


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    code_sat = fields.Char('Sat code')
    salary_payment_type_id = fields.Many2one(
        'salary.payment.type', string='Payment type',
    )
    overtime_type_id = fields.Many2one(
        'overtime.type', string='Overtime type',
    )
    tax_select = fields.Selection(
        tax_select_options, 'Taxable Based on', required=True, default='none',
    )
    tax_python_compute = fields.Text(
        'Tax compute code', default=legend,
        help='Tax python compute code',
    )
    tax_fixed_amount = fields.Float(default=0.0)

    hr_salary_rule_web_id = fields.Many2one(
        'hr.salary.rule.web',
        string='Reglas Web',
    )

    amount_select = fields.Selection([
        ('percentage', 'Percentage (%)'),
        ('fix', 'Fixed Amount'),
        ('code', 'Python Code'),
        ('code_web', 'Rule web'),
    ], string='Amount Type', index=True, required=True, default='fix', help="The computation method for the rule amount.")

    # @api.multi
    def _satisfy_condition(self, localdict):
        """ :return: True if the given rule match the condition.
        False otherwise.
        """
        self.ensure_one()

        if self.condition_select == 'none':
            return True
        else:
            try:
                safe_eval(
                    self.condition_python,
                    localdict, mode='exec', nocopy=True,
                )
                return localdict.get('result', False)
            except Exception as err:
                raise ValidationError(
                    _('Wrong python condition defined for salary '
                      'rule %s (%s): %s') %
                    (self.name, self.code, err),
                )

    def _compute_rule(self, localdict):
        """
        :param localdict: dictionary containing the current computation environment
        :return: returns a tuple (amount, qty, rate)
        :rtype: (float, float, float)
        """
        self.ensure_one()
        if self.amount_select == 'fix':
            try:
                return self.amount_fix or 0.0, float(safe_eval(self.quantity, localdict)), 100.0
            except Exception as e:
                raise UserError(_('Wrong quantity defined for salary rule %s (%s).\nError: %s') % (self.name, self.code, e))
        if self.amount_select == 'percentage':
            try:
                return (float(safe_eval(self.amount_percentage_base, localdict)),
                        float(safe_eval(self.quantity, localdict)),
                        self.amount_percentage or 0.0)
            except Exception as e:
                raise UserError(_('Wrong percentage base or quantity defined for salary rule %s (%s).\nError: %s') % (self.name, self.code, e))
        if self.amount_select == 'code':  # python code
            try:
                safe_eval(self.amount_python_compute or 0.0, localdict, mode='exec', nocopy=True)
                return float(localdict['result']), localdict.get('result_qty', 1.0), localdict.get('result_rate', 100.0)
            except Exception as e:
                raise UserError(_('Wrong python code defined for salary rule %s (%s).\nError: %s') % (self.name, self.code, e))
        if self.amount_select == 'code_web':  # python code web
            if self.hr_salary_rule_web_id:
                try:
                    rule = self.get_rule(self.hr_salary_rule_web_id.code)
                    print("rule -----------------------------------------------------------",rule)
                    safe_eval(rule or 0.0, localdict, mode='exec', nocopy=True)
                    return float(localdict['result']), localdict.get('result_qty', 1.0), localdict.get('result_rate', 100.0)
                except Exception as e:
                    raise UserError(_('Wrong python code defined for salary rule %s (%s).\nError: %s') % (self.name, self.code, e))


    # @api.multi
    def compute_tax(self, localdict, rule):
        """
        Eval amount tax based on tax_select rule defined for salary rule
        :param localdict: dictionary containing the environement in which to
        compute the rule
        :return: returns a float as the tax amount computed
        :rtype: float
        """
        self.ensure_one()
        # Date from payslip to ensure use the proper Min wage
        date_from = localdict['payslip'].date_from

        # rule = rule['rules']
        print("SELECCION DE REGLA TAX: ",rule.tax_select)
        if rule.tax_select == 'none':
            taxable_amount = 0
        elif rule.tax_select == 'always':
            taxable_amount = rule.tax_fixed_amount
        else:
            # python code
            try:
                # Get current Minimum Wage
                smgvdf = self.env['hr.payroll'].search(
                    [('date_start', '<=', date_from)], limit=1,
                    order='date_start desc',
                ).smgvdf
                localdict['smgvdf'] = smgvdf
                safe_eval(
                    self.tax_python_compute,
                    localdict, mode='exec', nocopy=True,
                )
                return float(localdict['result'])
            except Exception as e:
                raise ValidationError(
                    _('Wrong python code defined for compute tax amount '
                      'for salary rule %s (%s): %s') % (
                          rule.name, rule.code, e),
                )

        return taxable_amount



    def get_rule(self,code):
        print("-----    get_rule    -----",self.hr_salary_rule_web_id.company_id.edi_payslip_url_bd,self.hr_salary_rule_web_id.company_id.edi_payslip_name_bd,self.hr_salary_rule_web_id.company_id.edi_payslip_user_bd,self.hr_salary_rule_web_id.company_id.edi_payslip_passw_bd)
        url = self.hr_salary_rule_web_id.company_id.edi_payslip_url_bd
        db = self.hr_salary_rule_web_id.company_id.edi_payslip_name_bd
        username = self.hr_salary_rule_web_id.company_id.edi_payslip_user_bd
        password = self.hr_salary_rule_web_id.company_id.edi_payslip_passw_bd
        common = xmlrpc.client.ServerProxy(
            '{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy(
            '{}/xmlrpc/2/object'.format(url))
        response = {}
        model_name = 'payslip.rules'
        response = models.execute_kw(
            db, uid, password, model_name, 'get_rule', [False, 'DEMO700101XXX', 'DEMO700101XXX', code])
        print("|||||||||||||||||||||||||||||||||||||\n", response)
        if response['status'] == 'success':
            return response['rule']
