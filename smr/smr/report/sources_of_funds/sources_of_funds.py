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


def get_account_balance(account, from_date, to_date):
    """Get credit - debit balance (liability perspective)."""
    result = frappe.db.sql("""
        SELECT SUM(gl.credit) - SUM(gl.debit) AS balance
        FROM `tabGL Entry` gl
        WHERE gl.account = %s
            AND gl.is_cancelled = 0
            AND gl.posting_date BETWEEN %s AND %s
    """, (account, from_date, to_date))
    return float(result[0][0] or 0) if result else 0


def get_group_balance(parent_account, from_date, to_date):
    """Get total balance for all leaf accounts under a parent."""
    accounts = frappe.db.sql("""
        SELECT name, is_group
        FROM `tabAccount`
        WHERE parent_account = %s AND disabled = 0
    """, (parent_account,), as_dict=True)

    total = 0
    for acc in accounts:
        if acc.is_group:
            total += get_group_balance(acc.name, from_date, to_date)
        else:
            total += get_account_balance(acc.name, from_date, to_date)
    return total


def get_children_with_balance(parent_account, from_date, to_date):
    """Get all direct/indirect leaf accounts with non-zero balance."""
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


def row(particulars, sanctioned=None, outstanding=None, available=None, bold=0):
    return {
        "particulars": particulars,
        "sanctioned": sanctioned,
        "outstanding": outstanding,
        "available": available,
        "bold": bold,
    }


def spacer():
    return row("")


def get_data(from_date, to_date):
    data = []

    # ── SECTION 1: CREDIT FACILITY ────────────────────────────────────────
    # Sanctioned limits — update these when bank revises limits
    SANCTIONED_LIMITS = {
        "DOD":   40000000.00,   # 4,00,00,000
        "TL":    78500000.00,   # 7,85,00,000
        "BG/LC": 20000000.00,   # 2,00,00,000
    }

    # Outstanding balances from GL
    dod_outstanding = get_group_balance(
        "Bank Overdraft Account - SRPL", from_date, to_date)

    tl_outstanding = get_group_balance(
        "Secured Loans - SRPL", from_date, to_date)

    # BG/LC — add account name here once created in COA
    bglc_outstanding = 0.0

    total_sanctioned = sum(SANCTIONED_LIMITS.values())
    total_outstanding_cf = dod_outstanding + tl_outstanding + bglc_outstanding
    total_available = (
        max(0, SANCTIONED_LIMITS["DOD"] - dod_outstanding) +
        max(0, SANCTIONED_LIMITS["BG/LC"] - bglc_outstanding)
    )

    data.append(row("Credit Facility", bold=1))
    data.append(row(
        "\u00a0\u00a0\u00a0\u00a0",
        sanctioned="Sanctioned Limits",
        outstanding="Outstanding",
        available="Available",
        bold=1,
    ))

    # DOD row
    dod_available = max(0, SANCTIONED_LIMITS["DOD"] - dod_outstanding)
    data.append(row(
        "\u00a0\u00a0\u00a0\u00a0DOD",
        sanctioned=SANCTIONED_LIMITS["DOD"],
        outstanding=dod_outstanding if dod_outstanding else None,
        available=dod_available if dod_available else None,
    ))

    # TL row (no available — fully drawn)
    data.append(row(
        "\u00a0\u00a0\u00a0\u00a0TL",
        sanctioned=SANCTIONED_LIMITS["TL"],
        outstanding=tl_outstanding if tl_outstanding else None,
        available=None,
    ))

    # BG/LC row
    bglc_available = max(0, SANCTIONED_LIMITS["BG/LC"] - bglc_outstanding)
    data.append(row(
        "\u00a0\u00a0\u00a0\u00a0BG/LC",
        sanctioned=SANCTIONED_LIMITS["BG/LC"],
        outstanding=bglc_outstanding if bglc_outstanding else None,
        available=bglc_available if bglc_available else None,
    ))

    # Credit Facility Total
    data.append(row(
        "Total Credit Facility",
        sanctioned=total_sanctioned,
        outstanding=total_outstanding_cf,
        available=total_available,
        bold=1,
    ))

    data.append(spacer())

    # ── SECTION 2: SOURCES OUTSTANDING ───────────────────────────────────
    data.append(row("Sources Outstanding", bold=1))

    grand_sources_total = 0

    # Director's Capital → Shareholders Funds - SRPL
    directors_capital = get_group_balance(
        "Shareholders Funds - SRPL", from_date, to_date)
    if directors_capital != 0:
        data.append(row(
            "\u00a0\u00a0\u00a0\u00a0Director's Capital",
            outstanding=directors_capital,
        ))
        grand_sources_total += directors_capital

    # ICICI Bank limits → Secured Loans - SRPL
    icici_loans = get_group_balance(
        "Secured Loans - SRPL", from_date, to_date)
    if icici_loans != 0:
        data.append(row(
            "\u00a0\u00a0\u00a0\u00a0ICICI Bank Limits",
            outstanding=icici_loans,
        ))
        grand_sources_total += icici_loans

    # Unsecured Loans → Unsecured Loans - SRPL (children)
    unsecured = get_children_with_balance(
        "Unsecured Loans - SRPL", from_date, to_date)
    for acc in unsecured:
        data.append(row(
            "\u00a0\u00a0\u00a0\u00a0" + acc["account_name"],
            outstanding=acc["balance"],
        ))
        grand_sources_total += acc["balance"]

    # Sundry Creditors → Accounts Payable - SRPL
    creditors = get_group_balance(
        "Accounts Payable - SRPL", from_date, to_date)
    if creditors != 0:
        data.append(row(
            "\u00a0\u00a0\u00a0\u00a0Sundry Creditors",
            outstanding=creditors,
        ))
        grand_sources_total += creditors

    data.append(spacer())

    # Grand Total Sources
    data.append(row(
        "Total Funds from Sources",
        outstanding=grand_sources_total,
        bold=1,
    ))

    return data
