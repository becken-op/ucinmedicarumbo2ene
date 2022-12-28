# -*- coding: utf-8 -*-
{
    'name': "Complemento de pago adjunto",

    'summary': """
        Modulo que copia el UUID del complemento de pagos desde el xml adjuntos""",

    'description': """
        Modulo que copia el UUID del complemento de pagos desde el xml adjuntos
    """,

    'author': "Nicols Consultores",
    'website': "http://nicols.mx",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '14.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'prodigia-facturacion'],

    # always loaded
    'data': [
        'views/views.xml',

    ],
}
