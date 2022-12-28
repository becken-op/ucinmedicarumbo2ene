# -*- coding: utf-8 -*-
{
    'name': "Apuntes Contables Prodigia",
    'summary': """
        Modulo de Odoo que nos muestra todos los apuntes generados por la factura o el pago""",
    'description': """
        Modulo de odoo desarrollado por prodigia que se encarga de mostrar todos los
         movimientos contables relacionados con el pago o la factura padre de los mismos, 
         esto con el fin de visualizar todos estos movimientos desde un mismo lugar.
    """,
    'author': "Prodigia",
    'website': "http://www.prodigia.mx",
    'category': 'Invoicing & Payments',
    'version': '1.0.30',
    # any module necessary for this one to work correctly
    'depends': [
        'l10n_mx_edi'
    ],
    # always loaded
    'data': [
        'reports/journal_entry_payment.xml',
        'views/account_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
