# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo import fields, models, api, _
from odoo.addons.iap import jsonrpc, InsufficientCreditError
from odoo.exceptions import UserError
import datetime
from datetime import timezone, datetime

class ResCompany(models.Model):
	_inherit = "res.company"

	def _compute_balance_credits(self):
		for rec in self:
			balance_credits = 0
			if not rec.customer_id and not rec.client_id and not rec.api_key_id:
				# rec.balance_credits = 0
				rec.write({
					'balance_credits': 0,
					'used_credits': 0,
					'total_credits': 0,
				})
				return True
			customer_id = ''
			if rec.customer_id:
				customer_id = rec.customer_id
			elif rec.partner_id.customer_id:
				customer_id = rec.partner_id.customer_id
			customer_host = rec.customer_host
			subscription_date = ''
			if rec.is_trial:
				subscription_date = rec.trial_start_date if rec.trial_start_date else None
			elif rec.is_subscribed:
				subscription_date = rec.subscription_start if rec.subscription_start else None
			if not subscription_date:
				# rec.balance_credits = 0
				rec.write({
					'balance_credits': 0,
					'used_credits': 0,
					'total_credits': 0,
				})
				return True
			try:
				subscription_date = datetime.strftime(subscription_date, "%Y-%m-%d %H:%M:%S") if subscription_date else None
				call = 'get'
				params = {
					'call': 'get',
					'customer_id': customer_id,
					'uid_id': False,
					'subscription_date': subscription_date,
					'trial': True if rec.is_trial else False
				}
				endpoint = self.env.user.company_id.customer_host
				url = endpoint + "/credit_balance_check"
				api, status = jsonrpc(url, params=params)
				if api in [200, 201]:
					if status:
						balance_credits = int(status['total_credits']) - int(status['total_used_credits'])
				# rec.balance_credits = balance_credits
				rec.write({
					'balance_credits': balance_credits,
					'used_credits': int(status['total_used_credits']),
					'total_credits': int(status['total_credits']),
				})
			except Exception as e:
				raise UserError(e)
			return True

	def _fetch_registry_service_url(self):
		try:
			registry_url = self.env.ref("solvithub_registry.hiredrate_registry_service_url_parameter")
			if not registry_url or not registry_url.value:
				registry_url = "https://odoo14.hiredrate.com"
			else:
				registry_url = registry_url.value
		except:
			registry_url = "https://odoo14.hiredrate.com"
		return registry_url

	api_key_id = fields.Char('Api Key')
	client_id = fields.Char('Client Id')
	customer_id = fields.Char('Customer Id')
	customer_host = fields.Char('Customer Host', default=_fetch_registry_service_url)
	is_trial = fields.Boolean('Is trial')
	is_subscribed = fields.Boolean("Is Subscribed", readonly=True)
	trial_start_date = fields.Datetime('Trial Start Date')
	trial_end_date = fields.Datetime('Trial End Date')
	subscription_start = fields.Datetime('Subscription Start')
	subscription_end = fields.Datetime('Subscription End')
	# trial_period = fields.Integer('Trial Period(in days)', default=0)
	balance_credits = fields.Integer("Balance Credits", compute='_compute_balance_credits')
	used_credits = fields.Integer('Used Credits', compute='_compute_balance_credits')
	total_credits = fields.Integer('Total Credits', compute='_compute_balance_credits')
	credits = fields.Integer('Credits')
	plan_name = fields.Char("Plan Name")
	service_name = fields.Char("Service Name")
	plan_id = fields.Many2one('subscription.plans', 'Plan')
	addon_ids = fields.Many2many('subscription.addons', string='Addons')
	user_limit = fields.Integer('Maximum Users')

	@api.model
	def create(self, vals):
		service_name = self.env.context.get('service_name', False)
		res = super(ResCompany, self).create(vals)
		res.partner_id.write({'company_id': res.id})
		if res:
			name = ''
			if res.name:
				name = res.name.split()
			f_name = name[0]
			name.pop(0)
			l_name = " ".join(name)
			location = ''
			if res.street:
				location += res.street
			if res.street2:
				location += ','
				location += res.street2
			if res.city:
				location += ','
				location += res.city
			if res.state_id:
				location += ','
				location += res.state_id.name
			if res.country_id:
				location += ','
				location += res.country_id.name
			email = ''
			if res.email:
				email = res.email
			else:
				email = res.name
			contact_no = ''
			if res.phone:
				contact_no = res.phone
			state_id = ''
			if res.state_id:
				state_id = res.state_id.name
			country_id = ''
			if res.country_id:
				country_id = res.country_id.name
			currency_id = ''
			if res.currency_id:
				currency_id = res.currency_id.name
			company_id = {
				'name': res.name,
				'street': res.street,
				'street2': res.street2,
				'city': res.city,
				'state_id': state_id,
				'zip': res.zip,
				'country_id': country_id,
				'website': res.website,
				'phone': res.phone,
				'email': res.email,
				'currency_id': currency_id
			}

			data = {
				"sso_name": res.name,
				"legal_name": res.name,
				"location": location,
				"email": email,
				"contact_no": contact_no,
				"contact_name": res.name,
				'service_name': 'chargebee' if self.env.context.get('subscription', False) else 'iap',
				'credit_applicable': self.env.context.get('credit_applicable') if self.env.context.get('credit_applicable', False) else False,
				'service_cust_id': self.env.context.get('customer_id') if self.env.context.get('customer_id', False) else False,
				'service_subscription_id': self.env.context.get('subscription_id') if self.env.context.get('subscription_id', False) else False,
				'payment_id': self.env.context.get('payment_id') if self.env.context.get('payment_id', False) else False,
				'credits_purchased': self.env.context.get('credits_purchased') if self.env.context.get('credits_purchased', False) else 0,
				'credits_cost': self.env.context.get('credits_cost') if self.env.context.get('credits_cost', False) else 0,
				'txn_status': self.env.context.get('txn_status') if self.env.context.get('txn_status', False) else False,
				'is_trial': self.env.context.get('trial') if self.env.context.get('trial', False) else False,
				'billing_cycle': self.env.context.get('billing_cycle') if self.env.context.get('billing_cycle', False) else False,
				'billing_date_start': self.env.context.get('billing_date_start') if self.env.context.get('billing_date_start', False) else False,
				'trial_end_date': self.env.context.get('trial_end_date') if self.env.context.get('trial_end_date', False) else False,
				'block_type': self.env.context.get('block_type') if self.env.context.get('block_type', False) else False,
				'limiter': self.env.context.get('limiter') if self.env.context.get('limiter', False) else False,
				'subscription_response': self.env.context.get('subscription_response') if self.env.context.get('subscription_response', False) else False,
			}
			params = {
				'data': data,
				'call': 'post',
				'company_id': company_id,
				'subscription': False,
			}
			endpoint = self.env.user.company_id.customer_host
			if not endpoint:
				raise UserError("Please configure company host in SolvitHub Settings!")
			url = endpoint + "/customer_creation_credit"
			api, status = jsonrpc(url, params=params)
			if api in [200, 201]:
				if status and status.get('customer_information', False) and 'cust_id' in status['customer_information'].keys():
					key_vals = {
						"name": status['customer_information']['sso_name'],
						"note": ""
					}
					endpoint = self.env.user.company_id.customer_host
					url = endpoint + "/customer_key_creation"
					params = {
						'data': key_vals,
						'call': 'post',
						'customer_id': status['customer_information']['cust_id']
					}
					response_api, response_status = jsonrpc(url, params=params)
					if response_api in [200, 201]:
						if response_status and response_status.get('customer_key_information', False):
							res.api_key_id = response_status['customer_key_information']['key']
							res.client_id = response_status['customer_key_information']['client_id']
							res.customer_id = response_status['customer_key_information']['sso_customer_id']
		return res

	def fetch_customer_details(self, cust_id):
		if self.env.user.company_id.customer_host:
			params = {
				# 'account_token': token.account_token,
				'call': 'get',
				'customer_id': cust_id
			}
			endpoint = self.env.user.company_id.customer_host
			if not endpoint:
				raise UserError("Please configure company host in SolvitHub Settings!")
			url = endpoint + "/customer_fetch_details"
			api, status = jsonrpc(url, params=params)
			return status
