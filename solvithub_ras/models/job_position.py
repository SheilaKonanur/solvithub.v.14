# -*- coding: utf-8 -*-
from odoo import models, fields, api, SUPERUSER_ID, _
from odoo.exceptions import UserError
from datetime import datetime

class Job(models.Model):
	_inherit = "hr.job"

	@api.depends('skills', 'certifications', 'qualification', 'min_exp', 'max_exp')
	def compute_form_fill(self):
		for rec in self:
			if rec.skills or rec.certifications or rec.qualification or rec.min_exp not in ['--', False] or rec.max_exp not in ['--', False]:
				rec.is_form_fill = True
			elif rec.skills and rec.certifications and rec.qualification and rec.min_exp in ['--', False] and rec.max_exp in ['--', False]:
				rec.is_form_fill = False

	@api.model
	def default_get(self, field_list):
		result = super(Job, self).default_get(field_list)
		company_id = None
		if self.env.context.get('allowed_company_ids', False):
			company_id = self.env.context['allowed_company_ids']
		company_rec = self.env['res.company'].browse(company_id)
		partner_rec = company_rec.partner_id
		partner_child = self.env['res.partner'].search([('parent_id', '=', partner_rec.id)])
		if not partner_child:
			vals = {
				'name': partner_rec.name,
				'company_type': 'person',
				'street': partner_rec.street,
				'street2': partner_rec.street2,
				'city': partner_rec.city.id if partner_rec.city else None,
				'state_id': partner_rec.state_id.id if partner_rec.state_id else None,
				'zip': partner_rec.zip,
				'country_id': partner_rec.country_id.id if partner_rec.country_id else None,
				'phone': partner_rec.phone,
				'mobile': partner_rec.mobile,
				'email': partner_rec.email,
				'website': partner_rec.website,
				'parent_id': partner_rec.id
			}
			partner_creation = self.env['res.partner'].create(vals)
			result['job_location'] = partner_creation.id
		return result

	is_form_fill = fields.Boolean('Form Fill', compute='compute_form_fill', store=True, default=False)
	cmplify_position = fields.Boolean('SolvitHub RAS Position', default=lambda self: self.env.user.company_id.cmplify_recruitment)
	certifications = fields.Many2many('certificate.details', string='Certifications')
	skills = fields.Many2many('skill.details', string='Skills')
	qualification = fields.One2many('qualification.details', 'qualification_id', 'Qualifications')
	job_id = fields.Char('Position Id')
	job_position_id = fields.Char('Job Position Id')
	response_status = fields.Char('Response Status')
	analytic_status = fields.Char('Status')
	submit_match_analytic = fields.Boolean('Enable', default=lambda self: self.env.user.company_id.match_analytic)
	min_exp = fields.Selection(
		[('--', '--'), ('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'),
		 ('8', '8'), ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'),
		 ('16', '16'), ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20')], default='--',
		string="Minimum Experience")
	max_exp = fields.Selection(
		[('--', '--'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('6', '6'), ('7', '7'), ('8', '8'),
		 ('9', '9'), ('10', '10'), ('11', '11'), ('12', '12'), ('13', '13'), ('14', '14'), ('15', '15'), ('16', '16'),
		 ('17', '17'), ('18', '18'), ('19', '19'), ('20', '20')], default='--', string="Maximum Experience")
	active = fields.Boolean('Active', default=True)
	hr_job = fields.Many2one('hr.job', 'Job Id')
	app_cnt = fields.Integer('Application Count', default=0)
	match_cnt = fields.Integer('Match Count', default=0)
	match_analytics_ids = fields.Many2many('match.run.history', string='Match Analytics')
	model = fields.Char('Training Model')
	application_template = fields.Many2one('ir.actions.report', 'Report Template')
	parse_required = fields.Boolean('Parse Required?', default=lambda self: self.env.user.company_id.job_position_parsing)
	job_ref_id = fields.Char('Job Ref Id')
	average_closing_recruitment = fields.Float('Recruitment Time in Days')
	average_shortlisted = fields.Float("Average Shortlisted Days")
	job_location = fields.Many2one('res.partner', 'Job Location')
	actual_skill = fields.Many2many('skill.details', 'act_skill_details_ref_reference', string='Actual Skills')
	synonym_skill = fields.Many2many('skill.details', 'synonym_skill_details_reference', string='Synonym Skills')
	ignore_skill = fields.Many2many('skill.details', 'ignore_skill_details_reference', string='Ignore Skills')
	normalised_skill = fields.Many2many('skill.details', 'job_position_normalised_skill', string='Normalised Skills')


	@api.onchange('address_id')
	def onchange_address_id(self):
		for rec in self:
			if rec.address_id:
				partner_id = self.env['res.partner'].search([('parent_id', '=', rec.address_id.id)])
				if not partner_id:
					vals = {
						'name': rec.address_id.name,
						'company_type': 'person',
						'street': rec.address_id.street,
						'street2': rec.address_id.street2,
						'city': rec.address_id.city.id if rec.address_id.city else None,
						'state_id': rec.address_id.state_id.id if rec.address_id.state_id else None,
						'zip': rec.address_id.zip,
						'country_id': rec.address_id.country_id.id if rec.address_id.country_id else None,
						'phone': rec.address_id.phone,
						'mobile': rec.address_id.mobile,
						'email': rec.address_id.email,
						'website': rec.address_id.website,
						'parent_id': rec.address_id.id
					}
					partner_creation = self.env['res.partner'].create(vals)

	# @api.multi
	def _error_message(self):
		return ('Job Position [%s] cannot be repeated!' % (self.name))

	# @api.multi
	def _check_job_position_is_duplicated(self):
		hr_job = self.env['hr.job'].search([('active', '=', True)])
		job_position = []
		if hr_job:
			for rec in hr_job:
				if rec.name in job_position:
					return False
				else:
					job_position.append(rec.name)
		return True

	_constraints = [
		(_check_job_position_is_duplicated, _error_message, ['name']),
	]

	# @api.multi
	def fetch_customer_id(self):
		customer_id = ''
		# if self.env.user.company_id.partner_id and self.env.user.company_id.partner_id.customer_id:
		# 	customer_id = self.env.user.company_id.partner_id.customer_id
		if self.env.user.company_id and self.env.user.company_id.customer_id:
			customer_id = self.env.user.company_id.customer_id
		return customer_id

	"""Getting record Ids of Certificate, Skills and Qualification."""

	# @api.multi
	def getting_form_parameters(self, api):
		certifi_id = []
		skill_id = []
		qualifi_id = []
		"""Checking in database whether the certificate is there or its newly created. """
		if 'certifications' in api['parameters'].keys():
			for certi in api['parameters']['certifications']:
				certificates = self.env['certificate.details'].search([('name', '=ilike', certi), ('company_id', '=', self.company_id.id)])
				if certificates:
					certifi_id.append(certificates[0].id)
				else:
					certi_vals = {
						'name': certi,
						'company_id': self.company_id.id
					}
					certifi_id.append(self.env['certificate.details'].create(certi_vals).id)

		"""Checking in database whether the skill is there or its newly created. """
		if 'skills' in api['parameters'].keys():
			for skill in api['parameters']['skills']:
				skill_list = self.env['skill.details'].search([('name', '=ilike', skill), ('company_id', '=', self.company_id.id)])
				if skill_list:
					skill_id.append(skill_list[0].id)
				else:
					skill_vals = {
						'name': skill,
						'company_id': self.company_id.id
					}
					skill_id.append(self.env['skill.details'].create(skill_vals).id)

		"""Checking in database whether the qualification is there or its newly created. """
		if 'qualification' in api['parameters'].keys():
			for qual in api['parameters']['qualification']:
				qual_list = self.env['qualification.details'].search([('name', '=ilike', qual), ('company_id', '=', self.company_id.id)])
				if qual_list:
					qualifi_id.append(qual_list[0].id)
				else:
					qual_vals = {
						'name': qual,
						'company_id': self.company_id.id
					}
					qualifi_id.append(self.env['qualification.details'].create(qual_vals).id)
		return certifi_id, skill_id, qualifi_id

	# @api.multi
	def account_token(self):
		user_token = self.env['iap.account'].get('analytic_service_ma')
		return user_token

	"""On Creation or Updation if Job Position Id is not created then this function will execute."""

	# @api.multi
	def job_position_creation(self, vals, call=''):
		certifi = []
		qualifi = []
		skills = []
		api = {}
		customer_id = self.fetch_customer_id()
		if not customer_id:
			raise UserError("Please enter Customer Id. \nGo to Recruitment -> Settings -> SolvitHub -> Enter Customer Id")
		# if self.env.user.partner_id.id not in self.env.user.company_id.partner_id.child_ids.ids:
		# 	raise UserError("Please register your User[%s] under your company [%s] \n Go to Contacts -> %s -> Add your company" % (self.env.user.partner_id.name, self.env.user.company_id.partner_id.name, self.env.user.partner_id.name))
		if vals.get('job_location', False):
			address = self.env['res.partner'].browse(vals['job_location'])
		else:
			address = self.job_location
		if vals.get('name', False):
			title = vals['name']
		else:
			title = self.name
		job_id = ''
		if vals.get('job_id', False):
			job_id = vals['job_id']
		elif self.job_id:
			job_id = self.job_id
		data = {
			"cust_id": customer_id or None,
			"org_job_id": job_id or '',
			"org_job_location": address.state_id.name or '',
			"org_job_title": title,
			'job_description': '',
			"max_experience": 0,
			"min_experience": 0,
			"qualification": [],
			"skills": [],
			"certifications": [],
			"job_position_state": self.state,
			"position_count": self.no_of_recruitment,
			"position_hired_count": self.no_of_hired_employee,
			"parse": self.parse_required
		}

		if (vals.get('description', False) or self.description) and not self.is_form_fill:
			if vals.get('description', False):
				data['job_description'] = vals['description']
			elif self.description:
				data['job_description'] = self.description

		elif self.is_form_fill:
			if self.certifications:
				for line in self.certifications:
					certifi.append(line.name)

			if self.qualification:
				for line in self.qualification:
					qualifi.append(line.name)

			if self.skills:
				for line in self.skills:
					skills.append(line.name)
			parse = self.parse_required
			max_exp = 0
			min_exp = 0
			if vals.get('max_exp', False):
				max_exp = int(vals['max_exp']) if vals['max_exp'] != '--' else 0
			elif self.max_exp:
				max_exp = self.max_exp if self.max_exp != '--' else 0
			if vals.get('min_exp', False):
				min_exp = int(vals['min_exp']) if vals['min_exp'] != '--' else 0
			elif self.min_exp:
				min_exp = self.min_exp if self.min_exp != '--' else 0

			data['certifications'] = certifi
			data['skills'] = skills
			data['qualification'] = qualifi
			data['max_experience'] = int(max_exp)
			data['min_experience'] = int(min_exp)
		if data:
			token = self.account_token()
			if token:
				api, status = self.env['api.request'].job_position_iap(data, token, call=call)
				model_api, model_status = self.env['api.request'].model_fetch_iap(token, name=self.name, job_position_id=self.job_position_id, call='get')
			if model_api in [200, 201]:
				if model_status.get('parameters', False) and model_status['parameters']['available_models'] and 'Generic Model' in model_status['parameters']['available_models']:
					self.with_context(skip_updation=True).write({
					'model': 'Generic Model'
					})
			if api not in [200, 201]:
				self.with_context(skip_updation=True).write({
					'analytic_status': status['status'],
					'response_status': status['message']
				})
			elif api in [200, 201]:
				if 'description' in vals.keys() and not self.parse_required:
					status_message = 'Successfully created Job Position.'
					status_analytics = 'COMPLETE'
				else:
					status_message = status['message']
					status_analytics = status['status']

				self.with_context(skip_updation=True).write({
					'analytic_status': status_analytics,
					'response_status': status_message,
					'job_position_id': status['parameters']['job_position_id']
				})
				
			if api in[200,201] and self.skills:
				
				skill_id_list = []
				if status['parameters'] and 'skills' in status['parameters'].keys() and status['parameters']['skills']:

					for skill in status['parameters']['skills']:
						
						skill_id = self.env['skill.details'].search([('name', '=like', skill)], limit=1)
						
						if skill_id:
							skill_id_list.append(skill_id.id)
						else:
							skill_id = self.env['skill.details'].create({'name': skill})
							skill_id_list.append(skill_id.id)
							

		
				rejected_ignore_id = []
				rejected_synonym_id=[]
				rejected_skill_id=[]
				if status['parameters'] and status['parameters']['rejected_skills']:
					for rej_skill in range(len(status['parameters']['rejected_skills'])):
						rejected_skills = status['parameters']['rejected_skills']
						
						for skill in rejected_skills:
							rejected_skill= self.env['skill.details'].search([('name', '=ilike', skill['skill_name'])], limit=1)
							rejected_reason = skill['reason']
							rejected_skill_id.append(rejected_skill.id)
							
			
							if rejected_skill and rejected_reason == 'IGNORE':
								rejected_ignore_id.append(rejected_skill.id)
								
							if rejected_skill and rejected_reason == 'SYNONYM':
								rejected_synonym_id.append(rejected_skill.id)

				
				self.with_context(skip_updation=True).write({"synonym_skill":[(6,0,rejected_synonym_id)],"ignore_skill":[(6,0,rejected_ignore_id)]})
			
				# self.normalised_skill = skill_id_list
				
				self.with_context(skip_updation=True).write({"normalised_skill":skill_id_list})

				actual_skill_id = []
				if status['parameters'] and status['parameters']['actual_skills']:
						actual_skills = status['parameters']['actual_skills']
						
						for skill in actual_skills :
							actual_skill = self.env['skill.details'].search([('name', '=ilike', skill)], limit=1)
							if actual_skill:
								actual_skill_id.append(actual_skill.id)

				# self.actual_skill = actual_skill_id
				self.with_context(skip_updation=True).write({"actual_skill":actual_skill_id})


				skills_synonym_map=[]
				primary_skill_id =[]
				secondary_skill_id=[]
				if status['parameters'] and status['parameters']['skills_synonym_map']:
					synonym_map = status['parameters']['skills_synonym_map']

					for skill in synonym_map:

						primary_skill = skill['primary_skill'] 
						primary_id = self.env['skill.details'].search([('name', '=ilike',primary_skill)], limit=1)
						primary_skill_id.append(primary_id.id)

						secondary_skill = skill['secondary_skill']
						secondary_id = self.env['skill.details'].search([('name', '=ilike', secondary_skill)], limit=1)
						secondary_skill_id.append(secondary_id.id)

					
						primary_rec = self.env['synonym.map'].search([('primary_id', '=', primary_id.id)], limit=1)
						secondary_rec = self.env['synonym.map'].search([('secondary_id', '=', primary_rec.secondary_id)], limit=1)
						if secondary_rec:
							rec = secondary_rec
						else :
							self.env['synonym.map'].create({'primary_id': primary_id.id,'secondary_id': secondary_id.id})
		return data, status

	""""Once Job Position Id is created then Get call will be triggered for updation."""
	# @api.multi
	def job_position_updation(self, vals, call=''):
		certifi = []
		qualifi = []
		skills = []
		api = {}
		if vals.get('name', False):
			name = vals['name']
		elif self.name:
			name = self.name
		location = ''
		if vals.get('job_location', False):
			partner = self.env['res.partner'].browse(vals['job_location'])
			location = partner.state_id.name
		elif self.job_location:
			location = self.job_location.state_id.name
		if self.certifications:
			for line in self.certifications:
				certifi.append(line.name)
		if self.skills:
			for line in self.skills:
				skills.append(line.name)
		if self.qualification:
			for line in self.qualification:
				qualifi.append(line.name)
		if vals.get('max_exp', False):
			max_exp = vals['max_exp']
		elif self.max_exp:
			max_exp = self.max_exp
		if vals.get('min_exp', False):
			min_exp = vals['min_exp']
		elif self.min_exp:
			min_exp = self.min_exp
		data = {
			"org_job_location": location if location else '',
			"org_job_title": name,
			"certifications": [],
			"qualification": [],
			"skills": [],
			"max_experience": 0,
			"min_experience": 0,
			"job_description": '',
			"job_position_state": self.state,
			"position_count": self.no_of_recruitment,
			"position_hired_count": self.no_of_hired_employee,
			"parse": self.parse_required
		}

		if self.is_form_fill:
			data['certifications'] = certifi
			data['skills'] = skills
			data['qualification'] = qualifi
			data['min_experience'] = int(min_exp) if min_exp != '--' else 0
			data['max_experience'] = int(max_exp) if max_exp != '--' else 0

		elif not self.is_form_fill and vals.get('description', False):
			data['job_description'] = vals['description']

		job_position = self.job_position_id
		if data:
			token = self.account_token()
			api, status = self.env['api.request'].job_position_iap(data, token, job_position_id=job_position, call=call)
			if api not in [200, 201]:
				self.with_context(skip_updation=True).write({
					'analytic_status': status['status'],
					'response_status': status['message']
				})
			elif api in [200, 201]:
				if 'description' in vals.keys() and not self.parse_required:
					status_message = 'Successfully updated Job Position.'
					status_analytics = 'COMPLETE'
				else:
					status_message = status['message']
					status_analytics = status['status']
				self.with_context(skip_updation=True).write({
					'analytic_status': status_analytics,
					'response_status': status_message,
				})

			if api in[200,201] and self.skills:
				
				skill_id_list = []
				if status['parameters'] and 'skills' in status['parameters'].keys() and status['parameters']['skills']:

					for skill in status['parameters']['skills']:
						
						skill_id = self.env['skill.details'].search([('name', '=like', skill)], limit=1)
						
						if skill_id:
							skill_id_list.append(skill_id.id)
						else:
							skill_id = self.env['skill.details'].create({'name': skill})
							skill_id_list.append(skill_id.id)
							

		
				rejected_ignore_id = []
				rejected_synonym_id=[]
				rejected_skill_id=[]
				if status['parameters'] and status['parameters']['rejected_skills']:
					for rej_skill in range(len(status['parameters']['rejected_skills'])):
						rejected_skills = status['parameters']['rejected_skills']
						
						for skill in rejected_skills:
							rejected_skill= self.env['skill.details'].search([('name', '=ilike', skill['skill_name'])], limit=1)
							rejected_reason = skill['reason']
							rejected_skill_id.append(rejected_skill.id)
							
			
							if rejected_skill and rejected_reason == 'IGNORE':
								rejected_ignore_id.append(rejected_skill.id)
								
							if rejected_skill and rejected_reason == 'SYNONYM':
								rejected_synonym_id.append(rejected_skill.id)

				
				self.with_context(skip_updation=True).write({"synonym_skill":[(6,0,rejected_synonym_id)],"ignore_skill":[(6,0,rejected_ignore_id)]})
			
				# self.normalised_skill = skill_id_list
				
				self.with_context(skip_updation=True).write({"normalised_skill":skill_id_list})

				actual_skill_id = []
				if status['parameters'] and status['parameters']['actual_skills']:
						actual_skills = status['parameters']['actual_skills']
						
						for skill in actual_skills :
							actual_skill = self.env['skill.details'].search([('name', '=ilike', skill)], limit=1)
							if actual_skill:
								actual_skill_id.append(actual_skill.id)

				# self.actual_skill = actual_skill_id
				self.with_context(skip_updation=True).write({"actual_skill":actual_skill_id})


				skills_synonym_map=[]
				primary_skill_id =[]
				secondary_skill_id=[]
				if status['parameters'] and status['parameters']['skills_synonym_map']:
					synonym_map = status['parameters']['skills_synonym_map']

					for skill in synonym_map:

						primary_skill = skill['primary_skill'] 
						primary_id = self.env['skill.details'].search([('name', '=ilike',primary_skill)], limit=1)
						primary_skill_id.append(primary_id.id)

						secondary_skill = skill['secondary_skill']
						secondary_id = self.env['skill.details'].search([('name', '=ilike', secondary_skill)], limit=1)
						secondary_skill_id.append(secondary_id.id)

					
						primary_rec = self.env['synonym.map'].search([('primary_id', '=', primary_id.id)], limit=1)
						secondary_rec = self.env['synonym.map'].search([('secondary_id', '=', primary_rec.secondary_id)], limit=1)
						if secondary_rec:
							rec = secondary_rec
						else :
							self.env['synonym.map'].create({'primary_id': primary_id.id,'secondary_id': secondary_id.id})
		return api

	def normalise_skill_fetch(self):                   
        
		rec_ids=[]

		for skill in self.ignore_skill:
			
			ignore = self.env['actual.skill.details'].create({'skill_id': skill.id, 'ignore': True, "job_position_ref":self.id})
			rec_ids.append(ignore.id)
		for skill in self.synonym_skill:
			synonym_skill = self.env['synonym.map'].search([('secondary_id', '=', skill.id)], limit=1)
			
			primary_skill= self.env['skill.details'].search([('id', '=', synonym_skill.primary_id)], limit=1)
			synonym = self.env['actual.skill.details'].create({'skill_id': skill.id, 'synonym': True, "job_position_ref":self.id, "synonym_name":primary_skill.name})
			rec_ids.append(synonym.id)
			
		for skill in self.skills:
			if skill not in self.ignore_skill  :
				if skill not in self.synonym_skill:
					normalise = self.env['actual.skill.details'].create({'skill_id': skill.id, "job_position_ref":self.id})
					rec_ids.append(normalise.id)


		action = self.env.ref('solvithub_ras.action_normalised_skills_wizard').sudo()
		result = {
			'name': action.name,
			'help': action.help,
			'type': action.type,
			'view_mode': action.view_mode,
			'target': 'new',
			'context': {'default_normalised_skill':rec_ids},
			'res_model': action.res_model,
		}
		return result	

	@api.model
	def create(self, vals):
		"""Job Id auto sequence part"""
		self = super(Job, self).create(vals)
		"""Checking whether company_id is there not for configuration part."""
		cmplify_position = False
		if 'cmplify_position' in vals.keys():
			cmplify_position = vals.get('cmplify_position', False)
		else:
			cmplify_position = self.cmplify_position
		if cmplify_position:
			if vals.get('description', False) and self.is_form_fill:
				raise UserError("Please clear the form before entering the description.")
			"""Fetching and assigning sequence for Job Position"""
			if vals.get('company_id', False):
				self.with_context(skip_updation=True).write({'job_id': self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('hr.job') or _('New')})
			else:
				self.with_context(skip_updation=True).write({'job_id': self.env['ir.sequence'].next_by_code('hr.job') or _('New')})
			""" Calling Bridge Server for Odoo Credits"""
			data, api = self.job_position_creation(vals=vals, call='post')
		return self

	# @api.multi
	def write(self, vals):
		rec = super(Job, self).write(vals)
		if vals.get('state', False) and vals['state'] == 'open':
			start_date = self.create_date
			end_date = self.write_date
			diff = end_date - start_date
			days, seconds = diff.days, diff.seconds
			hours = diff.total_seconds() / 3600
			self.with_context(skip_updation=True).average_closing_recruitment = round(hours/24, 2)
		cmplify_position = False
		if 'cmplify_position' in vals.keys():
			cmplify_position = vals.get('cmplify_positon', False)
		else:
			cmplify_position = self.cmplify_position
		if cmplify_position:
			if vals.get('description', False) and self.is_form_fill:
				raise UserError("Please clear the form before entering the description.")
			if self.env.context.get('skip_updation', False) or 'is_published' in vals.keys() or 'website_published' in vals.keys():
				return super(Job, self).write(vals)
			if not self.job_position_id:
				data, api = self.job_position_creation(vals, call='post')
			if self.job_position_id:
				api = self.job_position_updation(vals, call='put')
			if 'parse_required' in vals.keys() and vals.get('parse_required', False) and not self.is_form_fill:
				self.refresh_request()
			elif 'parse_required' in vals.keys() and not vals.get('parse_required', False):
				self.write({
					'certifications': [[6, 0, False]],
					'skills': [[6, 0, False]],
					'qualification': [[6, 0, False]],
					'min_exp': '--',
					'max_exp': '--'
				})
		return rec

	# @api.multi
	def action_match_analysis(self):
		if not self.skills:
			raise UserError("Please enter Skills before Match Analytics.!")
		if not self.model:
			raise UserError("Please select Training Model before running Match Analytics.!")
		if self.analytic_status not in ['COMPLETE', 'COMPLETED']:
			raise UserError("Your Job Position cannot be send to Match Analysis on Progress State.")
		application_id = self.env['hr.applicant'].search(
			[('job_id', '=', self.id), ('analytic_status', '=', 'COMPLETE')])
		if len(application_id) < 2:
			raise UserError("Atleast two applications are required to run Match Analytics.")
		job_position = self.job_position_id
		action = self.env.ref('solvithub_ras.action_match_run_history').sudo()
		result = {
			'name': _('Match Run History'),
			'help': action.help,
			'type': action.type,
			# 'view_type': action.view_type,
			'view_mode': 'tree,form',
			'target': action.target,
			'domain': [('job_position_id', '=', job_position)],
			'res_model': action.res_model,
		}
		return result

	# @api.multi
	def refresh_request(self):
		if self.cmplify_position:
			customer_id = self.fetch_customer_id()
			job_position = self.job_position_id
			document_attach = self.env['ir.attachment'].search([('res_model', '=', 'hr.job'), ('res_id', '=', self.id)])
			if not self.description and not document_attach:
				return True
			type = ''
			if document_attach:
				type = 'document'
			elif self.description:
				type = 'description'
			token = self.account_token()
			api = {}
			if self.analytic_status == 'IN_PROGRESS':
				data = {
					"cust_id": customer_id or None,
					"org_job_id": self.job_id,
					"org_job_location": self.job_location.state_id.name or '',
					"org_job_title": self.name,
				}
				# document_attach = self.env['ir.attachment'].search([('res_model', '=', 'hr.job'), ('res_id', '=', self.id)])
				# job_position = self.job_position_id
				data = {
					'certifications': [],
					'skills': [],
					'qualification': [],
					'min_experience': 0,
					'max_experience': 0,
				}
				# token = self.account_token()
				if token:
					# type = ''
					# if self.description:
					# 	type = 'description'
					# elif document_attach:
					# 	type = 'document'
					api, status = self.env['api.request'].job_position_iap(data, token, job_position_id=job_position, call='get', type=type)
				if api not in [200, 201]:
					self.with_context(skip_updation=True).write({
						'analytic_status': status['status'],
						'response_status': status['message']
					})

				elif api in [200, 201]:
					self.with_context(skip_updation=True).write({
						'analytic_status': status['status'],
						'response_status': status['message']
					})

					certifi_id, skill_id, qualifi_id = self.getting_form_parameters(status)
					self.write({
						'certifications': [(4, rec, None) for rec in certifi_id],
						'skills': [(4, rec, None) for rec in skill_id],
						'qualification': [(4, rec, None) for rec in qualifi_id],
						'min_exp': str(int(status['parameters']['min_experience'])) if status['parameters']['min_experience'] != None else '--',
						'max_exp': str(int(status['parameters']['max_experience'])) if status['parameters']['max_experience'] != None else '--'
					})
			else:
				data = {
					"org_job_location": self.job_location.state_id.name or '',
					"org_job_title": self.name,
					"certifications": [],
					"qualification": [],
					"skills": [],
					"max_experience": 0,
					"min_experience": 0,
					"job_description": '',
					"job_position_state": self.state,
					"position_count": self.no_of_recruitment,
					"position_hired_count": self.no_of_hired_employee,
					"parse": self.parse_required
				}
				if type == 'description':
					data['job_description'] = self.description
				if token:
					if type == 'description':
						api, status = self.env['api.request'].job_position_iap(data, token, job_position_id=job_position, call='put')
					elif type == 'document':
						binary_doc = document_attach.datas
						doc_name = document_attach.name
						api, status = self.env['api.request'].document_parser_iap(token=token, job_position_id=job_position, binary_doc=binary_doc, doc_name=doc_name, call='put', model='hr_job', parse=self.parse_required)
					if api not in [200, 201]:
						self.with_context(skip_updation=True).write({
							'analytic_status': status['status'],
							'response_status': status['message']
						})
					elif api in [200, 201]:
						self.with_context(skip_updation=True).write({
							'analytic_status': status['status'],
							'response_status': status['message']
						})

						certifi_id, skill_id, qualifi_id = self.getting_form_parameters(status)

	# @api.multi
	def refresh_request_cron(self):
		job_position = self.env['hr.job'].search([])
		if job_position:
			for rec in job_position:
				rec.response_status = ''
				rec.refresh_request()

	# @api.multi
	def action_reset_form(self):
		if self.analytic_status == 'IN_PROGRESS':
			raise UserError("You cannot reset the form while processing.")
		if self.submit_match_analytic:
			job_position = self.job_position_id
			data = {
				"min_experience": 0,
				"max_experience": 0,
				"skills": [],
				"certifications": [],
				"qualification": []
			}
			token = self.account_token()
			if data and token:
				api, status = self.env['api.request'].job_position_iap(data, token, job_position_id=job_position, call='put', reset=1)
			if api in [200, 201]:
				self.with_context(skip_updation=True).write({
					'analytic_status': status['status'],
					'response_status': status['message'],
				})
		else:
			self.with_context(skip_updation=True).write({
				'analytic_status': '',
				'response_status': '',
			})
		self.with_context(skip_updation=True).write({
			'certifications': False,
			'skills': False,
			'qualification': [[6, 0, False]],
			'min_exp': '--',
			'max_exp': '--',
			'is_form_fill': False
		})

	# @api.multi
	def unlink(self):
		for position in self:
			token = self.account_token()
			if token:
				position.with_context(skip_updation=True).active = False
				if position.job_position_id:
					job_position = position.job_position_id
					application_id = self.env['hr.applicant'].search([('job_id', '=', position.id)])
					if application_id:
						for app in application_id:
							app.with_context(skip_updation=True).active = False
					analytic_id = self.env['match.run.history'].search([('job_position_rec', '=', position.id)])
					if analytic_id:
						for match in analytic_id:
							match.active = False
					api, status = self.env['api.request'].delete_iap(token, job_position_id=job_position, call='delete', model='hr_job')
					# api = self.env['api.request'].delete_request('delete', job_position)

	# @api.multi
	def skill_fetch(self):
		skill_id = []
		if self.name:
			name = self.name
			job_position = self.job_position_id
			token = self.account_token()
			if token:
				api, status = self.env['api.request'].skill_suggestion_iap(token, name=name, job_position_id=job_position, call='get')
			if api in [200, 201]:
				if status.get('predicted_skills', False):
					for skill in status['predicted_skills']:
						skill_rec = self.env['skill.details'].search([('name', '=ilike', skill)])
						if skill_rec:
							skill_id.append(skill_rec[0].id)
						else:
							vals = {
								'name': skill,
								'company_id': self.env.user.company_id.id
							}
							skill_rec = self.env['skill.details'].create(vals)
							skill_id.append(skill_rec.id)

		action = self.env.ref('solvithub_ras.action_skill_wizard').sudo()
		result = {
			'name': action.name,
			'help': action.help,
			'type': action.type,
			# 'view_type': action.view_type,
			'view_mode': action.view_mode,
			'target': 'new',
			'context': {'default_job_position_id': self.id, 'default_skill_id': skill_id},
			'res_model': action.res_model,
		}
		return result

	# @api.multi
	def model_fetch(self):
		model_id = []
		if self.name:
			name = self.name
			job_position = self.job_position_id
			token = self.account_token()
			if token:
				api, status = self.env['api.request'].model_fetch_iap(token, name=name, job_position_id=job_position, call='get')
			if api in [200, 201]:
				if status.get('parameters', False) and status['parameters']['available_models']:
					model_rec = self.env['model.details'].search([])
					if model_rec:
						for line in model_rec:
							line.unlink()
					for model in status['parameters']['available_models']:
						vals = {
							'name': model,
							'company_id': self.env.user.company_id.id
						}
						model_rec = self.env['model.details'].create(vals)
						model_id.append(model_rec.id)

		action = self.env.ref('solvithub_ras.action_model_wizard').sudo()
		result = {
			'name': action.name,
			'help': action.help,
			'type': action.type,
			# 'view_type': action.view_type,
			'view_mode': action.view_mode,
			'target': 'new',
			'context': {'default_job_position_id': self.id},
			'res_model': action.res_model,
		}
		return result

	# @api.multi
	def toggle_active(self):
		self = self.with_context(skip_updation=True)
		super(Job, self).toggle_active()

	# @api.multi
	def set_open(self):
		# self = self.with_context(skip_updation=True)
		return super(Job, self).set_open()

	# @api.multi
	def set_recruit(self):
		# self = self.with_context(skip_updation=True)
		return super(Job, self).set_recruit()

	# @api.multi
	def refresh_report_status_cron(self):
		self = self.with_context(skip_updation=True)
		hr_job_rec = self.env['hr.job'].search([])
		if hr_job_rec:

			for rec in hr_job_rec:
				"""Average Job Position to close a recruitment"""
				start_date = rec.create_date
				end_date = datetime.today()
				diff = end_date - start_date
				hours = diff.total_seconds() / 3600
				rec.average_closing_recruitment = round(hours / 24, 2)

				application_rec = self.env['hr.applicant'].search([('job_id', '=', rec.id), ('active', '=', True)])
				app_cnt = 0
				total_hour = 0
				rec.average_shortlisted = None
				if application_rec:
					for app in application_rec:
						if app.shortlisted_date:
							app_start = app.create_date
							app_end = app.shortlisted_date
							diff = app_end - app_start
							hours = diff.total_seconds() / 3600
							total_hour += hours
							app_cnt += 1
				if total_hour:
					total_hour = total_hour / app_cnt
					rec.average_shortlisted = round(total_hour / 24, 2)
				analytic_rec = self.env['match.run.history'].search(
					[('job_position_rec', '=', rec.id), ('active', '=', True)])
				if application_rec:
					rec.app_cnt = len(application_rec)
				if analytic_rec:
					rec.match_cnt = len(analytic_rec)


class ModelDetails(models.Model):
	_name = "model.details"
	_description = "Model Details"

	name = fields.Char('Name')
	company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)


class CertificationDetails(models.Model):
	_name = "certificate.details"
	_description = "Certificate Details"

	name = fields.Char('Certification Name')
	certificate_id = fields.Many2one('hr.job', 'Certification Id')
	certificate_fm = fields.Many2one('job.description', 'Certificate Ref')
	certificate_jd = fields.Many2one('job.description', 'Certificate Ref')
	company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)


class SkillDetails(models.Model):
	_name = "skill.details"
	_description = "Skill Details"

	name = fields.Char('Skill Name')
	active = fields.Boolean("Active", default=True)
	skill_id = fields.Many2one('hr.job', 'Skill Id')
	skill_match = fields.Many2one('match.run.history', 'Skill Match')
	skill_fm = fields.Many2one('job.description', 'Skill Ref')
	skill_jd = fields.Many2one('job.description', 'Skill Ref')
	color = fields.Integer('Color Index')
	company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)


class QualificationDetails(models.Model):
	_name = "qualification.details"
	_description = "Qualification Details"

	name = fields.Char('Qualification')
	qualification_id = fields.Many2one('hr.job', 'Qualification Id')
	qualification_fm = fields.Many2one('job.description', 'Qualification Ref')
	qualification_jd = fields.Many2one('job.description', 'Qualification Ref')
	company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)


class RecruitmentStage(models.Model):
	_inherit = "hr.recruitment.stage"

	code = fields.Char('Code', readonly=True)
