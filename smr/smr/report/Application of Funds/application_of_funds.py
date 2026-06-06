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
            "width": 350,
        },
        {
            "label": _("Amount"),
            "fieldname": "amount",
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


def get_account_balance(account, from_date, to_date):
    """Get net balance for an account within date range."""
    result = frappe.db.sql("""
        SELECT
            SUM(gl.debit) - SUM(gl.credit) AS balance
        FROM `tabGL Entry` gl
        WHERE gl.account = %s
            AND gl.is_cancelled = 0
            AND gl.posting_date BETWEEN %s AND %s
    """, (account, from_date, to_date))
    return result[0][0] or 0 if result else 0


def get_children_balances(parent_account, from_date, to_date):
    """Get all leaf account balances under a parent, recursively."""
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
            children = get_children_balances(acc.name, from_date, to_date)
            if children:
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
    """Recursively build report rows from account tree."""
    if data is None:
        data = []

    for acc in accounts:
        prefix = "\u00a0" * (indent * 6)
        if acc["is_group"]:
            children = acc.get("children", [])
            group_total = acc["_balance"]

            if indent == 0:
                # Top level section header — bold, show total in Total column
                data.append({
                    "particulars": acc["account_name"],
                    "amount": None,
                    "total": group_total,
                    "bold": 1,
                    "indent": indent,
                })
            else:
                # Sub-group — show name and subtotal in amount column
                data.append({
                    "particulars": prefix + acc["account_name"],
                    "amount": group_total,
                    "total": None,
                    "bold": 1,
                    "indent": indent,
                })

            build_rows(children, indent + 1, data)
        else:
            # Leaf account — show in amount column
            data.append({
                "particulars": prefix + acc["account_name"],
                "amount": acc["_balance"],
                "total": None,
                "bold": 0,
                "indent": indent,
            })

    return data


def get_data(from_date, to_date):
    data = []

    # ── SECTION 1: FIXED ASSETS ──────────────────────────────────────────
    fixed_assets_account = "Fixed Assets - SRPL"
    fixed_assets = get_children_balances(fixed_assets_account, from_date, to_date)
    fixed_assets_total = sum(a["_balance"] for a in fixed_assets)

    # Section header
    data.append({
        "particulars": "FIXED ASSETS",
        "amount": None,
        "total": None,
        "bold": 1,
        "indent": 0,
    })

    build_rows(fixed_assets, indent=1, data=data)

    if fixed_assets_total != 0:
        data.append({
            "particulars": "Total Fixed Assets",
            "amount": None,
            "total": fixed_assets_total,
            "bold": 1,
            "indent": 0,
        })

    data.append({"particulars": "", "amount": None, "total": None})  # spacer

    # ── SECTION 2: CURRENT ASSETS ─────────────────────────────────────────
    current_assets_account = "Current Assets - SRPL"
    current_assets = get_children_balances(current_assets_account, from_date, to_date)
    current_assets_total = sum(a["_balance"] for a in current_assets)

    data.append({
        "particulars": "CURRENT ASSETS",
        "amount": None,
        "total": None,
        "bold": 1,
        "indent": 0,
    })

    build_rows(current_assets, indent=1, data=data)

    if current_assets_total != 0:
        data.append({
            "particulars": "Total Current Assets",
            "amount": None,
            "total": current_assets_total,
            "bold": 1,
            "indent": 0,
        })

    data.append({"particulars": "", "amount": None, "total": None})  # spacer

    # ── SECTION 3: INVESTMENTS ────────────────────────────────────────────
    investments_account = "Investments - SRPL"
    investments = get_children_balances(investments_account, from_date, to_date)
    investments_total = sum(a["_balance"] for a in investments)

    if investments_total != 0:
        data.append({
            "particulars": "INVESTMENTS",
            "amount": None,
            "total": None,
            "bold": 1,
            "indent": 0,
        })
        build_rows(investments, indent=1, data=data)
        data.append({
            "particulars": "Total Investments",
            "amount": None,
            "total": investments_total,
            "bold": 1,
            "indent": 0,
        })
        data.append({"particulars": "", "amount": None, "total": None})

    # ── GRAND TOTAL ───────────────────────────────────────────────────────
    grand_total = fixed_assets_total + current_assets_total + investments_total

    data.append({
        "particulars": "GRAND TOTAL",
        "amount": None,
        "total": grand_total,
        "bold": 1,
        "indent": 0,
    })

    return data
