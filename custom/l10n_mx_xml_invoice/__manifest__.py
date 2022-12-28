{
    'name': "Import MX XML purchase invoice",
    'summary': """""",
    'description': """
    """,
    'author': "Xmarts",
    'license': 'OPL-1',
    'price': 19.99,
    'currency': 'USD',
    'images': ['static/description/banners/banner.gif'],
    'website': "https://www.xmarts.com",
    'live_test_url': "https://youtu.be/CNmOTkOoyMA",
    'category': 'Location',
    'version': '14.0.1',
    'price': 199.99,
    'currency': 'USD',
    'depends': [
        'base',
        'account_accountant',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/data_sequence.xml',
        'views/account_move_views.xml',
        'views/xml_import_invoice_views.xml',
        'wizard/xml_import_wizard_views.xml',
    ],
    'external_dependencies': {
        'python': [
            'cfdiclient',
        ],
    },
}
