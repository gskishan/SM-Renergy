import frappe

def set_itc_claim_period(doc, method=None):
    if not doc.posting_date:
        return

    month_names = {
        1: "January", 2: "February", 3: "March", 4: "April",
        5: "May", 6: "June", 7: "July", 8: "August",
        9: "September", 10: "October", 11: "November", 12: "December"
    }

    gstin = frappe.db.get_value("Company", doc.company, "gstin")
    
    # posting_date may be a string "YYYY-MM-DD" or a date object
    if isinstance(doc.posting_date, str):
        parts = doc.posting_date.split("-")
        month = int(parts[1])
        year = int(parts[0])
    else:
        month = int(doc.posting_date.strftime("%m"))
        year = int(doc.posting_date.strftime("%Y"))

    for _ in range(12):
        period = str(month).zfill(2) + str(year)
        log_name = f"GSTR3B-{period}-{gstin}"
        filing_status = frappe.db.get_value("GST Return Log", log_name, "filing_status")

        if filing_status != "Filed":
            doc.itc_claim_period = period
            return

        if month == 12:
            month = 1
            year += 1
        else:
            month += 1
