# coding: utf-8

from odoo import fields, models, api, _, tools
import xmlrpc.client
import logging
from lxml.objectify import fromstring
import base64
from datetime import datetime, timedelta
import requests

class PayslipRulesWeb(models.Model):
    _name = "hr.salary.rule.web"

    name = fields.Char(string="Nombre")
    code = fields.Char()
    company_id = fields.Many2one('res.company', string='Company', readonly=True, copy=False, required=True,
        default=lambda self: self.env.company)

    def get_list_rules(self):
        print("---------",self.env.company)
        print("xxxx",self.env.company.edi_payslip_url_bd,self.env.company.edi_payslip_name_bd,self.env.company.edi_payslip_user_bd,self.env.company.edi_payslip_passw_bd)
        url = self.env.company.edi_payslip_url_bd
        db = self.env.company.edi_payslip_name_bd
        username = self.env.company.edi_payslip_user_bd
        password = self.env.company.edi_payslip_passw_bd
        common = xmlrpc.client.ServerProxy(
            '{}/xmlrpc/2/common'.format(url))
        uid = common.authenticate(db, username, password, {})
        models = xmlrpc.client.ServerProxy(
            '{}/xmlrpc/2/object'.format(url))
        response = {}
        model_name = 'payslip.rules'
        response = models.execute_kw(db, uid, password, model_name, 'get_list_rules', [False, 'DEMO700101XXX', 'DEMO700101XXX', 'MX'])
        print("|||||||||||||||||||||||||||||||||||||", response)
        if response['status'] == 'success':
            for res in response['rules']:
                rule = self.env['hr.salary.rule.web'].search_count([('name', '=', res['name']),('code', '=', res['code'])])
                print("-----------",rule)
                if rule == 0:
                    self.env['hr.salary.rule.web'].create({
                            'name': res['name'],
                            'code': res['code'],
                    })

