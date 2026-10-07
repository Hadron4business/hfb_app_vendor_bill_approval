# -*- coding: utf-8 -*-
#################################################################################
#
# Odoo, Open Source Management Solution
# Copyright (C) 2017-2026 Hadron for Business sp. z o.o. (http://hadronforbusiness.com)
#
# This program is proprietary software, licensed under the Odoo Proprietary
# License v1.0 (OPL-1). Its use is governed by the Odoo Apps terms available
# at https://www.odoo.com/documentation/user/legal/licenses.html and the
# license agreement accepted at purchase / installation.
#
# It is forbidden to publish, distribute, sublicense, or sell copies of the
# Software or modified copies of the Software.
#
# The above copyright notice and this permission notice must be included in
# all copies or substantial portions of the Software.
#
#################################################################################
"""	@version	19.0.1.0.2
	@owner  Hadron for Business
	@author Hadron for Business sp. z o.o.
	@date   2026.10.07

	Vendor Bill Approval - rules
	Approval rule: bills from an amount (taxes included, company currency) and
	optionally of chosen vendors need the approval of the listed users;
	approvers are added to the approver group automatically.
"""
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class BillApprovalRule(models.Model):
    _name = 'bill.approval.rule'
    _description = "Vendor Bill Approval Rule"
    _order = 'sequence, id'

    name = fields.Char(string="Rule", required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string="Company", required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id')
    min_amount = fields.Monetary(
        string="Bills From", default=0.0,
        help="Bills of this total (taxes included, in the company currency) or more match the rule.")
    partner_ids = fields.Many2many(
        'res.partner', string="Vendors", help="Only bills of these vendors. Empty: all vendors.")
    user_ids = fields.Many2many(
        'res.users', string="Approvers", required=True, domain="[('share', '=', False)]",
        help="Each of these users gets an approval task.")
    description_required = fields.Boolean(
        string="Description Required", default=True,
        help="Approvers must describe the expense before approving.")

    @api.constrains('min_amount')
    def _check_min_amount(self):
        for rule in self:
            if rule.min_amount < 0:
                raise ValidationError(_("The amount of rule %s cannot be negative.", rule.name))

    @api.model_create_multi
    def create(self, vals_list):
        rules = super().create(vals_list)
        rules._grant_approver_group()
        return rules

    def write(self, vals):
        result = super().write(vals)
        if 'user_ids' in vals:
            self._grant_approver_group()
        return result

    def _grant_approver_group(self):
        """Approvers need the approver group to see their tasks and the menu."""
        group = self.env.ref('hfb_app_vendor_bill_approval.group_bill_approver')
        users = self.user_ids - group.sudo().user_ids
        if users:
            group.sudo().write({'user_ids': [(4, user.id) for user in users]})

    def _matches(self, move):
        self.ensure_one()
        amount = abs(move.amount_total_signed)
        if self.company_id.currency_id.compare_amounts(amount, self.min_amount) < 0:
            return False
        return not self.partner_ids or move.commercial_partner_id in self.partner_ids.commercial_partner_id

#EoF
