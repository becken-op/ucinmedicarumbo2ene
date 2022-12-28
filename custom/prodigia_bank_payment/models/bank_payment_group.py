# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, date
from odoo import api, exceptions, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import UserError, ValidationError

# TRABAJAR CON LOS EXCEL
import base64
import xlsxwriter
import tempfile
from xlsxwriter.utility import xl_rowcol_to_cell
import csv
import io


"""
Modelo que contendra los datos
del grupo de pagos como tal
"""

# revisar
BANK_IDENTIFIERS = {
    '044': 'scotiabank',
    '072': 'banorte',
    '002': 'banamex',
    '012': 'bancomer',
    '021': 'hsbc',
    '014': 'santander',
}


class ProdigiaBankPaymentGroup(models.Model):
    _name = 'prodigia.bank.payment.group'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Grupo de pago a banco'

    ########### CAMPOS ###########
    allow_cancel = fields.Boolean(string='Permitir cancelacion',
                                  compute='_compute_allow_cancel',
                                  help='Indica si se activa el boton de cancelar'
                                  )
    name = fields.Char(string='Nombre',
                       default=lambda self: 'Nuevo',
                       readonly=True,
                       required=True)
    invoice_ids = fields.One2many('account.invoice',
                                  'prodigia_bank_payment_id',
                                  string='Facturas')
    # advance_payment_ids = fields.One2many('account.payment',
    #     string='Anticipos')
    state = fields.Selection([
        ('draft', 'Borrador'),
        ('open', 'Abierto'),
        ('validation', 'En Validacion'),
        ('done', 'Terminado'),
        ('cancel', 'Cancelado'),
    ],
        string='Estado',
        index=True,
        readonly=True,
        default='draft',)
    # payment_count = fields.Integer(string='No. pagos',
    #     compute='_compute_payments')
    payment_ids = fields.One2many('account.payment',
                                  'prodigia_bank_payment_id',
                                  string='Pagos')
    journal_id = fields.Many2one('account.journal',
                                 string='Diario de pago',
                                 domain=[('type', 'in', ['bank', 'cash'])],
                                 required=True
                                 )
    # payment_date = fields.Date(string='Fecha de pago',
    #     default=lambda x: date.today())
    currency_id = fields.Many2one('res.currency',
                                  string='Moneda',
                                  required=True)
    company_id = fields.Many2one('res.company',
                                 'Company',
                                 default=lambda self: self.env.user.company_id,
                                 required=True)
    # Clave numérica del banco
    prodigia_bank = fields.Char(
        string='Clave de banco',
        compute='_compute_prodigia_bank',
        # store=True,
    )
    communication = fields.Char(string='Memo')
    payment_method_id = fields.Many2one('account.payment.method',
                                        string='Metodo de pago',
                                        # required=True,
                                        )

    ########### CONSTRAINTS ###########
    @api.constrains('journal_id')
    def _check_journal_id(self):
        """
        valida que el diario seleccionado cuente con un banco,
        y que el banco contenga un valor en el campo
        prodigia_bank
        """
        if not self.journal_id.bank_id:
            raise ValidationError(
                'El diario seleccionado no cuenta con un banco!!')
        if not self.journal_id.bank_id.bic:
            raise ValidationError(
                'El banco del diario asignado no cuenta con una clave definida')

    ########### FUNCIONES DE BOTONES ###########

    def action_view_payments(self):
        print('action_view_payments')
        self.ensure_one()

    ########### FUNCIONES DE BOTONES DE CAMBIO DE ESTADO ###########

    def action_draft(self):
        print('action_draft')
        self.ensure_one()
        self.state = 'draft'

    def action_open(self):
        print('action_open')
        self.ensure_one()
        self.state = 'open'
        self.create_payments()
        self._process_payment_difference()

    def action_validation(self):
        print('action_validation')
        self.ensure_one()
        self.state = 'validation'
        self.action_create_files()

    def action_done(self):
        print('action_done')
        self.ensure_one()
        self.state = 'done'
        self._confirm_payments()

    def action_cancel(self):
        print('action_cancel')
        self.ensure_one()
        self.state = 'cancel'

        # eliminar relacion de las facturas a pago
        self.invoice_ids.write({'prodigia_bank_payment_id': False})

        # eliminar pagos en estado borrador
        for payment in self.payment_ids:
            if payment.state == 'draft':
                payment.unlink()
        return True

    def action_create_files(self):
        """
        boton para crear archivos xls
        """
        self.ensure_one()
        print('action_create_files')

        bank = BANK_IDENTIFIERS.get(self.prodigia_bank, '')
        if self.journal_id.type == 'bank':
            # JCT: Comment next lines
            if hasattr(self, '_run_%s' % bank):
                print('_run_%s' % bank)

                getattr(self, '_run_%s' % bank)()
            else:
                raise ValidationError(
                    'No se encontro un metodo definido para el banco del diario de pagos seleccionado')

    ########### FUNCIONES ###########

    def _get_journal_bank_data(self, journal):
        """
        obtener informacion de cuenta bancaria de diario
        este metodo se usara en lugar de _get_partner_bank_data
        cuando no exista un partner definido en el pago (transferencias internas)
        """
        print('-----_get_journal_bank_data: ', journal.display_name)
        self.ensure_one()
        if not journal:
            raise ValidationError(
                'El Pago de tipo transferencia interna no contiene un diario de destino seleccionado!')
        if journal.type not in ('bank', 'cash'):
            raise ValidationError(
                'El diario de pago no es del tipo Banco o Efectivo!')
        bank_format = journal and journal.bank_id and journal.bank_id.bic or False
        bank_format = bank_format and BANK_IDENTIFIERS.get(bank_format, '')

        if bank_format == BANK_IDENTIFIERS.get(self.prodigia_bank, ''):
            account = journal.bank_account_id and journal.bank_account_id.acc_number or False
            error_msg = 'El diario {} no cuenta con una cuenta banco configurada'.format(
                journal.display_name)
        else:
            account = journal.clabe or False
            error_msg = 'El diario {} no cuenta con una cuenta banco y clabe interbancaria configurada'.format(
                journal.display_name)
        if not account:
            raise ValidationError(error_msg)
        return account, bank_format

    def _get_partner_bank_data(self, partner):
        """
        obtiene la primera cuenta de banco
        que se encuentre en el parter
        y si cuenta con banco definido, devuelve el formato
        regresa cuenta_bancaria, formato
        """
        print('-----_get_partner_bank_data: ', partner.display_name)
        self.ensure_one()
        # obtener padre
        while(partner.parent_id):
            partner = partner.parent_id

        # obtener cuenta de banco con secuencia mas baja
        res_partner_bank = False
        if partner.bank_ids:
            res_partner_bank = partner.bank_ids.sorted(
                key=lambda r: r.sequence)[0]

        # bank_format = res_partner_bank and res_partner_bank.bank_id and res_partner_bank.bank_id.prodigia_bank or False
        bank_format = res_partner_bank and res_partner_bank.bank_id and res_partner_bank.bank_id.bic or False
        bank_format = bank_format and BANK_IDENTIFIERS.get(bank_format, '')

        # dependiendo si el banco es el mismo se toma la cuenta o clabe
        print('bank_format: ', bank_format)
        print('prodigia_bank: ', self.prodigia_bank)
        account = res_partner_bank and res_partner_bank.acc_number or False
        clabe = res_partner_bank and res_partner_bank.clabe or False
        currency_id = res_partner_bank and res_partner_bank.currency_id or False
        print("currency_id: ", currency_id)

        if not account and not clabe:
            error_msg = 'La empresa {} no cuenta con una cuenta banco o clabe interbancaria configurada'.format(
                partner.display_name)
            raise ValidationError(error_msg)
        print('account: ', account)
        return account, clabe, bank_format, currency_id

    def _confirm_payments(self):
        print('_confirm_payments')
        self.ensure_one()
        self.payment_ids.filtered(lambda p: p.state in ('draft',)).post()

    def _run_scotiabank(self):
        """
        metodo que genera el formato xls para
        scotiabank
        """
        print('_run_scotiabank')
        self.ensure_one()
        data = []
        data_tmb = []

        # formato de otros bancos
        columns = [
            ['NOMBRE EMISOR', 'CHAR'],
            ['TELEFONO DEL EMISOR', 'TEXT'],
            ['TIPO CUENTA DE CARGO', 'CHAR'],
            ['MONEDA CARGO', 'CHAR'],
            ['PLAZA CARGO', 'CHAR'],
            ['CUENTA DE CARGO', 'CHAR'],
            ['IMPORTE', 'FLOAT'],
            ['CLAVE DE ESTADO', 'CHAR'],
            ['CLAVE DE POBLACION', 'CHAR'],
            ['CLAVE BANCO DESTINO', 'CHAR'],
            ['NOMBRE DEL BENEFICIARIO', 'CHAR'],
            ['TELEFONO BENEFICIARIO', 'TEXT'],
            ['CUENTA DE ABONO', 'CHAR'],
            ['CONCEPTO SPEI', 'CHAR'],
            ['INSTRUCCIÓN DE PAGO', 'CHAR'],
            ['SUCURSAL', 'CHAR'],
            ['TIPO DE PERSONA', 'CHAR'],
            ['RFC DEL BENEFICIARIO', 'CHAR'],
            ['IMPORTE (I.V.A)', 'FLOAT'],
            ['TIPO DE ENVÍO', 'CHAR'],
            ['FECHA DE APLICACIÓN', 'DATE'],
            ['REFERNCIA NUMÉRICA', 'CHAR'],
        ]

        # formato de banco scotiabank
        columns_tmb = [
            ['TIPO CUENTA (CARGO)', 'CHAR'],
            ['PLAZA (CARGO)', 'CHAR'],
            ['CUENTA DE CARGO', 'CHAR'],
            ['TIPO CUENTA (ABONO)', 'CHAR'],
            ['PLAZA (ABONO)', 'CHAR'],
            ['CUENTA ABONO', 'CHAR'],
            ['MONEDA', 'CHAR'],
            ['IMPORTE', 'FLOAT'],
            ['REFERENCIA EMPRESA', 'CHAR'],
            ['REFERENCIA NUMERICA', 'CHAR'],
            ['TIPO PERSONA', 'CHAR'],
            ['RFC BENEFICIARIO', 'CHAR'],
            ['IMPORTE I.V.A.', 'FLOAT'],
            ['FECHA DE APLICACIÓN', 'DATE'],
            ['REFERENCIA ALFANUMÉRICA', 'CHAR'],
        ]

        # obtener diccionario de datos de los pagos (pagos en estado borrador)
        for payment in self.payment_ids.filtered(lambda p: p.state in ('draft',)):
            partner = payment.partner_id
            if partner:
                partner_bank_acc, clabe, partner_bank_format, partner_currency_id = self._get_partner_bank_data(
                    partner)
            elif payment.payment_type == 'transfer':
                # si el partner = False, es que es transferencia interna
                print('payment.destination_journal_id: ',
                      payment.destination_journal_id.name)
                partner_bank_acc, partner_bank_format = self._get_journal_bank_data(
                    payment.destination_journal_id)
            else:
                raise ValidationError(
                    'Error en el pago {}'.format(payment.display_name))
            if not partner_bank_acc:
                partner_bank_acc = clabe

            print(
                "0000000000000000000000000000000000000000000000000000000000000000000000000000")
            print("partner_bank_acc: ", partner_bank_acc)
            print("partner_bank_format: ", partner_bank_format)
            print(
                "11111111111111111111111111111111111111111111111111111111111111111111111111111111111")
            print("partner_bank_format: ", partner_bank_format)
            # formatear fecha "YYYY/MM/DD"
            payment_date = ''
            if payment.payment_date:
                payment_date = payment.payment_date.strftime("%Y/%m/%d")

            # se define en que formato caera el pago
            if partner_bank_format == 'scotiabank':
                vals_tmb = {
                    'TIPO CUENTA (CARGO)': 'CHQ',
                    'PLAZA (CARGO)': '000',
                    'CUENTA DE CARGO': payment.journal_id.bank_account_id and payment.journal_id.bank_account_id.acc_number or '',
                    'TIPO CUENTA (ABONO)': 'CHQ',
                    'PLAZA (ABONO)': '000',
                    'CUENTA ABONO': partner_bank_acc,  # revisar
                    'MONEDA': payment.currency_id.name,
                    'IMPORTE': payment.amount,
                    # 'REFERENCIA EMPRESA': payment.company_id.name,
                    'REFERENCIA EMPRESA': partner and partner.name or '',
                    'REFERENCIA NUMERICA': '',  # revisar
                    'TIPO PERSONA': '',
                    'RFC BENEFICIARIO': '',
                    'IMPORTE I.V.A.': '',
                    'FECHA DE APLICACIÓN': payment_date,
                    'REFERENCIA ALFANUMÉRICA': payment.communication or '',
                }
                data_tmb.append(vals_tmb)
            else:  # otros bancos
                vals = {
                    'NOMBRE EMISOR': payment.company_id.name,
                    'TELEFONO DEL EMISOR': '0000000000',
                    'TIPO CUENTA DE CARGO': 'CHQ',
                    'MONEDA CARGO': payment.currency_id.name,
                    'PLAZA CARGO': '000',
                    # revisar si es necesario validar
                    'CUENTA DE CARGO': payment.journal_id.bank_account_id and payment.journal_id.bank_account_id.acc_number or '',
                    'IMPORTE': payment.amount,
                    'CLAVE DE ESTADO': '00',
                    'CLAVE DE POBLACION': '000',
                    'CLAVE BANCO DESTINO': partner_bank_acc[0:3],  # revisar
                    'NOMBRE DEL BENEFICIARIO': payment.partner_id.name,
                    'TELEFONO BENEFICIARIO': '0000000000',
                    'CUENTA DE ABONO': partner_bank_acc,  # revisar
                    'CONCEPTO SPEI': payment.communication or '',
                    'INSTRUCCIÓN DE PAGO': '3',
                    'SUCURSAL': '00000',
                    'TIPO DE PERSONA': '1',
                    'RFC DEL BENEFICIARIO': '',
                    'IMPORTE (I.V.A)': '',
                    'TIPO DE ENVÍO': '1',
                    'FECHA DE APLICACIÓN': payment_date,
                    'REFERNCIA NUMÉRICA': '',
                }
                data.append(vals)

        # creacion de workbook
        fname = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        workbook = xlsxwriter.Workbook(fname)

        # generacion de pestañas
        workbook = self._prepare_worksheet(workbook, 'TOB', data, columns)
        workbook = self._prepare_worksheet(
            workbook, 'TMB', data_tmb, columns_tmb)

        # se finalizar workbook
        workbook.close()
        f = open(fname.name, "rb")
        data = f.read()
        f.close()

        # crear y adjuntar archivo
        self._attach_file(data)

    def _run_banorte(self):
        """
        metodo que genera el formato xls para
        scotiabank
        """
        print('_run_scotiabank')
        self.ensure_one()
        data = []
        data_tmb = []
        data_spid = []

        # formato de otros bancos
        columns = [
            'Operación',
            'Clave ID',
            'Cuenta Origen',
            'Cuenta/CLABE destino',
            'Importe',
            'Referencia',
            'Descripción',
            'RFC Ordenante',
            'IVA',
            'Fecha aplicación',
            'Instrucción de pago',
            'Clave tipo cambio',
        ]

        columns_spid = [
            'OPERACIÓN',
            'CLAVE ID',
            'CUENTA ORIGEN',
            'CUENTA DESTINO',
            'IMPORTE',
            'REFERENCIA',
            'CLAVE TIPO CAMBIO',
            'DESCRIPCIÓN',
            'MONEDA ORIGEN',
            'MONEDA DESTINO',
            'RFC ORDENANTE',
            'IVA',
            'E-MAIL BENEFICIARIO',
            'FECHA DE APLICACIÓN',
            'INSTRUCCIÓN DE PAGO',
            'TIPO DE OPERACIÓN',
        ]

        # formato de banco scotiabank
        columns_tmb = columns

        usd_currency = self.env.ref('base.USD')
        mxn_currency = self.env.ref('base.MXN')
        # obtener diccionario de datos de los pagos (pagos en estado borrador)
        for payment in self.payment_ids.filtered(lambda p: p.state in ('draft',)):
            partner = payment.partner_id
            if partner:
                partner_bank_acc, clabe, partner_bank_format, partner_currency_id = self._get_partner_bank_data(
                    partner)
                print("partner_currency_id *****************: ",
                      partner_currency_id)
                if not partner.supplier_id_key:
                    raise ValidationError(
                        'La cuenta bancaria de "%s" no tiene configurado "Clave ID" proporcionado por el portal del banco' % partner.name)
            elif payment.payment_type == 'transfer':
                # si el partner = False, es que es transferencia interna
                print('payment.destination_journal_id: ',
                      payment.destination_journal_id.name)
                partner_bank_acc, partner_bank_format = self._get_journal_bank_data(
                    payment.destination_journal_id)
            else:
                raise ValidationError(
                    'Error en el pago {}'.format(payment.display_name))

            acc_customer_number = payment.journal_id.bank_account_id.customer_number
            # formatear fecha "YYYY/MM/DD"
            payment_date = ''
            if payment.payment_date:
                payment_date = payment.payment_date.strftime("%Y/%m/%d")

            if not partner_bank_acc:
                raise UserError(
                    "La cuenta bancaria de \"%s\" no tiene definido el campo cuenta en cuenta bancaria." % partner.name)
            # Se define en que formato caera el pago
            iva_amount_total = 0.00
            for invoice_id in payment.invoice_ids:
                for tax_line_id in invoice_id.tax_line_ids:
                    if tax_line_id.tax_id.type_tax_use == 'purchase' and tax_line_id.tax_id.amount > 0:
                        print("tax_line_id.amount_total: ",
                              tax_line_id.amount_total)
                        iva_amount_total += tax_line_id.amount_total

            print("******************************************************")
            print("partner_currency_id: ", partner_currency_id)
            print("usd_currency: ", usd_currency)
            print("******************************************************")

            if partner_currency_id == usd_currency:
                # Validar que la cuenta del ORDENANTE (Company) sea también en USD
                if payment.journal_id.bank_account_id.currency_id != usd_currency:
                    raise UserError(
                        "La cuenta bancaria del Diario de pago debe ser en moneda USD\nó la cuenta a depositar debe estar en moneda MXN.")

                # SPID
                vals_tmb = {
                    # Se agregará nuevo número de operación para identificar las operaciones SPID "13"
                    'OPERACIÓN': '13',
                    # El campo deberá de estar justificado a la izquierda, rellenar con espacios a la derecha
                    'CLAVE ID': partner.supplier_id_key.rjust(13),
                    # El campo deberá de estar con ceros a la izquierda
                    'CUENTA ORIGEN':  payment.journal_id.bank_account_id.acc_number.zfill(20),
                    # El campo deberá de estar con ceros a la izquierd
                    'CUENTA DESTINO': partner_bank_acc.zfill(30),
                    # Para complementar la longitud del campo, se deberá colocar ceros a la izquierda. Los últimos digitos se toman como decimales. Ej. $200 --> 00000000020000
                    'IMPORTE': str(int(round(payment.amount*100, 0))).zfill(14),
                    # Campo requerido, se debe capturar un número mayor a "
                    'REFERENCIA': payment.communication.zfill(10),
                    # Campo requerido se debe capturar ceros Ej. 0000000
                    'CLAVE TIPO CAMBIO': '0000000',
                    'DESCRIPCIÓN': payment.communication.rjust(40),
                    'MONEDA ORIGEN': '2',
                    'MONEDA DESTINO': '2',
                    # Solo aplica en SPEI
                    'RFC ORDENANTE': payment.company_id.vat.rjust(13),
                    # Incluye 2 decimales
                    'IVA': str(int(round(iva_amount_total*100, 0))).zfill(14),
                    'E-MAIL BENEFICIARIO': partner.email.rjust(39),
                    # Fecha actual DDMMAAAA
                    'FECHA DE APLICACIÓN': payment.payment_date.strftime("%d%m%Y"),
                    # Se debe capturar el Nombre del Beneficiario
                    'INSTRUCCIÓN DE PAGO': partner.name.rjust(99),
                    'TIPO DE OPERACIÓN': 1,  # Tipo de operación con Valor por default 1
                }
                data_spid.append(vals_tmb)
            elif partner_bank_format == 'banorte':
                if partner_currency_id != mxn_currency:
                    raise UserError(
                        "La cuenta bancaria de \"%s\" debe ser en moneda MXN." % partner.name)
                # Validar que la cuenta del ORDENANTE (Company) NO sea en USD
                if payment.journal_id.currency_id or payment.journal_id.bank_account_id.currency_id != mxn_currency:
                    raise UserError(
                        "La cuenta bancaria del Diario de pago debe ser en moneda MXN.")

                vals_tmb = {
                    'Operación': '02',
                    'Clave ID': partner.supplier_id_key.rjust(13),  # CLAVE DEL PROVEEDOR, NUEVO CAMPO ?
                    'Cuenta Origen':  payment.journal_id.bank_account_id and payment.journal_id.bank_account_id.acc_number.rjust(10) or ''.rjust(10),
                    'Cuenta/CLABE destino': partner_bank_acc.rjust(20),
                    'Importe': str(payment.amount).rjust(16),
                    'Referencia': payment.payment_date.strftime("%d%m%y").rjust(10) or ''.rjust(10),
                    'Descripción': payment.communication and payment.communication.replace(",", "").rjust(30) or ''.rjust(30),
                    'RFC Ordenante': payment.company_id.vat.rjust(13),  # Solo aplica en SPEI
                    'IVA': str(0).rjust(14),  # Extraer IVA de las facturas perteneciente al pago, aplica para SPEI Oper = 04
                    'Fecha aplicación': ''.rjust(8),  # Aplica solamente para Oper = 05. Quitar diagonales ddmmaaaa
                    'Instrucción de pago': 'x'.rjust(100),  # Para operaciones 01,02, 05 y 07 marcar con una "X"
                    'Clave tipo cambio': '0'.rjust(7),
                }
                data_tmb.append(vals_tmb)
            else:  # otros bancos
                if partner_currency_id != mxn_currency:
                    raise UserError(
                        "La cuenta bancaria de \"%s\" debe ser en moneda MXN." % partner.name)
                # Validar que la cuenta del ORDENANTE (Company) NO sea en USD
                if payment.journal_id.currency_id or payment.journal_id.bank_account_id.currency_id != mxn_currency:
                    raise UserError(
                        "La cuenta bancaria del Diario de pago debe ser en moneda MXN.")
                if not clabe:
                    raise UserError(
                        "La cuenta bancaria de \"%s\" no tiene definido el campo clabe en su cuenta bancaria." % partner.name)
                vals_tmb = {
                    'Operación': '04',  # SIEMPRE USAR SPEI?
                    'Clave ID': partner.supplier_id_key.rjust(13),  # CLAVE DEL PROVEEDOR, NUEVO CAMPO ?
                    'Cuenta Origen': payment.journal_id.bank_account_id and payment.journal_id.bank_account_id.acc_number.rjust(10) or ''.rjust(10),
                    'Cuenta/CLABE destino': clabe.rjust(20),
                    'Importe': str(payment.amount).rjust(16),
                    'Referencia': payment.payment_date.strftime("%d%m%y").rjust(10) or ''.rjust(10),
                    'Descripción': payment.communication and payment.communication.replace(",", "").rjust(30) or ''.rjust(30),
                    'RFC Ordenante': payment.company_id.vat.rjust(13),  # Solo aplica en SPEI
                    # Extraer IVA de las facturas perteneciente al pago, aplica para SPEI Oper = 04
                    'IVA': str(iva_amount_total).rjust(14),
                    'Fecha aplicación': ''.rjust(8),  # Aplica solamente para Oper = 05. Quitar diagonales ddmmaaaa
                    # Para operaciones 01,02, 05 y 07 marcar con una "X"
                    'Instrucción de pago': payment.partner_id.name.rjust(100),
                    'Clave tipo cambio': '0'.rjust(7),
                }
                data.append(vals_tmb)

        # creacion de workbook
        # Archivo CSV delimitado por TABS
        fname = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
        fname2 = tempfile.NamedTemporaryFile(suffix='.csv', delete=False)
        # print('fname: ', fname)
        # print('fname.name: ', fname.name)
        # print('fname2: ', fname2)
        # print("data: ", data)
        # print("data_tmb: ", data_tmb)
        # print("data_spid: ", data_spid)

        if data:
            with open(fname.name, 'w') as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=columns, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerows(data)

            f = open(fname.name, "rb")
            data = f.read()
            f.close()
            # crear y adjuntar archivo
            date = fields.Date.context_today(self).strftime('%d-%m-%Y')
            filename = self.name+'_SPEI_'+str(date)
            self._attach_file(data, extension='.txt', filename=filename)

        if data_tmb:
            with open(fname2.name, 'w') as csvfile:
                writer = csv.DictWriter(
                    csvfile, fieldnames=columns_tmb, delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerows(data_tmb)

            f = open(fname2.name, "rb")
            data = f.read()
            f.close()
            # crear y adjuntar archivo
            date = fields.Date.context_today(self).strftime('%d-%m-%Y')
            filename = self.name+'_BANORTE_'+str(date)
            self._attach_file(data, extension='.txt', filename=filename)

        if data_spid:
            if not acc_customer_number:
                raise ValidationError(
                    'La cuenta Banorte de su empresa debe tener el campo "Número de Empresa".')
            with open(fname2.name, 'w') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=columns_spid,
                                        delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                print("columns_spid: ", columns_spid)
                print("data_spid: ", data_spid)
                writer.writerows(data_spid)

            f = open(fname2.name, "rb")
            data = f.read()
            f.close()

            # Layout de archivos de pagos SPID Masivo
            # Nombre del archivo: Longitud de 21 posiciones, donde PS(2)+NumEmp(6)+AAMMDD(6)+Consecutivo(3)+.TXT(4)
            # Ejemplo: PS000003180306001.TXT
            # crear y adjuntar archivo
            spid_consecutive, spid_date = self.get_spid_date_consecutive_parameter()
            filename = 'PS' + \
                acc_customer_number.zfill(
                    6) + spid_date + str(spid_consecutive).zfill(3)
            self._attach_file(data, extension='.txt', filename=filename)

    def get_spid_date_consecutive_parameter(self):
        spid_date_consecutive = self.env['ir.config_parameter'].sudo(
        ).get_param('spid.date.consecutive', default=False)
        if not spid_date_consecutive:
            spid_consecutive = 1
            spid_date = fields.Date.context_today(self)
        else:
            spid_date_consecutive = spid_date_consecutive.split("|")
            if len(spid_date_consecutive) == 2:
                spid_date = spid_date_consecutive[0]
                try:
                    spid_date = datetime.strptime(spid_date, '%y%m%d').date()
                except:
                    spid_date = fields.Date.context_today(self)
                spid_consecutive = spid_date_consecutive[1]
                try:
                    spid_consecutive = int(spid_consecutive)
                except:
                    spid_consecutive = 1
                if spid_date == fields.Date.context_today(self):
                    spid_consecutive += 1
                else:
                    spid_consecutive = 1
                    spid_date = fields.Date.context_today(self)
            else:
                spid_consecutive = 1
                spid_date = fields.Date.context_today(self)
        spid_date = spid_date.strftime('%y%m%d')
        value = spid_date+'|'+str(spid_consecutive)
        self.env['ir.config_parameter'].sudo().set_param(
            'spid.date.consecutive', value)
        return spid_consecutive, spid_date

    def _get_cell_formats(self, workbook):
        """
        crea los formatos de celda del archivo
        devuelve diccionario con formatos de celda
        """
        print('_get_cell_formats')
        #FORMATOS DE CELDA ###########
        bold = workbook.add_format({'bold': True})
        blue_bg = workbook.add_format()
        blue_bg.set_font_color('white')
        blue_bg.set_bold()
        blue_bg.set_bg_color('blue')

        totals_blue_bg = workbook.add_format({'num_format': '#,##0.00'})
        totals_blue_bg.set_font_color('white')
        totals_blue_bg.set_bold()
        totals_blue_bg.set_bg_color('blue')

        border = workbook.add_format()
        border.set_border(1)
        # border.set_bold()

        report_title_style = workbook.add_format({'bold': True})
        report_title_style.set_font_size(12)

        border_number = workbook.add_format({'num_format': '#,##0.00'})
        border_number.set_border(1)

        borderless_num_format = workbook.add_format({'num_format': '#,##0.00'})
        borderless_num_format.set_bold()

        # fechas seran texto y se tendran que mandar ya formateadas 'yyyy/mm/dd'
        # border_date = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        border_date = workbook.add_format({'num_format': '@'})
        border_date.set_border(1)

        # date_format = workbook.add_format({'num_format': 'yyyy/mm/dd'})
        date_format = workbook.add_format({'num_format': '@'})

        percentage_format = workbook.add_format({'num_format': '0.00%'})
        percentage_format.set_border(1)

        cell_formats = {
            'CHAR': border,
            'TEXT': border,
            'BOOLEAN': border,
            'INTEGER': border_number,
            'FLOAT': border_number,
            'DATE': border_date,
            'DATETIME': border_date,

            'PERCENTAGE': percentage_format,
            'TITLE': report_title_style,
            'TITLE_DATE': date_format,
            'BOLD': bold,
            'BLUE_BG': blue_bg,
        }
        return cell_formats

    def _prepare_worksheet(self, workbook, worksheet_name, xlines, columns, row=0):
        """
        crea una pestaña de excel
        regresa el workbook
        """
        print('_prepare_worksheet')
        cell_formats = self._get_cell_formats(workbook)
        worksheet = False

        # SE REALIZA EL RPOCESO POR PRODUCTO
        if len(xlines) > 0:
            data_exists = True

            # se crea pestaña si no se ha creado aun
            if not worksheet:
                worksheet = workbook.add_worksheet(worksheet_name)
                # Widen the first column to make the text clearer.
                worksheet.set_column('A:Z', 20)

            # SE CREA LA TABLA DEL REPORTE
            # SE CREAN LOS NOMBRES DE COLUMNAS
            column = 0
            column_titles = [x[0] for x in columns]
            for title in column_titles:
                worksheet.write(row, column, title, cell_formats['BLUE_BG'])
                column += 1
            row += 1
            ########################################
            # SE CREA TABLA CON INFO
            for line in xlines:
                column = 0
                for cell in column_titles:
                    format = [x[1] for x in columns if x[0] == cell][0]
                    x_format = cell_formats[format]
                    worksheet.write(row, column, line[cell], x_format)
                    column += 1
                row += 1

            ########################################
        return workbook

    def _attach_file(self, data, extension=False, filename=False):
        """
        crea archivo a partir de file
        y lo adjunta a record de grupo
        """
        print('_attach_file')

        # se genera nombre del archivo
        date = fields.Date.context_today(self).strftime('%d-%m-%Y')
        if not extension:
            extension = ".xlsx"
        if not filename:
            datas_fname = self.name+'_'+str(date)+extension
        else:
            datas_fname = filename+extension

        irAttachment = self.env['ir.attachment']
        vals = {
            'name': datas_fname,
            # 'type': 'binary',
            'datas': base64.encodestring(data),
            'datas_fname': datas_fname,
            # 'datas': data,
            'res_model': 'prodigia.bank.payment.group',
            'res_id': self.id,
        }
        return irAttachment.create(vals)

    def _get_writeoff_account(self, payment):
        """
        Metodo que busca en configuraciones un diario de diferencias,
        de encontrarlo revuelve la cuenta deudora o acredora por defecto
        dependiendo si la diferencia de pago es positiva o negativa
        """
        journal_id = self.company_id.currency_exchange_journal_id
        if journal_id:
            if not journal_id.default_debit_account_id or not journal_id.default_credit_account_id:
                raise ValidationError(
                    'Es necesario configurar una cuenta deudora y acreedora por defecto en el diario de diferencias')
            if payment.partner_type == 'supplier':
                if payment.payment_group_difference > 0:
                    return journal_id.default_debit_account_id
                else:
                    return journal_id.default_credit_account_id
            else:
                if payment.payment_group_difference > 0:
                    return journal_id.default_credit_account_id
                else:
                    return journal_id.default_debit_account_id
        else:
            raise ValidationError(
                'Es necesario configurar un diario de diferencias en Contabilidad -> Ajustes')

    def _process_payment_difference(self):
        """
        Revisa los pagos, si existe alguna diferencia debido al uso
        de distinats monedas, estableces cuentas de diferencia cambiaria
        en el pago
        """
        print('_process_payment_difference')
        for payment in self.payment_ids:
            # solo hacer algo si tiene facturas
            print('-----------------------------------------')
            print('payment.id: ', payment.id)
            print('payment.amount: ', payment.amount)
            print('payment.invoice_ids: ', payment.invoice_ids)
            if payment.invoice_ids:
                invoice_currency = payment.invoice_ids[0].currency_id
                # if payment.currency_id.id != invoice_currency.id:
                #     pass
                if payment.payment_difference:
                    payment.payment_difference_handling = 'reconcile'
                    writeoff_account_id = self._get_writeoff_account(payment)
                    payment.writeoff_account_id = writeoff_account_id.id
                    # payment.writeoff_label = 'Write-Off'
                print('invoice_currency: ', invoice_currency.name)
                print('payment.currency_id: ', payment.currency_id.name)
                print('payment.payment_difference: ',
                      payment.payment_difference)
        # raise ValidationError('Error')

    def create_payments(self):
        # revisar
        print('create_payments')
        if not self.payment_ids:
            # old version -> 1 pago x factura
            # AccountPayment = self.env['account.payment']
            # invoice_ids = self.invoice_ids
            # payment_val_list = []
            # payment_ids = False
            # for invoice in invoice_ids:
            #     payment_val_list.append(self._get_payment_vals(invoice))
            # if len(payment_val_list):
            #     payment_ids = AccountPayment.create(payment_val_list)
            # return payment_ids

            # version 2 1 pago x grupo de facturas de partner
            AccountPayment = self.env['account.payment']
            invoice_ids = self.invoice_ids
            payment_val_list = []
            payment_ids = False
            partner_ids = self._get_invoice_partner_ids()
            for partner_id in partner_ids:
                # obtener facturas del partner en estado abierto
                invoices = self.invoice_ids.filtered(
                    lambda i: i.partner_id.id == partner_id and i.state in ('open',))
                if invoices:
                    communication = self._get_invoices_communication(invoices)
                    payment_val_list.append(
                        self._get_invoices_payment_vals(invoices, communication))
            if len(payment_val_list):
                payment_ids = AccountPayment.create(payment_val_list)
            return payment_ids

    def _get_invoice_partner_ids(self):
        """
        devuelve lista con ids de partners
        de las facturas del grupo
        (se usa para agrupar facturas por partner y
        ´posteriormente crear 1 pago por grupo)
        """
        partner_ids = self.env['res.partner']
        for invoice in self.invoice_ids:
            partner_ids |= invoice.partner_id
        return partner_ids and partner_ids.ids or []

    def _get_invoices_payment_vals(self, invoices, communication):
        """
        obtiene valores de pago de un grupo de facturas
        las facturas deben ser del mismo diario, cuenta, partner
        """
        print('_get_payment_vals')
        invoice = invoices[0]
        if invoice.type == 'out_invoice':
            payment_type = 'inbound'
            partner_type = 'customer'
        else:
            payment_type = 'outbound'
            partner_type = 'supplier'

        # invoices = self.env['account.invoice']
        # invoices |= invoice
        currency = self.currency_id

        # calcular total con la tasa de cambio actual
        # se calcula el monto a la moneda de la compañia, con la tasa del dia actual
        invoice_total = sum([x.residual for x in invoices])
        # JCT: total_amount = abs(invoice.currency_id.compute(invoice_total, self.company_id.currency_id))
        total_amount = invoice_total
        print('total_amount: ', total_amount)

        # total de facturas con la moneda de la compañia
        invoice_amount = abs(self.env['account.payment']._compute_payment_amount(
            invoices=invoices, currency=currency))
        print('invoice_amount: ', invoice_amount)
        payment_difference = total_amount - invoice_amount
        print('payment_difference: ', payment_difference)
        # raise ValidationError('error')
        vals = {
            'payment_type': payment_type,
            'partner_type': partner_type,
            'partner_id': invoice.partner_id.id,
            'amount': total_amount,
            'journal_id': self.journal_id.id,
            'payment_date': fields.Date.context_today(self),
            'communication': communication,
            'prodigia_bank_payment_id': self.id,
            'currency_id': currency.id,
            'payment_method_id': self.payment_method_id.id,
            'invoice_ids': [(6, 0, invoices.ids)],
            'company_id': self.company_id.id,
            'payment_group_difference': payment_difference,
        }
        return vals

    def _get_invoices_communication(self, invoices):
        """
        devuelve string conteniendo als referencias de invoices
        separados por ', '
        """
        return ', '.join([(invoice.reference or invoice.number or '') for invoice in invoices])

    def _get_payment_vals(self, invoice):
        """
        NO SE USA
        vieja version del metodo para obtener valores de 1 sola factura
        """
        print('_get_payment_vals')
        if invoice.type == 'out_invoice':
            payment_type = 'inbound'
            partner_type = 'customer'
        else:
            payment_type = 'outbound'
            partner_type = 'supplier'

        invoices = self.env['account.invoice']
        invoices |= invoice
        currency = self.currency_id

        # calcular total con la tasa de cambio actual
        # se calcula el monto a la moneda de la compañia, con la tasa del dia actual
        total_amount = abs(invoice.currency_id.compute(
            invoice.residual, self.company_id.currency_id))
        print('total_amount: ', total_amount)

        # total de facturas con la moneda de la compañia
        invoice_amount = abs(self.env['account.payment']._compute_payment_amount(
            invoices=invoices, currency=currency))
        print('invoice_amount: ', invoice_amount)
        payment_difference = total_amount - invoice_amount
        print('payment_difference: ', payment_difference)
        # raise ValidationError('error')
        vals = {
            'payment_type': payment_type,
            'partner_type': partner_type,
            'partner_id': invoice.partner_id.id,
            # 'amount': invoice.residual,
            # 'currency_id': invoice.currency_id.id,
            'amount': total_amount,
            'journal_id': self.journal_id.id,
            # 'l10n_mx_edi_payment_method_id': ,
            'payment_date': fields.Date.context_today(self),
            # 'communication': self.communication,
            'communication': invoice.reference or invoice.number or '',
            # 'l10n_mx_partner_bank_id': ,
            'prodigia_bank_payment_id': self.id,
            'currency_id': currency.id,
            'payment_method_id': self.payment_method_id.id,
            'invoice_ids': [(6, 0, [invoice.id, ])],
            'company_id': self.company_id.id,
            'payment_group_difference': payment_difference,
        }
        return vals

    ########### FUNCIONES DE CAMPOS COMPUTADOS ###########
    # @api.depends('journal_id')

    def _compute_prodigia_bank(self):
        for rec in self:
            if rec.journal_id and rec.journal_id.type == 'bank' and rec.journal_id.bank_id:
                # rec.prodigia_bank = rec.journal_id.bank_id.prodigia_bank
                # Clave numérica del banco
                rec.prodigia_bank = rec.journal_id.bank_id.bic

    @api.multi
    def _compute_allow_cancel(self):
        print('_compute_allow_cancel')
        for rec in self:
            allow_cancel = False
            if rec.state == 'done':
                if all(rec.payment_ids.mapped(lambda p: p.state == 'cancelled')) or not rec.payment_ids:
                    allow_cancel = True
            elif rec.state in ('cancel', 'done'):
                allow_cancel = False
            else:
                allow_cancel = True
            rec.allow_cancel = allow_cancel

    ########### FUNCIONES ORM ###########

    @api.model
    def create(self, vals):
        """
        herencia de create para establecer la secuencia
        en el nombre del record
        """
        if vals.get('name', 'Nuevo') == 'Nuevo':
            if 'company_id' in vals:
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'prodigia.bank.payment.group') or 'Nuevo'
        result = super(ProdigiaBankPaymentGroup, self).create(vals)
        return result
