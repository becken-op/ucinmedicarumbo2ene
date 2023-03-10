# -*- coding: utf-8 -*-
#################################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2021-today Ascetic Business Solution <www.asceticbs.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#################################################################################
{
    'name'        :"Internal Reference On Website Product",
    'author'      :'Ascetic Business Solution',
    'category'    :'Website',
    'summary'     :"""Internal Reference On Product""",
    'website'     :'http://www.asceticbs.com',
    'description' :""" Internal Reference On Product """,
    'version'      :'14.0.1.0',
    'depends'     :['website_sale','website','sale_management'],
    'data'        :[
                    'views/internel_reference_template.xml',
                   ],
    'images': ['static/description/banner.png'],
    'license': 'AGPL-3',
    'installable' :True,
    'application' :True,
    'auto_install':False,
}
