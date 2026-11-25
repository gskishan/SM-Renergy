import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    return get_columns(), get_data(filters)


def get_columns():
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 140},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 180},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 130},
        {"label": _("Description"), "fieldname": "description", "fieldtype": "Data", "width": 220},
        {"label": _("Delivery Note Number"), "fieldname": "delivery_note", "fieldtype": "Link", "options": "Delivery Note", "width": 170},
        {"label": _("Posting Date"), "fieldname": "posting_date", "fieldtype": "Date", "width": 100},
        {"label": _("Customer Name"), "fieldname": "customer_name", "fieldtype": "Data", "width": 180},
        {"label": _("Project"), "fieldname": "project", "fieldtype": "Link", "options": "Project", "width": 140},
        {"label": _("Sales Invoice"), "fieldname": "sales_invoice", "fieldtype": "Data", "width": 170},
        {"label": _("Stock Qty"), "fieldname": "stock_qty", "fieldtype": "Float", "width": 90},
        {"label": _("Stock UOM"), "fieldname": "stock_uom", "fieldtype": "Link", "options": "UOM", "width": 80},
        {"label": _("Rate"), "fieldname": "rate", "fieldtype": "Currency", "width": 110},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
    ]


def get_conditions(filters):
    conditions = []
    if filters.get("company"):
        conditions.append("dn.company = %(company)s")
    if filters.get("from_date"):
        conditions.append("dn.posting_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("dn.posting_date <= %(to_date)s")
    if filters.get("customer"):
        conditions.append("dn.customer = %(customer)s")
    if filters.get("project"):
        conditions.append("COALESCE(NULLIF(dni.project, ''), dn.project) = %(project)s")
    if filters.get("item_group"):
        conditions.append("dni.item_group = %(item_group)s")
    if filters.get("item_code"):
        conditions.append("dni.item_code = %(item_code)s")
    if filters.get("delivery_note"):
        conditions.append("dn.name = %(delivery_note)s")
    return (" AND " + " AND ".join(conditions)) if conditions else ""


def get_data(filters):
    # Sales Invoice is resolved in three steps, first match wins:
    # 1. the DN item was made from an invoice (against_sales_invoice)
    # 2. an invoice was made from this DN (Sales Invoice Item.dn_detail)
    # 3. an invoice was made from the same Sales Order line (Sales Invoice Item.so_detail)
    #    without referencing any Delivery Note
    return frappe.db.sql(
        """
        SELECT
            dni.item_code,
            dni.item_name,
            dni.item_group,
            dni.description,
            dn.name AS delivery_note,
            dn.posting_date,
            dn.customer_name,
            COALESCE(NULLIF(dni.project, ''), dn.project) AS project,
            COALESCE(
                NULLIF(dni.against_sales_invoice, ''),
                (
                    SELECT GROUP_CONCAT(DISTINCT sii.parent ORDER BY sii.parent SEPARATOR ', ')
                    FROM `tabSales Invoice Item` sii
                    WHERE sii.docstatus = 1 AND sii.dn_detail = dni.name
                ),
                (
                    SELECT GROUP_CONCAT(DISTINCT sii.parent ORDER BY sii.parent SEPARATOR ', ')
                    FROM `tabSales Invoice Item` sii
                    WHERE sii.docstatus = 1
                        AND IFNULL(dni.so_detail, '') != ''
                        AND sii.so_detail = dni.so_detail
                        AND IFNULL(sii.delivery_note, '') = ''
                )
            ) AS sales_invoice,
            dni.stock_qty,
            dni.stock_uom,
            dni.base_rate AS rate,
            dni.base_amount AS amount
        FROM `tabDelivery Note` dn
        INNER JOIN `tabDelivery Note Item` dni ON dni.parent = dn.name
        WHERE dn.docstatus = 1
            AND dn.is_return = 0
            {conditions}
        ORDER BY dn.posting_date DESC, dn.name DESC, dni.idx ASC
        """.format(conditions=get_conditions(filters)),
        filters,
        as_dict=True,
    )
