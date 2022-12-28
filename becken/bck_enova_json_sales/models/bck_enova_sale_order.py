# -*- coding: utf-8 -*-

import ftplib
import logging
import json
from odoo import models, fields

_logger = logging.getLogger(__name__)


class EnovaException(Exception):
    def __init__(self, msg, type, object, json):
        self.msg = msg
        self.type = type
        self.object = object
        self.json = json


class ConfigException(Exception):
    def __init__(self, msg, type, object):
        self.msg = msg
        self.type = type
        self.object = object


class EnovaSaleOrder(models.Model):
    _inherit = 'sale.order'

    def _fetch_sales_quotation(self):
        Transaction = self.env['enova.ftp.transaction']
        # Create new Order after process all in queue
        if Transaction.queue_processing():
            return
        # Clear done files before ftp connection
        Transaction.clear_processed()
        try:
            ftp_files = Transaction.retrive_from_ftp()
            for file, content in ftp_files:
                out_json = self._process_json(file, content)
                Transaction.add_to_queue(file, out_json, content)
                self.env.cr.commit()

        except ftplib.all_errors as ftp_all:
            Transaction.record_transaction('connection', 'FTP', str(ftp_all))
        except ConfigException as ce:
            Transaction.record_transaction('conf', 'Setting configuration', str(ce))
        except Exception as ex:
            Transaction.record_transaction('file', 'Not Controlled', str(ex))
            raise Exception(ex)

    def _execute_queue(self):
        Transactions = self.env['enova.ftp.transaction']
        queue = Transactions.get_queue()
        for tran in queue:
            if tran.status == 'processed':
                tran.delete_ftp()
            elif tran.status == 'moved':
                tran.move_to_processed()
            elif tran.status == 'deleted':
                tran.move_to_out()
            else:
                continue
            self.env.cr.commit()


    def _process_json(self, file, content):
        Transaction = self.env['enova.ftp.transaction']
        json_out = Transaction.json_out_template('', '', '', '', '', '')
        try:
            sale = json.loads(content)
            json_out['channel'] = sale['channel']
            json_out['id'] = sale['id']
            json_out['created_on'] = sale['created_on']
            json_out['customer_rfc'] = sale['customer_rfc']
            json_out['vendor_rfc'] = sale['vendor_rfc']
            json_out['reference'] = sale['id']

            json_out = Transaction.json_out_template(
                sale['channel'],
                sale['id'],
                sale['created_on'],
                sale['customer_rfc'],
                sale['vendor_rfc'],
                sale['id']
            )

            json_out['action'] = 'reject'

            # Quotation exists?
            sale_order = self.search([
                ('client_order_ref', '=', sale['id'])
                ], limit = 1)

            # Quotation exists
            if sale_order:
                error = f'Quotation with id: {sale["id"]} exists. Reference filename {file} exists'
                json_out['description'] = error
                json_out['reason'] = 'PS'
                raise EnovaException(error, 'file', file, json_out)


            # Plant field is stored in ref field
            partner = self.env['res.partner'].search([
                ('ref', '=', sale['plant'])
                ], limit=1)

            if not partner:
                error = f'Partner [{sale["plant"]}] doesn\'t exists. Error in file: {file}'
                json_out['description'] = error
                json_out['reason'] = 'PS'
                raise EnovaException(error, 'file', file, json_out)


            if not partner.user_id:
                error = f'Partner {partner.display_name} needs to assign Saleperson. Erro in file: {file}'
                json_out['description'] = error
                json_out['reason'] = 'PS'
                raise EnovaException(error, 'file', file, json_out)

            employee = partner.user_id
            user_id = employee.id
            warehouse_id = self.warehouse_from_branch(partner.branch_id)

            # plant: (es el cliente buscar esta res.partner.<plant> buscar)  es el id del cliente.  ya la tiene el cliente.
            sale_order = {
                'client_order_ref': sale['id'],
                'date_order': sale['created_on'],
                'validity_date': sale['release_date'],
                'state': 'draft',
                'partner_id': partner.id,
                'user_id': user_id,
                'payment_term_id': partner.property_payment_term_id.id,
                'branch_id': partner.branch_id,
                'warehouse_id': warehouse_id
            }

            if partner.property_product_pricelist:
                sale_order['pricelist_id'] = partner.property_product_pricelist.id

            order = self.env['sale.order'].with_user(user_id).sudo().create(sale_order)
            if order:
                json_out['id'] = order.name
                json_out['action'] = 'accept'
            else:
                error = ''
                json_out['description'] = error
                json_out['reason'] = 'PS'
                raise EnovaException(error, 'file', file, json_out)

            if order:
                index = 0
                line_error = False
                lines = []
                for line in sale['positions']:
                    index += 1
                    json_line = {
                            'line': index,
                            'reference': line['line'],
                            'delivery_date': sale['release_date']
                            }
                    # Product code related to partner
                    CustomerInfo = self.env['product.customer.info'].search([
                        ('customer_product_code', '=', line['material_id'])
                        ], limit=1)

                    # Validate product
                    if not CustomerInfo:
                        error = f'{index} {line["line"]} - Producto {line["material_id"]} doesn\'t exists in partner {partner.display_name}'
                        json_line['action'] = 'reject'
                        json_line['reason'] = 'PS'
                        json_line['description'] = error
                        json_out['positions'].append(json_line)
                        line_error = True
                        Transaction.record_transaction('file', file, error)
                        continue
                    else:
                        product = self.env['product.product'].search([
                            ('product_tmpl_id', 'in', CustomerInfo.product_tmpl_id.ids)
                        ], limit=1)

                        quantity = line['qty']
                        qty_backorder = 0
                        current_warehouse = self.env['stock.warehouse'].search([('id', '=', warehouse_id)], limit=1)
                        if (current_warehouse):
                            # Get stock location
                            loc_stock_id = current_warehouse.lot_stock_id
                            stock = self.env['stock.quant'].sudo().search([('location_id', '=', loc_stock_id), ('product_id', '=', product.id)], limit=1)
                            if stock:
                                qty_backorder = stock.quantity - quantity
                                qty_backorder = abs(qty_backorder) if qty_backorder < 0 else 0
                                quantity = quantity - qty_backorder 

                        if line['price'] != product.price:
                            error = f'{index} {line["line"]} - Precio de de Odoo no corresponde al precio de Enova'
                            json_line['action'] = 'reject'
                            json_line['reason'] = 'UP'
                            json_line['description'] = error
                            json_out['positions'].append(json_line)
                            line_error = True
                            Transaction.record_transaction('file', file, error)
                            continue

                        line = {
                                'order_id': order.id,
                                'product_id': product.id,
                                'name': product.display_name,
                                'product_uom_qty': quantity,
                                'qty_backorder': qty_backorder
                                }
                        lines.append(line)

                        if line:
                            json_line['action'] = 'accept'
                            json_out['positions'].append(json_line)

                if line_error:
                    json_out['reference'] = sale['id']
                    order.sudo().unlink()
                else:
                    for current in lines:
                        new_line = self.env['sale.order.line'].with_user(user_id).sudo().create(current)
                    self.send_mail(order.id)

        except EnovaException as enova:
            Transaction.record_transaction(enova.type, enova.object, enova.msg)
            if enova.json:
                Transaction.save_file(enova.json)
        except Exception as ex:
            raise Exception(ex)
        finally:
            return json_out

    def send_mail(self, order_id):
        template = self.env.ref('bck_enova_json_sales.email_template_enova_confirmation_b2b')
        template.send_mail(order_id, force_send=True)

    def warehouse_from_branch(self, branch_id):
        warehouse_id = 0

        # 1 -> GDL
        if branch_id == 1:
            warehouse_id = 1
        # 2 -> PUE
        elif branch_id == 2:
            warehouse_id = 3
        # 3 -> TIJ
        elif branch_id == 3:
            warehouse_id = 2
        # 4 -> MER
        elif branch_id == 4:
            warehouse_id = 6
        # 5 -> MEX
        elif branch_id == 5:
            warehouse_id = 5
        # 6 -> MTY
        elif branch_id == 6:
            warehouse_id = 4

        return warehouse_id
