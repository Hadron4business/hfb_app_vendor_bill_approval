# -*- coding: utf-8 -*-
# vim: tabstop=4 softtabstop=0 shiftwidth=4 smarttab expandtab fileformat=unix
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
{
    'name': "Vendor Bill Approval",
    'summary': "Route vendor bills to the right people by amount and vendor: they describe the expense, approve or "
               "reject it, and only approved bills can be posted",
    'description': """
Vendor Bill Approval
====================

A vendor bill arrives and the accountant does not know what it is for, who
ordered it or whether the service was delivered. The answer is usually
collected by e-mail or on paper.

With this app, approval rules (amount from, vendors) decide who has to
approve a bill. Each approver gets a task with the PDF of the bill next to
it - no access to Accounting is needed - describes the expense, and approves
or rejects it with a reason. Tasks can be handed over to a colleague. The
bill shows the status of every approval, cannot be posted until all
approvers have approved it, and the accountant is notified when everything
is done.
""",
    'version': "20.0.1.0.0",
    'author': "Hadron for Business sp. z o.o.",
    'website': "http://hadronforbusiness.com",
    'license': "OPL-1",
    'category': "Accounting/Accounting",
    'depends': [
        'account',
    ],
    'data': [
        'security/bill_approval_security.xml',
        'security/ir.access.csv',
        'data/mail_activity_type_data.xml',
        'wizard/bill_approval_wizard_views.xml',
        'views/bill_approval_rule_views.xml',
        'views/bill_approval_views.xml',
        'views/account_move_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': [
        'static/description/banner_screenshot.png',
    ],
    'installable': True,
    'application': False,
}
