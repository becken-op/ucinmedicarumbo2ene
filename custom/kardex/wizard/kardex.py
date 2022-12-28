#-*- encoding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning, ValidationError

#PARA FECHAS
from datetime import datetime, timedelta

####### TRABAJAR CON LOS EXCEL
import base64
import xlsxwriter
import tempfile
from xlsxwriter.utility import xl_rowcol_to_cell

#OTROS
import re
from collections import defaultdict
from odoo.tools import float_compare, float_round, float_is_zero, pycompat


class StockKardex(models.TransientModel):
    _name = 'stock.kardex'

    #CAMPOS PARA GENERAR EL ARCHIVO
    datas_fname = fields.Char('File Name',size=256)
    file = fields.Binary('Layout')
    download_file = fields.Boolean('Download File')
    cadena_decoding = fields.Text('Binary')

    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id, required=True)
    start_date = fields.Datetime("Start date", required=True)
    end_date = fields.Datetime("End date", required=True)

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse',
        help='Si no se elige un almacen, el reporte obtendra info de todos los almacenes y la separara por pestaña de excel')
    product_id = fields.Many2one('product.product', 'Product', 
        help='Si no se elige un producto, se sacara info de todos los productos')

    #SOLO SE USAN PARA REPORTE, EN CASO DE QUE NO SE LLENEN LOS CAMPOS DEL FORMULARIO
    warehouse_ids = fields.Many2many('stock.warehouse')
    product_ids = fields.Many2many('product.product')



    def _check_dates(self):
        """VALIDA QUE LA FECHA FINAL NO SEA ANTES QUE LA INICIAL"""
        if self.end_date < self.start_date:
            return False
        return True

    _constraints = [
        (_check_dates, 'End date must be equal or greater than start date', ['end_date'])
    ]

    
    def fix_date(self, date, hours, hour, minute, second):
        """METODO QUE HACE QUE LA HORA DE LAS FECHAS SEA IGUAL A 0 Y LA DEVUELVE"""
        fixed_date = False
        #SE LES DA FORMATO A LAS FECHAS
        fixed_date = datetime.strptime(str(date),"%Y-%m-%d %H:%M:%S")
        #SE RESTA 7 HORAS A CADA FECHA, DEBIDO A QUE SE CALCULAN CON 1 DIA DE MAS
        fixed_date = fixed_date - timedelta(hours=hours)
        #SE ELIMINA LA HORA EN LA FECHA
        fixed_date = fixed_date.replace(hour=hour,minute=minute,second=second)
        return fixed_date


    def get_child_location_ids(self, location_ids):
        """METODO RECURSIVO QUE OBTIENE LOS IDS DE UBICACIONES HIJAS DE UNA UBICACION DADA"""
        new_location_ids = []
        location_obj = self.env['stock.location']
        res = location_obj.browse(location_ids)
        #SE RECORREN LOS IDS
        for rec in location_obj.browse(location_ids):
            child_ids = [x.id for x in rec.child_ids]
            new_location_ids.extend(child_ids)

        if new_location_ids != []:
            new_location_ids = self.get_child_location_ids(new_location_ids)
        new_location_ids.extend(location_ids)
        return new_location_ids

    
    def calculate(self):
        """METODO PRINCIPAL DEL MODULO KARDEX"""

        #SE OBTIENE LA INFO DEL FORMULARIO
        # start_date = self.start_date
        # end_date = self.end_date

        if self.warehouse_id:
            warehouse_ids = [self.warehouse_id.id,]
        else:
            domain = [('active','=',True),]
            warehouse_ids = self.env['stock.warehouse'].search(domain)
            if warehouse_ids:
                warehouse_ids = warehouse_ids.ids

        if self.product_id:
            product_ids = [self.product_id.id,]
        else:
            domain = [('active','=',True),]
            product_ids = self.env['product.product'].search(domain)
            if product_ids:
                product_ids = product_ids.ids

        self.write({
            'warehouse_ids': [[6, False, warehouse_ids]],
            'product_ids': [[6, False, product_ids]]
            })
        #start_date = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
        return self.export_xlsx_file()


    def get_warehouse_locations(self, warehouse_id):
        """
        devuelve lista de ubicaciones correspondientes
        al almacen indicado
        """
        wh_input_stock_loc_id = warehouse_id.lot_stock_id.id
        wh_qc_stock_loc_id = warehouse_id.wh_qc_stock_loc_id.id
        wh_output_stock_loc_id = warehouse_id.wh_output_stock_loc_id.id
        wh_pack_stock_loc_id = warehouse_id.wh_pack_stock_loc_id.id
        wh_view_location_id = warehouse_id.view_location_id.id
        location_ids = [wh_view_location_id,
                        wh_input_stock_loc_id,
                        wh_qc_stock_loc_id,
                        wh_output_stock_loc_id,
                        wh_pack_stock_loc_id]
        location_ids = self.get_child_location_ids(location_ids)
        return location_ids

    
    def get_lines(self, product, location_ids):
        xlines = []
        start_date = self.start_date
        end_date = self.end_date
        product_id = product.id
        #SE BUSCAN LOS IDS DE LOS REGISTROS DENTRO DEL RANGO DE FECHAS SELECCIONADO
        move_obj = self.env['stock.move']
        move_ids = move_obj.search(
            [
                ('date','<=',str(end_date)),
                ('state','=','done'),
                ('product_id','=',product_id)
            ], order='date'
        )

        ##SE CALCULAN DATOS INICIALES
        existencia_inicial = 0.0
        costo_inicial = 0.0
        existencia = 0.0
        costo_total = 0.0
        costo_viejo = 0.0
        titulo_colulmna_coste = ''

        for rec in move_ids:
            line_ok = True
            movimiento = rec.inventory_id and rec.inventory_id.name or rec.picking_id.name or ''
            origen_id = rec.location_id.id
            destino_id = rec.location_dest_id.id
            origen = rec.location_id.name
            destino = rec.location_dest_id.name
            origen_completo = rec.location_id.complete_name
            destino_completo = rec.location_dest_id.complete_name
            fecha = rec.date
            empresa = rec.picking_id.partner_id.name
            cantidad = rec.product_uom_qty
            metodo_coste = rec.product_id.categ_id.property_cost_method

            udm = rec.product_uom.name
            udm_id = rec.product_uom.id
            product_uom = rec.product_id.uom_id.name
            product_id = rec.product_id.uom_id.id

            #SE CALCULA CANTIDAD CON UDM DEL MOVIMIENTO
            cantidad = rec.product_uom._compute_quantity(cantidad, rec.product_id.uom_id)
            #def _compute_quantity(self, qty, to_unit, round=True, rounding_method='UP'):

            
            estado = rec.state
            pedido_origen = rec.inventory_id and rec.inventory_id.name or rec.origin or ''
            precio_compra = rec.purchase_line_id.price_unit

            #SE OBTIENE EL VALOR DEL MOVIMIENTO
            # obtener costo total de stock.valuation.layer
            value = 0
            for svl in rec.stock_valuation_layer_ids:
                value += abs(svl.value)
            costo_rec = value

            entradas = 0.0
            salidas = 0.0
            costo_entradas = 0.0
            costo_esalidas = 0.0

            titulo_colulmna_coste = 'COSTO UNITARIO'
            costo = 0.0

            ############################################################
            #SE DETERMINA EL TIPO EN BASE A LAS UBICACIONES DE ENTRADA Y SALIDA (Y NO DEL TIPO DE ALBARAN)
            if (origen_id in location_ids) and (destino_id not in location_ids):
                tipo = 'outgoing'
                costo_rec = -costo_rec
            elif (origen_id not in location_ids) and (destino_id in location_ids):
                tipo = 'incoming'
            else:
                tipo = 'internal'

            #################################################
            #SE DETERMINA SI SE USA COSTO ESTANDAR O PROMEDIO#########
            if metodo_coste.upper() == 'STANDARD':
                # titulo_colulmna_coste = 'COSTO STANDARD'
                # titulo_colulmna_coste = 'COSTO'
                if tipo == 'outgoing': #EN LAS SALIDAS S CALCULA EL COSTO ESTANDAR EN BASE A LA CANTIDAD, PARA DETERMINAR EL COSTO EN LA FECHA
  
                    if cantidad != 0:
                        costo = abs(costo_rec / cantidad)
                    else:
                        costo = 0.0
                else:
                    costo = 0.0
                #costo = rec.product_id.standard_price
            elif metodo_coste.upper() =='AVERAGE':
                # titulo_colulmna_coste = 'COSTO PROMEDIO'
                # costo = rec.average_cost
                if cantidad != 0:
                    costo = abs(costo_rec / cantidad)
                else:
                    costo = 0.0
            ####################################################33
            #LA LINEA NO APARECERA SI LA FECHA NO ENTRA EN EL RANGO ESPECIFICADO
            if rec.date < self.start_date:
                line_ok = False
                #SE CALCULA LOS DATOS INICIALES#################
                if tipo == 'incoming':
                    existencia_inicial += cantidad
                    existencia += cantidad
                    costo_inicial += costo_rec
                    costo_total += costo_rec
                elif tipo == 'outgoing':
                    existencia_inicial -= cantidad
                    existencia -= cantidad
                    costo_inicial += costo_rec
                    costo_total += costo_rec
                ######################################
            #LA LINEA NO APARECE SI LA UBICACION DESTINO NI LA DE ORIGEN CONTIENEN ALGUNA UBICACION DEL ALMACEN ESPECIFICADO
            if (origen_id not in location_ids) and (destino_id not in location_ids):
                line_ok = False

            if line_ok:
                #OPERACIONES QUE SOLO SE DEBEN HACER SI SE MOSTRARA LA LINEA
                if (costo or 0.0) == 0.0:
                    costo = costo_viejo
                costo_viejo = costo
                if tipo == 'incoming':
                    entradas = cantidad
                    existencia += cantidad
                    costo_entradas = costo_rec
                    costo_salidas = 0.0
                    costo_total += costo_entradas
                elif tipo == 'outgoing':
                    salidas = cantidad
                    existencia -= cantidad
                    costo_salidas = costo_rec
                    costo_entradas = 0.0
                    costo_total += costo_salidas
                elif tipo == 'internal':
                    costo_salidas = 0.0
                    costo_entradas = 0.0

                    #SE DETERMINA SI EL INTERNO ES DE SALIDA O ENTRADA
                    #*********
                    if (origen_id in location_ids) and (destino_id not in location_ids):
                        #tipo = 'outgoing'
                        salidas = cantidad
                        existencia -= cantidad
                        costo_salidas = costo_rec
                        costo_entradas = 0.0
                        costo_total += costo_salidas
                    if (origen_id not in location_ids) and (destino_id in location_ids):
                        entradas = cantidad
                        existencia += cantidad
                        costo_entradas = costo_rec
                        costo_salidas = 0.0
                        costo_total += costo_entradas

                ####################################
                #SE OBTIENEN ALS FACTURAS DE COMPRA####################
                facturas = '' #FACTURAS DE COMPRA
                datos_de_facturas = rec.purchase_line_id.order_id.invoice_ids
                facturas = ', '.join([str(fact.name or 'Borrador') for fact in datos_de_facturas if fact.state != 'cancel'])

                #SE OBTIENEN LAS FACTURAS DE VENTA
                grupo_id = rec.group_id.id
                facturas_v = [] #FACTURAS DE VENTA
                pedimentos = []
                if grupo_id:
                    pedidos_venta = self.env['sale.order'].search([('procurement_group_id', '=', grupo_id)])

                    for venta in pedidos_venta:
                        #SE RECORREN LAS FACTURAS DE CADA PEDIDO
                        for fact in venta.invoice_ids:
                            if fact.state != 'cancel':
                                facturas_v.append(fact.name or 'Borrador')
                                for line in fact.invoice_line_ids:
                                    if 'l10n_mx_edi_customs_number' in line and line.l10n_mx_edi_customs_number:
                                        pedimentos.append(line.l10n_mx_edi_customs_number)
                facturas = facturas + ', '.join(facturas_v)
                pedimentos = ', '.join(pedimentos)
                #######################################################3
                #SE OBTIENEN LOS MOVIMIENTOS CONTABLES GENERADOS##########
                movimientos_contables = ', '.join( list(set([str(move.name) for move in rec.account_move_ids])) )
                #######################################################

                # titulo_colulmna_coste = 'COSTO UNITARIO'
                costo_unitario = 0
                if (entradas + salidas) != 0:
                    costo_unitario = abs((costo_entradas + costo_salidas) / (entradas + salidas))

                line_data = {
                        'FECHA': fecha,
                        'MOVIMIENTO': movimiento or '',
                        'DOCUMENTO ORIGEN': pedido_origen or '',
                        'FACTURA(S)': facturas or '',
                        'PEDIMENTO(S)': pedimentos or '',
                        'EMPRESA': empresa or '',
                        'MOVIMIENTO CONTABLE': movimientos_contables or '',
                        'ORIGEN': origen_completo or '',
                        'DESTINO': destino_completo or '',
                        'UDM': udm or '',
                        'ENTRADAS': entradas or 0.0,
                        'SALIDAS': salidas or 0.0,
                        'EXISTENCIA': existencia or 0.0,
                        'PRECIO DE COMPRA': precio_compra or 0.0,
                        titulo_colulmna_coste: costo_unitario or 0.0,
                        'COSTO ENTRADAS': costo_entradas or 0.0,
                        'COSTO SALIDAS': costo_salidas or 0.0,
                        'COSTO TOTAL': costo_total or 0.0,
                        'ESTADO': estado or '',
                        'TIPO': tipo or '',
                        }
                xlines.append(line_data)

        columns = [['FECHA', 'DATE'],
                ['MOVIMIENTO', 'CHAR'],
                ['DOCUMENTO ORIGEN', 'CHAR'],
                ['FACTURA(S)', 'CHAR'],
                ['PEDIMENTO(S)', 'CHAR'],
                ['EMPRESA', 'CHAR'],
                ['MOVIMIENTO CONTABLE', 'CHAR'],
                ['ORIGEN', 'CHAR'],
                ['DESTINO', 'CHAR'],
                ['UDM', 'CHAR'],
                ['ENTRADAS', 'FLOAT'],
                ['SALIDAS', 'FLOAT'],
                ['EXISTENCIA', 'FLOAT'],
                ['PRECIO DE COMPRA', 'FLOAT'],
                [titulo_colulmna_coste, 'FLOAT'],
                ['COSTO ENTRADAS', 'FLOAT'],
                ['COSTO SALIDAS', 'FLOAT'],
                ['COSTO TOTAL', 'FLOAT'],
                ['ESTADO', 'CHAR'],
                ['TIPO', 'CHAR'],
                ]
        return xlines,columns,existencia_inicial,costo_inicial
   
    def prepare_worksheet(self, workbook, warehouse, location_ids, data_exists, row=7):
        """
        crea una pestaña de excel
        regresa el workbook 
        y el row final
        """
        #print('prepare_worksheet')
        cell_formats = self.get_cell_formats(workbook)
        worksheet = False

        #SE REALIZA EL RPOCESO POR PRODUCTO
        for product in self.product_ids:
            xlines,columns,existencia_inicial,costo_inicial = self.sudo().\
                get_lines(product, location_ids)
            
            if len(xlines) > 0:
                data_exists = True

                #se crea pestaña si no se ha creado aun
                if not worksheet:
                    worksheet = workbook.add_worksheet(warehouse.name)
                    # Widen the first column to make the text clearer.
                    worksheet.set_column('A:K', 20)

                    #SE ESTABLECE ENCABEZADO
                    worksheet = self.set_worksheet_header(worksheet, warehouse, cell_formats)

                #SE CREA LA TABLA DEL REPORTE
                #SE CREAN LOS NOMBRES DE COLUMNAS
                #row = start_row # la primera sera en 7
                worksheet.write(row ,0, product.display_name, cell_formats['BOLD'])
                row += 1
                column = 0
                column_titles = [x[0] for x in columns]
                for title in column_titles:
                    ##################################33
                    if title == 'EXISTENCIA':
                        worksheet.write(row-1 ,column-1, 'EXISTENCIA INICIAL', cell_formats['BLUE_BG'])
                        worksheet.write(row-1 ,column, existencia_inicial, cell_formats['FLOAT'])

                    if title == 'COSTO TOTAL':
                        worksheet.write(row-1 ,column-1, 'COSTO INICIAL', cell_formats['BLUE_BG'])
                        worksheet.write(row-1 ,column, costo_inicial, cell_formats['FLOAT'])
                    ##################################
                    worksheet.write(row ,column, title, cell_formats['BLUE_BG'])
                    column += 1
                row += 1
                ########################################

                for line in xlines:
                    column = 0
                    for cell in column_titles:
                        format = [x[1] for x in columns if x[0]==cell][0]
                        x_format = cell_formats[format]

                        worksheet.write(row ,column, line[cell],x_format)

                        column += 1
                    row += 1
                row += 1

        return workbook, data_exists


    def get_cell_formats(self, workbook):
        """
        crea los formatos de celda del archivo
        devuelve diccionario con formatos de celda
        """
        #print('get_cell_formats')
        #FORMATOS DE CELDA ###########
        bold = workbook.add_format({'bold': True})
        blue_bg =  workbook.add_format()
        blue_bg.set_font_color('white')
        blue_bg.set_bold()
        blue_bg.set_bg_color('blue')


        totals_blue_bg =  workbook.add_format({'num_format': '#,##0.00'})
        totals_blue_bg.set_font_color('white')
        totals_blue_bg.set_bold()
        totals_blue_bg.set_bg_color('blue')

        border = workbook.add_format()
        border.set_border(1)
        #border.set_bold()

        report_title_style = workbook.add_format({'bold': True})
        report_title_style.set_font_size(12)

        border_number = workbook.add_format({'num_format': '#,##0.00'})
        border_number.set_border(1)

        borderless_num_format = workbook.add_format({'num_format': '#,##0.00'})
        borderless_num_format.set_bold()

        border_date = workbook.add_format({'num_format': 'dd-mm-yyyy'})
        border_date.set_border(1)

        date_format = workbook.add_format({'num_format': 'dd-mm-yyyy'})

        cell_formats = {
            'CHAR': border,
            'TEXT': border,
            'BOOLEAN': border,
            'INTEGER':border_number,
            'FLOAT':border_number,
            'DATE':border_date,
            'DATETIME':border_date,

            'TITLE': report_title_style,
            'TITLE_DATE': date_format,
            'BOLD': bold,
            'BLUE_BG': blue_bg,
        }
        return cell_formats
        ##############################3


    def set_worksheet_header(self, worksheet, warehouse, cell_formats):
        """
        establece el encabezado de la pestaña
        """
        #print('set_worksheet_header')
        report_title = 'Kardex de Producto'

        date = datetime.now().strftime('%d-%m-%Y')

        #ENCABEZADO####################################################
        worksheet.write('A1', self.company_id.name.upper(), cell_formats['TITLE'])
        worksheet.write('A2', report_title, cell_formats['TITLE'])
        worksheet.write('B2', date, cell_formats['BOLD'])
        worksheet.write('A4', 'Almacen', cell_formats['BOLD'])
        worksheet.write('B4', warehouse.name, cell_formats['BOLD'])
        worksheet.write('A5', 'Fecha de inicio', cell_formats['BOLD'])
        worksheet.write('B5', self.start_date, cell_formats['TITLE_DATE'])
        worksheet.write('A6', 'Fecha final', cell_formats['BOLD'])
        worksheet.write('B6', self.end_date, cell_formats['TITLE_DATE'])
        return worksheet

    
    def export_xlsx_file(self):
        #print('export_xlsx_file')
        start_date = self.start_date
        end_date = self.end_date
        product_name = self.product_id.name
        warehouse_name = self.warehouse_id.name
        company_name = self.company_id.name
        fname=tempfile.NamedTemporaryFile(suffix='.xlsx',delete=False)
        workbook = xlsxwriter.Workbook(fname)
        date = datetime.now().strftime('%d-%m-%Y')
        datas_fname = 'KARDEX DE PRODUCTO_'+str(date)+".xlsx" # Nombre del Archivo

        #se añade pestaña(s)
        row = 7
        data_exists = False
        for warehouse in self.warehouse_ids:
            location_ids = self.get_warehouse_locations(warehouse)
            workbook, data_exists = self.prepare_worksheet(workbook, warehouse, location_ids, data_exists)

        if not data_exists:
            raise ValidationError(_('Los parametros seleccionados actualmente no generan informacion para el reporte, intente modificándolos.'))
            return {}

        ### Finalizando con la Generación del Reporte en Excel ###
        workbook.close()
        f = open(fname.name, "rb")
        data = f.read()
        f.close()

        self.write({'cadena_decoding':"",
            'datas_fname':datas_fname,
            'file':base64.encodestring(data),
            'download_file': True})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.kardex',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
            }


