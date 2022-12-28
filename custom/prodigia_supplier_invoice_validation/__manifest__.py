# -*- coding: utf-8 -*-
{
    'name': "Validacion de xmls de factura de proveedor",

    'summary': """
       Modulo que valida xml adjunto de facturas de proveedores
       """,

    'description': """
       Modulo que valida xml adjunto de facturas de proveedores.
       Antes de validar revisa lo siguiente:
       -Que el monto del xml coincida con el monto de la factura en Odoo
       -Que el RFC del emisor coincida con el proveedor de la factura
       -Que el RFC del receptor coincida con el rfc del la compañia de Odoo
       -Que el UUID del xml no este repetido en odoo

       -Se agrega un checkbox en facturas de proveedores que si se marca, no
        realiza la validacion del xml al validar la factura
       -Se agrega en configuracion el margen de diferencia permitodo entre
        el monto del xml y la factura
    """,

    'author': "Prodigia",
    'website': "http://prodigia.mx",
    'category': 'Invoicing',
    'version': '1.0.1',

    'maintainer':"Marco Cid",

    # dependencias
    'depends': [
        'purchase',
        'account',
        'l10n_mx_edi',
        ],

    # always loaded
    'data': [
        'security/groups.xml',
        'views/config_views.xml',
        'views/invoice_views.xml',      
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}