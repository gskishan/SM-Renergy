frappe.query_reports["NIAP FMT - PAYMENTS"] = {
    "filters": [
        {
            "fieldname": "bank_account",
            "label": "Debit Account",
            "fieldtype": "Link",
            "options": "Bank Account",
            "filters": {
                "is_company_account": 1
            }
        },
        {
            "fieldname": "from_date",
            "label": "From Date",
            "fieldtype": "Date",
            "default": frappe.datetime.month_start(),
            "reqd": 0
        },
        {
            "fieldname": "to_date",
            "label": "To Date",
            "fieldtype": "Date",
            "default": frappe.datetime.month_end(),
            "reqd": 0
        }
    ]
};
