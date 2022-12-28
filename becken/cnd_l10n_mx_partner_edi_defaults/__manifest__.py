# -*- coding: utf-8 -*-
{
    'name': 'Partner EDI Defaults (Mexican Localization)',

    'summary': """
    To define defaults values to CFDI Usage and Payment Method fields to every Partner.""",

    'description': """
    Adds the fields CFDI Usage and Payment Method to Partner, so that, the invoices created will have these values by default.
    """,

    'author': 'José Candelas',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 34.00,
    'maintainer': 'José Candelas',
    # 'live_test_url': 'https://www.youtube.com/watch?v=vWjKCwlyMdE',
    'images': ['static/description/cnd_partner_tradename_banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '14.0.1.0',

    # any module necessary for this one to work correctly
    # TODO: Quitar la dependencia de ventas, dividirlo en dos módulos o tres, base, ventas y facturación, 4to POS
    # Desarrollo: Agregar Cliente en Ticket
    # Investigar: Hacer factura en Punto de Venta
    'depends': ['base', 'sale_management', 'account', 'l10n_mx_edi'],

    # always loaded
    'data': [
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'pre_init_hook': 'pre_init_check',
}
