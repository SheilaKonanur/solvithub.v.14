# -*- coding: utf-8 -*-

from odoo import models, fields, api
import csv
import base64

class SkillWizard(models.TransientModel):
	"""Skill Wizard"""

	_name = "skill.wizard"
	_description = "Skill Wizard"

	name = fields.Char('Name')
	skill_id = fields.Many2many('skill.details', string='Skills')
	job_position_id = fields.Many2one('hr.job', 'Job Position')

	# @api.multi
	def skill_fetch_action(self):
		if self.skill_id:
			self.job_position_id.write({
				'skills': [[6, 0, self.skill_id.ids]]
			})

	def import_attach(self):
		with open ('/opt/finaloutput.csv', mode='r') as app_file:
			app_reader = csv.DictReader(app_file)
			for line in app_reader:
				attachment = self.env['ir.attachment'].create({
					'name': line['name'],
					'res_model': line['res_model'],
					'res_id': line['res_id'],
					'datas': line['mimetype'],
					'mimetype': line['res_name']
				})

class ActualSkillDetails(models.TransientModel):
    _name = "actual.skill.details"

    skill_id = fields.Many2one("skill.details", "Skill Id")
    synonym = fields.Boolean( string='Synonym')
    ignore = fields.Boolean(string='Ignore')
    synonym_name = fields.Char(string='Synonym Skill')
    applicant_ref = fields.Many2one("hr.applicant", "Applicant Ref")
    job_position_ref =fields.Many2one("hr.job", "Job Ref")

class NormalisedWizard(models.TransientModel):
	"""Skill Wizard for application """
	
	_name = "normalised.wizard"

	# name = fields.Char('Name')
	# skill_id = fields.Many2many('skill.details', string='Skills')
	normalised_skills = fields.One2many('actual.skill.details','applicant_ref', string='Normalised Skills')

class NormalisedSkillwizard(models.TransientModel):
	"""Skill Wizard for job position"""
	
	_name = "normalised.skillwizard"

	# name = fields.Char('Name')
	# skill_id = fields.Many2many('skill.details', string='Skills')
	normalised_skill = fields.One2many('actual.skill.details','job_position_ref', string='Normalised Skill')
	

class SynonymMap(models.TransientModel):
	_name = "synonym.map"

	primary_id = fields.Integer("Primary Id")
	secondary_id = fields.Integer("Secondary Id")
