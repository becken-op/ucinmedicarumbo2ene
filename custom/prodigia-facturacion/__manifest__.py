# -*- coding: utf-8 -*-
{
    'name': "Prodigia Facturación CFDI 4.0",

    'summary': """
       Módulo de facturación para enviar facturas al servicio de Prodigia.""",
    'description': """
        Éste módulo agrega a Prodigia como opción para emitir facturas desde el módulo de facturación de odoo-enterprise. para versión 12
    """,
    'author': "Prodigia",
    'website': "https://www.prodigia.mx",
    'support': 'soporte@prodigia.com.mx',
    'category': 'Invoicing',
    'version': '1.1.14.7',
    'maintainer': "Prodigia",
    'license': 'OPL-1',
    # dependencias
    'depends': [
        'l10n_mx_edi',
        'l10n_mx_edi_40'
    ],
    # always loaded
    'data': [
        'views/res_config_settings_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'auto_install': False,
}
