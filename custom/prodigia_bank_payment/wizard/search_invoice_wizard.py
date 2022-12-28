# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_round
from datetime import datetime, timedelta, date


"""
wizard de busqueda de facturas
o pagos
"""


DATE_RANGES = {
    'single': 1,
    'weekly': 7,
    'biweekly': 14,
    '30_days': 30,
    '45_days': 45,
}


class ProdigiaBankPaymentWizard(models.TransientModel):
    _name = 'prodigia.bank.payment.wizard'

    ########### CAMPOS ###########
    type = fields.Selection([
        ('out_invoice', 'Cliente'),
        ('in_invoice', 'Proveedor'),
    ],
        string='Tipo de factura/pago',
        required=True,
        default='in_invoice',)
    filter_type = fields.Selection([
        ('single', '1 dia'),
        ('weekly', '7 dias'),
        ('biweekly', '14 dias'),
        ('30_days', '30 dias'),
        ('45_days', '45 dias'),
    ],
        string='Rango de tiempo',
        required=True,
        default='biweekly',)
    due_type = fields.Selection([
        ('pastdue', 'Facturas vencidas'),
        ('predue', 'Proyeccion de pagos'),
    ],
        string='Tipo de busqueda',
        required=True,
        default='pastdue',)
    company_id = fields.Many2one('res.company',
                                 'Company',
                                 default=lambda self: self.env.user.company_id,
                                 required=True)

    ########### FUNCIONES DE BOTONES ###########

    def button_search_invoices(self):
        """
        busca facturas, cambia estado y devuelve accion de para visualizar
        resultados en vista de arbol
        """
        # print('button_search_invoices')
        self.ensure_one()
        invoices = self._get_invoices()
        #print('invoices: ',invoices)
        lines = self.create_invoice_lines(invoices)
        view_ref = self._get_view()
        if not lines:
            raise ValidationError("No se encontraron facturas abiertas!")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Facturas',
            'res_model': 'prodigia.bank.payment.invoice.line',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', (lines.ids)), ],
            'context': {'search_default_currency_filter': 1, 'search_default_partner_filter': 1},
            # 'res_id': self.id,
            'views': [(view_ref.id, 'tree'), (False, 'form')],
            # 'target': 'new',
        }

    def button_search_payments(self):
        """
        busca pagos (anticipos)
        """
        # print('button_search_payments')
        self.ensure_one()
        invoices = False
        payments = self._get_payments()
        lines = self.create_invoice_lines(invoices, payments)
        view_ref = self._get_view()
        if not lines:
            raise ValidationError("No se encontraron anticipos en borrador!")
        return {
            'type': 'ir.actions.act_window',
            'name': 'Anticipo',
            'res_model': 'prodigia.bank.payment.invoice.line',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', (lines.ids)), ],
            'context': {'search_default_currency_filter': 1, 'search_default_partner_filter': 1},
            # 'res_id': self.id,
            'views': [(view_ref.id, 'tree'), (False, 'form')],
            # 'target': 'new',
        }

    ########### FUNCIONES ###########

    def _get_view(self):
        """
        selecciona la vista correspondiente a mostrar,
        dependiendo del rango de dias seleccionado
        """
        # print('_get_view')
        view_ref = False
        if self.filter_type == 'single':
            view_ref = self.env.ref(
                'prodigia_bank_payment.prodigia_bank_payment_invoice_line_single_tree')
        if self.filter_type == 'weekly':
            view_ref = self.env.ref(
                'prodigia_bank_payment.prodigia_bank_payment_invoice_line_weekly_tree')
        elif self.filter_type == 'biweekly':
            view_ref = self.env.ref(
                'prodigia_bank_payment.prodigia_bank_payment_invoice_line_biweekly_tree')
        elif self.filter_type == '30_days':
            view_ref = self.env.ref(
                'prodigia_bank_payment.prodigia_bank_payment_invoice_line_30_tree')
        elif self.filter_type == '45_days':
            view_ref = self.env.ref(
                'prodigia_bank_payment.prodigia_bank_payment_invoice_line_45_tree')
        if not view_ref:
            raise ValidationError(
                "No se encontro una vista definida para el rango {}".format(self.filter_type))
        #print('view_ref: ', view_ref)
        return view_ref

    def create_invoice_lines(self, invoices, payments=False):
        """
        crea lineas de facturas
        si invoices= False, significa que las lineas seran en base
        a pagos (anticipos)
        """
        # print('create_invoice_lines')
        self.ensure_one()
        self.invoice_line_ids = False
        ProdigiaInvoiceLine = self.env['prodigia.bank.payment.invoice.line']
        val_list = []
        res = False
        if invoices:
            for invoice in invoices:
                val_list.append({
                    # 'wizard_id': self.id,
                    'day_range': DATE_RANGES[self.filter_type],
                    'invoice_id': invoice.id,
                })
        elif payments:
            for payment in payments:
                val_list.append({
                    # 'wizard_id': self.id,
                    'day_range': DATE_RANGES[self.filter_type],
                    'payment_id': payment.id,
                })
        if len(val_list):
            res = ProdigiaInvoiceLine.create(val_list)
        return res

    def _get_search_invoice_domain(self):
        domain = [
            ('state', 'in', ('open',)),
            ('type', '=', self.type),
            ('company_id', '=', self.company_id.id),
            # que no pertenesca a un grupo de pago
            ('prodigia_bank_payment_id', '=', False),
        ]
        return domain

    def _get_invoices(self):
        # print('get_invoices')
        self.ensure_one()
        AccountInvoice = self.env['account.invoice']
        domain = self._get_search_invoice_domain()
        invoices = AccountInvoice.search(domain)
        # se filtran dependiendo del tipo de busqueda
        if self.due_type == 'pastdue':
            invoices = invoices and invoices.filtered(
                lambda invoice: invoice.date_due < fields.date.today())
        else:
            invoices = invoices and invoices.filtered(
                lambda invoice: invoice.date_due >= fields.date.today())
        return invoices

    def _get_search_payment_domain(self, payment_types):
        domain = [
            ('state', 'in', ('draft',)),
            ('payment_type', 'in', payment_types),
            ('company_id', '=', self.company_id.id),
            # que no pertenesca a un grupo de pago
            ('prodigia_bank_payment_id', '=', False),
        ]
        return domain

    def _get_payments(self):
        # print('_get_payments')
        self.ensure_one()
        Accountpayment = self.env['account.payment']
        payment_types = ('inbound',) if self.type == 'out_invoice' else (
            'outbound', 'transfer')
        #print('payment_types: ',payment_types)
        domain = self._get_search_payment_domain(payment_types)
        payments = Accountpayment.search(domain)
        return payments
