// Copyright (c) 2026, Ignite Digital and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shift Opening Entry", {
	refresh(frm) {
		cur_frm.add_custom_button("Close Shift", () => {
			frappe.model.open_mapped_doc({
				method: "petrol_station.petrol_station.doctype.shift_opening_entry.shift_opening_entry.make_shift_closing_entry",
				frm: frm,
				// args: { default_supplier: values.default_supplier },
				run_link_triggers: true,
			});
		})
	},
	onload(frm){
		if (frm.is_new()) {
			frappe.run_serially([
				getPumpReadings,
				getTankReadings,
				getPaymentMethods,
				getFuelPrices
			])
		}
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
						// console.log(r.message);
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
					else
					{
						frappe.model.set_value(cdt, cdn, 'opening', 0);
                        frappe.model.set_value(cdt, cdn, 'book_stock', 0);
					}
                }
            })
        }
    },
	physical_liters(frm, cdt, cdn){
		let row = locals[cdt][cdn]

		if(row.physical_liters){
			let variation = flt(row.opening) - flt(row.physical_liters)
			variation = flt(variation) * -1
			frappe.model.set_value(cdt, cdn, 'variation', variation)

		}
	}

})

function getPumpReadings(){
	frappe.call({
		method: 'petrol_station.petrol_station.doctype.pump_meter_reading.pump_meter_reading.get_all_nozzles_with_opening_reading',
		freeze: true,
		freeze_message: __('Fetching last closing reading for all nozzles'),
		callback: function(r) {
			if (r.message) {
				let readings = r.message;
				cur_frm.clear_table("opening_meter_readings");
				readings.forEach(function(reading) {
					let row = cur_frm.add_child("opening_meter_readings");
					row.nozzle = reading.nozzle;
					row.pump = reading.pump;
					row.tank = reading.tank;
					row.opening_reading = reading.last_reading;
					row.expected_reading = reading.last_reading;
				});
				cur_frm.refresh_field("opening_meter_readings");
			}
		}
	})
}

function getTankReadings(){
	frappe.call({
		method: 'petrol_station.petrol_station.doctype.fuel_ledger.fuel_ledger.get_all_tanks_with_closing_balance',
		freeze: true,
		freeze_message: __('Fetching last closing reading for all tanks'),
		callback: function(r) {
			if (r.message) {
				let readings = r.message;
				cur_frm.clear_table("tank_dips");
				readings.forEach(function(reading) {
					let row = cur_frm.add_child("tank_dips");
					row.tank = reading.tank;
					row.fuel_item = reading.fuel_item;
					row.opening = reading.closing_balance;
					row.book_stock = reading.closing_balance;
				});
				cur_frm.refresh_field("tank_dips");
			}
		}
	})
}

function getPaymentMethods(){
		frappe.db.get_list("Mode of Payment", {
			filters: {"enabled": 1},
			fields:	['mode_of_payment']
		}).then(methods => {
			if (methods.length > 0){
				cur_frm.clear_table("opening_balances");
				methods.forEach(function(method) {
					let row = cur_frm.add_child("opening_balances");
					row.mode_of_payment = method.mode_of_payment;
					row.opening_amount = 0;
				});
				cur_frm.refresh_field("opening_balances");
			}
		})
}

function getFuelPrices(){
	frappe.call({
		method: 'petrol_station.petrol_station.doctype.pump_meter_reading.pump_meter_reading.get_all_fuel_items_with_prices',
		freeze: true,
		freeze_message: __('Fetching selling price for all fuel items'),
		callback: function(r) {
			if (r.message) {
				let prices = r.message;
				cur_frm.clear_table("selling_prices");
				prices.forEach(function(price) {
					let row = cur_frm.add_child("selling_prices");
					row.fuel_item = price.item;
					row.rate = price.price;
				})

				cur_frm.refresh_field("selling_prices");
			}
		}
	})
}