# Copyright (c) 2026, SMR and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Designing(Document):
    def before_save(self):
        if self.site_survey:
            frappe.db.set_value(
                "Site Survey",
                self.site_survey,
                "designing",
                self.name
            )

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