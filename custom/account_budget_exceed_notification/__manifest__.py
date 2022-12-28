# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.

{
    'name': 'Account Budget Exceed Practical Amount Notify',
    'price': 59.0,
    'version': '2.1.2',
    'depends': [
       'account_budget',
    ],
    'currency': 'EUR',
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'http://www.probuse.com',
    'support': 'contact@probuse.com',
    'images': ['static/description/img1.jpg'],
    'live_test_url': 'http://probuseappdemo.com/probuse_apps/account_budget_exceed_notification/284',#'https://youtu.be/eVU5REReXC8',
    'data':[
        'data/account_budget_notify_mail_template.xml',
        'views/account_budget_post_view.xml',
        'views/account_budget_view.xml',
    ],
    'category': 'Accounting/Accounting',
    'license': 'Other proprietary',
    'summary': """Send email notification if budget practical amount exceed planned amount""",
    'description': """
This app send email notification if budget practical amount exceed planned amount
account budget
account budget exceeds
budget notification
budget alert notification
alert budget account
    """,
    'installable' : True,
    'application' : False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
