# Copyright (c) 2026, SMR and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class SiteSurvey(Document):
    def before_save(self):
        if self.lead_from:
            frappe.db.set_value("Lead", self.lead_from, "custom_site_survey", self.name)

    def before_cancel(self):
        self.flags.ignore_links = True

        if self.designing:
            frappe.db.set_value(
                "Designing",
                self.designing,
                "site_survey",
                ""
            )

        if self.lead_from:
            frappe.db.set_value("Lead", self.lead_from, "custom_site_survey", "")

        if self.quotation:
            frappe.db.set_value(
                "Quotation",
                self.quotation,
                "custom_site_survey",
                ""
            )

    def on_trash(self):
        if self.designing:
            frappe.db.set_value(
                "Designing",
                self.designing,
                "site_survey",
                ""
            )

        if self.lead_from:
            frappe.db.set_value("Lead", self.lead_from, "custom_site_survey", "")

        if self.quotation:
            frappe.db.set_value(
                "Quotation",
                self.quotation,
                "custom_site_survey",
                ""
            )