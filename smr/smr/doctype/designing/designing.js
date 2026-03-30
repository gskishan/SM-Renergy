// Copyright (c) 2026, SMR and contributors
// For license information, please see license.txt

frappe.ui.form.on("Designing", {
    refresh: function(frm) {
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button('Quotation', () => {
                frappe.model.with_doctype('Quotation', function() {
                    let quotation = frappe.model.get_new_doc('Quotation');
                    quotation.quotation_to = "Lead";
                    quotation.party_name = frm.doc.lead_from;
                    quotation.project = frm.doc.project;
                    quotation.custom_designing = frm.doc.name || "";
                    quotation.custom_site_survey = frm.doc.site_survey || "";
                    quotation.selling_price_list="Custom Use Only";
                    if (frm.doc.bom_item && frm.doc.bom_item.length) {
                        frm.doc.bom_item.forEach(item => {
                                let new_item = frappe.model.add_child(quotation, "Quotation Item", "items");
                                Object.assign(new_item, {
                                    item_code: item.item_code,
                                    item_name: item.item_name || "",
                                    uom: item.uom || "",
                                    description: item.description || "",
                                    qty: item.qty || 0,
                                    rate: item.rate || 0,
                                    amount: item.amount || 0,
                                });
                        });
                    }
                    frappe.set_route("Form", "Quotation", quotation.name);
                });
            });
           }
       },
       lead_from: function(frm) {
        if (frm.doc.lead_from) {
    
            // Fetch Lead details
            frappe.db.get_doc("Lead", frm.doc.lead_from).then(doc => {
    
                frm.set_value("clint_name", doc.company_name || doc.lead_name);
    
            });
    
            
        }
    }
    })
   
    frappe.ui.form.on('SMR BOM Item', {
        qty(frm, cdt, cdn) {
            calculate_row(frm, cdt, cdn);
        },
        rate(frm, cdt, cdn) {
            calculate_row(frm, cdt, cdn);
        },
        bom_item_remove(frm) {
            calculate_totals(frm);
            
        }
    });
    
    function calculate_row(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.amount = (row.qty || 0) * (row.rate || 0);
        frm.refresh_field("bom_item");
        calculate_totals(frm);
    }
    
    function calculate_totals(frm) {
        let total_qty = 0;
        let total_amount = 0;
    
        (frm.doc.bom_item || []).forEach(row => {
            total_qty += row.qty || 0;
            total_amount += row.amount || 0;
        });
    
        frm.set_value("total_qty", total_qty);
        frm.set_value("amount", total_amount);
    }