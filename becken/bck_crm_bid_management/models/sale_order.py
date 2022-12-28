# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


####### TRABAJAR CON LOS EXCEL
import base64
import xlsxwriter
import tempfile
from xlsxwriter.utility import xl_rowcol_to_cell
from io import BytesIO

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    is_bid = fields.Boolean(
        string='Is Bid',
        related='opportunity_id.is_bid',
        copy=False,
        store=True,
        default=False)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        values = super(SaleOrder, self).onchange_partner_id()
        if self.is_bid:
            values = {
                'pricelist_id': self.opportunity_id.pricelist_id,
            }
            self.update(values)
        return values

    class PartnerXlsx(models.AbstractModel):
        _name = 'report.module_name.report_name'
        _inherit = 'report.report_xlsx.abstract'

        def generate_xlsx_report(self, workbook, data, partners):

            gdl_warehouse_id = self.env['stock.warehouse'].search([('name', '=', 'GDL')], limit=1)
            mex_warehouse_id = self.env['stock.warehouse'].search([('name', '=', 'MEX')], limit=1)
            mty_warehouse_id = self.env['stock.warehouse'].search([('name', '=', 'MTY')], limit=1)

            for sale_order in partners:
                report_name = sale_order.name
                report_name = 'PARTIDAS OFERTADAS'
                # One sheet by partner
                sheet = workbook.add_worksheet(report_name[:31])
                header_label = workbook.add_format({'bold': True, 'font_color': 'white', 'bg_color': '#00b0f0', 'border': 2, 'align': 'right', 'font_name': 'Tahoma', 'font_size': 10})
                header_value = workbook.add_format({'bold': True, 'font_color': 'black', 'bg_color': '#dbeef4', 'border': 2, 'font_name': 'Tahoma', 'font_size': 10})
                header_comments = workbook.add_format({'bold': True, 'font_color': 'black', 'bg_color': '#ffff00', 'border': 2, 'font_name': 'Tahoma', 'font_size': 10})
                header_line = workbook.add_format({'bold': True, 'font_color': 'black', 'bg_color': '#00b0f0', 'border': 1, 'align': 'center', 'font_name': 'Tahoma', 'font_size': 10})
                line_value = workbook.add_format({'font_color': 'black', 'bg_color': '#e0e0e0', 'border': 1, 'font_name': 'Tahoma', 'font_size': 10})

                # Set width = 5 a Columa A hasta G
                sheet.set_column(0, 6, 5)
                # Set width = 60 a Columa H
                sheet.set_column(7, 7, 70)

                sheet.set_column(9, 22, 12)
                # Almacenes
                sheet.set_column(23, 26, 7)
                sheet.set_column(27, 27, 18)
                sheet.set_column(28, 32, 18)
                # Set width = 60 a Columa I
                # sheet.set_column(9, 8, 30)

                sheet.write(0, 7, 'INSTITUTO', header_label)
                sheet.merge_range('I1:R1', sale_order.opportunity_id.bidder_id.name if sale_order.opportunity_id.bidder_id else '', header_value)
                sheet.write(1, 7, 'CLIENTE', header_label)
                sheet.merge_range('I2:R2', sale_order.opportunity_id.partner_id.name, header_value)
                sheet.write(2, 7, 'ENTIDAD FEDERATIVA', header_label)
                sheet.merge_range('I3:R3', sale_order.opportunity_id.partner_id.state_id.name, header_value)
                sheet.write(3, 7, 'No. DE EXPEDIENTE', header_label)
                sheet.merge_range('I4:R4', sale_order.opportunity_id.document_folio, header_value)
                # sheet.write(3, 8, sale_order.opportunity_id.document_folio, header_value)
                sheet.write(4, 7, 'No. DE LICITACION', header_label)
                sheet.merge_range('I5:R5', sale_order.opportunity_id.bid_folio, header_value)
                # sheet.write(4, 8, sale_order.opportunity_id.bid_folio, header_value)
                sheet.write(5, 7, 'MODALIDAD', header_label)
                sheet.merge_range('I6:R6', dict(self.env['crm.lead']._fields['modality']._description_selection(self.with_context(lang='es_MX').env)).get(sale_order.opportunity_id.modality), header_value)
                # sheet.write(5, 8, sale_order.opportunity_id.modality, header_value)
                sheet.write(6, 7, 'CARÁCTER (NACIONAL, BAJO TRATADOS, INTERNACIONAL ABIERTA)', header_label)
                sheet.merge_range('I7:R7', dict(self.env['crm.lead']._fields['character']._description_selection(self.with_context(lang='es_MX').env)).get(sale_order.opportunity_id.character), header_value)
                # sheet.write(6, 8, sale_order.opportunity_id.character, header_value)
                sheet.write(7, 7, 'FECHA JUNTA DE ACLARACIONES', header_label)
                sheet.merge_range('I8:R8', sale_order.opportunity_id.clarifications_meeting_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if sale_order.opportunity_id.clarifications_meeting_datetime else '', header_value)
                # sheet.write(7, 8, sale_order.opportunity_id.clarifications_meeting_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT), header_value)
                sheet.write(8, 7, 'ACEPTAN ENTREGAS POR PAQUETERIA', header_label)
                sheet.merge_range('I9:R9', sale_order.opportunity_id.partner_id.shipping_mode, header_value)
                # sheet.write(8, 8, sale_order.opportunity_id.partner_id.shipping_mode, header_value)
                sheet.write(9, 7, 'REQUISITOS AL MOMENTO DE ENTREGAR PRODUCTO', header_label)
                sheet.merge_range('I10:R10', sale_order.opportunity_id.delivery_requirements, header_value)
                # sheet.write(9, 8, sale_order.opportunity_id.delivery_requirements, header_value)
                sheet.write(10, 7, 'FECHA DE ENTREGA DE MUESTRAS', header_label)
                sheet.merge_range('I11:R11', sale_order.opportunity_id.sample_delivery_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT) if sale_order.opportunity_id.sample_delivery_datetime else '', header_value)
                # sheet.write(10, 8, sale_order.opportunity_id.sample_delivery_datetime.strftime(DEFAULT_SERVER_DATETIME_FORMAT), header_value)
                sheet.write(11, 7, 'FECHA DE ENTREGA DE PROPUESTAS TECNICA - ECONOMICA', header_label)
                sheet.merge_range('I12:R12', sale_order.opportunity_id.proposals_delivery_date.strftime(DEFAULT_SERVER_DATE_FORMAT) if sale_order.opportunity_id.proposals_delivery_date else '', header_value)
                # sheet.write(11, 8, sale_order.opportunity_id.proposals_delivery_date.strftime(DEFAULT_SERVER_DATE_FORMAT), header_value)
                sheet.write(12, 7, 'FECHA DE FALLO', header_label)
                sheet.merge_range('I13:R13', sale_order.opportunity_id.decision_date.strftime(DEFAULT_SERVER_DATE_FORMAT) if sale_order.opportunity_id.decision_date else '', header_value)
                # sheet.write(12, 8, sale_order.opportunity_id.decision_date.strftime(DEFAULT_SERVER_DATE_FORMAT), header_value)
                sheet.write(13, 7, 'DEVOLUCION DE MUESTRAS', header_label)
                sheet.merge_range('I14:R14', 'Sí' if sale_order.opportunity_id.return_samples else 'No', header_value)
                # sheet.write(13, 8, 'Sí' if sale_order.opportunity_id.return_samples else 'No', header_value)
                sheet.write(14, 7, 'TIPO DE ENTREGA ', header_label)
                sheet.merge_range('I15:R15', sale_order.opportunity_id.partner_id.shipping_mode, header_value)
                # sheet.write(14, 8, sale_order.opportunity_id.partner_id.shipping_mode, header_value)
                sheet.write(15, 7, 'LUGAR DE ENTREGA', header_label)
                sheet.merge_range('I16:R16', sale_order.partner_shipping_id.contact_address, header_value)
                # sheet.write(15, 8, sale_order.partner_shipping_id.contact_address, header_value)
                sheet.write(16, 7, 'VIGENCIA DEL CONTRATO', header_label)
                sheet.merge_range('I17:R17', sale_order.opportunity_id.effective_start_date.strftime(DEFAULT_SERVER_DATE_FORMAT) + ' hasta '+ sale_order.opportunity_id.effective_end_date.strftime(DEFAULT_SERVER_DATE_FORMAT) if sale_order.opportunity_id.effective_start_date and sale_order.opportunity_id.effective_end_date else '', header_value)
                # sheet.write(16, 8, sale_order.opportunity_id.effective_start_date.strftime(DEFAULT_SERVER_DATE_FORMAT) + ' hasta '+ sale_order.opportunity_id.effective_end_date.strftime(DEFAULT_SERVER_DATE_FORMAT), header_value)
                sheet.write(17, 7, 'OBSERVACIONES', header_label)
                sheet.merge_range('I18:R18', sale_order.opportunity_id.bid_notes if sale_order.opportunity_id.bid_notes else '', header_comments)
                # sheet.write(17, 8, sale_order.opportunity_id.bid_notes if sale_order.opportunity_id.bid_notes else '', header_comments)
                sheet.write(18, 7, 'EVENTO REALIZADO POR', header_label)
                sheet.merge_range('I19:R19', sale_order.opportunity_id.user_id.name, header_value)
                # sheet.write(18, 8, sale_order.opportunity_id.user_id.name, header_value)
                sheet.write(19, 7, 'EVENTO REVISADO POR', header_label)
                sheet.merge_range('I20:R20', sale_order.opportunity_id.carried_out_id.name, header_value)
                # sheet.write(19, 8, sale_order.opportunity_id.carried_out_id.name, header_value)
                

                # Encabezado de la líneas
                sheet.write(21, 0, 'REQ.', header_line)
                sheet.write(21, 1, 'GPO', header_line)
                sheet.write(21, 2, 'GEN', header_line)
                sheet.write(21, 3, 'ESP.', header_line)
                sheet.write(21, 4, 'DIF.', header_line)
                sheet.write(21, 5, 'VAR.', header_line)
                sheet.write(21, 6, 'P.P.', header_line)
                sheet.write(21, 7, 'DESC_ART', header_line)
                # REQ.	GPO	GEN	ESP	DIF	VAR	P.P.	DESC_ART
                sheet.write(21, 8, 'UND.', header_line)
                sheet.write(21, 9, 'CANT PRES', header_line)
                sheet.write(21, 10, 'TIPO PRES', header_line)
                sheet.write(21, 11, 'CANT SOLIC. MIN', header_line)
                sheet.write(21, 12, 'CANT SOLIC. MAX', header_line)
                sheet.write(21, 13, 'MARCA', header_line)
                sheet.write(21, 14, 'MODELO', header_line)
                sheet.write(21, 15, 'REGISTRO SANITARIO', header_line)
                sheet.write(21, 16, 'PROCEDENCIA', header_line)
                sheet.write(21, 17, 'PRECIO UNITARIO', header_line)
                sheet.write(21, 18, 'TOTAL MINIMO', header_line)
                sheet.write(21, 19, 'TOTAL MAXIMO', header_line)
                sheet.write(21, 20, 'Días inventario', header_line)
                sheet.write(21, 21, 'DESCRIPCION UCIN MEDICA', header_line)
                sheet.write(21, 22, 'OBSERVACIONES', header_line)
                sheet.merge_range('X21:AB21', 'EXISTENCIAS (SALVO VENTA)', header_line)
                sheet.write(21, 23, 'GDL', header_line)
                sheet.write(21, 24, 'MEX', header_line)
                sheet.write(21, 25, 'MTY', header_line)
                sheet.write(21, 26, 'TOTAL', header_line)
                sheet.write(21, 27, 'DIAS INVENTARIO', header_line)
                sheet.write(21, 28, 'ESTATUS', header_line)
                sheet.write(21, 29, 'NOMBRE DEL PARTICIPANTE', header_line)
                sheet.write(21, 30, 'COSTO', header_line)
                sheet.write(21, 31, 'MARCA', header_line)
                sheet.write(21, 32, 'PROCEDENCIA', header_line)

                # sheet.write('A1', '=1+2', hidden)

                # UND.	CANT PRES	TIPO PRES	CANT SOLIC. MIN	CANT SOLIC. MAX	MARCA	MODELO	REGISTRO SANITARIO	PROCEDENCIA
                # PRECIO UNITARIO	TOTAL MINIMO	TOTAL MAXIMO	Dias inventario	DESCRIPCION UCIN MEDICA	OBSERVACIONES
                # GDL	MEX	MTY	TOTAL	DIAS INVENTARIO	ESTATUS	NOMBRE DEL PARTICIPANTE Y COSTO	MARCA Y PROCEDENCIA
                company_logo = BytesIO(base64.b64decode(sale_order.company_id.logo))
                sheet.insert_image(0, 0, "logo.png", {'image_data': company_logo, 'x_scale': 2.4, 'y_scale': 2.4})

                index = 22
                for line in sale_order.order_line:
                    sheet.write(index, 0, line.bid_requisition if line.bid_requisition else '', line_value)
                    # sheet.write(index, 2, line.basic_chart, line_value)
                    sheet.merge_range(index, 1, index, 6, line.basic_chart if line.basic_chart else '', line_value)
                    sheet.write(index, 7, line.name, line_value)
                    sheet.write(index, 8, _(line.product_id.uom_id.name), line_value)

                    sheet.write(index, 11, line.qty_min_requested, line_value)
                    sheet.write(index, 12, line.qty_max_requested, line_value)
                    sheet.write(index, 13, line.product_brand_ept_id.name, line_value)
                    sheet.write(index, 14, line.product_id.default_code, line_value)

                    sheet.write(index, 15, line.product_health_register_id.name, line_value)
                    sheet.write(index, 16, line.manufactured_place, line_value)
                    sheet.write(index, 17, line.price_unit, line_value)

                    strrow = str(index + 1)
                    sheet.write_formula(index, 18, '=R'+strrow+'*L'+strrow, line_value)
                    sheet.write_formula(index, 19, '=R'+strrow+'*M'+strrow, line_value)
                    

                    sheet.write(index, 21, line.product_id.name, line_value)
                    sheet.write(index, 22, line.note if line.note else '', line_value)

                    gdl_stock = 0
                    if gdl_warehouse_id:
                        product_qties = line.product_id.with_context(to_date=fields.Datetime.now(), warehouse=gdl_warehouse_id.id).read([
                            'qty_available',
                            'free_qty',
                            'virtual_available',
                        ])
                        if product_qties:
                            gdl_stock = product_qties[0]['qty_available']
                    # Existencia GDL
                    sheet.write(index, 23, gdl_stock, line_value)

                    mex_stock = 0
                    if mex_warehouse_id:
                        product_qties = line.product_id.with_context(to_date=fields.Datetime.now(), warehouse=mex_warehouse_id.id).read([
                            'qty_available',
                            'free_qty',
                            'virtual_available',
                        ])
                        if product_qties:
                            mex_stock = product_qties[0]['qty_available']
                    #  # Existencia MEX
                    sheet.write(index, 24, mex_stock, line_value)

                    mty_stock = 0
                    if mty_warehouse_id:
                        product_qties = line.product_id.with_context(to_date=fields.Datetime.now(), warehouse=mty_warehouse_id.id).read([
                            'qty_available',
                            'free_qty',
                            'virtual_available',
                        ])
                        if product_qties:
                            mty_stock = product_qties[0]['qty_available']                 
                    # Existencia MTY
                    sheet.write(index, 25, mty_stock, line_value)

                    # Existencia TOTAL
                    sheet.write(index, 26, line.product_id.qty_available, line_value)
                    # Días Inventario
                    # sheet.write(index, 27, line.product_id.qty_available, line_value)

                    sheet.write(index, 28, dict(self.env['sale.order.line']._fields['bid_line_state']._description_selection(self.with_context(lang='es_MX').env)).get(line.bid_line_state), line_value)
                    sheet.write(index, 29, line.awarded_supplier if line.awarded_supplier else '', line_value)
                    sheet.write(index, 30, line.awarded_supplier_price_unit if line.awarded_supplier_price_unit else '', line_value)
                    sheet.write(index, 31, line.awarded_product_brand if line.awarded_product_brand else '', line_value)
                    sheet.write(index, 32, line.awarded_supplier_origin if line.awarded_supplier_origin else '', line_value)
                    
                    index += 1
