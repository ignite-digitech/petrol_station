// Copyright (c) 2026, Ignite Digital and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shift Closing Entry", {
	refresh(frm) {
		if (!frm.doc.shift_opening_entry) {
			frm.toggle_display(['meter_readings'], false);
		}
		else {
			frm.toggle_display(['meter_readings'], true);
		}

		// Disable adding/removing rows in payment_reconciliation table
		frm.fields_dict.payment_reconciliation.grid.cannot_add_rows = true;
		frm.fields_dict.payment_reconciliation.grid.cannot_delete_rows = true;
		frm.refresh_field('payment_reconciliation');
	},
	onload(frm){
		if(frm.doc.shift_opening_entry){
			update_payment_reconciliation(frm);
		}
	},
	shift_opening_entry(frm) {
		if (!frm.doc.shift_opening_entry) {
			frm.toggle_display(['meter_readings'], false);
		}
		else {
			frm.toggle_display(['meter_readings'], true);
			// Load opening balances when shift is selected
			frm.clear_table('payment_reconciliation');
			update_payment_reconciliation(frm);
		}
	},

	total_meter_sales(frm) {
		// Recalculate payment reconciliation when total sales changes
		update_payment_reconciliation(frm);
	}
});

frappe.ui.form.on("Closing Meter Reading", {
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
						frappe.model.set_value(cdt, cdn, 'opening', r.message.opening_reading);
					}
				}
			});

            frappe.db.get_value("Pump Nozzle", row.nozzle, "fuel_item", (r) => {
                frappe.call({
                    method: "petrol_station.petrol_station.doctype.shift_opening_entry.shift_opening_entry.get_item_price_from_shift",
                    args: {
                        item_code: r.fuel_item,
                        shift_opening_entry: frm.doc.shift_opening_entry
                    },
                    callback: function(r) {
                        console.log(r.message);
                        frappe.model.set_value(cdt, cdn, 'unit_price', r.message.price);
                    }
                })
            })

			frappe.call({
				method: "petrol_station.petrol_station.doctype.pump_nozzle.pump_nozzle.get_tank",
				args: {
					nozzle: row.nozzle
				},
				callback: function (r){
					console.log(r.message)
					frappe.model.set_value(cdt, cdn, 'tank', r.message)
				}
			})
		}
	},

	closing(frm, cdt, cdn) {
		calculate_sales_qty(frm, cdt, cdn);
	},

	opening(frm, cdt, cdn) {
		calculate_sales_qty(frm, cdt, cdn);
	},

	return_to_tank(frm, cdt, cdn) {
		calculate_sales_qty(frm, cdt, cdn);
		calculate_totals(frm);
	},

	unit_price(frm, cdt, cdn) {
		calculate_total_amount(frm, cdt, cdn);
	},

	sales_qty(frm, cdt, cdn) {
		calculate_total_amount(frm, cdt, cdn);
	},

	total_amount(frm, cdt, cdn) {
		calculate_totals(frm);
	},

	meter_readings_remove(frm) {
		calculate_totals(frm);
	}
});

frappe.ui.form.on("POS Closing Entry Detail", {
	closing_amount(frm, cdt, cdn) {
		calculate_payment_difference(frm, cdt, cdn);
	},

	payment_reconciliation_remove(frm) {
		// Optional: handle when a payment row is removed
	}
});

frappe.ui.form.on("Shift Credit Sale", {
    fuel_item(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if(row.fuel_item){
            frappe.call({
                method: "petrol_station.petrol_station.doctype.shift_opening_entry.shift_opening_entry.get_item_price_from_shift",
                args: {
                    item_code: row.fuel_item,
                    shift_opening_entry: frm.doc.shift_opening_entry
                },
                callback: function(r) {
                    let amount = flt(row.rate) * flt(r.message.qty);

                    frappe.model.set_value(cdt, cdn, 'rate', r.message.price);
                    frappe.model.set_value(cdt, cdn, 'amount', amount);
                }
            })
        }
    },
    qty(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let amount = flt(row.rate) * flt(row.qty);
        frappe.model.set_value(cdt, cdn, 'amount', amount);
        calculate_total_credit_sale(frm);
    },
    rate(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let amount = flt(row.rate) * flt(row.qty);

        frappe.model.set_value(cdt, cdn, 'amount', amount);
        calculate_total_credit_sale(frm);
    }
});

function calculate_total_credit_sale(frm) {
    let total_credit_sale = 0;
    frm.doc.credit_sales.forEach(function(row) {
        total_credit_sale += flt(row.amount);
    });
    frm.set_value('total_credit_sales', total_credit_sale);

    update_payment_reconciliation(frm);
}

function calculate_sales_qty(frm, cdt, cdn) {
	let row = locals[cdt][cdn];

	let sales_qty = 0

	// Calculate sales_qty = closing - opening - return_to_tank
	if (flt(row.closing) > 0 || flt(row.return_to_tank) > 0){
		sales_qty = (flt(row.opening) - flt(row.closing) - flt(row.return_to_tank));
	}

	// Ensure non-negative
	sales_qty = Math.max(sales_qty, 0);

	frappe.model.set_value(cdt, cdn, 'sales_qty', sales_qty);
}

