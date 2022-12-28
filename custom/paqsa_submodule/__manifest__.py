# -*- coding: utf-8 -*-
{
    'name': "paqsa_submodel",

    'summary': """ Agrega 
    *- carga informacion de cddi en asociada a clientes que se carga automaticamente en facturacion y ventas \n
    *- bloquea transferencias inmediatas en movimientos de stock internos \n
    *- registra los cambios de precio de proveedor desde compras\n
    *- tarifa a precio de proveedor\n
    *- formato de entrega con cantidad de productos por unidades de medida\n
    *- widget con porcentaje de productos apartados , entregados y facturados en ventas\n
    *- agrega el nro de la factura al formato de entrega en stock\n
    """,
    'description': """
        Long description of module's purpose
    """,

    'author': "Xmarts",
    'website': "https://www.xmarts.com",

    # for the full list
    'category': 'Uncategorized',
    'version': '14.0',

    # any module necessary for this one to work correctly
    'depends': [
        'account',
        'base',
        'contacts',
        'l10n_mx_edi',
        'l10n_mx',
        'purchase',
        'sale_management',
        'sale_stock',
        'stock',
        'purchase_stock',
        ],
    
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/inherit_stock_picking_view.xml',
        'report/report_delivery.xml',
        'report/report_sale_order.xml',
        'report/report_account.xml',
        'report/report_delivery_tickect.xml',
        'views/sale_order.xml',
        'views/account.xml',
        'views/product.xml',
        'views/product_template.xml',
        'views/res_partner.xml',
        ]

}
