# -*- coding: utf-8 -*-
{
    'name': "Account Budget Alert / Warning [Only for Odoo Enterprise Version]",
    'version': '6.1.8',
    'category': 'Accounting/Accounting',
    'price': 99.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'summary': """This app allow you to raise warnings and alert for budget exceed situations on Sales and Purchase.  [Only for Odoo Enterprise Version]""",
    'description':  """
        Odoo Account Budget Alert
        accounting budget
        analytic account
        cost center
        income account
        expense budget
        income budget
        customer budger
        budget report
        report budget
        budget
        yearly budget
        budget account
        account_budget
        account budget
        budget odoo 12
        odoo 12 budget
        budget community
        community edition budget
        accounting budget
        budget
        budget module
        module budget
        budget app
        odoo budget
        erp budget
        account budget app
        budget alert
        budget warning
        budget message
        sale budget
        purchase budget                
    """,
    'author': "Probuse Consulting Service Pvt. Ltd.",
    'website': "http://www.probuse.com",
    'support': 'contact@probuse.com',
    'live_test_url': 'http://probuseappdemo.com/probuse_apps/odoo_account_budget_alert_enterprise/610',
    'images': [
        'static/description/img1.jpg'
    ],
    'depends': [
        'account',
        'account_budget',
        'sale',
        'purchase',
    ],
    'data': [
        'views/res_config_settings_views.xml',
        'views/budget_views.xml',
        'views/account_invoice_view.xml',
        'views/purchase_order_view.xml',
        'views/sale_order_views.xml',
    ],
   'installable' : True,
   'application' : False,
}
