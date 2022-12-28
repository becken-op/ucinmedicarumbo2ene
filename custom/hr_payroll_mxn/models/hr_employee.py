# -*- coding: utf-8 -*-

from collections import defaultdict
from datetime import timedelta
import re
from pytz import utc
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_utils
ROUNDING_FACTOR = 16


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    work_number = fields.Char(
        'Employee Number', required=True, size=15,
    )
    vat = fields.Char(required=True)
    curp = fields.Char('CURP', required=True)
    address_fiscal_id = fields.Many2one(
        'res.partner', string='Fiscal Address', required=True,
    )
    syndicated = fields.Boolean(
        help='Helper field to indicate if employee is syndicated or not',
    )
    # Other employee benefits
    infonavit_loan_type = fields.Selection(
        selection=[('none', 'None'), ('percent', 'Percent'),
                   ('fixed', 'Fixed Amount'), ('smvdf', 'Minimal Wage Times')],
        default='none',
        help='Select the Infonavit loan that employee is currently paying.'
        'The amount will be deducted from paysilp automatically according'
        'with loan type you selected on this field\n'
        'Use none for employees with no active infonavit loan to pay.',
    )
    infonavit_loan_qty = fields.Float(
        string='Amount',
        help='For loan percent the decimal percent amount.\n'
        'For Minimal Wage the qty of Minimal Wage',
    )
    infonavit_loan_amount = fields.Float(
        help='Amount per day to deduct when employee have an active credit',
    )

    @api.constrains('work_number')
    def _check_work_number(self):
        pattern = re.compile(
            '([A-Z]|[a-z]|[0-9]|Ñ|ñ|!|"|%|&|\'|´|-|:|;|>|=|<|@|_|,|{|}|`|~|á'
            '|é|í|ó|ú|Á|É|Í|Ó|Ú|ü|Ü){1,15}',
        )
        wrong = self.mapped(
            lambda r: not bool(pattern.match(r.work_number)),
        )
        if any(wrong):
            raise ValidationError(
                _('Invalid Employee Number'),
            )
        return

    @api.constrains('ssnid')
    def _check_medical_insurance(self):
        pattern = re.compile('[0-9]{1,15}')
        wrong = self.mapped(
            lambda r: not bool(pattern.match(r.work_number)),
        )
        if any(wrong):
            raise ValidationError(
                _('Invalid Social Security Number'),
            )
        return

    def get_work_days_data(self, from_datetime, to_datetime, compute_leaves=True, calendar=None, domain=None):
        """
            By default the resource calendar is used, but it can be
            changed using the `calendar` argument.

            `domain` is used in order to recognise the leaves to take,
            None means default value ('time_type', '=', 'leave')

            Returns a dict {'days': n, 'hours': h} containing the
            quantity of working time expressed as days and as hours.
        """
        resource = self.resource_id
        calendar = calendar or self.resource_calendar_id

        # naive datetimes are made explicit in UTC
        if not from_datetime.tzinfo:
            from_datetime = from_datetime.replace(tzinfo=utc)
        if not to_datetime.tzinfo:
            to_datetime = to_datetime.replace(tzinfo=utc)

        # total hours per day: retrieve attendances with one extra day margin,
        # in order to compute the total hours on the first and last days
        from_full = from_datetime - timedelta(days=1)
        to_full = to_datetime + timedelta(days=1)
        intervals = calendar._attendance_intervals(from_full, to_full, resource)
        day_total = defaultdict(float)
        for start, stop, meta in intervals:
            day_total[start.date()] += (stop - start).total_seconds() / 3600

        # actual hours per day
        if compute_leaves:
            intervals = calendar._work_intervals(from_datetime, to_datetime, resource, domain)
        else:
            intervals = calendar._attendance_intervals(from_datetime, to_datetime, resource)
        day_hours = defaultdict(float)
        for start, stop, meta in intervals:
            day_hours[start.date()] += (stop - start).total_seconds() / 3600

        # compute number of days as quarters
        days = sum(
            float_utils.round(ROUNDING_FACTOR * day_hours[day] / day_total[day]) / ROUNDING_FACTOR
            for day in day_hours
        )
        return {
            'days': days,
            'hours': sum(day_hours.values()),
        }