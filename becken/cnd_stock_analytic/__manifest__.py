# -*- coding: utf-8 -*-
{
    "name": "Stock Move Analytic",
    "summary": "Adds an analytic account and analytic tags in stock move",
    'description': """
    """,
    "author": "Candelas Software Factory",
    'support': 'support@candelassoftware.com',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 59.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner.png'],
    "category": "Warehouse Management",
    "version": "14.0.1.1",
    'license': 'OPL-1',
    "depends": ["account", "analytic"],
    "data": [
        'views/res_config_settings_views.xml',
        "views/stock_move_views.xml",
        "views/stock_scrap_views.xml",
        "views/stock_move_line_views.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    # 'pre_init_hook': 'pre_init_check',
}