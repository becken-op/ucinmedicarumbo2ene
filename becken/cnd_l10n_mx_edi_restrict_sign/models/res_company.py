# -*- coding: utf-8 -*-
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    l10n_mx_edi_xml_file_require = fields.Boolean(
        string='Is xml file required?',
        default=True,
        help='Check if the xml file is going to be required or not, in not '
        'signed invoices.')
