# -*- coding: utf-8 -*-
###############################################################################
#
#   Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#   Copyright (C) 2016-today Geminate Consultancy Services (<http://geminatecs.com>).
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': "Customer Terms And Conditions",
    "description":
        """
            This module will introduce a new feature to manage customer terms and condition added 
            in (Internal Notes). those terms and condition will be displayed in note field of 
            sale order and comment field on account invoice.
            
            So we can get individual terms and condition to be printed on Sale Quotation, 
            Sale Order and Sale Invoice Either Customer Specific or Company Specific 
            (Global - incase if customer doesn't have terms and condition) 
        """,
    'version': '14.0.0.1',
    'author': 'Geminate Consultancy Services',
    'company': 'Geminate Consultancy Services',
    'summary': 'Customer Terms And Conditions',
    'license': 'Other proprietary',
    'website': 'www.geminatecs.com',
    'category': 'sale',
    'depends': ['sale_management','account'],
    'data': [
             'views/res_partner_view.xml',
             ],
    'installable': True,
    'application': True,
    'price': 10.99,
    'currency': 'USD'
}
