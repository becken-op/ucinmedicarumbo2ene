# -*- coding: utf-8 -*-
# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Minimum Sales Margin Restriction Product',
    'version': '1.1.0',
    'license': 'Other proprietary',
    'price': 12.0,
    'currency': 'EUR',
    'author' : 'Probuse Consulting Service Pvt. Ltd.',
    'website' : 'www.probuse.com',
    'summary':  """Minimum Sales Margin on Product and Product Category""",
    'description': """
        Sales Margin Minimum Percentage Policy on Product and Category Odoo App
    """,
    'category': 'Sales/Sales',
    'depends': [
        'sale',
        'sale_margin'
    ],
    'support': 'contact@probuse.com',
    'images': ['static/description/limit_image.png'],
    'live_test_url': 'https://probuseappdemo.com/probuse_apps/sale_margin_limit_restriction/1221',
    'data': [
        'views/product_view.xml',
        'views/sale_order_view.xml',
        'views/product_category_view.xml'
    ],
    'installable' : True,
    'application' : False,
    'auto_install' : False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
