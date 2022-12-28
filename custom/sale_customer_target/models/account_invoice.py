""" Inherit Account Invoice """

from odoo import api, fields, models


class AccountInvoice(models.Model):
    """
        Inherit Account Invoice:
         - to add customer target
    """
    _inherit = 'account.invoice'

    customer_target_id = fields.Many2one('sale.customer.target',
                                         compute='_compute_customer_target_id',
                                         store=True, )

    @api.depends('date_invoice', 'partner_id', 'state', 'type')
    def _compute_customer_target_id(self):
        """ Compute customer_target_id value """
        target_obj = self.env['sale.customer.target']

        for record in self:
            target_id = False
            if record.state in ['open', 'paid'] and record.type in [
                'out_invoice', 'out_refund']:
                target = target_obj.search([
                    ('date_from', '<=', record.date_invoice),
                    ('date_to', '>=', record.date_invoice),
                    ('partner_id', '=', record.commercial_partner_id.id),
                ], limit=1)
                if target:
                    target_id = target.id
            record.customer_target_id = target_id
