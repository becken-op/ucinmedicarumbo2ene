# -*- coding: utf-8 -*-

from odoo import fields, models, _
import math
from odoo.tools.misc import clean_context
from datetime import datetime


class MailActivity(models.Model):
    _inherit = 'mail.activity'

    use_geolocation = fields.Boolean(
        string='Use Geolocation',
        related='activity_type_id.use_geolocation',
        help="If marked, this type of activities are going to be able to check in geolocation.")

    def distance(self, origin, destination):
        """
        Calculate the Haversine distance.

        Parameters
        ----------
        origin : tuple of float
            (lat, long)
        destination : tuple of float
            (lat, long)

        Returns
        -------
        distance_in_km : float

        Examples
        --------
        >>> origin = (48.1372, 11.5756)  # Munich
        >>> destination = (52.5186, 13.4083)  # Berlin
        >>> round(distance(origin, destination), 1)
        504.2
        """
        lat1, lon1 = origin
        lat2, lon2 = destination
        radius = 6371  # km

        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) * math.sin(dlon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d = radius * c

        return d

    def action_done(self, check_in_latitude=False, check_in_longitude=False):
        message_id = super(MailActivity, self).action_done()
        record_id = self.env['mail.message'].browse(message_id)
        if record_id and check_in_latitude and check_in_longitude:
            record_id.check_in_latitude = check_in_latitude
            record_id.check_in_longitude = check_in_longitude
            record_id.check_in_date = fields.Datetime.now()

        return message_id

    def action_feedback(self, feedback=False, attachment_ids=None, check_in_latitude=False, check_in_longitude=False):
        self = self.with_context(clean_context(self.env.context))
        message_id = super(MailActivity, self).action_feedback(
            feedback=feedback, attachment_ids=attachment_ids)
        record_id = self.env['mail.message'].browse(message_id)
        if record_id and check_in_latitude and check_in_longitude:
            record_id.check_in_latitude = check_in_latitude
            record_id.check_in_longitude = check_in_longitude
            record_id.check_in_date = fields.Datetime.now()

        return message_id

    def action_feedback_schedule_next(self, feedback=False, check_in_latitude=False, check_in_longitude=False):
        ctx = dict(
            clean_context(self.env.context),
            default_previous_activity_type_id=self.activity_type_id.id,
            activity_previous_deadline=self.date_deadline,
            default_res_id=self.res_id,
            default_res_model=self.res_model,
        )
        # will unlink activity, dont access self after that
        messages, next_activities = self._action_done(feedback=feedback)

        # New code
        record_id = messages[0]
        print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        print('record_id: ', record_id)
        print('check_in_latitude: ', check_in_latitude)
        print('check_in_longitude: ', check_in_longitude)
        if record_id and check_in_latitude and check_in_longitude:
            record_id.check_in_latitude = check_in_latitude
            record_id.check_in_longitude = check_in_longitude
            record_id.check_in_date = fields.Datetime.now()
        # End new code

        if next_activities:
            return False
        return {
            'name': _('Schedule an Activity'),
            'context': ctx,
            'view_mode': 'form',
            'res_model': 'mail.activity',
            'views': [(False, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
        }

    # def _attendance_action_change(self):
    #     res = super()._attendance_action_change()
    #     location = self.env.context.get("attendance_location", False)
    #     # self.env.user.company_id.id
    #     geolocation_maximum_distance_meters = self.env.company.geolocation_maximum_distance_meters
    #     if location:
    #         res.write(
    #             {
    #                 'check_in_latitude': location[0],
    #                 'check_in_longitude': location[1],
    #                 'check_in_date': fields
    #             }
    #         )
    #     return res

# if __name__ == '__main__':
#     origin = (48.1372, 11.5756)  # Munich
#     destination = (52.5186, 13.4083)  # Berlin
#
#     origin = (20.7648672, -103.3854078)  # Yo
#     destination = (20.7261015, -103.3531233)  # Marco
#     print(round(distance(origin, destination), 4)*1000)
