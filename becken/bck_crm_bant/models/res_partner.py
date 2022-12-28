# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Partner(models.Model):
    _inherit = 'res.partner'

    partner_classification = fields.Selection([
            ('direct_customer', 'Direct Customer'),
            ('distributor', 'Distributor'),
            ('integrator', 'Integrator'),
            ('surrogate', 'Surrogate'),
            ('oem', 'OEM'),
            ('private_hospital', 'Private Hospital'),
            ('public_hospital', 'Public Hospital'),
            ('subrogated_service', 'Subrogated Service'),
            ('supplier_obs', 'Supplier OBS'),
            ('supplier_pc', 'Supplier PC')],
        string='Classification',
        index=True, tracking=15,
        help='Integradores: Es aquel distribuidor que vende de manera integral a algún hospital público o privado.\n'
        'OEM (Original Equipment Manufacturer): Fabricante de equipos originales confecciona piezas o componentes que se utilizan en los productos.\n'
        'Servicios Subrrogados: Empresa que ofrece un servicio a un hospital que generalmente va dirigida a alguna área.'
        # ', en nuestro caso a anestesia o terapia respiratoria, comúnmente conocido como servicio integral.'
    )
    shipping_mode = fields.Selection([
            ('rel', 'REL'),
            ('rho', 'RHO'),
            ('rdi', 'RDI'),
            ('pco', 'PCO'),
            ('ppa', 'PPA'),
            ('eav', 'EAV'),
            ('epr', 'EPR'),
            ('eur', 'EUR'), ],
        string='Shipping mode',
        help='REL: Recolección\n'
        'RHO: Ruta UCIN Hospitales\n'
        'RDI: Ruta UCIN Distribuidores\n'
        'PCO: Paqueteria con cobro\n'
        'PPA: Paqueteria pagada por UCIN\n'
        'EAV: Entrega Asesor de Ventas asignado\n'
        'EPR: Entrega programada\n'
        'EUR: Urgencia por error de UCIN\n'
    )
    customer_type = fields.Selection([
            ('a', 'A'),
            ('b', 'B'),
            ('c', 'C'),
            ('top', 'TOP'),
            ('blac', 'BLAC')],
        string='Customer type',
        help='CLASIFICACIÓN POR TAMAÑO O POTENCIAL\n\n'
        'Los Hospitales Privados y Públicos: son clasificados con base a la siguiente tabla:\n\n'
        'Hospital       Camas       Terapia intensiva       Quirófanos\n'
        'Tipo A         50 o más    Sí                      3 o más\n'
        'Tipo A         100 o más   Sí                      Sí\n'
        'Tipo B         30 A 49     Sí                      1 a 2\n'
        'Tipo B         50 a 99     Sí                      Sí\n'
        'Tipo C         30 a 49     Sí                      No\n'
        'Tipo C         15 a 29     Sí                      Sí\n'
        'Tipo C         Justificación de negocio por @GVR o @MKT\n'
        'Tipo A         los que no cumplen con lo anterior\n\n'
    )
    hospital_infrastructure_ids = fields.One2many(
        comodel_name='partner.hospital.infrastructure',
        inverse_name='partner_id',
        string='Hospital Infrastructure',
        copy=False)
    # Aceptan entregas por paquetería
    parcel_service_accepted = fields.Boolean(
        string="Parcel Service", default=False, help="Parcel Service Accepted")
    credit_type = fields.Selection([
            ('Seguro de cartera', 'Seguro de cartera'),
            ('Pagaré', 'Pagaré'),
            ('Cadenas Productivas', 'Cadenas Productivas'),
            ('Contado', 'Contado')],
        string='Tipo de Crédito',
        default='Contado',
        help='')

    def _check_hospital_infrastructure_ids(self, vals):
        for partner in self:
            if 'partner_classification' in vals:
                partner_classification = vals['partner_classification']
            else:
                partner_classification = partner.partner_classification

            if partner_classification in ('private_hospital', 'public_hospital', 'subrogated_service'):
                if 'hospital_infrastructure_ids' in vals:
                    hospital_infrastructure_ids = vals['hospital_infrastructure_ids']

                    # Contar los registros eliminados +! y los agregados -1
                    delete_count = 0
                    for hospital_infrastructure_id in hospital_infrastructure_ids:
                        if hospital_infrastructure_id[0] in (2, 3) and hospital_infrastructure_id[2] is False:
                            delete_count += 1
                        else:
                            delete_count -= 1
                    if delete_count == len(partner.hospital_infrastructure_ids):
                        hospital_infrastructure_ids = False
                else:
                    hospital_infrastructure_ids = partner.hospital_infrastructure_ids
                if not hospital_infrastructure_ids:
                    raise UserError(
                        _('You must add at least one Hospital Infrastructure Line!'))

    @api.model
    def create(self, vals):
        self._check_hospital_infrastructure_ids(vals)
        return super(Partner, self).create(vals)

    def write(self, vals):
        self._check_hospital_infrastructure_ids(vals)
        return super(Partner, self).write(vals)


class partner_hospital_infrastructure(models.Model):
    _name = 'partner.hospital.infrastructure'
    _description = 'Partner Hospital Infrastructure'

    name = fields.Selection([
            ('aicu', 'AICU'),
            ('picu', 'PICU'),
            ('nicu', 'NICU'),
            ('operating_theaters', 'Operating Theaters'),
            ('hospitalization', 'Hospitalization')],
        string='Classification',
        index=True, required=True,
        help='AICU - Adult Intensive Care Unit\n'
        'PICU - Pediatric Intensive Care Unit\n'
        'NICU - Neonatal Intensive Care Unit\n'
        'Operating Theaters'
    )
    partner_id = fields.Many2one(
        'res.partner', 'Customer',
        required=True,
        help='')
    beds_operating_rooms_quantity = fields.Integer(
        string='Beds / Operating Rooms',
        help='Beds or Operating Rooms of the customer',
    )
    fans_anesthesia_machines_quantity = fields.Integer(
        string='Fans / Anesthesia Machines',
        help='Fans or Anesthesia Machines of the customer',
    )
