import frappe
from frappe import db

@frappe.whitelist()
def get_remaining_qty(designing_name):
    designing = frappe.get_doc("Designing", designing_name)
    
    used_qty_map = {}
    
    quotations = frappe.get_all("Quotation", filters={"custom_designing": designing_name, "docstatus": 1}, fields=["name"])
    
    for q in quotations:
        items = frappe.get_all("Quotation Item", filters={"parent": q.name}, fields=["item_code", "qty"])
        for item in items:
            used_qty_map[item.item_code] = used_qty_map.get(item.item_code, 0) + item.qty
    
    remaining_qty_map = {}
    for row in designing.bom_item:
        used_qty = used_qty_map.get(row.item_code, 0)
        remaining_qty_map[row.item_code] = max(row.qty - used_qty, 0)
    
    return remaining_qty_map

def on_update_after_submit(doc, method):

    # GL Entry update
    db.sql("""
        UPDATE `tabGL Entry`
        SET 
            trading = %s,
            epc = %s,
            avenue = %s
        WHERE voucher_type = 'Sales Invoice'
        AND voucher_no = %s
    """, (
        doc.trading,
        doc.epc,
        doc.avenue,
        doc.name
    ))

    db.commit()