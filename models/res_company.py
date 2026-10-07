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

	Vendor Bill Approval - company settings
	Company switch for vendor bill approval and whether approval is requested
	automatically for new bills.
"""
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    bill_approval = fields.Boolean(string="Vendor Bill Approval")
    bill_approval_auto = fields.Boolean(string="Request Approval when a Bill is Created", default=True)

#EoF
