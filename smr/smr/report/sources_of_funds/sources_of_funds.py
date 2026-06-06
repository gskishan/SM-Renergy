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
    """Recursively sum all leaf account balances up to as_on_date."""
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


def get_children_with_balance(parent_account, as_on_date, only_positive=True):
    """Get child accounts with non-zero balances."""
    accounts = frappe.db.sql("""
        SELECT name, account_name, is_group
        FROM `tabAccount`
        WHERE parent_account = %s AND disabled = 0
        ORDER BY account_name
    """, (parent_account,), as_dict=True)

    results = []
    for acc in accounts:
        if acc.is_group:
            children = get_children_with_balance(acc.name, as_on_date, only_positive)
            group_total = sum(c["balance"] for c in children)
            if (only_positive and group_total > 0) or (not only_positive and group_total != 0):
                results.append({
                    "account_name": acc.account_name,
                    "balance": group_total,
                    "is_group": True,
                    "children": children,
                })
        else:
            balance = get_account_balance(acc.name, as_on_date)
            if (only_positive and balance > 0) or (not only_positive and balance != 0):
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


def get_data(as_on_date):
    data = []
    indent = "\u00a0" * 4

    # ── SECTION 1: CREDIT FACILITY ────────────────────────────────────────
    data.append(make_row("Credit Facility", bold=1))

    # Sanctioned limits — posted via JE by accounts team
    dod_sanctioned  = get_account_balance("DOD Sanctioned Limit - SRPL",   as_on_date)
    tl_sanctioned   = get_account_balance("TL Sanctioned Limit - SRPL",    as_on_date)
    bglc_sanctioned = get_account_balance("BG/LC Sanctioned Limit - SRPL", as_on_date)

    # Outstanding — cumulative balance from beginning
    dod_outstanding  = get_group_balance("Bank Overdraft Account - SRPL", as_on_date)
    tl_outstanding   = get_group_balance("Secured Loans - SRPL",          as_on_date)
    bglc_outstanding = 0.0

    # Available = Sanctioned - Outstanding
    dod_available  = max(0, dod_sanctioned - dod_outstanding)
    tl_available   = max(0, tl_sanctioned - tl_outstanding)
    bglc_available = max(0, bglc_sanctioned - bglc_outstanding)

    total_sanctioned  = dod_sanctioned + tl_sanctioned + bglc_sanctioned
    total_outstanding = dod_outstanding + tl_outstanding + bglc_outstanding
    total_available   = dod_available + tl_available + bglc_available

    data.append(make_row(
        indent + "DOD",
        sanctioned=dod_sanctioned or None,
        outstanding=dod_outstanding if dod_outstanding > 0 else None,
        available=dod_available or None,
    ))
    data.append(make_row(
        indent + "TL",
        sanctioned=tl_sanctioned or None,
        outstanding=tl_outstanding if tl_outstanding > 0 else None,
        available=tl_available or None,
    ))
    data.append(make_row(
        indent + "BG/LC",
        sanctioned=bglc_sanctioned or None,
        outstanding=bglc_outstanding if bglc_outstanding > 0 else None,
        available=bglc_available or None,
    ))
    data.append(make_row(
        "Total",
        sanctioned=total_sanctioned or None,
        outstanding=total_outstanding if total_outstanding > 0 else None,
        available=total_available or None,
        bold=1,
    ))

    data.append(spacer())

    # ── SECTION 2: SOURCES OUTSTANDING ───────────────────────────────────
    data.append(make_row("Sources Outstanding", bold=1))

    grand_sources_total = 0

    # Director's Capital
    directors_capital = get_group_balance("Shareholders Funds - SRPL", as_on_date)
    if directors_capital > 0:
        data.append(make_row(indent + "Director's Capital", outstanding=directors_capital))
        grand_sources_total += directors_capital

    # ICICI Bank Limits — Secured Loans
    icici_loans = get_group_balance("Secured Loans - SRPL", as_on_date)
    if icici_loans > 0:
        data.append(make_row(indent + "ICICI Bank Limits", outstanding=icici_loans))
        grand_sources_total += icici_loans

    # Unsecured Loans — only positive balances
    unsecured_accounts = get_children_with_balance(
        "Unsecured Loans - SRPL", as_on_date, only_positive=True)
    for acc in unsecured_accounts:
        data.append(make_row(indent + acc["account_name"], outstanding=acc["balance"]))
        grand_sources_total += acc["balance"]

    # Directors USL
    directors_usl = get_group_balance("Directors - USL - SRPL", as_on_date)
    if directors_usl > 0:
        data.append(make_row(indent + "Directors USL", outstanding=directors_usl))
        grand_sources_total += directors_usl

    # Creditors for Goods
    creditors_goods = get_account_balance("Creditors for Goods - SRPL", as_on_date)
    if creditors_goods > 0:
        data.append(make_row(indent + "Creditors for Goods", outstanding=creditors_goods))
        grand_sources_total += creditors_goods

    # Creditors for Services
    creditors_services = get_account_balance("Creditors for Services - SRPL", as_on_date)
    if creditors_services > 0:
        data.append(make_row(indent + "Creditors for Services", outstanding=creditors_services))
        grand_sources_total += creditors_services

    data.append(spacer())

    data.append(make_row(
        "Total Funds from Sources",
        outstanding=grand_sources_total,
        bold=1,
    ))

    return data
