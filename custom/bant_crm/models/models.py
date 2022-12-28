# -*- coding: utf-8 -*-

from odoo import models, fields, api

class CrmLeadInherit(models.Model):
	_inherit = 'crm.lead'

	partner_id = fields.Many2one(
        'res.partner', string='Customer', index=True, tracking=10,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Linked partner (optional). Usually created when converting the lead. You can find a partner by its Name, TIN, Email or Internal Reference.", required=True)


	budget = fields.Many2many(
		'criterios.budget', 
		string="Budget",
		help="Presupuesto con el que cuenta el cliente")

	authority = fields.Many2many(
		'criterios.authority',
		string="Authority",
		help="Si se tiene contacto directo con los tomadores de decisiones")

	need = fields.Selection([
		('1','25% si está en problemas'),
		('2','20% si está en crecimiento'),
		('3','10% si está en estabilidad'),
		('4','0% si está en zona de confort')], 
		string="Need",
		help="En que momento de la necesidad de encuentran: en problemas, en crecimiento, en estabilidad y zona de confort")

	time = fields.Selection([
		('1','25%: de 0 a 30 días'),
		('2','20%: de 30 a 90 días'),
		('3','10%: de 90 a 180 días'),
		('4','0%: más de 180 días'),], 
		string="Time",
		readonly=True,
		help="En cuanto tiempo estimamos que se genere la venta.")

	score = fields.Integer(string="Puntuación", compute="calculo_puntuacion", reload=True)

	@api.depends('budget','authority','need')
	def calculo_puntuacion(self):

		contador_buget = 0
		extra_budget = 0
		contador_authority = 0
		total = 0

		for rec in self.budget:
			contador_buget += rec.value
			if rec.name == 'Tiene seguro de cartera en UCIN':
				extra_budget = 5
		total += (contador_buget / 7 * 25) + extra_budget

		for rec1 in self.authority:
			contador_authority += rec1.value
		total += contador_authority / 6 * 25	

		if self.need == '1':
			self.time = '1'
			total += 50
		if self.need == '2':
			self.time = '2'
			total += 40
		if self.need == '3':
			self.time = '3'
			total += 20
		if self.need == '4':
		 	self.time = '4'		
		self.score = total


class CriteriosBudget(models.Model):
	_name = 'criterios.budget'

	name = fields.Char(string="Descripción")
	value = fields.Float(string="Valor", default=1)

class CriteriosAuthority(models.Model):
	_name = 'criterios.authority'

	name = fields.Char(string="Descripción")
	value = fields.Float(string="Valor", default=1, readonly=True)