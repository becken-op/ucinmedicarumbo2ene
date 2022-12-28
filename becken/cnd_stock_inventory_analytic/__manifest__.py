# -*- coding: utf-8 -*-
{
    'name': 'Stock Inventory Analytic',

    "summary": """
        Stock Inventory Analytic """,
    'description': """
    """,

    'author': 'Candelas Software Factory',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 29.00,
    'maintainer': 'José Candelas',
    # 'live_test_url': 'https://www.youtube.com/watch?v=vWjKCwlyMdE',
    'images': ['static/description/cnd_partner_tradename_banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Account',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['account', 'account_accountant', 'stock'],

    # always loaded
    'data': [
        'views/res_config_settings_views.xml',
        'views/stock_inventory_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_check',
}
