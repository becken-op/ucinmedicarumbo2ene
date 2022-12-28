# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright 2021 Odoo IT now <http://www.odooitnow.com/>
# See LICENSE file for full copyright and licensing details.
#
##############################################################################
{
    'name': 'Backorder from Sale Order',
    'version': '14.0.1.1',
    'category': 'Sales',
    'summary': 'Create a Backorder from sale order based on product availability',

    'author': 'Odoo IT now',
    'website': 'http://www.odooitnow.com/',
    'license': 'Other proprietary',

    'description': """
Backorder from Sale Order
=========================
Allows to create a backorder from Sale Order based on product availability.

Using this extension, the user will know the quantity available in stock and
what quantity will be in a backorder from the sales order line.

The available quantity and backorder quantity will auto compute when the user
will select the product in the sales order line.

Once the user will confirm the sale order, the backorder will auto-generated
if the backorder quantity exists in the sales order line.
""",
    'depends': ['base', 'sale_stock', 'sale_management'],
    'data': [
            'security/ir.model.access.csv',
            'views/sale_view.xml',
            'views/sale_order_cancellation_reason_views.xml',
            'views/sale_order_backorder_reason_views.xml',
            'report/sale_report.xml',
            'report/sale_report_templates.xml',
            'data/reason_data.xml',
    ],
    'images': ['images/OdooITnow_screenshot.png'],

    'price': 58.0,
    'currency': 'EUR',

    'installable': True,
    'application': False,
    'auto_install': False
}
