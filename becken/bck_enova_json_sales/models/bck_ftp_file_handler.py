from ftplib import FTP
from io import BytesIO
import json
import logging

from odoo.addons.bck_enova_json_sales.models.bck_enova_sale_order import ConfigException
from odoo import models, fields

_logger = logging.getLogger(__name__)

class BckEnovaFtpTransaction(models.Model):
    _name = 'enova.ftp.transaction'
    _description = 'Ftp transaction log for enova'

    date = fields.Datetime(readonly=True, default=fields.Datetime.now())
    type = fields.Selection([
        ('connection', 'FTP Connection'),
        ('file', 'Retrieve File'),
        ('conf', 'Configuration'),
        ('queue', 'queue')
    ])
    object = fields.Char(string='File name or ftp operation o any help value.')
    file_name = fields.Char(string='File name if exists.', invisible=True, readonly=True)
    description = fields.Char('Erro description as validation o exception error.')
    processed = fields.Boolean(readonly=True, default=False)
    status = fields.Selection([('processed', 'processed'), ('moved', 'moved'), ('deleted', 'delete'), ('end', 'end')], readonly=True, invisible=True)
    content = fields.Text(readonly=True, invisible=True)
    processed_json = fields.Text(readonly=True, invisible=True)

    def check_params(self):
        Params = self.env['ir.config_parameter'].sudo()
        server = Params.get_param('bck_enova_json_sales.enova_server')
        user = Params.get_param('bck_enova_json_sales.enova_user')
        password = Params.get_param('bck_enova_json_sales.enova_password')
        in_path = Params.get_param('bck_enova_json_sales.enova_in_path')
        out_path = Params.get_param('bck_enova_json_sales.enova_out_path')
        processed_path = Params.get_param('bck_enova_json_sales.enova_processed_path')

        if server and user and password and in_path and out_path and processed_path:
            return server, user, password, in_path, out_path, processed_path

        error = f'Check [Sales] -> [Enova files server] for: "Ftp Server" [{"OK" if server else "CHECK"}] "Ftp username" [{"OK" if user else "CHECK"}] "Ftp password" [{"OK" if password else "CHECK"}] "In Path" [{"OK" if in_path else "CHECK"}] "Out path" [{"OK" if out_path else "CHECK"}], Processed path [{"OK" if processed_path else "CHECK"}]'
        raise ConfigException(error, 'config', 'Ftp Configuration')

    def retrive_from_ftp(self):
        server, user, password, in_path, _, _ = self.check_params()
        with FTP(server, user, password, timeout=60000) as ftp:
            sections = [s for s in in_path.split("/") if s not in ""]

            for section in sections:
                ftp.cwd(section)

            retrieved_files = ftp.nlst()
            files = [file for file in retrieved_files if file not in [".", ".."]]

            for file in files:
                with BytesIO() as json:
                    ftp.retrbinary("RETR " + file, json.write)
                    yield file, json.getvalue()

    def move_to_out(self):
        server, user, password, _, out_path, _ = self.check_params()
        # Open ftp
        content = json.loads(self.processed_json)

        with FTP(server, user, password, timeout=60000) as ftp:
            sections = [s for s in out_path.split("/") if s not in ""]
            # Search dir
            for section in sections:
                ftp.cwd(section)

            with BytesIO() as file:
                file.write(self.processed_json.encode())
                content = json.loads(self.processed_json)
                reference_name = content['id'] if content['id'] else content['reference']
                file_name = content['channel'] + '-' + reference_name + '.json'
                file.seek(0)
                ftp.storbinary(f'STOR {file_name}', file)
            self.write({'status': 'moved'})

    def delete_ftp(self):
        server, user, password, in_path, _, _ = self.check_params()
        with FTP(server, user, password, timeout=60000) as ftp:
            sections = [s for s in in_path.split("/") if s not in ""]
            # Search dir
            for section in sections:
                ftp.cwd(section)
            ftp.delete(self.file_name)

        self.write({'status': 'deleted'})

    def move_to_processed(self):
        server, user, password, _, _, processed_path = self.check_params()
        # Open ftp
        with FTP(server, user, password, timeout=60000) as ftp:
            sections = [s for s in processed_path.split("/") if s not in ""]
            # Search dir
            for section in sections:
                ftp.cwd(section)

            with BytesIO() as file:
                file.write(self.content.encode())
                file_name = self.file_name
                file.seek(0)
                ftp.storbinary(f'STOR {file_name}', file)
                self.write({'status': 'end', 'processed': True})

    def record_transaction(self, type, object, description):
        vals = {
            'type': type,
            'object': object,
            'description': description,
            'date': fields.Datetime.now()
        }
        created = self.sudo().create(vals)
        return created

    def json_out_template(self, channel, id, created_on, customer_rfc, vendor_rfc, reference):
        return {
            "channel": channel,
            "id": id,
            "created_on": created_on,
            "customer_rfc": customer_rfc,
            "vendor_rfc": vendor_rfc,
            'reference': reference,
            "positions": []
        }

    def clear_processed(self):
        to_delete = self.search([('processed', '=', True), ('type', '=', 'queue')])
        if to_delete:
            for d in to_delete:
                d.sudo().unlink()
            self.env.cr.commit()

    def queue_processing(self):
        return self.search([('type', '=', 'queue'), ('processed', '=', False)], limit=1)

    def get_queue(self):
        return self.search([('type', '=', 'queue'), ('processed', '=', False)])

    def add_to_queue(self, file_name, out_json, content):
        processed_string = json.dumps(out_json).encode()
        vals = {
            'type': 'queue',
            'object': 'add_to_queue',
            'description': 'add to queue',
            'date': fields.Datetime.now(),
            'file_name': file_name,
            'status': 'processed',
            'content': content,
            'processed_json': processed_string
        }
        self.sudo().create(vals)
