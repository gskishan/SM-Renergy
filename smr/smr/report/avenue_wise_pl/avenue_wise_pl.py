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
            "label": _("Avenue"),
            "fieldname": "avenue",
            "fieldtype": "Data",
            "width": 280,
        },
        {
            "label": _("Revenue"),
            "fieldname": "revenue",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": _("Cost"),
            "fieldname": "cost",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": _("Gross Margin"),
            "fieldname": "gross_margin",
            "fieldtype": "Currency",
            "width": 150,
        },
        {
            "label": _("Margin %"),
            "fieldname": "margin_pct",
            "fieldtype": "Percent",
            "width": 100,
        },
    ]


def get_gl_data(from_date, to_date):
    return frappe.db.sql("""
        SELECT
            gl.avenue,
            gl.epc,
            gl.trading,
            acc.root_type,
            acc.account_type,
            SUM(CASE WHEN acc.root_type = 'Income' THEN gl.credit - gl.debit ELSE 0 END) AS revenue,
            SUM(CASE WHEN acc.root_type = 'Expense' AND acc.account_type != 'Tax'
                THEN gl.debit - gl.credit ELSE 0 END) AS cost
        FROM `tabGL Entry` gl
        INNER JOIN `tabAccount` acc ON acc.name = gl.account
        WHERE gl.is_cancelled = 0
            AND gl.posting_date BETWEEN %s AND %s
            AND acc.root_type IN ('Income', 'Expense')
            AND (
                (gl.avenue IS NOT NULL AND gl.avenue != '') OR
                (gl.epc IS NOT NULL AND gl.epc != '') OR
                (gl.trading IS NOT NULL AND gl.trading != '')
            )
        GROUP BY gl.avenue, gl.epc, gl.trading
    """, (from_date, to_date), as_dict=True)


def make_row(label, revenue, cost, indent=0):
    gross_margin = revenue - cost
    margin_pct = round((gross_margin / revenue * 100), 2) if revenue else 0
    return {
        "avenue": label,
        "revenue": round(revenue, 2),
        "cost": round(cost, 2),
        "gross_margin": round(gross_margin, 2),
        "margin_pct": margin_pct,
        "indent": indent,
    }


def get_data(from_date, to_date):
    gl_rows = get_gl_data(from_date, to_date)

    # Aggregate by dimension type and value
    dimensions = {
        "EPC": {},
        "Avenue": {},
        "Trading": {},
    }

    for row in gl_rows:
        revenue = float(row.revenue or 0)
        cost = float(row.cost or 0)

        if row.epc:
            d = dimensions["EPC"]
            if row.epc not in d:
                d[row.epc] = {"revenue": 0, "cost": 0}
            d[row.epc]["revenue"] += revenue
            d[row.epc]["cost"] += cost

        if row.avenue:
            d = dimensions["Avenue"]
            if row.avenue not in d:
                d[row.avenue] = {"revenue": 0, "cost": 0}
            d[row.avenue]["revenue"] += revenue
            d[row.avenue]["cost"] += cost

        if row.trading:
            d = dimensions["Trading"]
            if row.trading not in d:
                d[row.trading] = {"revenue": 0, "cost": 0}
            d[row.trading]["revenue"] += revenue
            d[row.trading]["cost"] += cost

    data = []

    for dim_type, dim_values in dimensions.items():
        if not dim_values:
            continue

        # Calculate group total
        total_rev = sum(v["revenue"] for v in dim_values.values())
        total_cost = sum(v["cost"] for v in dim_values.values())

        # Parent row (bold group header)
        parent = make_row(dim_type, total_rev, total_cost, indent=0)
        parent["bold"] = 1
        data.append(parent)

        # Child rows sorted by revenue desc
        for val, amounts in sorted(dim_values.items(), key=lambda x: x[1]["revenue"], reverse=True):
            child = make_row("    " + val, amounts["revenue"], amounts["cost"], indent=1)
            data.append(child)

    return data
