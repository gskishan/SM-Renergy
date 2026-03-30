// Copyright (c) 2026, SMR and contributors
// For license information, please see license.txt

frappe.ui.form.on("Site Survey", {
     refresh: function(frm) {
         if (frm.doc.docstatus == 1) {
             frm.add_custom_button('Quotation', () => {
                 frappe.model.with_doctype('Quotation', function() {
                     let quotation = frappe.model.get_new_doc('Quotation');
                     quotation.quotation_to = "Lead";
                     quotation.party_name = frm.doc.lead_from;
                     quotation.project = frm.doc.project;
                     quotation.customer_address = frm.doc.site_address|| "";
                     quotation.custom_site_survey = frm.doc.name || "";
                    
                     frappe.set_route("Form", "Quotation", quotation.name);
                 });
             },__("Create"));
             frm.add_custom_button('Designing', () => {
                frappe.model.with_doctype('Designing', function() {
                    let design = frappe.model.get_new_doc('Designing');
                    design.lead_from = frm.doc.lead_from;
                    design.clint_name = frm.doc.clint_name;
                    design.project = frm.doc.project;
                    design.capacity = frm.doc.capacity;
                    design.site_survey = frm.doc.name;
                    frappe.set_route("Form", "Designing", design.name);
                });
            },__("Create"));
            }
        },
        lead_from: function(frm) {
            if (frm.doc.lead_from) {
        
                // Fetch Lead details
                frappe.db.get_doc("Lead", frm.doc.lead_from).then(doc => {
        
                    frm.set_value("client_mobile_number", doc.mobile_no);
                    frm.set_value("clint_name", doc.company_name || doc.lead_name);
        
                });
        
                // Fetch Address linked to Lead
                frappe.db.get_value(
                    "Address",
                    {
                        "address_title": frm.doc.lead_from
                    },
                    "name"
                ).then(r => {
                    if (r.message) {
                        frm.set_value("site_address", r.message.name);
                    }
                });
            }
        },
        onload: function(frm) {

            frm.set_query("site_address", function() {
                return {
                    query: "frappe.contacts.doctype.address.address.address_query",
                    filters: {
                        // link_doctype: "Lead",
                        link_name: frm.doc.lead_from
                    }
                };
            });
    
        }
        
     })
     frappe.ui.form.on("Site Survey", "site_address", function(frm, cdt, cdn) { 
        if(frm.doc.site_address){ 
             return frm.call({
                method: "frappe.contacts.doctype.address.address.get_address_display",
                args: {
                    "address_dict": frm.doc.site_address 

                }, 
                callback: function(r) { 
                     if(r.message) 
                        frm.set_value("site_address_detail", r.message); 
                    } 
                }); 
            } 
            else{ 
                frm.set_value("site_address_detail", ""); 
            }});

            
