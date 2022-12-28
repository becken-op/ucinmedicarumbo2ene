# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID, _


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    paperformat_us = env.ref('base.paperformat_us', raise_if_not_found=False)
    if paperformat_us:
        values = {
            'margin_top': 20,
            'margin_bottom': 10,
            'margin_left': 7,
            'margin_right': 7,
            'header_spacing': 17,
        }
        paperformat_us.sudo().write(values)

        company_id = env.user.company_id
        values = {
            'paperformat_id': paperformat_us.id,
            'report_footer': '',
        }
        company_id.sudo().write(values)

    mxn_currency = env.ref('base.MXN')
    if mxn_currency:
        values = {
            'symbol': 'MXN',
            'position': 'after',
        }
        mxn_currency.sudo().write(values)

    usd_currency = env.ref('base.USD')
    if usd_currency:
        values = {
            'symbol': 'USD',
            'position': 'after',
        }
        usd_currency.sudo().write(values)

    country_mx = env.ref('base.mx')
    if country_mx:
        values = {
            'address_format': ('%(street)s Col. %(l10n_mx_edi_colony)s\n'
                               'C.P. %(zip)s, %(city)s, %(state_name)s, %(country_name)s'),
            'street_format': '%(street_name)s %(street_number)s %(street_number2)s',
        }
        country_mx.sudo().write(values)


def pre_init_hook(cr):
    pre_init_check(cr)
    env = api.Environment(cr, SUPERUSER_ID, {})
    paperformat_us = env.ref('base.paperformat_us', raise_if_not_found=False)
    if paperformat_us:
        values = {
            'margin_top': 15,
            'margin_bottom': 10,
            'margin_left': 7,
            'margin_right': 7,
            'header_spacing': 12,
        }
        paperformat_us.sudo().write(values)


def pre_init_check(cr):
    from odoo.service import common
    from odoo.exceptions import Warning
    version_info = common.exp_version()
    server_serie = version_info.get('server_serie')
    if server_serie != '14.0':
        raise Warning(_('Module support Odoo series 14.0, found %s.') % server_serie)
    return True
