#-*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.float_utils import float_compare
from collections import defaultdict


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    

    name_account_id = fields.Char(
        'Factura nro',
        related='sale_id.name_account_id')


    weight_ids = fields.One2many(
    'weight.total',
        'picking_id',
        string='Categories',
        readonly=True
    )
    
    total_weight = fields.Float(string='total entregado', compute='get_sum')
    show_weight_button = fields.Boolean(default=True, copy=False)
    picking_percentage = fields.Float('Reservado',compute='_compute_picking_p')
    show_check_availabili = fields.Boolean(
        compute='_compute_show_check_availabili')
    show_mark_as_todo_internal = fields.Boolean(
        compute='_compute_show_mark_as_todo_internal',
        help='Technical field used to compute whether the button "Mark as Todo" should be displayed.')
    show_operations = fields.Boolean(compute='_compute_show_operations_internal')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state_internal',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        )

    @api.model
    def create(self, vals):
        defaults = self.default_get(['name', 'picking_type_id'])
        picking_type = self.env['stock.picking.type'].browse(vals.get('picking_type_id', defaults.get('picking_type_id')))
        if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id', defaults.get('picking_type_id')):
            if picking_type.sequence_id:
                vals['name'] = picking_type.sequence_id.next_by_id()

        # As the on_change in one2many list is WIP, we will overwrite the locations on the stock moves here
        # As it is a create the format will be a list of (0, 0, dict)
        moves = vals.get('move_lines', []) + vals.get('move_ids_without_package', [])
        if moves and vals.get('location_id') and vals.get('location_dest_id'):
            for move in moves:
                if len(move) == 3 and move[0] == 0:
                    move[2]['location_id'] = vals['location_id']
                    move[2]['location_dest_id'] = vals['location_dest_id']
                    # When creating a new picking, a move can have no `company_id` (create before
                    # picking type was defined) or a different `company_id` (the picking type was
                    # changed for an another company picking type after the move was created).
                    # So, we define the `company_id` in one of these cases.
                    picking_type = self.env['stock.picking.type'].browse(vals['picking_type_id'])
                    if 'picking_type_id' not in move[2] or move[2]['picking_type_id'] != picking_type.id:
                        move[2]['picking_type_id'] = picking_type.id
                        move[2]['company_id'] = picking_type.company_id.id
        # make sure to write `schedule_date` *after* the `stock.move` creation in
        # order to get a determinist execution of `_set_scheduled_date`
        scheduled_date = vals.pop('scheduled_date', False)
        res = super(StockPicking, self).create(vals)
        if scheduled_date:
            res.with_context(mail_notrack=True).write({'scheduled_date': scheduled_date})
        res._autoconfirm_picking()

        # set partner as follower
        if vals.get('partner_id'):
            for picking in res.filtered(lambda p: p.location_id.usage == 'supplier' or p.location_dest_id.usage == 'customer'):
                picking.message_subscribe([vals.get('partner_id')])
        if vals.get('picking_type_id'):
            for move in res.move_lines:
                if not move.description_picking:
                    move.description_picking = move.product_id.with_context(lang=move._get_lang())._get_description(move.picking_id.picking_type_id)

        return res

    def _autoconfirm_picking(self):
        """ Automatically run `action_confirm` on `self` if the picking is an immediate transfer or
        if the picking is a planned transfer and one of its move was added after the initial
        call to `action_confirm`. Note that `action_confirm` will only work on draft moves.
        """
        # Clean-up the context key to avoid forcing the creation of immediate transfers.
        ctx = dict(self.env.context)
        ctx.pop('default_immediate_transfer', None)
        self = self.with_context(ctx)
        for picking in self:
            if picking.state in ('done', 'cancel'):
                continue
            if not picking.move_lines and not picking.package_level_ids:
                continue
            if picking.immediate_transfer or any(move.additional for move in picking.move_lines):
                    picking.move_lines.write({'state': 'draft'})

    @api.depends('state', 'move_lines')
    def _compute_show_mark_as_todo_internal(self):
        for picking in self:
            if not picking.move_lines and not picking.package_level_ids:
                picking.show_mark_as_todo_internal = False
            elif picking.state == 'draft':
                picking.show_mark_as_todo_internal = True
            elif picking.state != 'draft' or not picking.id:
                picking.show_mark_as_todo_internal = False
            else:
                picking.show_mark_as_todo_internal = True
    
    @api.depends('state')
    def _compute_show_validate(self):
        for picking in self:
            if (picking.immediate_transfer) and picking.state == 'draft':
                picking.show_validate = False
            elif picking.state not in ('draft', 'waiting', 'confirmed', 'assigned'):
                picking.show_validate = False
            else:
                picking.show_validate = True
    

    @api.depends('move_type', 'move_lines.state', 'move_lines.picking_id')
    def _compute_state_internal(self):
        ''' State of a picking depends on the state of its related stock.move
        - Draft: only used for "planned pickings"
        - Waiting: if the picking is not ready to be sent so if
          - (a) no quantity could be reserved at all or if
          - (b) some quantities could be reserved and the shipping policy is "deliver all at once"
        - Waiting another move: if the picking is waiting for another move
        - Ready: if the picking is ready to be sent so if:
          - (a) all quantities are reserved or if
          - (b) some quantities could be reserved and the shipping policy is "as soon as possible"
        - Done: if the picking is done.
        - Cancelled: if the picking is cancelled
        '''
        for picking in self:
            if not picking.move_lines:
                picking.state = 'draft'
            elif any(move.state == 'draft' for move in picking.move_lines):  # TDE FIXME: should be all ?
                picking.state = 'draft'
            elif all(move.state == 'cancel' for move in picking.move_lines):
                picking.state = 'cancel'
            elif all(move.state in ['cancel', 'done'] for move in picking.move_lines):
                picking.state = 'done'
            else:
                relevant_move_state = picking.move_lines._get_relevant_state_among_moves()
                if picking.immediate_transfer and relevant_move_state == 'draft ':
                    picking.state == 'draft'
                elif relevant_move_state == 'partially_available':
                    picking.state = 'assigned'
                else:
                    picking.state = relevant_move_state
        
    @api.depends('immediate_transfer', 'state')
    def _compute_show_check_availabili(self):
        """ According to `picking.show_check_availabili`, the "check availability" button will be
        displayed in the form view of a picking.
        """
        for picking in self:
            if picking.state not in ('confirmed', 'waiting', 'assigned'):
                picking.show_check_availabili = False
                continue
            picking.show_check_availabili = any(
                move.state in ('waiting', 'confirmed', 'partially_available') and
                float_compare(move.product_uom_qty, 0, precision_rounding=move.product_uom.rounding)
                for move in picking.move_lines
            )
    @api.depends('picking_type_id.show_operations')
    def _compute_show_operations_internal(self):
        for picking in self:
            if self.env.context.get('force_detailed_view'):
                picking.show_operations = True
                continue
            if picking.picking_type_id.show_operations:
                if (picking.state == 'draft' and picking.immediate_transfer) or picking.state != 'draft':
                    picking.show_operations = True
                else:
                    picking.show_operations = False
            else:
                picking.show_operations = False

    @api.depends('move_lines', 'state', 'picking_type_code', 'move_lines.forecast_availability', 'move_lines.forecast_expected_date')
    def _compute_products_availability(self):
        self.products_availability = False
        self.products_availability_state = 'available'
        pickings = self.filtered(lambda picking: picking.state not in ['cancel', 'draft', 'done'] and picking.picking_type_code != 'incoming')
        pickings.products_availability = _('Available')
        for picking in pickings:
            forecast_date = max(picking.move_lines.filtered('forecast_expected_date').mapped('forecast_expected_date'), default=False)
            if any(float_compare(move.forecast_availability, move.product_qty, move.product_id.uom_id.rounding) == -1 for move in picking.move_lines):
                picking.products_availability = _('Not Available')
                picking.products_availability_state = 'late'
            elif forecast_date:
                picking.products_availability = _('Exp %s', format_date(self.env, forecast_date))
                picking.products_availability_state = 'late' if picking.date_deadline and picking.date_deadline < forecast_date else 'expected'
    
    @api.depends("move_ids_without_package", "move_ids_without_package.forecast_availability")
    def _compute_picking_p(self): 
        for rec in self:
            reserved = 0
            productuom = 0
            picking_percentage = 0
            for picking in rec.move_ids_without_package:
                reserved += (picking.forecast_availability)
                productuom += (picking.product_uom_qty)
            if reserved !=0:    
                rec.picking_percentage = (reserved / productuom )*100 
            else:
                rec.picking_percentage = 0
    
    def show_weight_compute(self):
        for picking in self:
            if picking.state not in ['done']:
                continue
            picking.compute_total_per_uom()
            self.write({'show_weight_button': False})
        return True
    
    def get_sum(self):

        for rec in self:
            weight_total = 0
            for move in rec.move_ids_without_package:
                if move.quantity_done:
                    weight_total += move.quantity_done
            rec.total_weight = weight_total

    def compute_total_per_uom(self):
        params = dict()
        for rec in self:
            for move in rec.move_ids_without_package:
                product_catego = move.product_uom.id
                if product_catego:
                    params[product_catego] = move.quantity_done\
                        + params.get(product_catego, 0)
            for element in params:    
                self.env['weight.total'].create(
                    {
                        'uom_medida': element,
                        'total_weight_per_uom': params[element],
                        'picking_id': rec.id
                    }
                )
    