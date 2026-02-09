// Copyright (c) 2026, Ignite Digital and contributors
// For license information, please see license.txt

frappe.ui.form.on("Tank Dip Log", {
	refresh(frm) {

	},
    tank: function(frm) {
        frm.trigger("set_opening_dip");
    },
    set_opening_dip: function(frm) {
        frappe.call({
            method: "petrol_station.petrol_station.doctype.tank_dip_log.tank_dip_log.get_last_closing_book_balance",
            args: {
                tank: frm.doc.tank
            },
            freeze: true,
            freeze_message: __('Fetching last closing reading for {0}', [frm.doc.tank]),
            callback: function(r) {
                if (r.message) {
                    frm.set_value("opening_dip", r.message);
                    cur_frm.refresh_field("opening_dip");
                }
            }
        })
    }
});

