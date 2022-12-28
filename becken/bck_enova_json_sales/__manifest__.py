# -*- coding: utf-8 -*-
{
    'name': "Enova Json Import",

    'summary': """
        Create quotations through json files""",

    'description': """
        Configura los datos de FTP dentro de la sección Ventas para empezar a procesar archivos
    """,

    'author': "Alvaro Brena Robles",
    'support': 'contacto@becken.mx',
    'website': "http://www.becken.mx",
    'company': "Becken",
    'maintainer': 'Alvaro Brena Robles',

    'installable': True,
    'application': False,
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Sales',
    'version': '0.9.1',

    # any module necessary for this one to work correctly
    'depends': ['sale', 'sale_management', 'product_customer_info'],

    # always loaded
    'data': [
        'views/bck_config_settings_ftp_enova_view.xml',
        'data/bck_ftp_cron.xml',
        'data/mail_template_data.xml',
        'views/bck_sale_view.xml',
        'security/ir.model.access.csv'
    ],
    'license': "Other proprietary"
}
