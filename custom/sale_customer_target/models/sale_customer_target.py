""" Initialize Sale Customer Target """

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleCustomerTarget(models.Model):
    """
        Initialize Sale Customer Target
    """
    _name = 'sale.customer.target'
    _description = 'Sale Customer Target'
    _order = 'date_from, partner_id'

    date_from = fields.Date(
        required=True,
    )
    date_to = fields.Date(
        required=True,
    )
    target_amount = fields.Monetary(
        required=True,
        currency_field="currency_id",
    )
    actual_amount = fields.Monetary(
        compute='_compute_actual_amount',
        currency_field="currency_id",
        store=True
    )
    partner_id = fields.Many2one(
        'res.partner'
    )
    user_id = fields.Many2one(
        'res.users',
        related='partner_id.user_id',
        store=True,
    )
    crm_team_id = fields.Many2one(
        'crm.team',
        related='user_id.sale_team_id',
        store=True,
    )
    commercial_partner_id = fields.Many2one(
        'res.partner',
        string='Commercial Entity',
        related='partner_id.commercial_partner_id',
        store=True)
    invoice_ids = fields.One2many(
        'account.move',
        'customer_target_id',
        compute='_compute_invoice_ids',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Company Currency',
        readonly=True,
        default=lambda self: self.env.user.company_id.currency_id.id)

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        """ Validate dates to prevent overlaps """
        for record in self:
            start = record.date_from
            end = record.date_to
            if start and end and end < start:
                raise ValidationError(
                    _('Start date must be earlier than end date.'))
            overlaps = self.search([
                ('id', '!=', record.id),
                ('partner_id', '=', record.partner_id.commercial_partner_id.id),
                '|',
                '&',
                ('date_from', '<=', start), ('date_to', '>=', start),
                '&',
                ('date_from', '<=', end), ('date_to', '>=', end),
            ])
            if overlaps:
                raise ValidationError(
                    _("Period is overlapped with another period")
                )

    @api.depends('date_from', 'date_to')
    def _compute_invoice_ids(self):
        """
        compute invoice_ids for customer depends on date from, date to
        """
        invoice_obj = self.env['account.move']
        for record in self:
            if record.id:
                record.invoice_ids = invoice_obj.search([
                    ('commercial_partner_id', '=', record.partner_id.id),
                    ('invoice_date', '>=', record.date_from),
                    ('invoice_date', '<=', record.date_to),
                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                    ('state', '=', 'posted'),
                ])
            else:
                record.invoice_ids = False

    @api.depends('invoice_ids', 'date_from', 'date_to')
    def _compute_actual_amount(self):
        """
        compute actual amount depends on invoices
        """
        for record in self:
            record.actual_amount = sum(
                record.invoice_ids.mapped('amount_total_signed')
            )
