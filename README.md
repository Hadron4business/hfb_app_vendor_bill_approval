# Vendor Bill Approval

Approval rules route vendor bills to approvers, who describe and approve or reject them; posting is blocked until everything is approved.

## What it does

- **Rules, not manual routing** - Rules by amount (taxes included) and vendor decide who approves: e.g. every bill to the office manager, IT vendors to the IT manager, from 10,000 also to the CFO.
- **No Accounting access needed** - Approvers work in their own Bill Approvals menu: vendor, amounts, lines and the PDF of the bill side by side. Department heads do not need access to Accounting.
- **Expense description** - Approvers write what the expense is for (required per rule). The description is kept on the bill and in its chatter.
- **Approve, reject, hand over** - Reject with a reason (the accountant is notified), or hand the approval over to a colleague during holidays - with history.
- **Posting blocked** - A bill cannot be posted while an approval is waiting or rejected. The accountant gets a message when everything is approved.
- **Status everywhere** - Approval status on the bill (ribbon, Approvals tab) and as a column in the list of bills.

## How to use it

1. Go to Invoicing > Configuration > Settings, section Vendor Bills, enable Vendor Bill Approval (and optionally automatic requests for new bills).
2. Create your rules in Invoicing > Configuration > Bill Approval Rules: amount from, vendors (empty = all), approvers, description required.
3. Create or import a vendor bill. Approval is requested automatically (or with Request Approval). The approvers get an activity.
4. The approver opens Bill Approvals > To Approve, checks the PDF, describes the expense and clicks Approve - or Reject / Hand Over.
5. When all approvals are done, the accountant is notified and posts the bill. On the bill, the Approvals tab shows who approved what and when.

## Good to know

- Approvers named in a rule automatically get the "Vendor Bill Approver" access; they only see their own approvals.
- Use "Ask Someone Else" on the Approvals tab to add an approver to one bill only.
- A rejected bill can be sent for approval again with Request Approval after it has been corrected.
- Applies to vendor bills and vendor refunds; customer invoices are not affected.

## Technical

- Depends only on `account`.
- Models: `bill.approval.rule`, `bill.approval` (task, with the bill data readable by approvers), wizard `bill.approval.wizard`.
- Posting block in `account.move.action_post()`.

## Status

Odoo 20 build. Tested on the Odoo.sh test instances (automated RPC tests and manual tests, 2026-10-07). Missing before publication: icon, banner.
