import csv

import requests

from odoo import _, fields, models
from odoo.exceptions import UserError

SAT_FILE_URL = "http://omawww.sat.gob.mx/cifras_sat/Documents/Listado_Completo_69-B.csv"
sat_state_to_odoo = {
    "Definitivo": "definitive",
    "Desvirtuado": "distorted",
    "Presunto": "presumed",
    "Sentencia Favorable": "favorable",
}


class EFOS(models.Model):
    _name = "l10n_mx.efos"
    _description = "EFOS"

    name = fields.Char(
        required=True,
        readonly=True,
        index=True,
    )
    rfc = fields.Char(
        string="RFC",
        required=True,
        index=True,
    )
    state = fields.Selection(
        selection=[
            ("favorable", "Favorable Judgement"),
            ("distorted", "Distorted"),
            ("definitive", "Definitive"),
            ("presumed", "Presumed"),
        ],
        required=True,
        index=True,
    )

    def _download_sat_csv(self):
        """Download SAT file."""
        response = requests.get(SAT_FILE_URL)
        if response.status_code != 200:
            raise UserError(_("Error dowloading the CSV file from SAT"))
        content = str(response.content, "cp1252")
        data = csv.reader(content.splitlines())
        for _i in range(3):  # Remove header lines
            next(data)
        return data

    def _update_catalogs(self):
        """Get the catalogs from SAT service"""
        data = self._download_sat_csv()
        self.search([]).sudo().unlink()
        self.sudo().create(
            [
                {
                    "rfc": line[1],
                    "name": line[2],
                    "state": sat_state_to_odoo[line[3]],
                }
                for line in data
            ]
        )

    def _update_partners(self):
        """Check the status of current partners."""
        efos = self.search([])
        efos_dict = {efos.rfc: efos.state for efos in efos}
        rfcs_in_list = efos.mapped("rfc")
        partners = self.env["res.partner"].search([("vat", "in", rfcs_in_list)])
        for partner in partners:
            partner.sat_efos_state = efos_dict[partner.vat]

    def update_catalog_and_partners(self):
        """Get the catalogs from SAT service and check the status of current partners."""
        self._update_catalogs()
        self._update_partners()
