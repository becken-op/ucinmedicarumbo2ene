# -*- coding: utf-8 -*-
{
    'name': 'Sale Product Manager',

    'summary': """
    This module adds the field "Product Manager" to customers to use it in sale and invoice analysis.""",

    'description': """
    """,

    'author': 'Candelas Software Factory',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 29.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '14.0.1.1',
    # 13.0.1.1 Changelog
    # Add Settings

    # any module necessary for this one to work correctly
    'depends': ['sale'],

    # always loaded
    'data': [
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_check',
}
