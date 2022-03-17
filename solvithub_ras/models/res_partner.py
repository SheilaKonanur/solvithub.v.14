# -*- coding: utf-8 -*-
from odoo import fields, models, api

class ResPartner(models.Model):
	_inherit = "res.partner"

	@api.model
	def default_get(self, fields):
		rec = super(ResPartner, self).default_get(fields)
		if self.env.context.get('parent_id', False):
			rec['parent_id'] = self.env.context['parent_id']
		return rec
