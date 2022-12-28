# -*- coding: utf-8 -*-
{
    'name': 'Customer Credit Limit with Restrictions',

    'summary': """
    This module allow to manage a credit limit of customers with restrictions to the customer.""",

    'description': """
    <b>1. Configure Restrict <b>confirm Sale Orders</b>, <b>confirm Invoices</b> or <b>validate Stock Deliveries</b> if any customer has exceed its Credit Limit.</b>
    <b>2. Only the <b>Credit Limit Manager</b> can modify the credit limit or allow to avoid restrictions, keeps track of any modification related to the credit limit.</b>
    <b>3. Define a <b>Credit Limit</b> and optionally "Allow Override" to customers (without any restriction).</b>
    <b>4. Restrict <b>confirm Sale Orders</b> if any customer has exceed its Credit Limit.</b>
    <b>5. Restrict <b>confirm Invoices</b> if a customer has exceed its Credit Limit.</b>
    <b>6. Restrict <b>validate Stock Deliveries</b> if a customer has exceed its Credit Limit.</b>
    """,

    'author': 'Candelas Software Factory',
    'support': 'support@candelassoftware.com',
    'license': 'OPL-1',
    'website': 'http://www.candelassoftware.com',
    'currency': 'USD',
    'price': 139.00,
    'maintainer': 'José Candelas',
    'images': ['static/description/banner.png'],

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sales',
    'version': '14.0.1.1',
    # 14.0.1.1 Changelog
    # Add Settings

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale_management', 'account', 'stock'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'views/res_config_settings_views.xml',
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        'views/stock_picking_views.xml',
        'views/account_invoice_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'pre_init_hook': 'pre_init_check',
}