function calculate_total_amount(frm, cdt, cdn) {
	let row = locals[cdt][cdn];

	// Calculate total_amount = sales_qty * unit_price
	let total_amount = flt(row.sales_qty) * flt(row.unit_price);

	frappe.model.set_value(cdt, cdn, 'total_amount', total_amount);
}

function calculate_totals(frm) {
	let total_qty = 0;
	let total_returns = 0;
	let total_meter_sales = 0;

	// Sum up all rows in the meter readings table
	if (frm.doc.meter_readings) {
		frm.doc.meter_readings.forEach(function(row) {
			total_qty += flt(row.sales_qty);
			total_returns += flt(row.return_to_tank);
			total_meter_sales += flt(row.total_amount);
		});
	}

	// Update the parent form fields
	frm.set_value('total_qty', total_qty);
	frm.set_value('total_returns', total_returns);
	frm.set_value('total_meter_sales', total_meter_sales);

	// Refresh the table and parent fields
	frm.refresh_field("meter_readings");
	frm.refresh_field("total_qty");
	frm.refresh_field("total_returns");
	frm.refresh_field("total_meter_sales");
}

function update_payment_reconciliation(frm) {
	if (!frm.doc.shift_opening_entry) {
		return;
	}

	// Store existing closing amounts before clearing
	let existing_closing_amounts = {};
	let other_payments = {};

	if (frm.doc.payment_reconciliation) {
		frm.doc.payment_reconciliation.forEach(function(row) {
			// Store closing amount for this mode of payment
			existing_closing_amounts[row.mode_of_payment] = flt(row.closing_amount);

			let mode_lower = row.mode_of_payment.toLowerCase();
			// Collect all non-cash payments
			if (!mode_lower.includes('cash')) {
				other_payments[row.mode_of_payment] = flt(row.closing_amount);
			}
		});
	}

	// Fetch opening balances with expected calculations
	frappe.call({
		method: 'petrol_station.petrol_station.doctype.shift_opening_entry.shift_opening_entry.get_opening_balances_with_expected',
		args: {
			shift_opening_entry: frm.doc.shift_opening_entry,
			total_sales: flt(frm.doc.total_meter_sales),
			payments: other_payments,
			credit_sales: frm.doc.total_credit_sales
		},
		freeze: true,
		freeze_message: __('Loading payment reconciliation...'),
		callback: function(r) {
			if (r.message) {
				// Clear existing payment reconciliation
				frm.clear_table('payment_reconciliation');

				// Add new rows from opening balances
				r.message.forEach(function(balance) {
					let row = frm.add_child('payment_reconciliation');
					row.mode_of_payment = balance.mode_of_payment;
					row.opening_amount = balance.opening_amount;
					row.expected_amount = balance.expected || 0;

					// Restore closing_amount if it existed for this mode
					if (existing_closing_amounts[balance.mode_of_payment] !== undefined) {
						row.closing_amount = existing_closing_amounts[balance.mode_of_payment];
					} else {
						row.closing_amount = 0;
					}

					// Calculate difference
					row.difference = flt(row.closing_amount) - flt(row.expected_amount);
				});

				frm.refresh_field('payment_reconciliation');
			}
		}
	});
}

function calculate_payment_difference(frm, cdt, cdn) {
	let row = locals[cdt][cdn];

	// Calculate difference = closing_amount - expected_amount
	let difference = flt(row.closing_amount) - flt(row.expected_amount);
	frappe.model.set_value(cdt, cdn, 'difference', difference);

	// Trigger recalculation for cash expected if this is a non-cash payment
	let mode_lower = row.mode_of_payment.toLowerCase();
	if (!mode_lower.includes('cash')) {
		update_payment_reconciliation(frm);
	}
}

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
                    }
                }
            })
        }
    },
	physical_liters(frm, cdt, cdn){
		let row = locals[cdt][cdn]

		if (row.physical_liters){
			let book_stock = get_book_stock(row.tank, row.opening)
			frappe.model.set_value(cdt, cdn, 'book_stock', book_stock)

			let variation = calculate_dip_variation(cdt, cdn)
			frappe.model.set_value(cdt, cdn, 'variation', variation)
		}
	}

})

function calculate_dip_variation(cdt, cdn){
	let row = locals[cdt][cdn]

	let variation = 0
	if(row.physical_liters){
		variation = Math.abs(flt(row.physical_liters) - flt(row.book_stock))
	}

	variation = Math.max(variation, 0);

	return variation

}

function get_book_stock(tank, opening){
	let totals = get_sales_qty_sum_for_tank(tank)
	return flt(opening) - flt(totals.sales_qty) - flt(totals.returns)
}

function get_sales_qty_sum_for_tank(tank) {
	let total_sales_qty = 0;
	let total_returns = 0


	if (cur_frm.doc.meter_readings) {
		cur_frm.doc.meter_readings.forEach(function(row) {
			if (row.tank === tank) {
				total_sales_qty += flt(row.sales_qty);
				total_returns += flt(row.return_to_tank)
			}
		});
	}

	total_sales_qty = Math.max(total_sales_qty, 0);
	total_returns = Math.max(total_returns, 0);

	return {
		sales_qty: total_sales_qty,
		returns: total_returns
	};
}


