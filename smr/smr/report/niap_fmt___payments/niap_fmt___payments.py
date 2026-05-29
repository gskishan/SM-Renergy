import frappe

def execute(filters=None):

    columns = [
        {"label": "PYMT_PROD_TYPE_CODE", "fieldname": "pymt_prod_type_code", "fieldtype": "Data", "width": 180},
        {"label": "PYMT_MODE", "fieldname": "mode_of_payment", "fieldtype": "Data", "width": 120},
        {"label": "DEBIT_ACC_NO", "fieldname": "bank_account_no", "fieldtype": "Data", "width": 180},
        {"label": "BNF_NAME", "fieldname": "account_name", "fieldtype": "Data", "width": 180},
        {"label": "BENE_ACC_NO", "fieldname": "bene_account_no", "fieldtype": "Data", "width": 180},
        {"label": "BENE_IFSC", "fieldname": "branch_code", "fieldtype": "Data", "width": 180},
        {"label": "AMOUNT", "fieldname": "paid_amount", "fieldtype": "Currency", "width": 120},
        {"label": "PYMT_DATE", "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": "REMARK", "fieldname": "remarks", "fieldtype": "Data", "width": 200},
    ]

    conditions = []
    values = {}

    if filters.get("from_date") and filters.get("to_date"):
        conditions.append("pe.posting_date BETWEEN %(from_date)s AND %(to_date)s")
        values["from_date"] = filters.get("from_date")
        values["to_date"] = filters.get("to_date")

    if filters.get("bank_account"):
        conditions.append("pe.bank_account = %(bank_account)s")
        values["bank_account"] = filters.get("bank_account")

    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = " AND " + where_clause

    data = frappe.db.sql(f"""
        SELECT
            'PAB_VENDOR' AS pymt_prod_type_code,
            pe.mode_of_payment,
            ba.bank_account_no,
            baa.account_name,
            baa.bank_account_no AS bene_account_no,
            baa.branch_code,
            pe.paid_amount,
            pe.posting_date,
            pe.remarks
        FROM `tabPayment Entry` pe
        LEFT JOIN `tabBank Account` ba
            ON ba.name = pe.bank_account
        LEFT JOIN `tabBank Account` baa
            ON baa.name = pe.party_bank_account
        WHERE pe.docstatus = 1
        {where_clause}
        ORDER BY pe.posting_date
    """, values, as_dict=1)

    return columns, data
