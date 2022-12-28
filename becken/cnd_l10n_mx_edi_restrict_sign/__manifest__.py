# -*- coding: utf-8 -*-
{
    'name': "Restrict CFDI sign (Mexican Localization)",

    'summary': """
        Mexican Localization - CFDI 3.3
        This module is to decide if an invoice is going to be signed or not,
        by default the invoices are going to be signed.
    """,

    'description': """
    """,

    'author': 'José Candelas',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 89.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner_cnd_l10n_mx_edi_restrict_sign.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Accounting',
    'version': '14.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'sale', 'product', 'sale_stock', 'account', 'l10n_mx_edi'],

    # always loaded
    'data': [
        'security/user_groups.xml',
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
        'views/res_partner_views.xml',
        'report/account_invoice_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'pre_init_hook': 'pre_init_check',
}
