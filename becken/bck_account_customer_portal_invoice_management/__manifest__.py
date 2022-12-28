# -*- coding: utf-8 -*-
{
    'name': 'Customer Portal Invoice',

    'summary': """
    """,

    'description': """
    """,

    'author': 'José Candelas',
    'support': 'soporte@becken.mx',
    'license': 'OPL-1',
    'website': 'https://www.becken.mx',
    'currency': 'USD',
    'price': 60.00,
    'maintainer': 'José Candelas',
    # 'live_test_url': 'https://www.youtube.com/watch?v=vWjKCwlyMdE',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Account',
    'version': '14.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['account'],
    # always loaded
    'data': [
        'security/customer_portal_security.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/account_payment_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'pre_init_hook': 'pre_init_check',
}
