# -*- encoding: utf-8 -*-
#

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import csv
import os.path
import base64

import odoo.tools as tools

import logging
_logger = logging.getLogger(__name__)


class SAT_CatalogosWizardPayroll(models.TransientModel):
    _name = 'sat.catalogos.wizard.payroll'
    _description = "Wizard para abrir un catalogo en particular del SAT"

    catalogo = fields.Selection([('tipopercepcion', 'Percepciones'),
                                 ('tipodeduccion',  'Deducciones'),
                                 ('tipootropago', 'Otros Pagos'),
                                 ('tipoincapacidad', 'Incapacidades'),
                                 ('tipojornada',    'Jornada Laboral'),
                                 ('tipocontrato', 'Contratos'),
                                 ('riesgopuesto', 'Riesgos'),
                                 ('periodicidadpago', 'Periodicidad de Pago'),
                                 ('tiponomina',     'Nóminas'),
                                 ('tipohoraextra',  'Horas Extras'),
                                 ('origenrecurso',  'Origen Recurso'),
                                 ('tiporegimen',    'Regímenes Laborales'),
                                ],
                               string="Catálogo a revisar", required=True)
    

    
    def open_catalog(self):
        data = {'origenrecurso' :   ['c_OrigenRecurso'  ,'Origen Recurso'           ,'sat.nomina.origenrecurso'],
                'tipodeduccion' :   ['c_TipoDeduccion'  , 'Deducciones'             ,'sat.nomina.tipodeduccion'],
                'tipojornada'   :   ['c_TipoJornada'    , 'Tipo Jornada'            ,'sat.nomina.tipojornada'],
                'tipopercepcion':   ['c_TipoPercepcion' , 'Percepciones'            ,'sat.nomina.tipopercepcion'],
                'periodicidadpago': ['c_PeriodicidadPago', 'Periodicidad de Pago'   ,'sat.nomina.periodicidadpago'],
                'tipohoraextra' :   ['c_TipoHoras'      , 'Tipo de Horas Extras'    ,'sat.nomina.tipohoraextra'],
                'tiponomina'    :   ['c_TipoNomina'     , 'Tipos de Nómina'         ,'sat.nomina.tiponomina'],
                'tiporegimen'   :   ['c_TipoRegimen'    , 'Tipo de Régimen'         ,'sat.nomina.tiporegimen'],
                'tipocontrato'  :   ['c_TipoContrato'   , 'Tipo de Contratos'       ,'sat.nomina.tipocontrato'],
                'tipoincapacidad':  ['c_TipoIncapacidad', 'Tipo de Incapacidad'     ,'sat.nomina.tipoincapacidad'],
                'tipootropago'  :   ['c_TipoOtroPago'   , 'Otros Pagos'             ,'sat.nomina.tipootropago'],
                'riesgopuesto'  :   ['c_RiesgoPuesto'   , 'Tipo de Riesgos'         ,'sat.nomina.riesgopuesto'],
               }
        

        return {
            'name'      : data[self.catalogo][1],
            'type'      : 'ir.actions.act_window',
            'res_model' : data[self.catalogo][2],
            'context'   : {'create': False},
            'view_mode' : 'tree,form',
        }

