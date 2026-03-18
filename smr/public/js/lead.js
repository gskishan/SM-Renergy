frappe.ui.form.on("Lead", {
    refresh: function(frm) {
        if (frm.doc.status === "Interested") {
            frm.add_custom_button(__('Site Survey'), function() {

                // Fetch Address linked via Dynamic Link
                frappe.db.get_value(
                    "Address",
                    {
                        "address_title": frm.doc.lead_from
                    },
                    "name"
                ).then(r => {

                    frappe.new_doc("Site Survey", {
                        lead_from: frm.doc.name,
                        client_name: frm.doc.company_name || frm.doc.job_title,
                        client_mobile_number: frm.doc.mobile_no,
                        site_address: r.message ? r.message.name : null
                    });

                });

            }, __("Create"));
        }
    }
});