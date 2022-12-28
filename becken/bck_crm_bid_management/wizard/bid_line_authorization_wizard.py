from odoo import models, fields


class BidLineAuthorizationWizard(models.TransientModel):
    _name = 'bid.line.authorization.wizard'
    _description = "Bid Line Authorization Wizard"


    def _default_sale_order_line_id(self):
        lines_id = self.env['sale.order.line'].browse(self.env.context.get('active_id', []))
        return lines_id

    sale_order_line_id = fields.Many2one(
        'sale.order.line',
        string='Bid Line',
        help='',
        default=_default_sale_order_line_id)
    authorization_comment = fields.Text(
        string='Authorization comment',
        tracking=True)


    def do_authorization(self):
        # unset if any and set to the select
        if self.sale_order_line_id:
            values = {
                'authorization_user': self.env.uid,
                'authorization_date': fields.Datetime.now(),
                'authorization_comment': self.authorization_comment,
            }
            self.sale_order_line_id.write(values)
        return True
