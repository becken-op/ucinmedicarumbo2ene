# -*- coding: utf-8 -*-
{
    'name': "Quality Certificate",

    'summary': """
    Este módulo genera el certificado de calidad desde una factura""",

    'description': """
    """,

    'author': 'Becken',
    'support': 'jose.candelas@becken.com',
    'license': 'OPL-1',
    'website': 'http://www.becken.mx',
    'currency': 'USD',
    'price': 139.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner.png'],

    'category': 'Account',
    'version': '14.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['account', 'branch', 'bck_product_brand_ept'],

    # always loaded
    'data': [
        'views/res_branch_views.xml',
        'views/quatlity_certificate_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}