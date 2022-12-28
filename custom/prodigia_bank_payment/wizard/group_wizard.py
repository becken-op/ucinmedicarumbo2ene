# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_is_zero, float_round
from datetime import datetime, timedelta, date

"""
wizard de creacion de grupo de pagos
"""

class ProdigiaBankPaymentGroupWizard(models.TransientModel):
    _name = 'prodigia.bank.payment.group.wizard'


    ########### CONSTRAINTS ###########
    @api.constrains('journal_id')
    def _check_journal_id(self):
        """
        valida que el diario seleccionado cuente con un banco,
        y que el banco contenga un valor en el campo
        prodigia_bank
        """
        if not self.journal_id.bank_id:
            raise ValidationError('El diario seleccionado no cuenta con un banco!!')
        if not self.journal_id.bank_id.bic:
            raise ValidationError('El banco del diario asignado no cuenta con una clave definida')


    ########### CAMPOS ###########

    journal_id = fields.Many2one('account.journal',
        string='Diario de pago',
        domain=[('type', 'in', ('bank', 'cash'))],
        required=True,
        )
    # l10n_mx_edi_payment_method_id = fields.Many2one('l10n_mx_edi.payment.method',
    #     string='Metodo de pago',
    #     )
    payment_date = fields.Date(string='Fecha de pago',
        required=True)
    communication = fields.Char(string='Memo')
    company_id = fields.Many2one('res.company',
        'Company',
        default=lambda self: self.env.user.company_id,
        required=True)
    invoice_type = fields.Selection([
            ('out_invoice','Cliente'),
            ('in_invoice', 'Proveedor'),
        ],
        string='Tipo de factura',
        required=True,
        default='in_invoice',)

    group_id = fields.Integer(string='id de grupo',
        help='campo tecnico que almacenara el id del grupo creado, para usarse al llenar los valores de pago')
    currency_id = fields.Many2one('res.currency',
        string='Moneda',
        )
    payment_method_id = fields.Many2one('account.payment.method',
        string='Metodo de pago',
        required=True,
        )
    #borrar
    # partner_id = fields.Many2one('res.partner')


    ########### FUNCIONES DE BOTONES ###########
    def button_create_payment_group(self):
        print('button_create_payment_group')

        #creacion de grupo de pagos
        payment_group = self.create_payment_group()

        #se asigan el id para ser usado al momento de crear los pagos
        self.group_id = payment_group.id

        payment_group.action_open()

        action = self.env.ref('prodigia_bank_payment.menu_bank_payment_group_action').read()[0]
        action['domain'] = [('id','in',[self.group_id,]),]
        return action



    ########### FUNCIONES ###########

    @api.model
    def default_get(self, fields):
        print('default_get')
        res = super(ProdigiaBankPaymentGroupWizard, self).default_get(fields)
        if not self._context.get('from_payments'):
            #si no proviene de pagos, hacer lo sig:
            active_ids = self._context.get('active_ids')
            active_id = self._context.get('active_id')
            active_model = self._context.get('active_model')

            invoice_ids = self._get_invoices()

            #revisar moneda
            first_currency = invoice_ids and invoice_ids[0].currency_id
            print('first_currency.name: ',first_currency.name)
            same_currency = all(invoice_ids.mapped(lambda i: i.currency_id.id == first_currency.id))
            if not same_currency:
                raise ValidationError('Todas las facturas del grupo deben usar la misma moneda')
            invoice_type = self._context.get('invoice_type')

            #obtener valor de memo
            communication = self._get_communication(invoice_ids)

            #si se va a forzar la moneda del pago
            # if self.env.user.company_id.force_payment_group_currency_id:
            #     first_currency = self.env.user.company_id.force_payment_group_currency_id

            res['invoice_type'] = invoice_type
            res['payment_date'] = date.today()
            res['currency_id'] = first_currency.id
            res['communication'] = communication
            if not invoice_type:
                raise ValidationError('Error, no hay un tipo de factura/anticipo definido')
        return res


    def _get_communication(self, invoices):
        """
        obtiene los nombres / refs del record y lo devuelve
        """
        communication = ''
        for rec in invoices:
            communication += str(rec.reference or rec.number or '') + ', '
        # quitar el ultimo ', '
        if len(communication) > 2 and communication[-2:] == ', ':
                communication = communication[0:(len(communication)-2)]
        return communication


    # @api.onchange('currency_id')
    # def _onchange_currency_id(self):
    #     """
    #     cambiar el dominio de journal_id
    #     dependiendo del diario seleccionado
    #     """
    #     print('_onchange_currency_id')
    #     if self.currency_id:

    #         return {'domain': {'journal_id':
    #                 ['|',
    #                     ('currency_id', '=', self.currency_id.id),
    #                     ('currency_id', '=', False),
    #                     ('type','in',('bank','cash')),
    #                     # ('id', 'in', payment_methods_list)
    #                 ]
    #         }}
    #     return {}



    @api.onchange('journal_id')
    def _onchange_journal(self):
        print('_onchange_journal')
        """
        cambiar el dominio de payment_method_id
        dependiendo del diario seleccionado
        """
        if self.journal_id:
            #establecer moneda del diario
            if self.journal_id.currency_id:
                print('cambiar moneda')
                self.currency_id = self.journal_id.currency_id.id

            if self.invoice_type == 'out_invoice':
                payment_type = 'inbound'
            else:
                payment_type = 'outbound'
            # Set default payment method (we consider the first to be the default one)
            payment_methods = payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
            payment_methods_list = payment_methods.ids

            default_payment_method_id = self.env.context.get('default_payment_method_id')
            if default_payment_method_id:
                # Ensure the domain will accept the provided default value
                payment_methods_list.append(default_payment_method_id)
            else:
                self.payment_method_id = payment_methods and payment_methods[0] or False

            # Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
            payment_type = payment_type in ('outbound', 'transfer') and 'outbound' or 'inbound'
            return {'domain':
                {
                    'payment_method_id': [
                        ('payment_type', '=', payment_type),
                        ('id', 'in', payment_methods_list),
                        # ('type','in',('bank','cash')),
                    ]
                }
            }
        return {}


    def create_payment_group(self):
        print('create_payment_group')
        BankPaymentGroup = self.env['prodigia.bank.payment.group']
        vals = self._get_payment_group_vals()
        print('vals: \n',vals)
        return BankPaymentGroup.create(vals)


    def _get_invoices(self):
        print('_get_invoices')
        """
        obtiene facturas seleccionadas de active_ids
        """
        BankPaymentInvoiceLine = self.env['prodigia.bank.payment.invoice.line']
        active_ids = self._context.get('active_ids')
        print('active_ids: ',active_ids)
        invoice_ids = []
        if active_ids:
            payment_invoice_lines = BankPaymentInvoiceLine.browse(active_ids)
            invoice_ids = payment_invoice_lines.mapped('invoice_id')
            # invoice_ids = [rec.invoice_id for rec in payment_invoice_lines]
        return invoice_ids


    def _get_payments(self):
        print('_get_payments')
        """
        obtiene pagos seleccionadas de active_ids
        """
        BankPaymentInvoiceLine = self.env['prodigia.bank.payment.invoice.line']
        active_ids = self._context.get('active_ids')
        print('active_ids: ',active_ids)
        payment_ids = []
        if active_ids:
            payment_invoice_lines = BankPaymentInvoiceLine.browse(active_ids)
            payment_ids = payment_invoice_lines.mapped('payment_id')
            # invoice_ids = [rec.invoice_id for rec in payment_invoice_lines]
        return payment_ids


    def _get_payment_group_vals(self):
        """
        cuando sea un grupo regular, debera tener facturas
        si es basado en anticipos, las facturas deberans er False, y tener pagos
        """
        print('_get_payment_group_vals')
        invoice_ids = self._get_invoices()
        payment_ids = self._get_payments()
        invoices = [(6, 0, invoice_ids.ids)] if invoice_ids != [] else False
        payments = [(6, 0, payment_ids.ids)] if payment_ids != [] else False
        vals = {
            'name': 'Nuevo',
            'state': 'draft',
            'journal_id': self.journal_id.id,
            # 'payment_date': ,
            'currency_id': self.currency_id.id,
            'company_id': self.company_id.id,
            'invoice_ids': invoices,
            'payment_ids': payments,
            'communication': self.communication,
            'payment_method_id': self.payment_method_id.id,
        }
        return vals
