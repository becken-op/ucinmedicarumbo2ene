# -*- coding: utf-8 -*-
{
    'name': 'Product Brand',

    'summary': """
    This module adds Brand to Products.""",

    'author': 'Becken',
    'support': 'support@becken.mx',
    'license': 'OPL-1',
    'website': 'https://www.becken.mx',
    'currency': 'USD',
    'price': 29.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Product',
    'version': '14.0.1.0',
    # 15.0.1.1 Changelog

    # any module necessary for this one to work correctly
    'depends': ['product', 'sale', 'sale_management'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_template.xml',
        'views/product_brand_ept.xml',
        'wizard/product_brand_wizard_view.xml',
    ],
    'images': [
        'static/description/banner.png',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_check',
}