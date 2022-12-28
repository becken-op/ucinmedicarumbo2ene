# -*- coding: utf-8 -*-

{
    'name': 'Allowed Operation Types for Users | Stock Picking Types Restrict for Users |'
            ' Allowed Inventory Picking Types for Users',
    'author': 'Odoo Bin',
    'company': 'Odoo Bin',
    'maintainer': 'Odoo Bin',
    'description': """ Allowed Operation Types for Users | Stock Picking Types Restrict for Users |'
            ' Allowed Inventory Picking Types for Users| Stock Picking Types Restrict For Users
            allowed users can access that picking type | ALlowed operation types for users""",
    'summary': """This module allow you to define allowed operation types for users. User can see only the allowed operation types and 
    related transfers only
""",
    'version': '14.0',
    'license': 'OPL-1',
    'depends': ['stock'],
    'category': 'Inventory/Inventory',
    'demo': [],
    'data': [
        'security/security.xml',
        'views/res_users_view.xml',
        'views/picking_type_view.xml'
    ],
    'live_test_url': 'https://youtu.be/OcYo-UYBhb4',
    'images': ['static/description/banner.png'],
    "price": 4,
    "currency": 'USD',
    'installable': True,
    'application': True,
    'auto_install': False,
}
