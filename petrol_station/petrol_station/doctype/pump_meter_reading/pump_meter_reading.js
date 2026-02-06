// Copyright (c) 2026, Ignite Digital and contributors
// For license information, please see license.txt

frappe.ui.form.on("Pump Meter Reading", {
	refresh(frm) {
            cur_frm.set_query("nozzle", "readings", function(doc, cdt, cdn) {
            return {
                filters: {
                    "pump": doc.pump
                }
            }
        })
	},
});
