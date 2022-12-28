# -*- coding: utf-8 -*-

from odoo import models,fields,api,_
from odoo.exceptions import ValidationError

class SaleAdvancePayment(models.TransientModel):
	_name = 'sale.advance.payment'
	_description = "Sale Advance Payment"

	sale_order_id = fields.Many2one('sale.order', string="Name")
	journal_id = fields.Many2one('account.journal', string="Payment (Journal)")
	name = fields.Char(string="Origin", readonly=True)
	payment_date = fields.Datetime(string="Payment Date")
	total_amount = fields.Float(string="Total Amount", readonly=True)
	advance_amount = fields.Monetary(string='Payment Amount', required=True)
	currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=lambda self: self.env.user.company_id.currency_id)
	multi_currency_id = fields.Many2one('res.currency', string='Multi Currency')
	company_id = fields.Many2one('res.company', related='journal_id.company_id', string='Company', readonly=True)
	partner_id = fields.Many2one('res.partner', string="Partner")
	payment_method_id = fields.Many2one('account.payment.method', string='Payment Method', required=True,
		help="Manual: Get paid by cash, check or any other method outside of Odoo.\n"\
		"Electronic: Get paid automatically through a payment acquirer by requesting a transaction on a card saved by the customer when buying or subscribing online (payment token).\n"\
		"Check: Pay bill by check and print it from Odoo.\n"\
		"Batch Deposit: Encase several customer checks at once by generating a batch deposit to submit to your bank. When encoding the bank statement in Odoo, you are suggested to reconcile the transaction with the batch deposit.To enable batch deposit, module account_batch_payment must be installed.\n"\
		"SEPA Credit Transfer: Pay bill from a SEPA Credit Transfer file you submit to your bank. To enable sepa credit transfer, module account_sepa must be installed ")
	payment_type = fields.Selection([('outbound', 'Send Money'), ('inbound', 'Receive Money')], string='Payment Type')
	journal_id = fields.Many2one('account.journal', string='Payment (Journal)', required=True, domain=[('type', 'in',['bank','cash'])])
	company_curr_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Company Currency', readonly=True)
	paid_payment = fields.Monetary(compute='_compute_advance_amount_diff', readonly=True, currency_field='company_curr_id')
	payment_difference = fields.Monetary(compute='_compute_payment_difference', readonly=True, currency_field='company_curr_id')

	@api.model
	def default_get(self,default_fields):
		res = super(SaleAdvancePayment, self).default_get(default_fields)
		context = self._context
		payment_data = {
			'name':context.get('name'), 
			'currency_id': context.get('currency_id'),
			'total_amount': context.get('total_amount'),
			'payment_date': context.get('date_order'),
			'company_id': context.get('company_id'),
			'sale_order_id':context.get('order_id'),
			'partner_id': context.get('partner_id'),
		}
		res.update(payment_data)
		if 'journal_id' not in res:
			res['journal_id'] = self.env['account.journal'].search([('company_id', '=', self.env.user.company_id.id), ('type', 'in', ('bank', 'cash'))], limit=1).id
		return res

	@api.onchange('payment_type')
	def _onchange_payment_type(self):
		if self.payment_type:
			return {'domain': {'payment_method_id': [('payment_type', '=', self.payment_type)]}}

	@api.onchange('journal_id')
	def _onchange_journal(self):
		if self.journal_id:
			self.currency_id = self.journal_id.currency_id or self.company_id.currency_id
			# Set default payment method (we consider the first to be the default one)
			payment_methods = self.payment_type == 'inbound' and self.journal_id.inbound_payment_method_ids or self.journal_id.outbound_payment_method_ids
			self.payment_method_id = payment_methods and payment_methods[0] or False
			# Set payment method domain (restrict to methods enabled for the journal and to selected payment type)
			payment_type = self.payment_type in ('inbound', 'transfer') and 'inbound' or 'inbound'
			return {'domain': {'payment_method_id': [('payment_type', '=', payment_type), ('id', 'in', payment_methods.ids)]}}
		return {}

	@api.onchange('currency_id')
	def _onchange_currency(self):
		if self.currency_id and self.journal_id and self.payment_date:
			advance_amount = abs(self._compute_payment_amount(self.currency_id, self.journal_id, self.payment_date))
			self.advance_amount = advance_amount
		else:
			self.advance_amount = 0.0

		if self.journal_id:  # TODO: only return if currency differ?
			return

		# Set by default the first liquidity journal having this currency if exists.
		domain = [('type', 'in', ('bank', 'cash')), 
				  ('currency_id', '=', self.currency_id.id),
				  ('company_id', '=', self.company_id.id),]
		journal = self.env['account.journal'].search(domain, limit=1)
		if journal:
			return {'value': {'journal_id': journal.id}}

	@api.model
	def _compute_payment_amount(self, currency, journal, date):
		company = journal.company_id
		date = date or fields.Date.today()
		total = 0.0
		if company.currency_id == currency:
			if self.advance_amount == 0.0:
				total += self.advance_amount
			else:
				if self.multi_currency_id:
					total += self.multi_currency_id._convert(self.advance_amount, company.currency_id, company, date)
					self.multi_currency_id = False
				else:
					total += company.currency_id._convert(self.advance_amount, currency, company, date)
		else:
			total += company.currency_id._convert(self.advance_amount, currency, company, date)
			self.multi_currency_id = currency
		return total

	@api.depends('advance_amount', 'payment_date')
	def _compute_advance_amount_diff(self):
		self.paid_payment = 0.0
		active_id = self._context.get('active_id')
		sale_id = self.env['sale.order'].browse(active_id)
		if len(sale_id.payment_history_ids) == 0:
			return
		self.paid_payment= self._compute_total_amount()

	@api.model
	def _compute_total_amount(self):
		""" Compute the sum of the residual of invoices, expressed in the payment currency """
		total = 0
		active_id = self._context.get('active_id')
		sale_id = self.env['sale.order'].browse(active_id)
		for pay in sale_id.payment_history_ids:
			total += pay.advance_amount
		return abs(total)

	@api.depends('payment_date','total_amount')
	def _compute_payment_difference(self):
		active_id = self._context.get('active_id')
		sale_id = self.env['sale.order'].browse(active_id)
		payment_difference = 0.0
		if sale_id.payment_history_ids:
			for pay in sale_id.payment_history_ids:
				payment_difference += pay.advance_amount
			self.payment_difference = (self.total_amount - payment_difference)
		else:
			self.payment_difference = payment_difference


	def gen_sale_advance_payment(self):
		for record in self:
			if record.total_amount < record.advance_amount or record.advance_amount == 0.00:
				raise ValidationError(_('Please enter valid advance payment amount..!'))
	
			payment_data = {
				'currency_id':record.currency_id.id,
				'payment_type':'inbound',
				'partner_type':'customer',
				'partner_id':record.partner_id.id,
				'amount':record.advance_amount,
				'journal_id':record.journal_id.id,
				'date':record.payment_date,
				'ref':record.sale_order_id.name,
				'payment_method_id':record.payment_method_id.id,
				'check_advance_payment': True
			}
			account_payment_id = self.env['account.payment'].with_context(check_advance_payment=True).create(payment_data)
			account_payment_id.with_context(check_advance_payment=True).action_post()
	
			if record.currency_id != record.company_id.currency_id:
				amount_currency = record.advance_amount
				advance_amount = record.currency_id._convert(record.advance_amount, record.company_id.currency_id, record.company_id, record.payment_date)
				currency_id = record.currency_id
			else:
				advance_amount = abs(self._compute_payment_amount(record.currency_id, record.journal_id, record.payment_date))
				amount_currency = 0.0
				currency_id = record.company_id.currency_id
	
			if account_payment_id.state == 'posted':
				record.sale_order_id.write({'payment_history_ids':[(0,0,{
					'name': record.name,
					'payment_date': record.payment_date,
					'partner_id': record.partner_id.id,
					'journal_id': record.journal_id.id,
					'payment_method_id': record.payment_method_id.id,
					'amount_currency': amount_currency,
					'currency_id': currency_id.id,
					'advance_amount': advance_amount,
					'total_amount': record.total_amount})]})			
	
			action_vals = {
				'name': _('Advance Payment'),
				'domain': [('id', 'in', account_payment_id.ids), ('state', '=', 'posted')],
				'view_type': 'form',
				'res_model': 'account.payment',
				'view_id': False,
				'type': 'ir.actions.act_window',
			}
	
			if len(account_payment_id) == 1:
				action_vals.update({'res_id': account_payment_id[0].id, 'view_mode': 'form'})
			return action_vals


# Advance Payment History
class AdvancePaymentHistory(models.Model):
	_name = 'advance.payment.history'
	_description = 'advance.payment.history'

	name = fields.Char(string="Name", readonly=True)
	order_id = fields.Many2one('sale.order', string="Sale Order")
	journal_id = fields.Many2one('account.journal', string="Payment (Journal)", readonly=True)
	payment_date = fields.Datetime(string="Payment Date", readonly=True)
	company_currency_id = fields.Many2one('res.currency', string="Company Currency", readonly=True, default=lambda self: self.env.user.company_id.currency_id)
	total_amount = fields.Float(string="Total Amount", readonly=True)
	amount_currency = fields.Monetary(string="Amount in Currency", readonly=True)
	advance_amount = fields.Monetary(string="Advance Paid Amount", readonly=True, currency_field='company_currency_id')
	currency_id = fields.Many2one('res.currency', string="Currency", readonly=True)
	partner_id = fields.Many2one('res.partner', string="Partner")
	payment_method_id = fields.Many2one('account.payment.method', string="Payment Method", readonly=True)

