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
"""	@version	18.0.1.0.0
	@owner  Hadron for Business
	@author Hadron for Business sp. z o.o.
	@date   2026.10.07

	Vendor Bill Approval - decisions
	One dialog for approving (with the expense description), rejecting (with a
	reason), handing over to another approver and asking an additional person
	for approval.
"""
from odoo import _, fields, models
from odoo.exceptions import UserError


class BillApprovalWizard(models.TransientModel):
    _name = 'bill.approval.wizard'
    _description = "Vendor Bill Approval Decision"

    mode = fields.Selection(
        [('approve', "Approve"), ('reject', "Reject"), ('handover', "Hand Over"), ('add', "Ask for Approval")],
        required=True, default='approve')
    task_ids = fields.Many2many('bill.approval')
    move_id = fields.Many2one('account.move')
    description = fields.Html(string="Expense Description")
    description_required = fields.Boolean(compute='_compute_description_required')
    reason = fields.Text(string="Reason")
    user_id = fields.Many2one('res.users', string="New Approver", domain="[('share', '=', False)]")
    note = fields.Text(string="Note")

    def _compute_description_required(self):
        for wizard in self:
            wizard.description_required = any(wizard.task_ids.mapped('description_required'))

    def action_confirm(self):
        self.ensure_one()
        if self.mode == 'approve':
            self.task_ids._approve(self.description)
        elif self.mode == 'reject':
            if not self.reason:
                raise UserError(_("Please give the reason of the rejection."))
            self.task_ids._reject(self.reason)
        elif self.mode == 'handover':
            if not self.user_id:
                raise UserError(_("Please choose the new approver."))
            self.task_ids._hand_over(self.user_id, self.note)
        elif self.mode == 'add':
            if not self.user_id:
                raise UserError(_("Please choose the approver."))
            self.env['bill.approval'].sudo().create({
                'move_id': self.move_id.id, 'user_id': self.user_id.id,
                'rule_name': self.note or _("Requested manually"), 'description_required': True,
            })
            self.env.ref('hfb_app_vendor_bill_approval.group_bill_approver').sudo().write({'users': [(4, self.user_id.id)]})
            self.move_id.message_post(body=_("Approval requested from %s.", self.user_id.name))
        return {'type': 'ir.actions.act_window_close'}

#EoF
