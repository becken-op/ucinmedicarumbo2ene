from odoo import fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    partner_sat_efos_danger = fields.Boolean(
        related="partner_id.sat_efos_danger",
        store=True,
    )
