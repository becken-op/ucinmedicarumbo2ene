from odoo import _, api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def print_report(self):
        for move in self:
            return self.env.ref('journal_entry_prodigia.poliza_report').report_action(move)


class PaymentAccountMoveLine(models.Model):
    _inherit = 'account.payment'

    def button_journal_entries2(self):
        return {
            'name': _('Journal Items'),
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [
                ('id', 'in', self.account_move_line_ids.ids),
            ],
        }

    def _get_account_move_line(self):
        """
        se obtendran los full reconcile ids de las facturas
        asociadas al pago, luego a aprtir de ellos,
        se obtendra la poliza de ivas,
        y de esta se obtendran las lineas cuyas cuentas no
        esten asociadas en el campo 'cash_basis_base_account_id'
        de impuesto
        """
        print('_get_account_move_line')
        for rec in self:

            for invoice_line_id in rec.invoice_line_ids:
                move_id = invoice_line_id.move_id
                for line_id in move_id.line_ids:
                    rec.account_move_line_ids |= line_id

            iva_account_ids = []
            for invoice_line_id in rec.reconciled_bill_ids:

                # for line_id in invoice_line_id.line_ids:
                #     rec.account_move_line_ids |= line_id
                for lin_id in invoice_line_id.tax_cash_basis_move_id.line_ids:
                    rec.account_move_line_ids |= lin_id

                for lin_id in invoice_line_id.tax_cash_basis_move_id.line_ids:
                    rec.account_move_line_ids |= lin_id

                for line in invoice_line_id.invoice_line_ids:
                    for tax in line.tax_ids:
                        for tax_line in tax.invoice_repartition_line_ids:
                            iva_account_ids.append(tax_line.account_id.code)

                        iva_account_ids.append(
                            tax.cash_basis_transition_account_id.code)

                extra_line_ids = self.env["account.move.line"].search(
                    [('ref', '=', invoice_line_id.name), ('account_id.code', 'in', iva_account_ids)])
                for lines_id in extra_line_ids:
                    rec.account_move_line_ids |= lines_id

    account_move_line_ids = fields.Many2many(
        'account.move.line',
        string='Apuntes contables',
        compute=_get_account_move_line,
    )
