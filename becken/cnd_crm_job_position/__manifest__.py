# -*- coding: utf-8 -*-
{
    'name': 'Job Position categorized in CRM',

    'summary': """
    This module allow to manage a credit limit of customers with restriction to the customer.""",

    'description': """
    """,

    'author': 'Candelas Software Factory',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 49.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'CRM',
    'version': '14.0.1.0',
    # 13.0.1.1 Changelog
    # Add Settings

    # any module necessary for this one to work correctly
    'depends': ['crm', 'partner_contact_job_position'],

    # always loaded
    'data': [
        'views/crm_lead_views.xml',
        'views/res_partner_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_check',
}
