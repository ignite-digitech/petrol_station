// Copyright (c) 2026, Ignite Digital and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shift Opening Entry", {
	refresh(frm) {
	}
});

frappe.ui.form.on("Shift Opening Meter Reading", {
	nozzle(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		if (row.nozzle) {
			// Auto-fetch the last closing qty for this nozzle
			frappe.call({
				method: 'petrol_station.petrol_station.doctype.pump_meter_reading.pump_meter_reading.auto_fetch_nozzle_opening_reading',
				args: {
					nozzle: row.nozzle,
					posting_date: frm.doc.posting_date,
					posting_time: frm.doc.posting_time
				},
				freeze: true,
				freeze_message: __('Fetching last closing reading for {0}', [row.nozzle]),
				callback: function(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, 'opening_reading', r.message.opening_reading);
						frappe.model.set_value(cdt, cdn, 'expected_reading', r.message.expected_reading);
					}
				}
			});
		}
	}
});

frappe.ui.form.on("Shift Opening Fuel Price", {
	fuel_item(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		if (row.fuel_item) {
			// Auto-fetch the selling price for this fuel item
			frappe.call({
				method: 'petrol_station.petrol_station.doctype.pump_meter_reading.pump_meter_reading.get_selling_price',
				args: {
					item_code: row.fuel_item
				},
				freeze: true,
				freeze_message: __('Fetching selling price for {0}', [row.fuel_item]),
				callback: function(r) {
					if (r.message) {
						console.log(r.message);
						frappe.model.set_value(cdt, cdn, 'rate', r.message);

						frm.refresh_field("selling_prices");
					}
				}
			});
		}
	}
});

frappe.ui.form.on("Shift Tank Dip", {
    tank(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.tank) {
            frappe.call({
                method: "petrol_station.petrol_station.doctype.tank_dip_log.tank_dip_log.get_last_closing_book_balance",
                args: {
                    tank: row.tank
                },
                freeze: true,
                freeze_message: __('Fetching last closing reading for {0}', [frm.doc.tank]),
                callback: function (r) {
                    if (r.message) {
                        frappe.model.set_value(cdt, cdn, 'opening', r.message);
                        frappe.model.set_value(cdt, cdn, 'book_stock', r.message);
                    }
                }
            })
        }
    },
	physical_liters(frm, cdt, cdn){
		let row = locals[cdt][cdn]

		if(row.physical_liters){
			let variation = flt(row.opening) - flt(row.physical_liters)
			frappe.model.set_value(cdt, cdn, 'variation', variation)
		}
	}

})
