# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import request

class WarehousesStockSnippets(http.Controller):

  @http.route(['/bck_warehouses_stock/stocks/<int:product_id>'], type='json', auth='public', website='true')
  def stock(self, product_id):

    warehouses = request.env['stock.warehouse'].sudo().search([
      ('website_active', '=', True)
    ])

    # lot_stock_id 11770, 12102
    detail = [{ 'warehouse': 'Sin existencias.', 'quantity': ''}]
    if warehouses:
      locations = [warehouse.lot_stock_id.id for warehouse in warehouses]
      stocks = request.env['stock.quant'].sudo().search([
        ('location_id', 'in', locations),
        ('product_id', '=', product_id)
      ])
      if stocks:
        detail = []
        for stock in stocks:
          stock_warehouse = [warehouse for warehouse in warehouses if warehouse.lot_stock_id.id == stock.location_id.id][0]
          detail.append({ 'warehouse': stock_warehouse.display_name, 'quantity': int(stock.quantity)})

    return request.env['ir.ui.view']._render_template('bck_website_warehouses_stock.s_warehouses_details', {'warehouses': detail})

