""" Inherit Account Move """

from odoo import api, fields, models


class AccountMove(models.Model):
    """
        Inherit Account Move:
         - to add customer target
    """
    _inherit = 'account.move'

    customer_target_id = fields.Many2one(
        'sale.customer.target',
        compute='_compute_customer_target_id',
        store=True,
    )

    @api.depends('invoice_date', 'partner_id', 'state', 'move_type')
    def _compute_customer_target_id(self):
        """ Compute customer_target_id value """
        target_obj = self.env['sale.customer.target']

        for record in self:
            target_id = False
            if record.state == 'posted' and record.move_type in ['out_invoice',
                                                                 'out_refund']:
                target = target_obj.search([
                    ('date_from', '<=', record.invoice_date),
                    ('date_to', '>=', record.invoice_date),
                    ('partner_id', '=', record.commercial_partner_id.id),
                ], limit=1)
                if target:
                    target_id = target.id
            record.customer_target_id = target_id
