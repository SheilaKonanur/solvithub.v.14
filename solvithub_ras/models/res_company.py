# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class ResCompany(models.Model):
	_inherit = "res.company"

	def _fetch_ras_service_url(self):
		try:
			ras_url = self.env.ref("solvithub_ras.hiredrate_ras_service_url_parameter")
			if not ras_url or not ras_url.value:
				ras_url = "https://odoo14.hiredrate.com"
			else:
				ras_url = ras_url.value
		except:
			ras_url = "https://odoo14.hiredrate.com"
		return ras_url

	cmplify_recruitment = fields.Boolean('SolvitHub RAS', default=True)
	job_position_parsing = fields.Boolean('Job Position', default=False)
	job_application_parsing = fields.Boolean('Job Application', default=False)
	match_analytic = fields.Boolean('Match Analytic', default=True)
	ras_bridge_host = fields.Char('Host', default=_fetch_ras_service_url)
	job_position_limit = fields.Integer('Job Position Limit')
	application_limit = fields.Integer('Job Application Limit')
	analytic_limit = fields.Integer('Match Analytic Limit')