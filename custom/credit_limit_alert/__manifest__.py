{
    'name': 'Credit limit alert',
    'version': '4.1',
    'summary': 'Para odoo 11, Lanza una alerta de limite de credito, con limitacion al hacer venta y al validar una entrega',
    'description': 'Cuando un vendedor intenta de hacerle una venta a un cliente que ya exedio el limite de credito que tiene aprobado en la empresa, inmediatamente se genera una alerta indicando al vendedor que el cliente exedio su limite.',
    'author': 'Raul Ovalle, raul@xmarts.do, Pablo Osorio',
    'website': 'www.xmarts.com',
    'depends': ['sale','account_accountant', 'contacts','sale_management','stock'],
    'data': [
        'views/res_partner_view.xml',
        'views/sale_order_view.xml',
        'wizards/partnert_statement_wizard_view.xml'
    ],
    'installable': True,
}
