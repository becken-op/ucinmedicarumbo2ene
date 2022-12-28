#-*- coding: utf-8 -*-
from odoo import models, fields, api
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    l10n_mx_edi_payment_method_id = fields.Many2one('l10n_mx_edi.payment.method',
        string='Payment Way',
        help="Indicates the way the invoice was/will be paid, where the options could be: "
             "Cash, Nominal Check, Credit Card, etc. Leave empty if unkown and the XML will show 'Unidentified'.",
        default=lambda self: self.env.ref('l10n_mx_edi.payment_method_otros', raise_if_not_found=False))

    partner_payment_method_id = fields.Many2one('l10n_mx_edi.payment.method',string='Metodo de Pago')
    
    l10n_mx_edi_usage = fields.Selection(
        selection=[
            ('G01', 'Acquisition of merchandise'),
            ('G02', 'Returns, discounts or bonuses'),
            ('G03', 'General expenses'),
            ('I01', 'Constructions'),
            ('I02', 'Office furniture and equipment investment'),
            ('I03', 'Transportation equipment'),
            ('I04', 'Computer equipment and accessories'),
            ('I05', 'Dices, dies, molds, matrices and tooling'),
            ('I06', 'Telephone communications'),
            ('I07', 'Satellite communications'),
            ('I08', 'Other machinery and equipment'),
            ('D01', 'Medical, dental and hospital expenses.'),
            ('D02', 'Medical expenses for disability'),
            ('D03', 'Funeral expenses'),
            ('D04', 'Donations'),
            ('D05', 'Real interest effectively paid for mortgage loans (room house)'),
            ('D06', 'Voluntary contributions to SAR'),
            ('D07', 'Medical insurance premiums'),
            ('D08', 'Mandatory School Transportation Expenses'),
            ('D09', 'Deposits in savings accounts, premiums based on pension plans.'),
            ('D10', 'Payments for educational services (Colegiatura)'),
            ('P01', 'To define'),
        ],
        string='Usage',
        default='P01',
        help="Used in CFDI 3.3 to express the key to the usage that will gives the receiver to this invoice. This "
             "value is defined by the customer.\nNote: It is not cause for cancellation if the key set is not the usage "
             "that will give the receiver of the document.")

    @api.onchange('partner_id','partner_payment_method_id')
    def _payment_method(self): 
        for rec in self:
            default_payment_method_id = False
            for registro in rec.partner_id:
                default_payment_method_id = registro.l10n_mx_payment_method_id
            if not rec.partner_payment_method_id and not rec.l10n_mx_edi_payment_method_id:
                rec.partner_payment_method_id = default_payment_method_id
                rec.l10n_mx_edi_payment_method_id = default_payment_method_id
            if rec.partner_payment_method_id != default_payment_method_id:
                rec.l10n_mx_edi_payment_method_id = rec.partner_payment_method_id



    @api.onchange('partner_id')
    def _l10n_mx_edi_usage(self): 
        for rec in self:
            mx_edi_usage_id = 'P01'
            for registro in rec.partner_id:
                mx_edi_usage_id = registro.l10n_mx_edi_usage
            rec.l10n_mx_edi_usage = mx_edi_usage_id
    
    def _refresh_seller_price_value(self):
        for rec in self:
            diario = rec.journal_id
            if diario.type == 'purchase':
                for line in rec.invoice_line_ids:
                    price = line.price_unit
                    product = line.product_id
                    seller = line.product_id._select_seller(
                            partner_id=line.partner_id)
                    if price != seller.price:
                        seller.write({'price':price})    
                        product._compute_most_cost_price()
                



    def write(self, vals):
        for move in self:
            if (move.restrict_mode_hash_table and move.state == 'posted' and set(vals).intersection(INTEGRITY_HASH_MOVE_FIELDS)):
                raise UserError(_('You cannot edit the following fields due to restrict mode being activated on the journal: %s.') % ', '.join(INTEGRITY_HASH_MOVE_FIELDS))
            if (move.restrict_mode_hash_table and move.inalterable_hash and 'inalterable_hash' in vals) or (move.secure_sequence_number and 'secure_sequence_number' in vals):
                raise UserError(_('You cannot overwrite the values ensuring the inalterability of the accounting.'))
            if (move.posted_before and 'journal_id' in vals and move.journal_id.id != vals['journal_id']):
                raise UserError(_('You cannot edit the journal of an account move if it has been posted once.'))
            if (move.name and move.name != '/' and 'journal_id' in vals and move.journal_id.id != vals['journal_id']):
                raise UserError(_('You cannot edit the journal of an account move if it already has a sequence number assigned.'))

            # You can't change the date of a move being inside a locked period.
            if 'date' in vals and move.date != vals['date']:
                move._check_fiscalyear_lock_date()
                move.line_ids._check_tax_lock_date()

            # You can't post subtract a move to a locked period.
            if 'state' in vals and move.state == 'posted' and vals['state'] != 'posted':
                move._check_fiscalyear_lock_date()
                move.line_ids._check_tax_lock_date()

            if move.journal_id.sequence_override_regex and vals.get('name') and vals['name'] != '/' and not re.match(move.journal_id.sequence_override_regex, vals['name']):
                if not self.env.user.has_group('account.group_account_manager'):
                    raise UserError(_('The Journal Entry sequence is not conform to the current format. Only the Advisor can change it.'))
                move.journal_id.sequence_override_regex = False

        if self._move_autocomplete_invoice_lines_write(vals):
            res = True
        else:
            vals.pop('invoice_line_ids', None)
            res = super(AccountMove, self.with_context(check_move_validity=False, skip_account_move_synchronization=True)).write(vals)

        # You can't change the date of a not-locked move to a locked period.
        # You can't post a new journal entry inside a locked period.
        if 'date' in vals or 'state' in vals:
            self._check_fiscalyear_lock_date()
            self.mapped('line_ids')._check_tax_lock_date()

        if ('state' in vals and vals.get('state') == 'posted'):
            for move in self.filtered(lambda m: m.restrict_mode_hash_table and not(m.secure_sequence_number or m.inalterable_hash)).sorted(lambda m: (m.date, m.ref or '', m.id)):
                new_number = move.journal_id.secure_sequence_id.next_by_id()
                vals_hashing = {'secure_sequence_number': new_number,
                                'inalterable_hash': move._get_new_hash(new_number)}
                res |= super(AccountMove, move).write(vals_hashing)

        # Ensure the move is still well balanced.
        if 'line_ids' in vals:
            if self._context.get('check_move_validity', True):
                self._check_balanced()
            self.update_lines_tax_exigibility()

        self._synchronize_business_models(set(vals.keys()))
        for rec in self:
            rec._refresh_seller_price_value()
        return res
