# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class ResCompany(models.Model):
	_inherit = "res.company"

	def _fetch_service_url(self):
		try:
			dts_url = self.env.ref("solvithub_dts.hiredrate_dts_service_url_parameter")
			if not dts_url or not dts_url.value:
				dts_url = "https://odoo14.hiredrate.com"
			else:
				dts_url = dts_url.value
		except:
			dts_url = "https://odoo14.hiredrate.com"
		return dts_url

	cmplify_dts = fields.Boolean('SolvitHub DTS', default=True)
	dts_bridge_host = fields.Char('Host', default=_fetch_service_url)

	def write(self, vals):
		res = super(ResCompany, self).write(vals)
		customer_id = ''
		for rec in self:
			if vals.get('plan_id', False):
				template = self.env['template.settings'].search([('company_id', '=', rec.id)])
				if template:
					for temp in template:
						temp.active = False