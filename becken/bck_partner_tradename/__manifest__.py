# -*- coding: utf-8 -*-
{
    'name': 'Partner Tradename or Partner Commercial Name',

    'summary': """
    This module adds the tradename field or commercial name for partner, partner views, sale report and invoice report.""",

    'description': """
    The module adds the tradename field for customers and vendors, this new field can be use it for searching or filtering, also can be use it in sale report or invoice report.
    For example, Walmart’s trade name is Walmart, but the company’s legal name is Wal-Mart Stores, Inc. and International Business Machines Corporation is the legal name for IBM tradename.
    """,

    'author': 'Candelas Software Factory',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 29.00,
    'maintainer': 'José Candelas',
    # 'live_test_url': 'https://www.youtube.com/watch?v=vWjKCwlyMdE',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_management', 'account', 'crm'],

    # always loaded
    'data': [
        'views/res_partner_views.xml',
        'views/crm_lead_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_check',
    'post_init_hook': 'post_init_hook',
}
