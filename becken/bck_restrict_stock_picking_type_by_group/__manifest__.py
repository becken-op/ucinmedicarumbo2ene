# -*- coding: utf-8 -*-

{
    'name': 'Allowed Operation Types for User Groups | Stock Picking Types Restrict for User Groups |'
            ' Allowed Inventory Picking Types for User Groups',
    'author': 'Marco Villagrana',
    'company': 'Becken',
    'maintainer': 'Becken',
    'description': """ Allowed Operation Types for User Groups | Stock Picking Types Restrict for User Groups |'
            ' Allowed Inventory Picking Types for User Groups| Stock Picking Types Restrict For User Groups
            allowed users can access that picking type | ALlowed operation types for user groups""",
    'summary': """This module allow you to define allowed operation types for user groups. User can see only the allowed operation types and 
    related transfers only
""",
    'version': '14.1',
    'license': 'OPL-1',
    'depends': ['stock'],
    'category': 'Inventory/Inventory',
    'demo': [],
    'data': [
        'security/security.xml',
        'views/res_groups_view.xml',
        'views/picking_type_view.xml'
    ],
    'images': ['static/description/banner.png'],
    "price": 20,
    "currency": 'USD',
    'installable': True,
    'application': True,
    'auto_install': False,
}
