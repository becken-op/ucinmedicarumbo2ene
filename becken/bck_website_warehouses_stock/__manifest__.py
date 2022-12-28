# -*- coding: utf-8 -*-
{
    'name': "Warehouses stock",

    'summary': """
        Show stock warehouse from website sales.""",

    'description': """
        Show stock warehouse from website sales
    """,

    'author': "Alvaro Brena Robles",
    'support': 'contacto@becken.mx',
    'website': "http://www.becken.mx",
    'company': "Becken",
    'maintainer': 'Alvaro Brena Robles',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Website',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['website', 'sale', 'stock'],

    # always loaded
    'data': [
        'views/stock_warehouse_views.xml',
        'views/snippets/snippets.xml',
        'views/snippets/s_warehouses.xml',
        'views/bck_website_warehouses_stock_template.xml'
        # 'security/ir.model.access.csv',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
    'installable': True,
    'application': True
}
