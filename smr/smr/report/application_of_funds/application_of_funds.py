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
            "width": 380,
        },
        {
            "label": _("Breakup"),
            "fieldname": "breakup",
            "fieldtype": "Currency",
            "width": 180,
        },
        {
            "label": _("Total"),
            "fieldname": "total",
            "fieldtype": "Currency",
            "width": 180,
        },
    ]


def get_account_balance(account, from_date, to_date, root_type="Asset"):
    """Get net balance for a specific account."""
    result = frappe.db.sql("""
        SELECT SUM(gl.debit) - SUM(gl.credit) AS balance
        FROM `tabGL Entry` gl
        WHERE gl.account = %s
            AND gl.is_cancelled = 0
            AND gl.posting_date BETWEEN %s AND %s
    """, (account, from_date, to_date))
    balance = result[0][0] if result else 0
    return float(balance or 0)


def get_all_children(parent_account, from_date, to_date):
    """Recursively get all accounts under a parent with balances."""
    accounts = frappe.db.sql("""
        SELECT name, account_name, is_group
        FROM `tabAccount`
        WHERE parent_account = %s
            AND disabled = 0
        ORDER BY account_name
    """, (parent_account,), as_dict=True)

    results = []
    for acc in accounts:
        if acc.is_group:
            children = get_all_children(acc.name, from_date, to_date)
            group_total = sum(c["_balance"] for c in children)
            if group_total != 0:
                results.append({
                    "name": acc.name,
                    "account_name": acc.account_name,
                    "is_group": True,
                    "_balance": group_total,
                    "children": children,
                })
        else:
            balance = get_account_balance(acc.name, from_date, to_date)
            if balance != 0:
                results.append({
                    "name": acc.name,
                    "account_name": acc.account_name,
                    "is_group": False,
                    "_balance": balance,
                })
    return results


def build_rows(accounts, indent=0, data=None):
    """Build report rows — leaf accounts in Breakup, group totals in Total."""
    if data is None:
        data = []

    for acc in accounts:
        spaces = "\u00a0" * (indent * 4)

        if acc["is_group"]:
            children = acc.get("children", [])
            group_total = acc["_balance"]
            has_children_groups = any(c["is_group"] for c in children)

            # Group header row
            data.append({
                "particulars": spaces + acc["account_name"],
                "breakup": None,
                "total": None,
                "bold": 1,
                "indent": indent,
            })

            # Recurse into children
            build_rows(children, indent + 1, data)

            # Group subtotal row — show in Total if top level, Breakup if nested
            if indent == 0:
                data.append({
                    "particulars": spaces + "Total " + acc["account_name"],
                    "breakup": None,
                    "total": group_total,
                    "bold": 1,
                    "indent": indent,
                })
            else:
                data.append({
                    "particulars": spaces + "Subtotal - " + acc["account_name"],
                    "breakup": group_total,
                    "total": None,
                    "bold": 1,
                    "indent": indent,
                })
        else:
            # Leaf account — always in Breakup column
            data.append({
                "particulars": spaces + acc["account_name"],
                "breakup": acc["_balance"],
                "total": None,
                "bold": 0,
                "indent": indent,
            })

    return data


def section_header(label):
    return {
        "particulars": label,
        "breakup": None,
        "total": None,
        "bold": 1,
        "indent": 0,
    }


def section_total(label, amount):
    return {
        "particulars": label,
        "breakup": None,
        "total": amount,
        "bold": 1,
        "indent": 0,
    }


def spacer():
    return {"particulars": "", "breakup": None, "total": None}


def get_data(from_date, to_date):
    data = []
    grand_total = 0

    # ── SECTION 1: FIXED ASSETS ──────────────────────────────────────────
    data.append(section_header("Fixed Assets"))

    fixed_assets = get_all_children("Fixed Assets - SRPL", from_date, to_date)
    fixed_total = sum(a["_balance"] for a in fixed_assets)
    build_rows(fixed_assets, indent=1, data=data)

    data.append(section_total("Total Fixed Assets", fixed_total))
    data.append(spacer())
    grand_total += fixed_total

    # ── SECTION 2: CURRENT ASSETS ─────────────────────────────────────────
    data.append(section_header("Current Assets"))

    current_assets = get_all_children("Current Assets - SRPL", from_date, to_date)
    current_total = sum(a["_balance"] for a in current_assets)
    build_rows(current_assets, indent=1, data=data)

    data.append(section_total("Total Current Assets", current_total))
    data.append(spacer())
    grand_total += current_total

    # ── SECTION 3: EXPENDITURE FOR FUTURE REALISATION ────────────────────
    # This maps to Temporary Accounts or Investments in COA
    exp_accounts = []

    # Check Temporary Accounts
    temp = get_all_children("Temporary Accounts - SRPL", from_date, to_date)
    if temp:
        exp_accounts.extend(temp)

    # Check Investments
    investments = get_all_children("Investments - SRPL", from_date, to_date)
    if investments:
        exp_accounts.extend(investments)

    exp_total = sum(a["_balance"] for a in exp_accounts)

    if exp_total != 0:
        data.append(section_header("Expenditure for Future Realisation"))
        build_rows(exp_accounts, indent=1, data=data)
        data.append(section_total("Total Expenditure for Future Realisation", exp_total))
        data.append(spacer())
        grand_total += exp_total

    # ── GRAND TOTAL ───────────────────────────────────────────────────────
    data.append({
        "particulars": "Grand Total",
        "breakup": None,
        "total": grand_total,
        "bold": 1,
        "indent": 0,
    })

    return data
