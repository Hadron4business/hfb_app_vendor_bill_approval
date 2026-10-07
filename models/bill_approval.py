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
"""	@version	19.0.1.0.0
	@owner  Hadron for Business
	@author Hadron for Business sp. z o.o.
	@date   2026.10.07

	Vendor Bill Approval - approval tasks
	Approval task of one approver for one bill: expense description, approve /
	reject with a reason / hand over to a colleague, with the bill data and its
	PDF readable by approvers who have no access to Accounting.
"""
from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import is_html_empty

ACTIVITY_TYPE = 'hfb_app_vendor_bill_approval.mail_activity_type_bill_approval'


class BillApproval(models.Model):
    _name = 'bill.approval'
    _description = "Vendor Bill Approval Task"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _rec_name = 'move_id'

    move_id = fields.Many2one('account.move', string="Bill", required=True, index=True, ondelete='cascade')
    company_id = fields.Many2one(related='move_id.company_id', store=True)
    rule_id = fields.Many2one('bill.approval.rule', string="Rule", ondelete='set null')
    rule_name = fields.Char(string="Approval For", help="Rule that created the task, or the reason of a manual request.")
    user_id = fields.Many2one('res.users', string="Approver", required=True, tracking=True, index=True)
    requester_id = fields.Many2one('res.users', string="Requested By", default=lambda self: self.env.user)
    state = fields.Selection(
        [('pending', "Waiting"), ('approved', "Approved"), ('rejected', "Rejected")],
        default='pending', required=True, tracking=True)
    description = fields.Html(string="Expense Description", help="What the expense is for, filled in by the approver.")
    description_required = fields.Boolean(default=True)
    rejection_reason = fields.Text(string="Rejection Reason")
    decided_by_id = fields.Many2one('res.users', string="Decided By", readonly=True)
    decided_on = fields.Datetime(string="Decided On", readonly=True)
    handover_note = fields.Text(string="Hand-over History", readonly=True)

    # Information of the bill for approvers without access to Accounting (related fields are read as superuser).
    partner_id = fields.Many2one(related='move_id.partner_id', string="Vendor")
    bill_name = fields.Char(related='move_id.name', string="Bill Number")
    bill_ref = fields.Char(related='move_id.ref', string="Vendor Reference")
    bill_date = fields.Date(related='move_id.invoice_date', string="Bill Date")
    bill_due_date = fields.Date(related='move_id.invoice_date_due', string="Due Date")
    currency_id = fields.Many2one(related='move_id.currency_id')
    amount_untaxed = fields.Monetary(related='move_id.amount_untaxed', string="Untaxed Amount")
    amount_total = fields.Monetary(related='move_id.amount_total', string="Total")
    bill_lines_html = fields.Html(string="Bill Lines", compute='_compute_bill_info', sanitize=False)
    bill_pdf = fields.Binary(string="Bill Document", compute='_compute_bill_info')
    bill_pdf_name = fields.Char(compute='_compute_bill_info')
    can_decide = fields.Boolean(compute='_compute_can_decide')

    @api.depends('move_id')
    def _compute_bill_info(self):
        for task in self:
            move = task.move_id.sudo()
            rows = "".join(
                Markup("<tr><td>%s</td><td class='text-end'>%s</td><td class='text-end'>%s</td></tr>") % (
                    line.name or line.product_id.display_name or '',
                    line.quantity,
                    move.currency_id.format(line.price_subtotal),
                ) for line in move.invoice_line_ids.filtered(lambda l: l.display_type == 'product'))
            task.bill_lines_html = Markup(
                "<table class='table table-sm'><thead><tr><th>%s</th><th class='text-end'>%s</th>"
                "<th class='text-end'>%s</th></tr></thead><tbody>%s</tbody></table>"
            ) % (_("Description"), _("Quantity"), _("Untaxed"), Markup(rows)) if rows else False
            attachment = move.message_main_attachment_id
            is_pdf = attachment and attachment.mimetype == 'application/pdf'
            task.bill_pdf = attachment.datas if is_pdf else False
            task.bill_pdf_name = attachment.name if is_pdf else False

    @api.depends_context('uid')
    @api.depends('state', 'user_id')
    def _compute_can_decide(self):
        for task in self:
            task.can_decide = task.state == 'pending' and task.user_id == self.env.user

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        tasks.filtered(lambda t: t.state == 'pending')._schedule_activity()
        return tasks

    def _schedule_activity(self):
        for task in self:
            task.activity_unlink([ACTIVITY_TYPE])
            task.activity_schedule(
                ACTIVITY_TYPE, user_id=task.user_id.id,
                note=_("%(vendor)s - %(amount)s", vendor=task.partner_id.display_name or '',
                       amount=task.currency_id.format(task.amount_total)))

    def _check_can_decide(self):
        for task in self:
            if not task.can_decide:
                raise UserError(_("Only %(user)s can decide on this approval of bill %(bill)s.",
                                  user=task.user_id.name, bill=task.move_id.display_name))

    def _approve(self, description=None):
        self._check_can_decide()
        for task in self:
            text = description if description is not None else task.description
            if task.description_required and is_html_empty(text):
                raise UserError(_("Please describe the expense before approving bill %s.", task.move_id.display_name))
            task.sudo().write({
                'state': 'approved', 'description': text,
                'decided_by_id': self.env.uid, 'decided_on': fields.Datetime.now(),
            })
            task.sudo().activity_feedback([ACTIVITY_TYPE])
            task.move_id.sudo().message_post(body=Markup("%s<br/>%s") % (
                _("Approved by %s.", self.env.user.name), text or ''))
        self.move_id._bill_approval_notify_if_done()

    def _reject(self, reason):
        self._check_can_decide()
        for task in self:
            task.sudo().write({
                'state': 'rejected', 'rejection_reason': reason,
                'decided_by_id': self.env.uid, 'decided_on': fields.Datetime.now(),
            })
            task.sudo().activity_unlink([ACTIVITY_TYPE])
            move = task.move_id.sudo()
            partners = task.requester_id.partner_id | move.user_id.partner_id
            move.message_post(
                body=_("Rejected by %(user)s. Reason: %(reason)s", user=self.env.user.name, reason=reason),
                partner_ids=partners.ids)

    def _hand_over(self, user, note):
        for task in self:
            if task.state != 'pending':
                raise UserError(_("Only waiting approvals can be handed over."))
            if not (task.user_id == self.env.user or self.env.user.has_group('account.group_account_manager')):
                raise UserError(_("Only the approver or a billing administrator can hand over this approval."))
            line = _("%(date)s: %(old)s -> %(new)s (%(by)s) %(note)s", date=fields.Date.today(),
                     old=task.user_id.name, new=user.name, by=self.env.user.name, note=note or '')
            task.sudo().write({
                'user_id': user.id,
                'handover_note': "\n".join(filter(None, [task.handover_note, line])),
            })
            self.env.ref('hfb_app_vendor_bill_approval.group_bill_approver').sudo().write({'user_ids': [(4, user.id)]})
            task.sudo()._schedule_activity()
            task.move_id.sudo().message_post(body=_("Approval handed over: %s", line))

    def action_open_decision(self):
        self.ensure_one()
        mode = self.env.context.get('bill_approval_mode', 'approve')
        return {
            'name': {'approve': _("Approve Bill"), 'reject': _("Reject Bill"), 'handover': _("Hand Over")}[mode],
            'type': 'ir.actions.act_window',
            'res_model': 'bill.approval.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_task_ids': self.ids, 'default_mode': mode, 'default_description': self.description},
        }

#EoF
