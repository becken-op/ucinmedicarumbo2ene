# -*- coding: utf-8 -*-
{
    'name': "Ver movimientos contables desde trasnferencias",

    'summary': """
        Ver movimientos contables desde trasnferencias""",

    'description': """
        Ver movimientos contables desde trasnferencias
    """,

    'author': "Prodigia",
    'website': "http://www.prodigia.com.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Account',
    'version': '0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['stock_account',],

    # always loaded
    'data': [
        'views/views.xml',
    ],
    # only loaded in demonstration mode
}