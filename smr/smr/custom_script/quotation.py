import frappe

def before_save(doc, method):
    if doc.custom_site_survey:
        frappe.db.set_value(
            "Site Survey",
            doc.custom_site_survey,
            "quotation",
            doc.name
        )
    if doc.custom_designing:
        frappe.db.set_value(
            "Designing",
            doc.custom_designing,
            "quotation",
            doc.name
        )

def before_cancel(doc, method):
    doc.flags.ignore_links = True

    if doc.custom_site_survey:
        frappe.db.set_value(
            "Site Survey",
            doc.custom_site_survey,
            "quotation",
            ""
        )
    if doc.custom_designing:
        frappe.db.set_value(
            "Designing",
            doc.custom_designing,
            "quotation",
            ""
        )

def on_trash(doc, method):
    if doc.custom_site_survey:
        frappe.db.set_value(
            "Site Survey",
            doc.custom_site_survey,
            "quotation",
            ""
        )
    if doc.custom_designing:
        frappe.db.set_value(
            "Designing",
            doc.custom_designing,
            "quotation",
            ""
        )