import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    as_on_date = filters.get("as_on_date")

    columns = get_columns()
    data = get_data(as_on_date)
    return columns, data


def get_columns():
    return [
        {
            "label": _("Particulars"),
            "fieldname": "particulars",
            "fieldtype": "Data",
            "width": 280,
        },
        {
            "label": _("Sanctioned Limits"),
            "fieldname": "sanctioned",
            "fieldtype": "Currency",
            "width": 180,
        },
        {
            "label": _("Outstanding"),
            "fieldname": "outstanding",
            "fieldtype": "Currency",
            "width": 180,
        },
        {
            "label": _("Available"),
            "fieldname": "available",
            "fieldtype": "Currency",
            "width": 180,
        },
    ]


def get_account_balance(account, as_on_date):
    """Get cumulative credit - debit balance up to as_on_date."""
    result = frappe.db.sql("""
        SELECT SUM(gl.credit) - SUM(gl.debit) AS balance
        FROM `tabGL Entry` gl
        WHERE gl.account = %s
            AND gl.is_cancelled = 0
            AND gl.posting_date <= %s
    """, (account, as_on_date))
    return float(result[0][0] or 0) if result else 0


def get_group_balance(parent_account, as_on_date):
    """Recursively sum all leaf account balances under a parent."""
    accounts = frappe.db.sql("""
        SELECT name, is_group
        FROM `tabAccount`
        WHERE parent_account = %s AND disabled = 0
    """, (parent_account,), as_dict=True)

    total = 0
    for acc in accounts:
        if acc.is_group:
            total += get_group_balance(acc.name, as_on_date)
        else:
            total += get_account_balance(acc.name, as_on_date)
    return total


def get_all_children(parent_account, as_on_date):
    """Get all leaf accounts under a parent with their balances."""
    accounts = frappe.db.sql("""
        SELECT name, account_name, is_group
        FROM `tabAccount`
        WHERE parent_account = %s AND disabled = 0
        ORDER BY account_name
    """, (parent_account,), as_dict=True)

    results = []
    for acc in accounts:
        if acc.is_group:
            children = get_all_children(acc.name, as_on_date)
            group_total = sum(c["balance"] for c in children)
            if group_total != 0:
                results.append({
                    "account_name": acc.account_name,
                    "balance": group_total,
                    "is_group": True,
                    "children": children,
                })
        else:
            balance = get_account_balance(acc.name, as_on_date)
            if balance != 0:
                results.append({
                    "account_name": acc.account_name,
                    "account": acc.name,
                    "balance": balance,
                    "is_group": False,
                })
    return results


def get_sanctioned_limits():
    """Fetch sanctioned limits from Credit Facility doctype."""
    facilities = frappe.get_all(
        "Credit Facility",
        fields=["loan_account", "facility_type", "sanctioned_limit", "lender_name"],
    )
    # Map by loan_account for easy lookup
    return {f.loan_account: f for f in facilities}


def make_row(particulars, sanctioned=None, outstanding=None, available=None, bold=0):
    return {
        "particulars": particulars,
        "sanctioned": sanctioned,
        "outstanding": outstanding,
        "available": available,
        "bold": bold,
    }


def spacer():
    return make_row("")


