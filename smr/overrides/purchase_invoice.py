import frappe
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice

class CustomPurchaseInvoice(PurchaseInvoice):
    def set_itc_claim_period(self):
        month_names = {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        }

        gstin = frappe.db.get_value("Company", self.company, "gstin")
        month = int(self.posting_date.strftime("%m"))
        year = int(self.posting_date.strftime("%Y"))

        for _ in range(12):
            period = str(month).zfill(2) + str(year)
            log_name = f"GSTR3B-{period}-{gstin}"
            filing_status = frappe.db.get_value("GST Return Log", log_name, "filing_status")

            if filing_status != "Filed":
                self.itc_claim_period = period
                return

            if month == 12:
                month = 1
                year += 1
            else:
                month += 1
