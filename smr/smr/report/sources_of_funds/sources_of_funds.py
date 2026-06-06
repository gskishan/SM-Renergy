import frappe
from frappe import _


def execute(filters=None):
    filters = filters or {}
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")

    columns = get_columns()
    data = get_data(from_date, to_date)
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


def get_account_balance(account, from_date, to_date, perspective="liability"):
    """
    Get balance for an account.
    perspective='liability' → credit - debit (positive = owe money)
    perspective='asset'    → debit - credit (positive = we have money)
    """
    result = frappe.db.sql("""
        SELECT
            SUM(gl.credit) - SUM(gl.debit) AS balance
        FROM `tabGL Entry` gl
        WHERE gl.account = %s
            AND gl.is_cancelled = 0
            AND gl.posting_date BETWEEN %s AND %s
    """, (account, from_date, to_date))
    balance = float(result[0][0] or 0) if result else 0
    return balance if perspective == "liability" else -balance


def get_group_balance(parent_account, from_date, to_date, perspective="liability"):
    """Recursively sum all leaf account balances under a parent."""
    accounts = frappe.db.sql("""
        SELECT name, is_group
        FROM `tabAccount`
        WHERE parent_account = %s AND disabled = 0
    """, (parent_account,), as_dict=True)

    total = 0
    for acc in accounts:
        if acc.is_group:
            total += get_group_balance(acc.name, from_date, to_date, perspective)
        else:
            total += get_account_balance(acc.name, from_date, to_date, perspective)
    return total


def get_children_with_balance(parent_account, from_date, to_date):
    """Get all child accounts with non-zero balances."""
    accounts = frappe.db.sql("""
        SELECT name, account_name, is_group
        FROM `tabAccount`
        WHERE parent_account = %s AND disabled = 0
        ORDER BY account_name
    """, (parent_account,), as_dict=True)

    results = []
    for acc in accounts:
        if acc.is_group:
            children = get_children_with_balance(acc.name, from_date, to_date)
            group_total = sum(c["balance"] for c in children)
            if group_total != 0:
                results.append({
                    "account_name": acc.account_name,
                    "balance": group_total,
                    "is_group": True,
                    "children": children,
                })
        else:
            balance = get_account_balance(acc.name, from_date, to_date)
            if balance != 0:
                results.append({
                    "account_name": acc.account_name,
                    "balance": balance,
                    "is_group": False,
                })
    return results


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


def get_data(from_date, to_date):
    data = []
    indent = "\u00a0" * 4

    # ── SECTION 1: CREDIT FACILITY ────────────────────────────────────────
    data.append(make_row("Credit Facility", bold=1))

    # Sanctioned limits from GL accounts
    dod_sanctioned  = get_account_balance("DOD Sanctioned Limit - SRPL",   from_date, to_date)
    tl_sanctioned   = get_account_balance("TL Sanctioned Limit - SRPL",    from_date, to_date)
    bglc_sanctioned = get_account_balance("BG/LC Sanctioned Limit - SRPL", from_date, to_date)

    # Outstanding from GL accounts
    dod_outstanding  = get_group_balance("Bank Overdraft Account - SRPL", from_date, to_date)
    tl_outstanding   = get_group_balance("Secured Loans - SRPL",          from_date, to_date)
    bglc_outstanding = 0.0  # Update to correct account once created in COA

    # Available = Sanctioned - Outstanding
    dod_available  = max(0, dod_sanctioned - dod_outstanding)
    tl_available   = max(0, tl_sanctioned - tl_outstanding)
    bglc_available = max(0, bglc_sanctioned - bglc_outstanding)

    total_sanctioned   = dod_sanctioned + tl_sanctioned + bglc_sanctioned
    total_outstanding  = dod_outstanding + tl_outstanding + bglc_outstanding
    total_available    = dod_available + tl_available + bglc_available

    # DOD row
    data.append(make_row(
        indent + "DOD",
        sanctioned=dod_sanctioned or None,
        outstanding=dod_outstanding or None,
        available=dod_available or None,
    ))

    # TL row
    data.append(make_row(
        indent + "TL",
        sanctioned=tl_sanctioned or None,
        outstanding=tl_outstanding or None,
        available=tl_available or None,
    ))

    # BG/LC row
    data.append(make_row(
        indent + "BG/LC",
        sanctioned=bglc_sanctioned or None,
        outstanding=bglc_outstanding or None,
        available=bglc_available or None,
    ))

    # Credit Facility Total
    data.append(make_row(
        "Total",
        sanctioned=total_sanctioned or None,
        outstanding=total_outstanding or None,
        available=total_available or None,
        bold=1,
    ))

    data.append(spacer())

    # ── SECTION 2: SOURCES OUTSTANDING ───────────────────────────────────
    data.append(make_row("Sources Outstanding", bold=1))

    grand_sources_total = 0

    # Director's Capital → Shareholders Funds - SRPL
    directors_capital = get_group_balance("Shareholders Funds - SRPL", from_date, to_date)
    if directors_capital:
        data.append(make_row(indent + "Director's Capital", outstanding=directors_capital))
        grand_sources_total += directors_capital

    # ICICI Bank Limits → Secured Loans - SRPL
    icici_loans = get_group_balance("Secured Loans - SRPL", from_date, to_date)
    if icici_loans:
        data.append(make_row(indent + "ICICI Bank Limits", outstanding=icici_loans))
        grand_sources_total += icici_loans

    # Unsecured Loans → each child account dynamically
    unsecured_accounts = get_children_with_balance("Unsecured Loans - SRPL", from_date, to_date)
    for acc in unsecured_accounts:
        data.append(make_row(indent + acc["account_name"], outstanding=acc["balance"]))
        grand_sources_total += acc["balance"]

    # Directors USL
    directors_usl = get_group_balance("Directors - USL - SRPL", from_date, to_date)
    if directors_usl:
        data.append(make_row(indent + "Directors USL", outstanding=directors_usl))
        grand_sources_total += directors_usl

    # Sundry Creditors → Accounts Payable - SRPL
    creditors = get_group_balance("Accounts Payable - SRPL", from_date, to_date)
    if creditors:
        data.append(make_row(indent + "Sundry Creditors", outstanding=creditors))
        grand_sources_total += creditors

    data.append(spacer())

    # Grand Total
    data.append(make_row(
        "Total Funds from Sources",
        outstanding=grand_sources_total,
        bold=1,
    ))

    return data
