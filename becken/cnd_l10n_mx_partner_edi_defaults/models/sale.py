# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = "sale.order"

    l10n_mx_edi_usage = fields.Selection([
            ('G01', 'Acquisition of merchandise'),
            ('G02', 'Returns, discounts or bonuses'),
            ('G03', 'General expenses'),
            ('I01', 'Constructions'),
            ('I02', 'Office furniture and equipment investment'),
            ('I03', 'Transportation equipment'),
            ('I04', 'Computer equipment and accessories'),
            ('I05', 'Dices, dies, molds, matrices and tooling'),
            ('I06', 'Telephone communications'),
            ('I07', 'Satellite communications'),
            ('I08', 'Other machinery and equipment'),
            ('D01', 'Medical, dental and hospital expenses.'),
            ('D02', 'Medical expenses for disability'),
            ('D03', 'Funeral expenses'),
            ('D04', 'Donations'),
            ('D05', 'Real interest effectively paid for mortgage loans (room house)'),
            ('D06', 'Voluntary contributions to SAR'),
            ('D07', 'Medical insurance premiums'),
            ('D08', 'Mandatory School Transportation Expenses'),
            ('D09', 'Deposits in savings accounts, premiums based on pension plans.'),
            ('D10', 'Payments for educational services (Colegiatura)'),
            ('S01', 'No tax effects'),
            ('P01', 'To define'),
        ],
        string='Usage',
        default='P01',
        tracking=True,
        help="Used in CFDI to express the key to the usage that will gives the receiver to this invoice. This "
             "value is defined by the customer.\nNote: It is not cause for cancellation if the key set is not the usage "
             "that will give the receiver of the document.")

    l10n_mx_edi_payment_method_id = fields.Many2one(
        'l10n_mx_edi.payment.method',
        string="Payment Way",
        tracking=True,
        help="Indicates the way the invoice was/will be paid, where the options could be: "
             "Cash, Nominal Check, Credit Card, etc. Leave empty if unknown and the XML will show 'Unidentified'.",
        default=lambda self: self.env.ref('l10n_mx_edi.payment_method_otros', raise_if_not_found=False))


    @api.onchange('partner_id')
    def onchange_partner_id_l10n_mx_edi(self):
        '''Set the payment l10n_mx_edi_usage on the sale order as the first of the selected partner.
        '''
        # OVERRIDE
        if not self.partner_id:
            self.update({
                'l10n_mx_edi_usage': False,
                'l10n_mx_edi_payment_method_id': False,
            })
        res = super(SaleOrder, self).onchange_partner_id()
        if self.partner_id:
            # EDI Usage from Partner
            if self.partner_id.commercial_partner_id.l10n_mx_edi_usage:
                self.l10n_mx_edi_usage = self.partner_id.commercial_partner_id.l10n_mx_edi_usage

            # Method from Partner
            if self.partner_id.commercial_partner_id.l10n_mx_edi_payment_method_id:
                self.l10n_mx_edi_payment_method_id = self.partner_id.commercial_partner_id.l10n_mx_edi_payment_method_id
        return res

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a sales order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        self.ensure_one()

        invoice_vals = super(SaleOrder, self)._prepare_invoice()

        # EDI Usage from Partner
        l10n_mx_edi_usage = self.l10n_mx_edi_usage
        # Method from Partner
        l10n_mx_edi_payment_method_id = self.l10n_mx_edi_payment_method_id

        if l10n_mx_edi_usage:
            vals = {
                'l10n_mx_edi_usage': l10n_mx_edi_usage
            }
            invoice_vals.update(vals)

        if l10n_mx_edi_payment_method_id:
            vals = {
                'l10n_mx_edi_payment_method_id': l10n_mx_edi_payment_method_id
            }
            invoice_vals.update(vals)

        return invoice_vals
