# -*- coding: utf-8 -*-
{
    'name': 'Product Health Register',

    'summary': """
    This module adds Health Register to Products.""",

    'author': 'Becken',
    'support': 'support@becken.mx',
    'license': 'OPL-1',
    'website': 'https://www.becken.mx',
    'currency': 'USD',
    'price': 189.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Product',
    'version': '14.0.1.0',
    # 15.0.1.1 Changelog

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'stock', 'sale', 'account', 'purchase'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/product_health_register_views.xml',
        'views/product_template_views.xml',
        # 'views/sale_order_views.xml',
        'views/account_move_views.xml',
        'views/purchase_order_views.xml',
        'wizard/product_health_register_wizard_view.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_check',
}