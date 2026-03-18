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
                    if (frm.doc.bom_item && frm.doc.bom_item.length) {
                        frm.doc.bom_item.forEach(item => {
                                let new_item = frappe.model.add_child(quotation, "Quotation Item", "items");
                                Object.assign(new_item, {
                                    item_code: item.item_code,
                                    item_name: item.item_name || "",
                                    uom: item.uom || "",
                                    description: item.description || "",
                                    qty: item.qty || 0,
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
    
                frm.set_value("clint_name", doc.company_name || doc.job_title);
    
            });
    
            
        }
    },
    })
