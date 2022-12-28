from odoo import _, api, fields, models
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class ResourceCalendar(models.Model):
    _inherit = "resource.calendar"

    night_shift = fields.Boolean(string="Turno Nocturno",
        help="Active cuando se tiene un turno que inicia en un día y finaliza en el siguiente")


class ResourceCalendarAttendance(models.Model):
    _inherit = "resource.calendar.attendance"

    day_period = fields.Selection(selection_add=[('night','Noche')], 
        ondelete={'night': 'cascade'})