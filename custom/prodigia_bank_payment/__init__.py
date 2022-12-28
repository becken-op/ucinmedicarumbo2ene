# -*- coding: utf-8 -*-
from . import models
from . import wizard


# se implementa post-init hook
# para crear acciones contextuales para las acciones de servidor 
# despues de la instalacion
from odoo import api, SUPERUSER_ID

def _create_contextual_actions(cr, registry):
    print('_create_contextual_actions')
    #check the country of the main company (only) and eventually load some module needed in that country
    env = api.Environment(cr, SUPERUSER_ID, {})
    create_group_action = env.ref('prodigia_bank_payment.create_group_server_action')
    print('create_group_action: ',create_group_action)
    if create_group_action:
        print('se crea accion')
        create_group_action.create_action()