def get_data(as_on_date):
    data = []
    indent = "\u00a0" * 4

    # Fetch all sanctioned limits from Credit Facility doctype
    sanctioned_limits = get_sanctioned_limits()

    grand_total_sanctioned = 0
    grand_total_outstanding = 0
    grand_total_available = 0

    # ── SECTION 1: CREDIT FACILITY (DOD) ─────────────────────────────────
    data.append(make_row("Credit Facility", bold=1))

    # DOD
    dod_accounts = frappe.db.sql("""
        SELECT name, account_name FROM `tabAccount`
        WHERE parent_account = 'Bank Overdraft Account - SRPL'
            AND disabled = 0
    """, as_dict=True)

    dod_sanctioned_total = 0
    dod_outstanding_total = 0

    # If no children, check the account itself
    if not dod_accounts:
        bal = get_account_balance("Bank Overdraft Account - SRPL", as_on_date)
        cf = sanctioned_limits.get("Bank Overdraft Account - SRPL")
        sanctioned = cf.sanctioned_limit if cf else 0
        available = max(0, sanctioned - bal) if sanctioned else None
        data.append(make_row(
            indent + "DOD",
            sanctioned=sanctioned or None,
            outstanding=bal or None,
            available=available,
        ))
        dod_sanctioned_total = sanctioned
        dod_outstanding_total = bal
    else:
        for acc in dod_accounts:
            bal = get_account_balance(acc.name, as_on_date)
            cf = sanctioned_limits.get(acc.name)
            sanctioned = cf.sanctioned_limit if cf else 0
            available = max(0, sanctioned - bal) if sanctioned else None
            data.append(make_row(
                indent + acc.account_name,
                sanctioned=sanctioned or None,
                outstanding=bal or None,
                available=available,
            ))
            dod_sanctioned_total += sanctioned
            dod_outstanding_total += bal

    # ── SECTION 2: SECURED LOANS (TL) ─────────────────────────────────────
    data.append(make_row(indent + "Term Loans (TL)", bold=1))

    secured_accounts = get_all_children("Secured Loans - SRPL", as_on_date)
    tl_sanctioned_total = 0
    tl_outstanding_total = 0

    for acc in secured_accounts:
        cf = sanctioned_limits.get(acc["account"])
        sanctioned = cf.sanctioned_limit if cf else 0
        bal = acc["balance"]
        available = max(0, sanctioned - bal) if sanctioned else None
        data.append(make_row(
            indent * 2 + acc["account_name"],
            sanctioned=sanctioned or None,
            outstanding=bal or None,
            available=available,
        ))
        tl_sanctioned_total += sanctioned
        tl_outstanding_total += bal

    # ── SECTION 3: BG/LC ──────────────────────────────────────────────────
    # Add BG/LC account here once created in COA
    bglc_sanctioned_total = 0
    bglc_outstanding_total = 0

    # Credit Facility Total
    total_sanctioned = dod_sanctioned_total + tl_sanctioned_total + bglc_sanctioned_total
    total_outstanding = dod_outstanding_total + tl_outstanding_total + bglc_outstanding_total
    total_available = max(0, total_sanctioned - total_outstanding) if total_sanctioned else None

    data.append(make_row(
        "Total Credit Facility",
        sanctioned=total_sanctioned or None,
        outstanding=total_outstanding or None,
        available=total_available,
        bold=1,
    ))

    grand_total_sanctioned += total_sanctioned
    grand_total_outstanding += total_outstanding
    grand_total_available += total_available or 0

    data.append(spacer())

    # ── SECTION 4: UNSECURED LOANS ────────────────────────────────────────
    data.append(make_row("Unsecured Loans", bold=1))

    unsecured_accounts = get_all_children("Unsecured Loans - SRPL", as_on_date)
    usl_sanctioned_total = 0
    usl_outstanding_total = 0

    for acc in unsecured_accounts:
        cf = sanctioned_limits.get(acc["account"])
        sanctioned = cf.sanctioned_limit if cf else 0
        bal = acc["balance"]
        available = max(0, sanctioned - bal) if sanctioned else None
        data.append(make_row(
            indent + acc["account_name"],
            sanctioned=sanctioned or None,
            outstanding=bal or None,
            available=available,
        ))
        usl_sanctioned_total += sanctioned
        usl_outstanding_total += bal

    # Directors USL
    directors_usl_accounts = get_all_children("Directors - USL - SRPL", as_on_date)
    for acc in directors_usl_accounts:
        cf = sanctioned_limits.get(acc["account"])
        sanctioned = cf.sanctioned_limit if cf else 0
        bal = acc["balance"]
        available = max(0, sanctioned - bal) if sanctioned else None
        data.append(make_row(
            indent + acc["account_name"],
            sanctioned=sanctioned or None,
            outstanding=bal or None,
            available=available,
        ))
        usl_sanctioned_total += sanctioned
        usl_outstanding_total += bal

    data.append(make_row(
        "Total Unsecured Loans",
        sanctioned=usl_sanctioned_total or None,
        outstanding=usl_outstanding_total or None,
        available=max(0, usl_sanctioned_total - usl_outstanding_total) if usl_sanctioned_total else None,
        bold=1,
    ))

    grand_total_sanctioned += usl_sanctioned_total
    grand_total_outstanding += usl_outstanding_total

    data.append(spacer())

    # ── SECTION 5: OTHER SOURCES ──────────────────────────────────────────
    data.append(make_row("Other Sources", bold=1))

    other_total = 0

    # Director's Capital
    directors_capital = get_group_balance("Shareholders Funds - SRPL", as_on_date)
    if directors_capital != 0:
        data.append(make_row(indent + "Director's Capital", outstanding=directors_capital))
        other_total += directors_capital

    # Creditors for Goods
    creditors_goods = get_account_balance("Creditors for Goods - SRPL", as_on_date)
    if creditors_goods > 0:
        data.append(make_row(indent + "Creditors for Goods", outstanding=creditors_goods))
        other_total += creditors_goods

    # Creditors for Services
    creditors_services = get_account_balance("Creditors for Services - SRPL", as_on_date)
    if creditors_services > 0:
        data.append(make_row(indent + "Creditors for Services", outstanding=creditors_services))
        other_total += creditors_services

    grand_total_outstanding += other_total

    data.append(spacer())

    # ── GRAND TOTAL ───────────────────────────────────────────────────────
    data.append(make_row(
        "Total Funds from Sources",
        sanctioned=grand_total_sanctioned or None,
        outstanding=grand_total_outstanding or None,
        available=grand_total_available or None,
        bold=1,
    ))

    return data
