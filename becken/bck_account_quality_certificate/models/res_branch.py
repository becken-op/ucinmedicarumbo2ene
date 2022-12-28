from odoo import fields, models


class ResBranch(models.Model):
    _inherit = 'res.branch'

    responsible_id = fields.Many2one('res.partner',
        string='Certificate Responsible',
        required=True,
        domain=[('is_company', '=', False)],
        ondelete='restrict')
    responsible_title = fields.Many2one(
        'res.partner.title',
        related='responsible_id.title')
    responsible_professional_certificate = fields.Char(
        string='Professional Certificate',
        size=40,
        required=True)
    responsible_signature = fields.Binary(
        'Signature',
        help='Resposible Signature',
        required=True,
        copy=False,
        attachment=True)
