# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
from odoo import api, exceptions, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError



class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'


    @api.constrains('clabe')
    def _check_clabe(self):
    	if self.clabe and len(self.clabe) != 18:
    		raise ValidationError('La clabe interbancaria tiene que contener 18 caracteres!')


    clabe = fields.Char(string='Clabe interbancaria')


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'


    prodigia_bank_payment_id = fields.Many2one('prodigia.bank.payment.group',
        string='Grupo de pago',
        copy=False)


class AccountPayment(models.Model):
    _inherit = 'account.payment'


    @api.multi
    def unlink(self):
        # revisar facturas enlazadas y si el pago tiene un grupo de pago,
        # remover grupo de pago de dichas facturas
        print('unlink')
        for rec in self:
            if rec.prodigia_bank_payment_id:
                if rec.invoice_ids:
                    rec.invoice_ids.write({'prodigia_bank_payment_id': False})
        return super(AccountPayment, self).unlink()

    #borrar
    # @api.depends('invoice_ids', 'amount', 'payment_date', 'currency_id')
    # def _compute_payment_difference(self):
    #     print('_compute_payment_difference: ')
    #     for pay in self.filtered(lambda p: p.invoice_ids):
    #         payment_amount = -pay.amount if pay.payment_type == 'outbound' else pay.amount
    #         print('payment_amount: ',payment_amount)
    #         print('pay._compute_payment_amount(): ',pay._compute_payment_amount())
    #         pay.payment_difference = pay._compute_payment_amount() - payment_amount


    prodigia_bank_payment_id = fields.Many2one('prodigia.bank.payment.group',
        string='Grupo de pago',
        copy=False)
    payment_group_difference = fields.Float('Diferencia de pago (de grupo de pagos)')



class Accountjournal(models.Model):
    _inherit = 'account.journal'


    @api.constrains('clabe')
    def _check_clabe(self):
        if self.clabe and len(self.clabe) != 18:
            raise ValidationError('La clabe interbancaria tiene que contener 18 caracteres!')

    clabe = fields.Char(string='Clabe interbancaria',
        help='Esta clabe se usara en la creacion de grupos de pago cuando sean pagos de tipo transferencia interna')


# class ResBank(models.Model):
#     _inherit = 'res.bank'


#     prodigia_bank = fields.Selection([
#             ('scotiabank','Scotiabank'),
#         ],
#         string='Formato de pago a banco',
#     )