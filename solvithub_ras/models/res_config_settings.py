# -*- coding: utf-8 -*-
from odoo import fields, models, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    cmplify_recruitment = fields.Boolean('SolvitHub RAS', related='company_id.cmplify_recruitment', default=True, readonly=False)
    job_position_parsing = fields.Boolean('Job Position', related='company_id.job_position_parsing', default=False, readonly=False)
    job_application_parsing = fields.Boolean('Job Application', related='company_id.job_application_parsing', default=False, readonly=False)
    match_analytic = fields.Boolean('Match Analytic', related='company_id.match_analytic', default=True, readonly=False)
    ras_bridge_host = fields.Char('Host', related='company_id.ras_bridge_host', readonly=False)
    job_position_limit = fields.Integer('Job Position Limit', related='company_id.job_position_limit', readonly=False)
    application_limit = fields.Integer('Application Limit', related='company_id.application_limit', readonly=False)
    analytic_limit = fields.Integer('Analytic Limit', related='company_id.analytic_limit', readonly=False)