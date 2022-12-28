# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "All in one Hide Menu and Buttons - All Hide Menu, Button, Actions",
    'version': '14.0.0.3',
    "category" : "Extra Tools",
    'summary': 'Hide all in one Hide button hide action button hide create button hide duplicate button hide export button hide import button hide delete button hide edit button hide print button hide all button hide field hide any menu hide submenu hide menu hide report',
    "description": """

        All in one Hide Menu and Buttons in odoo,
        Hide Submenu and fields in odoo,
        Hide report in odoo,
        Hide/Show Create button in odoo,
        Hide/Show Edit button in odoo,
        Hide/Show Delete action button in odoo,
        Hide/Show Duplicate action button in odoo,
        Hide/Show Print button in odoo,
        Hide/Show Action button in odoo,
        Hide/Show Import button in odoo,
        Hide/Show Export button in odoo,

    """ , 
    'price': 25,
    'currency': "EUR",
    'author': 'BrowseInfo',
    'website': 'https://www.browseinfo.in',
    'depends': ['web', 'base_import'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/res_user.xml',
        'views/res_group.xml',
        'views/ir_actions_report.xml',
        'views/view_ir_model_fields.xml', 
    ],
    'qweb': [
        'static/src/xml/create_edit_button.xml',
    ],
    'installable': True,
    'auto_install': False,
    "live_test_url" : 'https://youtu.be/s7hSTCxnH1k',
    "images":['static/description/Banner.png'],
}
