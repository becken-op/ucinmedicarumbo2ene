# -*- coding: utf-8 -*-
from odoo import models, api

ADDRESS_FIELDS = (
    'street', 'street2', 'zip', 'city', 'state_id', 'country_id',
    'l10n_mx_edi_colony',)


class Partner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def _address_fields(self):
        """Returns the list of address fields that are synced from the parent."""
        return list(ADDRESS_FIELDS)
