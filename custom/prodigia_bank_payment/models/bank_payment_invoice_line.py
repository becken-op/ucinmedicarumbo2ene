# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
from odoo import api, exceptions, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError

"""
Modelo quese usa al momento de mostrar
el resultado de la busqueda de las facturas
mostrando el monto de la factura
en la columna de rango correspondiente
al no. de dias de vigencia de dicha factura
"""

class ProdigiaBankPaymentInvoiceLine(models.TransientModel):
    _name = 'prodigia.bank.payment.invoice.line'


    ########### FUNCIONES DE CAMPOS COMPUTADOS ########### 
    @api.multi
    @api.depends('invoice_id','payment_id')
    def _compute_data(self):
        for rec in self:
            if rec.invoice_id:
                rec.partner_id = rec.invoice_id.partner_id.id
                rec.date_due = rec.invoice_id.date_due
                rec.amount_total = rec.invoice_id.residual
                rec.bank = rec.invoice_id.partner_bank_id.id
                rec.currency_id = rec.invoice_id.currency_id.id
            elif rec.payment_id:
                rec.partner_id = rec.payment_id.partner_id.id
                #revisar fecha
                rec.date_due = False
                rec.amount_total = rec.payment_id.amount
                #revisar de donde se saca el banco
                rec.bank = rec.payment_id.l10n_mx_edi_partner_bank_id.id
                rec.currency_id = rec.payment_id.currency_id.id
                # if not rec.bank:
                #     raise ValidationError('El pago {} necesita tener una cuenta de banco asignada')



    @api.multi
    @api.depends('invoice_id','payment_id')
    def _compute_ranges(self):
        print('_compute_ranges')
        for rec in self:
            if rec.invoice_id and rec.date_due:

                #se calculan dias de expiracion
                if rec.invoice_id.type in ('in_invoice',): #de proveedores
                    expired_days = (date.today() - rec.date_due).days
                else: #de clienes
                    expired_days = (rec.date_due - date.today()).days
                
                #se calculan rango de fechas
                expired_days = abs(expired_days)
                rec.expired_days = expired_days
                x_range = self.select_range(rec.day_range, expired_days)

                if x_range == 1:
                    rec.date_range1 = rec.amount_total
                elif x_range == 2:
                    rec.date_range2 = rec.amount_total
                elif x_range == 3:
                    rec.date_range3 = rec.amount_total
                elif x_range == 4:
                    rec.date_range4 = rec.amount_total
                elif x_range == 5:
                    rec.date_range5 = rec.amount_total    


    ########### FUNCIONES ########### 
    @api.model
    def select_range(self, range_number, number):
        """
        parametros: 
        *range_number: numero de los rangos,
        *number = numero a comparar en los rangos
        ejemplo: days = 7
        rangos:
        *1-7
        *8-14
        *15-22, etc..
        devuelve un numero entero del 1 - 5
        dependiendo del rango indicado (maximo 5 rangos)
        0 = no hay dias de vencimiento
        """
        range1 = (0 + range_number)
        range2 = (range1 + range_number)
        range3 = (range2 + range_number)
        range4 = (range3 + range_number)

        if number > 0 and number <= range1:
            return 1
        elif number > range1 and number <= range2:
            return 2
        elif number > range2 and number <= range3:
            return 3
        elif number > range3 and number <= range4:
            return 4
        elif number > range4:
            return 5
        return 0


    @api.multi
    def get_group_wizard(self):
        """
        se llama en accion de servidor
        y devuelve wizard de creacion de grupo
        de pago a bancos
        """
        print('get_group_wizard')
        invoice_type = False
        #el invoice_type se define de facturas, o pagos
        if self and self[0].invoice_id:
            invoice_type = self[0].invoice_id.type
        elif self and self[0].payment_id:
            # payment_type = self[0].payment_id.payment_type
            # invoice_type = 'in_invoice' if payment_type == 'outbound' else 'out_invoice'

            #se crea el grupo automaticamente
            return self.create_wizard_obj()

        # currency_id = self and self[0].currency_id.id
        return  {
            'type': 'ir.actions.act_window',
            'name': 'Creacion de grupo de pagos',
            'res_model': 'prodigia.bank.payment.group.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_ids': self.ids,
                        'invoice_type': invoice_type,
                        # 'currency_id': currency_id,
                        }
            }

    @api.multi
    def create_wizard_obj(self):
        print('create_wizard_obj')
        """
        metodo que creara el obj del wizard, 
        y el grupo automaticamente
        Se usara cuando sea anticipos, el usuario nunca
        vera el wizard, todo sera transparente
        """
        Wizard = self.env['prodigia.bank.payment.group.wizard']

        payment_type = self[0].payment_id.payment_type or False
        invoice_type = 'in_invoice' if payment_type == 'outbound' else 'out_invoice'
        journal_id = self[0].payment_id.journal_id and self[0].payment_id.journal_id.id or False
        communication = ''
        company_id = self[0].payment_id.company_id and self[0].payment_id.company_id.id or False
        payment_method_id = self[0].payment_id.payment_method_id and self[0].payment_id.payment_method_id.id or False
        currency_id = self[0].payment_id.currency_id and self[0].payment_id.currency_id.id or False

        #revisar que los datos sean los mismos en los pagos
        payment_ids = self.mapped('payment_id')
        print('payment_ids: ',payment_ids)
        print('payment_type: ',payment_type)
        same_payment_type = all(payment_ids.mapped(lambda i: i.payment_type == payment_type))
        if not same_payment_type:
            raise ValidationError('Todos los pagos deben de ser del mismo tipo')

        same_journal_id = all(payment_ids.mapped(lambda i: i.journal_id.id == journal_id))
        if not same_journal_id:
            raise ValidationError('Todos los pagos deben de contener el mismo diario')

        same_payment_method_id = all(payment_ids.mapped(lambda i: i.payment_method_id.id == payment_method_id))
        if not same_journal_id:
            raise ValidationError('Todos los pagos deben de contener el mismo metodo de pago')

        same_currency = all(payment_ids.mapped(lambda i: i.currency_id.id == currency_id))
        if not same_currency:
            raise ValidationError('Todos los pagos deben usar la misma moneda')

        wizard_vals = {
            'journal_id': journal_id,
            'payment_date': date.today(),
            'communication': communication,
            'company_id': company_id,
            'invoice_type': invoice_type,
            'currency_id': currency_id,
            'payment_method_id': payment_method_id,
            'payment_ids': [(6, 0 ,payment_ids.ids)],
        }
        wizard_obj = Wizard.with_context({'from_payments':True,'active_ids':self.ids}).create(wizard_vals)
        print('wizard_obj: ',wizard_obj)
        return wizard_obj.button_create_payment_group()


    ########### CAMPOS ########### 
    # wizard_id = fields.Many2one('prodigia.bank.payment.wizard',
    #     string='Wizard_id')
    invoice_id = fields.Many2one('account.invoice',
        string='Factura',
        required=False)
    payment_id = fields.Many2one('account.payment',
        string='Pago',
        required=False)
    partner_id = fields.Many2one('res.partner',
        # related='invoice_id.partner_id',
        compute='_compute_data',
        store=True)
    date_due = fields.Date(string='Fecha vencimiento',
        # related='invoice_id.date_due',
        compute='_compute_data',
        store=True)
    amount_total = fields.Monetary(string='Importe',
        # related='invoice_id.amount_total',
        compute='_compute_data',
        store=True)
    bank = fields.Many2one('res.partner.bank',
        string='Diario Banco',
        # domain=[('type','=','bank')],
        # related='invoice_id.partner_bank_id',
        compute='_compute_data',
        store=True,
        )
    currency_id = fields.Many2one('res.currency',
        string='Moneda',
        # related='invoice_id.currency_id',
        compute='_compute_data',
        store=True,
        )

    expired_days = fields.Float(string='Dias',
        compute='_compute_ranges',
        store=True)
    day_range = fields.Integer(
        string='Cantidad de dias en rango',
        store=True,
        )
    date_range1 = fields.Float(
        string='Rango 1',
        compute='_compute_ranges',
        store=True,
        )
    date_range2 = fields.Float(
        string='Rango 2',
        compute='_compute_ranges',
        store=True,
        )
    date_range3 = fields.Float(
        string='Rango 3',
        compute='_compute_ranges',
        store=True,
        )
    date_range4 = fields.Float(
        string='Rango 4',
        compute='_compute_ranges',
        store=True,
        )
    date_range5 = fields.Float(
        string='Rango 5',
        compute='_compute_ranges',
        store=True,
        )


