#  GNU nano 2.5.3                                                      Archivo: hooks.py

# Copyright 2004 Tiny SPRL
# Copyright 2016 Sodexis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import _


def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import Warning
    version_info = common.exp_version()
    server_serie = version_info.get('server_serie')
    if server_serie != '14.0':
        raise Warning(_('This module support Odoo series 14.0, found %s.') %
                      server_serie)
    return True
