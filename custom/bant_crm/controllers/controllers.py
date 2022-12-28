# -*- coding: utf-8 -*-
# from odoo import http


# class BantCrm(http.Controller):
#     @http.route('/bant_crm/bant_crm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bant_crm/bant_crm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bant_crm.listing', {
#             'root': '/bant_crm/bant_crm',
#             'objects': http.request.env['bant_crm.bant_crm'].search([]),
#         })

#     @http.route('/bant_crm/bant_crm/objects/<model("bant_crm.bant_crm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bant_crm.object', {
#             'object': obj
#         })
