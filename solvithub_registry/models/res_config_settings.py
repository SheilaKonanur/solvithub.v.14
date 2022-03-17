# -*- coding: utf-8 -*-
from odoo import fields, models, api
import requests
from odoo.exceptions import UserError
from odoo.addons.iap import jsonrpc, InsufficientCreditError
import json
import logging
_logger = logging.getLogger(__name__)

class ResConfigSettings(models.TransientModel):
	_inherit = 'res.config.settings'

	api_key_id = fields.Char('Api Key', related='company_id.api_key_id', readonly=False)
	client_id = fields.Char('Client Id', related='company_id.client_id', readonly=False)
	customer_id = fields.Char('Customer Id', related='company_id.customer_id', readonly=False)
	customer_host = fields.Char('Host', related='company_id.customer_host', readonly=False)
	cmplify_company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id.id)
	user_limit = fields.Integer('Maximum Users', related='company_id.user_limit', readonly=False)

	# @api.multi
	def link_existing_company(self):
		_logger.error("----------link_existing_company--------------")
		if not self.customer_id and self.cmplify_company_id:
			if self.company_id and not self.company_id.email:
				raise UserError("Please enter email in Company!")
			# data = {}
			location = ''
			if self.cmplify_company_id.street:
				location += self.cmplify_company_id.street
			if self.cmplify_company_id.street2:
				location += ','
				location += self.cmplify_company_id.street2
			if self.cmplify_company_id.city:
				location += ','
				location += self.cmplify_company_id.city
			if self.cmplify_company_id.state_id:
				location += ','
				location += self.cmplify_company_id.state_id.name
			if self.cmplify_company_id.country_id:
				location += ','
				location += self.cmplify_company_id.country_id.name
			data = {
				"sso_name": self.cmplify_company_id.name,
				"legal_name": self.cmplify_company_id.name,
				"location": location,
				"email": self.cmplify_company_id.email,
				"contact_name": self.cmplify_company_id.name,
				"contact_no": self.cmplify_company_id.phone,
				"service_name": "iap",
				"credit_applicable": False,
				"service_cust_id": self.env.context.get("customer_id") if self.env.context.get("customer_id", False) else False,
				"payment_id": self.env.context.get("payment_id") if self.env.context.get("payment_id",False) else False,
				"credits_purchased": self.env.context.get("credits_purchased") if self.env.context.get("credits_purchased", False) else False,
				"credits_cost": self.env.context.get("credits_cost") if self.env.context.get("credits_cost", False) else 0,
				"txn_status": self.env.context.get("txn_status") if self.env.context.get("txn_status", False) else False,
				"is_trial": self.env.context.get("trial") if self.env.context.get("trial", False) else False,
				"is_limit": False,
			}
			endpoint = self.env.user.company_id.customer_host
			if not endpoint:
				raise UserError("Please configure company host in SolvitHub Settings!")
			sso_url = endpoint + "/customer_creation_credit"
			if data:
				params = {
					'data': data,
					'call': 'post',
					'currency': self.env.user.company_id.currency_id.name,
					'subscription': False
				}
				_logger.error(sso_url)
				headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
				response, status_code = jsonrpc(sso_url, params=params)
				if response in [200, 201]:
					if status_code and status_code.get('customer_information', False) and 'cust_id' in status_code['customer_information'].keys():
						update_url = endpoint + '/customer_key_creation'
						key_vals = {
							"name": status_code['customer_information']['sso_name'],
							"note": ""
						}
						if key_vals:
							param_data = {
							'data': key_vals,
							'customer_id': status_code['customer_information']['cust_id'],
							'call': 'post'
							}
							api_response, api_status_code = jsonrpc(update_url, params=param_data)
							if api_response in [200, 201]:
								if api_status_code and api_status_code.get('customer_key_information', False) and 'client_id' in api_status_code['customer_key_information'] and 'key' in api_status_code['customer_key_information']:
									self.client_id = api_status_code['customer_key_information']['client_id']
									self.api_key_id = api_status_code['customer_key_information']['key']
									self.customer_id = api_status_code['customer_key_information']['sso_customer_id']
		else:
			raise UserError("Customer Id is already entered!")

	# @api.multi
	def reset_api_key(self):
		if self.customer_id:
			update_url = sso_url + str(self.customer_id) + "/keys"
			key_vals = {
				"name": self.cmplify_company_id.name,
				"note": ""
			}
			if key_vals:
				key_vals = json.dumps(key_vals)
				headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
				api_response = requests.post(update_url, key_vals, headers=headers)
				if api_response.status_code in [200, 201]:
					api_key = api_response.json()
					if api_key and api_key.get('customer_key_information', False) and 'client_id' in api_key[
						'customer_key_information'] and 'key' in api_key['customer_key_information']:
						self.client_id = api_key['customer_key_information']['client_id']
						self.api_key_id = api_key['customer_key_information']['key']
						self.customer_id = api_key['customer_key_information']['sso_customer_id']

	def recharge_credits(self):
		customer_id = self.env.user.company_id.customer_id
		if customer_id:
			return {'name': 'Recharge',
					'res_model': 'ir.actions.act_url',
					'type': 'ir.actions.act_url',
					'target': 'self',
					'url': "/recharge?cust_id=" + customer_id
					}
		else:
			raise UserError("Please configure company host in SolvitHub Settings!")