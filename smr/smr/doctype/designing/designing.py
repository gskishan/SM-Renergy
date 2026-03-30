# Copyright (c) 2026, SMR and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class Designing(Document):
    def before_save(self):
        # Existing logic
        if self.site_survey:
            frappe.db.set_value(
                "Site Survey",
                self.site_survey,
                "designing",
                self.name
            )
        
        total_qty = 0
        total_amount = 0

        for row in self.bom_item: 
            row.qty = row.qty or 0
            row.rate = row.rate or 0

            row.amount = row.qty * row.rate

            total_qty += row.qty
            total_amount += row.amount

        self.total_qty = total_qty
        self.amount = total_amount

    def before_cancel(self):
        self.flags.ignore_links = True

        if self.site_survey:
            frappe.db.set_value(
                "Site Survey",
                self.site_survey,
                "designing",
                ""
            )

        if self.quotation:
            frappe.db.set_value(
                "Quotation",
                self.quotation,
                "custom_designing",
                ""
            )

    def on_trash(self):
        if self.quotation:
            frappe.db.set_value(
                "Quotation",
                self.quotation,
                "custom_designing",
                ""
            )

        if self.site_survey:
            frappe.db.set_value(
                "Site Survey",
                self.site_survey,
                "designing",
                ""
            )