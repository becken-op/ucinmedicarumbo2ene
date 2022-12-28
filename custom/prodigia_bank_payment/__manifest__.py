# -*- coding: utf-8 -*-
{
    'name': "Pagos a banco",

    'summary': """
        Creacion de archivo xls para bancos""",

    'description': """
        Creacion de archivo xls para bancos
    """,

    'author': "Nicols Consultores",
    'website': "https://www.nicols.mx",
    'developer': "José Candelas",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Account',
    'version': '12.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['account_accountant', ],

    # always loaded
    'data': [
        'data/data.xml',
        'data/sequence_data.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/account_views.xml',
        'views/partner_views.xml',
        'views/partner_bank_views.xml',
        'views/bank_payment_group_views.xml',
        'views/bank_payment_invoice_line_views.xml',
        'wizard/search_invoice_wizard_views.xml',
        'wizard/group_wizard_views.xml',
    ],
    # only loaded in demonstration mode
    'post_init_hook': '_create_contextual_actions',
}
