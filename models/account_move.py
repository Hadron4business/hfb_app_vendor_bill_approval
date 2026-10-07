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
"""	@version	20.0.1.0.1
	@owner  Hadron for Business
	@author Hadron for Business sp. z o.o.
	@date   2026.10.07

	Vendor Bill Approval - bills
	Approval status of vendor bills and refunds, request of the tasks required
	by the rules (automatically when a bill is created, or with a button), ad-
	hoc approvers, and the posting block while an approval is missing or
	rejected.
"""
from odoo import _, api, fields, models
from odoo.exceptions import UserError

BILL_TYPES = ('in_invoice', 'in_refund')


class AccountMove(models.Model):
    _inherit = 'account.move'

    bill_approval_ids = fields.One2many('bill.approval', 'move_id', string="Approvals", copy=False)
    bill_approval_state = fields.Selection(
        [('none', "Not Required"), ('pending', "Waiting for Approval"),
         ('approved', "Approved"), ('rejected', "Rejected")],
        string="Approval", compute='_compute_bill_approval_state', store=True)
    bill_approval_enabled = fields.Boolean(related='company_id.bill_approval')
    bill_approval_can_decide = fields.Boolean(compute='_compute_bill_approval_can_decide')

    @api.depends('bill_approval_ids.state')
    def _compute_bill_approval_state(self):
        for move in self:
            states = set(move.bill_approval_ids.mapped('state'))
            if not states:
                move.bill_approval_state = 'none'
            elif 'rejected' in states:
                move.bill_approval_state = 'rejected'
            elif 'pending' in states:
                move.bill_approval_state = 'pending'
            else:
                move.bill_approval_state = 'approved'

    @api.depends_context('uid')
    @api.depends('bill_approval_ids.state', 'bill_approval_ids.user_id')
    def _compute_bill_approval_can_decide(self):
        for move in self:
            move.bill_approval_can_decide = any(t.can_decide for t in move.bill_approval_ids)

    def _bill_approval_matching_rules(self):
        self.ensure_one()
        rules = self.env['bill.approval.rule'].sudo().search([('company_id', '=', self.company_id.id)])
        return rules.filtered(lambda r: r._matches(self))

    def action_bill_approval_request(self):
        """Create the tasks required by the rules; waiting again for rejected ones."""
        Task = self.env['bill.approval'].sudo()
        for move in self.filtered(lambda m: m.move_type in BILL_TYPES and m.state == 'draft'):
            rejected = move.bill_approval_ids.filtered(lambda t: t.state == 'rejected')
            for task in rejected:
                task.write({'state': 'pending', 'rejection_reason': False, 'decided_by_id': False, 'decided_on': False})
            rejected._schedule_activity()
            existing = {(t.rule_id.id, t.user_id.id) for t in move.bill_approval_ids}
            vals = []
            for rule in move._bill_approval_matching_rules():
                for user in rule.user_ids:
                    if (rule.id, user.id) not in existing and user not in move.bill_approval_ids.user_id:
                        existing.add((rule.id, user.id))
                        vals.append({
                            'move_id': move.id, 'rule_id': rule.id, 'rule_name': rule.name, 'user_id': user.id,
                            'description_required': rule.description_required,
                        })
            if vals:
                Task.create(vals)
            if vals or rejected:
                move.message_post(body=_("Approval requested from: %s.", ", ".join(
                    move.bill_approval_ids.filtered(lambda t: t.state == 'pending').user_id.mapped('name'))))
        return True

    def action_bill_approval_add(self):
        self.ensure_one()
        return {
            'name': _("Ask for Approval"),
            'type': 'ir.actions.act_window',
            'res_model': 'bill.approval.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_move_id': self.id, 'default_mode': 'add'},
        }

    def _bill_approval_my_tasks(self):
        return self.bill_approval_ids.filtered('can_decide')

    def action_bill_approval_decide(self):
        tasks = self._bill_approval_my_tasks()
        if not tasks:
            raise UserError(_("You have no waiting approval on this bill."))
        return tasks[:1].with_context(bill_approval_mode=self.env.context.get('bill_approval_mode', 'approve')).action_open_decision()

    def _bill_approval_notify_if_done(self):
        for move in self.sudo():
            if move.bill_approval_state != 'approved':
                continue
            partners = move.user_id.partner_id | move.bill_approval_ids.requester_id.partner_id
            move.message_post(body=_("All approvals done - the bill can be posted."), partner_ids=partners.ids)

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves.filtered(
            lambda m: m.move_type in BILL_TYPES and m.company_id.bill_approval and m.company_id.bill_approval_auto
        ).action_bill_approval_request()
        return moves

    def action_post(self):
        for move in self.filtered(lambda m: m.move_type in BILL_TYPES and m.company_id.bill_approval):
            move._bill_approval_check_postable()
        return super().action_post()

    def _bill_approval_check_postable(self):
        self.ensure_one()
        if not self.bill_approval_ids and self._bill_approval_matching_rules():
            raise UserError(_("Bill %s needs approval: click Request Approval first.", self.display_name))
        rejected = self.bill_approval_ids.filtered(lambda t: t.state == 'rejected')
        if rejected:
            raise UserError(_("Bill %(bill)s was rejected by %(users)s: %(reasons)s", bill=self.display_name,
                              users=", ".join(rejected.user_id.mapped('name')),
                              reasons="; ".join(filter(None, rejected.mapped('rejection_reason')))))
        pending = self.bill_approval_ids.filtered(lambda t: t.state == 'pending')
        if pending:
            raise UserError(_("Bill %(bill)s is still waiting for the approval of: %(users)s",
                              bill=self.display_name, users=", ".join(pending.user_id.mapped('name'))))

#EoF
