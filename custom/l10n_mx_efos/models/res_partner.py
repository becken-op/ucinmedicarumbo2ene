from odoo import api, fields, models


class Partner(models.Model):
    _inherit = "res.partner"

    sat_efos_state = fields.Selection(
        string="EFOS Condition",
        selection=[
            ("unknown", "Unknown"),
            ("favorable", "Favorable Judgement"),
            ("distorted", "Distorted"),
            ("definitive", "Definitive"),
            ("presumed", "Presumed"),
        ],
        default="unknown",
        compute="_compute_sat_efos_state",
        store=True,
        index=True,
    )
    sat_efos_danger = fields.Boolean(
        string="EFOS Danger",
        compute="_compute_sat_efos_danger",
        store=True,
    )

    @api.depends("vat")
    def _compute_sat_efos_state(self):
        for partner in self:
            efos = self.env["l10n_mx.efos"].search([("rfc", "=", partner.vat)], limit=1)
            partner.sat_efos_state = efos.state if efos else "unknown"

    @api.depends("sat_efos_state")
    def _compute_sat_efos_danger(self):
        for partner in self:
            partner.sat_efos_danger = partner.sat_efos_state in ("presumed", "definitive")
