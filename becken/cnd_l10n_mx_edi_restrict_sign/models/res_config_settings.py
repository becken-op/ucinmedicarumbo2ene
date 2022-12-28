# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    l10n_mx_edi_xml_file_require = fields.Boolean(
        string='Is xml file required?',
        related='company_id.l10n_mx_edi_xml_file_require',
        readonly=False,
        default=True,
        help='Check if the xml file is going to be required or not, in not '
        'signed invoices.')
