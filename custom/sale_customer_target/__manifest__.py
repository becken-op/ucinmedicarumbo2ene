# pylint: disable=missing-docstring,manifest-required-author
{
    'name': 'Customer Target',
    'summary': 'Sales Customer Target',
    'author': 'CORE B.P.O',
    'maintainer': 'Eslam Abdelmaaboud',
    'website': 'http://www.core-bpo.com',
    'support': 'apps@core-bpo.com',
    'version': '14.0.1.0.0',
    'category': 'Accounting/Accounting',
    'license': 'OPL-1',
    'depends': [
        'sale', 'sale_management',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/account_invoice.xml',
        'views/res_partner.xml',
        'views/res_users_views.xml',
        'views/sale_customer_target.xml',
        'views/crm_team_views.xml',
    ],
    'images': [
        'static/description/banner.gif',
        'static/description/main_screenshot.gif',
        'static/description/corebpo_logo.png',
        'static/description/customer.png',
        'static/description/customer_target_actual.png',
        'static/description/invoices.png',
        'static/description/report_pivot_view.png',
        'static/description/report_tree_view.png',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 15,
    'currency': 'USD',
}
