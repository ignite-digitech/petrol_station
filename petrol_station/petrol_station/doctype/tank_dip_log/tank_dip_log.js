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

frappe.ui.form.on("Fuel Delivery", {
    deliveries_add: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (frm.doc.tank && frm.doc.fuel_item) {
            frappe.model.set_value(cdt, cdn, "tank", frm.doc.tank);
            frappe.model.set_value(cdt, cdn, "fuel_item", frm.doc.fuel_item);
        }
    },
    qty: function(frm, cdt, cdn) {
        calculate_stock_in()
    },
    rate: function(frm, cdt, cdn) {
        calculate_stock_in()
    },
    deliveries_remove: function(frm) {
        calculate_stock_in()
    }
});

function calculate_stock_in() {
    let total_stock_in = 0;
    if (cur_frm.doc.deliveries) {
        cur_frm.doc.deliveries.forEach(function(delivery) {
            if (delivery.qty) {
                total_stock_in += delivery.qty;
            }
        });
    }
    cur_frm.set_value("stock_in", total_stock_in);
}

