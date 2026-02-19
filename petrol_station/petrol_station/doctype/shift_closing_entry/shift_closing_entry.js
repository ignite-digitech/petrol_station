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

		// if (frm.is_new()) {
		// 	frm.toggle_display(['dip_readings'], false);
		// }
		// else {
		// 	frm.toggle_display(['dip_readings'], true);
		// }

		// Disable adding/removing rows in payment_reconciliation table
		frm.fields_dict.payment_reconciliation.grid.cannot_add_rows = true;
		frm.fields_dict.payment_reconciliation.grid.cannot_delete_rows = true;
		frm.refresh_field('payment_reconciliation');

		// Render summary
		render_shift_summary(frm);
	},
	onload(frm){
		if(frm.doc.shift_opening_entry && frm.doc.docstatus === 0){
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
		render_shift_summary(frm);
	},

	total_credit_sales(frm) {
		render_shift_summary(frm);
	},

	total_items_sales(frm) {
		render_shift_summary(frm);
	},

	total_expenses(frm) {
		render_shift_summary(frm);
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
		update_all_dip_book_stocks(frm);
	},

	unit_price(frm, cdt, cdn) {
		calculate_total_amount(frm, cdt, cdn);
	},

	sales_qty(frm, cdt, cdn) {
		calculate_total_amount(frm, cdt, cdn);
		update_all_dip_book_stocks(frm);
	},

	total_amount(frm, cdt, cdn) {
		calculate_totals(frm);
	},

	meter_readings_remove(frm) {
		calculate_totals(frm);
		render_shift_summary(frm);
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

        // If rate and amount are both set and > 0, calculate qty
        if (flt(row.rate) > 0 && flt(row.amount) > 0) {
            let qty = flt(row.amount) / flt(row.rate);
            frappe.model.set_value(cdt, cdn, 'qty', qty);
        } else {
            let amount = flt(row.rate) * flt(row.qty);
            frappe.model.set_value(cdt, cdn, 'amount', amount);
        }

        calculate_total_credit_sale(frm);
    },
    amount(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        // If rate and amount are both set and > 0, calculate qty
        if (flt(row.rate) > 0 && flt(row.amount) > 0) {
            let qty = flt(row.amount) / flt(row.rate);
            frappe.model.set_value(cdt, cdn, 'qty', qty);
        }

        calculate_total_credit_sale(frm);
    },

    credit_sales_remove(frm) {
        calculate_total_credit_sale(frm);
        render_shift_summary(frm);
    }
});

function calculate_total_credit_sale(frm) {
    let total_credit_sale = 0;
    frm.doc.credit_sales.forEach(function(row) {
        total_credit_sale += flt(row.amount);
    });
    frm.set_value('total_credit_sales', total_credit_sale);

    update_payment_reconciliation(frm);
    render_shift_summary(frm);
}

function calculate_sales_qty(frm, cdt, cdn) {
	let row = locals[cdt][cdn];

	let sales_qty = 0

	// Calculate sales_qty = closing - opening - return_to_tank
	if (flt(row.closing) > 0 || flt(row.return_to_tank) > 0){
		sales_qty = Math.abs(flt(row.opening) - flt(row.closing));
		if(flt(row.return_to_tank) > 0){
			sales_qty -= flt(row.return_to_tank);
		}
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

frappe.ui.form.on("POS Closing Entry Detail", {
	closing_amount(frm, cdt, cdn) {
		calculate_payment_difference(frm, cdt, cdn);
		render_shift_summary(frm);
	},

	payment_reconciliation_remove(frm) {
		render_shift_summary(frm);
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
						let opening = r.message
                        frappe.model.set_value(cdt, cdn, 'opening',opening);

						let book_stock = get_book_stock(row.tank, opening)

						frappe.model.set_value(cdt, cdn, 'book_stock', book_stock)
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

			let variation = calculate_dip_variation(cdt, cdn, book_stock)
			frappe.model.set_value(cdt, cdn, 'variation', variation)
		}
	},

	dip_readings_remove(frm) {
		render_shift_summary(frm);
	}
})

function calculate_dip_variation(cdt, cdn, book_stock){
	let row = locals[cdt][cdn]

	let variation = 0
	if(row.physical_liters){
		variation =  flt(book_stock) - flt(row.physical_liters)
	}

	variation = variation * -1;

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

function update_all_dip_book_stocks(frm) {
	if (frm.doc.dip_readings) {
		frm.doc.dip_readings.forEach(function(dip_row) {
			if (dip_row.tank && dip_row.opening !== undefined) {
				let book_stock = get_book_stock(dip_row.tank, dip_row.opening);
				frappe.model.set_value(dip_row.doctype, dip_row.name, 'book_stock', book_stock);

				// Recalculate variation if physical_liters exists
				if (dip_row.physical_liters) {
					let variation = flt(book_stock) - flt(dip_row.physical_liters);
					variation = variation * -1;
					frappe.model.set_value(dip_row.doctype, dip_row.name, 'variation', variation);

					// Format variation column with color
					let actual_variation = flt(dip_row.physical_liters) - flt(book_stock)
				}
			}
		});
	}
}

frappe.ui.form.on("Shift Expense", {
	amount(frm, cdt, cdn) {
		calculate_total_expense(frm);
	},

	expenses_remove(frm) {
		calculate_total_expense(frm);
		render_shift_summary(frm);
	}
})

function calculate_total_expense(frm) {
	let total_expense = 0;
	frm.doc.expenses.forEach(function(row) {
		total_expense += flt(row.amount);
	});
	frm.set_value('total_expenses', total_expense);
	render_shift_summary(frm);
}

frappe.ui.form.on("Shift Item Sales", {
	item_code(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		frappe.call({
			method: "petrol_station.petrol_station.doctype.pump_meter_reading.pump_meter_reading.get_selling_price",
			args: {
				item_code: row.item_code,
				price_list: "Standard Selling",
			},
			freeze: true,
			callback: function(r) {
				frappe.model.set_value(cdt, cdn, 'rate', r.message)

				calculate_item_amount(frm, cdt, cdn);
			}
		})

	},
	qty(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
	},
	rate(frm, cdt, cdn) {
		calculate_item_amount(frm, cdt, cdn);
	},

	items_sales_remove(frm) {
		calculate_total_item_sales(frm);
		render_shift_summary(frm);
	}
})

function calculate_item_amount(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	let amount = flt(row.qty) * flt(row.rate);
	frappe.model.set_value(cdt, cdn, 'amount', amount);

	calculate_total_item_sales(frm);
}

function calculate_total_item_sales(frm) {
	let total_item_sales = 0;
	frm.doc.items_sales.forEach(function(row) {
		total_item_sales += flt(row.amount);
	});
	frm.set_value('total_items_sales', total_item_sales);
	render_shift_summary(frm);
}

function render_shift_summary(frm) {
	if (!frm.doc.name || frm.is_new()) {
		return;
	}

	frappe.call({
		method: 'get_summary_data',
		doc: frm.doc,
		callback: function(r) {
			if (r.message) {
				let summary_html = generate_summary_html(r.message);
				frm.set_df_property('summary', 'options', summary_html);
			}
		}
	});
}

function generate_summary_html(data) {
	let html = `
		<style>
			.summary-container {
				font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
				padding: 20px;
				background: #f8f9fa;
			}
			.kpi-grid {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
				gap: 15px;
				margin-bottom: 30px;
			}
			.kpi-card {
				background: white;
				padding: 20px;
				border-radius: 8px;
				box-shadow: 0 2px 4px rgba(0,0,0,0.1);
				border-left: 4px solid #2490ef;
			}
			.kpi-card.success { border-left-color: #28a745; }
			.kpi-card.warning { border-left-color: #ffc107; }
			.kpi-card.danger { border-left-color: #dc3545; }
			.kpi-card.info { border-left-color: #17a2b8; }
			.kpi-label {
				font-size: 12px;
				color: #6c757d;
				text-transform: uppercase;
				margin-bottom: 5px;
			}
			.kpi-value {
				font-size: 24px;
				font-weight: bold;
				color: #212529;
			}
			.summary-section {
				background: white;
				padding: 20px;
				border-radius: 8px;
				box-shadow: 0 2px 4px rgba(0,0,0,0.1);
				margin-bottom: 20px;
			}
			.section-title {
				font-size: 18px;
				font-weight: 600;
				color: #212529;
				margin-bottom: 15px;
				padding-bottom: 10px;
				border-bottom: 2px solid #e9ecef;
			}
			.summary-table {
				width: 100%;
				border-collapse: collapse;
			}
			.summary-table th {
				background: #f8f9fa;
				padding: 10px;
				text-align: left;
				font-size: 12px;
				font-weight: 600;
				color: #495057;
				border-bottom: 2px solid #dee2e6;
			}
			.summary-table td {
				padding: 10px;
				border-bottom: 1px solid #e9ecef;
				font-size: 14px;
			}
			.summary-table tr:hover {
				background: #f8f9fa;
			}
			.text-right {
				text-align: right;
			}
			.text-success {
				color: #28a745;
				font-weight: 600;
			}
			.text-danger {
				color: #dc3545;
				font-weight: 600;
			}
			.text-muted {
				color: #6c757d;
			}
		</style>

		<div class="summary-container">
			<div class="kpi-grid">
				<div class="kpi-card success">
					<div class="kpi-label">Total Fuel Sales</div>
					<div class="kpi-value">${format_currency(data.kpis.total_fuel_sales)}</div>
				</div>
				<div class="kpi-card info">
					<div class="kpi-label">Total Credit Sales</div>
					<div class="kpi-value">${format_currency(data.kpis.total_credit_sales)}</div>
				</div>
				<div class="kpi-card success">
					<div class="kpi-label">Total Item Sales</div>
					<div class="kpi-value">${format_currency(data.kpis.total_item_sales)}</div>
				</div>
				<div class="kpi-card danger">
					<div class="kpi-label">Total Expenses</div>
					<div class="kpi-value">${format_currency(data.kpis.total_expenses)}</div>
				</div>
				<div class="kpi-card info">
					<div class="kpi-label">Total Qty Sold (L)</div>
					<div class="kpi-value">${format_number(data.kpis.total_qty)}</div>
				</div>
				<div class="kpi-card warning">
					<div class="kpi-label">Total Returns (L)</div>
					<div class="kpi-value">${format_number(data.kpis.total_returns)}</div>
				</div>
			</div>
	`;

	// Sales by Fuel Item
	if (data.fuel_sales_by_item && data.fuel_sales_by_item.length > 0) {
		html += `
			<div class="summary-section">
				<div class="section-title">Fuel Sales by Item</div>
				<table class="summary-table">
					<thead>
						<tr>
							<th>Fuel Item</th>
							<th class="text-right">Quantity (L)</th>
							<th class="text-right">Amount</th>
							<th class="text-right">Transactions</th>
						</tr>
					</thead>
					<tbody>
		`;
		data.fuel_sales_by_item.forEach(function(item) {
			html += `
				<tr>
					<td><strong>${item.fuel_item}</strong></td>
					<td class="text-right">${format_number(item.qty)}</td>
					<td class="text-right">${format_currency(item.amount)}</td>
					<td class="text-right">${item.count}</td>
				</tr>
			`;
		});
		html += `
					</tbody>
				</table>
			</div>
		`;
	}

	// Sales by Attendant
	if (data.sales_by_attendant && data.sales_by_attendant.length > 0) {
		html += `
			<div class="summary-section">
				<div class="section-title">Sales by Attendant</div>
				<table class="summary-table">
					<thead>
						<tr>
							<th>Attendant</th>
							<th class="text-right">Fuel Qty (L)</th>
							<th class="text-right">Fuel Amount</th>
							<th class="text-right">Credit Amount</th>
							<th class="text-right">Item Amount</th>
							<th class="text-right">Total Amount</th>
						</tr>
					</thead>
					<tbody>
		`;
		data.sales_by_attendant.forEach(function(attendant) {
			html += `
				<tr>
					<td><strong>${attendant.employee_name}</strong></td>
					<td class="text-right">${format_number(attendant.fuel_qty)}</td>
					<td class="text-right">${format_currency(attendant.fuel_amount)}</td>
					<td class="text-right">${format_currency(attendant.credit_amount)}</td>
					<td class="text-right">${format_currency(attendant.item_amount)}</td>
					<td class="text-right text-success">${format_currency(attendant.total_amount)}</td>
				</tr>
			`;
		});
		html += `
					</tbody>
				</table>
			</div>
		`;
	}

	// Tank Variations
	if (data.tank_variations && data.tank_variations.length > 0) {
		html += `
			<div class="summary-section">
				<div class="section-title">Tank Variations</div>
				<table class="summary-table">
					<thead>
						<tr>
							<th>Tank</th>
							<th>Fuel Item</th>
							<th class="text-right">Opening (L)</th>
							<th class="text-right">Physical (L)</th>
							<th class="text-right">Book Stock (L)</th>
							<th class="text-right">Variation (L)</th>
						</tr>
					</thead>
					<tbody>
		`;
		data.tank_variations.forEach(function(tank) {
			let variation_class = tank.variation < 0 ? 'text-danger' : (tank.variation > 0 ? 'text-success' : '');
			html += `
				<tr>
					<td><strong>${tank.tank}</strong></td>
					<td>${tank.fuel_item}</td>
					<td class="text-right">${format_number(tank.opening)}</td>
					<td class="text-right">${format_number(tank.physical_liters)}</td>
					<td class="text-right">${format_number(tank.book_stock)}</td>
					<td class="text-right ${variation_class}">${format_number(tank.variation)}</td>
				</tr>
			`;
		});
		html += `
					</tbody>
				</table>
			</div>
		`;
	}

	// Item Sales by Group
	if (data.item_sales_by_group && data.item_sales_by_group.length > 0) {
		html += `
			<div class="summary-section">
				<div class="section-title">Item Sales by Group</div>
				<table class="summary-table">
					<thead>
						<tr>
							<th>Item Group</th>
							<th class="text-right">Quantity</th>
							<th class="text-right">Amount</th>
							<th class="text-right">Items</th>
						</tr>
					</thead>
					<tbody>
		`;
		data.item_sales_by_group.forEach(function(group) {
			html += `
				<tr>
					<td><strong>${group.item_group}</strong></td>
					<td class="text-right">${format_number(group.qty)}</td>
					<td class="text-right">${format_currency(group.amount)}</td>
					<td class="text-right">${group.count}</td>
				</tr>
			`;
		});
		html += `
					</tbody>
				</table>
			</div>
		`;
	}

	// Expenses by Type
	if (data.expenses_by_type && data.expenses_by_type.length > 0) {
		html += `
			<div class="summary-section">
				<div class="section-title">Expenses by Type</div>
				<table class="summary-table">
					<thead>
						<tr>
							<th>Expense Type</th>
							<th class="text-right">Amount</th>
							<th class="text-right">Transactions</th>
						</tr>
					</thead>
					<tbody>
		`;
		data.expenses_by_type.forEach(function(expense) {
			html += `
				<tr>
					<td><strong>${expense.expense_type}</strong></td>
					<td class="text-right text-danger">${format_currency(expense.amount)}</td>
					<td class="text-right">${expense.count}</td>
				</tr>
			`;
		});
		html += `
					</tbody>
				</table>
			</div>
		`;
	}

	// Payment Summary
	if (data.payment_summary && data.payment_summary.length > 0) {
		html += `
			<div class="summary-section">
				<div class="section-title">Payment Reconciliation</div>
				<table class="summary-table">
					<thead>
						<tr>
							<th>Mode of Payment</th>
							<th class="text-right">Opening</th>
							<th class="text-right">Expected</th>
							<th class="text-right">Closing</th>
							<th class="text-right">Difference</th>
						</tr>
					</thead>
					<tbody>
		`;
		data.payment_summary.forEach(function(payment) {
			let diff_class = payment.difference < 0 ? 'text-danger' : (payment.difference > 0 ? 'text-success' : '');
			html += `
				<tr>
					<td><strong>${payment.mode_of_payment}</strong></td>
					<td class="text-right">${format_currency(payment.opening_amount)}</td>
					<td class="text-right">${format_currency(payment.expected_amount)}</td>
					<td class="text-right">${format_currency(payment.closing_amount)}</td>
					<td class="text-right ${diff_class}">${format_currency(payment.difference)}</td>
				</tr>
			`;
		});
		html += `
					</tbody>
				</table>
			</div>
		`;
	}

	// Credit Sales by Customer
	if (data.credit_sales_by_customer && data.credit_sales_by_customer.length > 0) {
		html += `
			<div class="summary-section">
				<div class="section-title">Credit Sales by Customer</div>
				<table class="summary-table">
					<thead>
						<tr>
							<th>Customer</th>
							<th class="text-right">Quantity (L)</th>
							<th class="text-right">Amount</th>
							<th class="text-right">Transactions</th>
						</tr>
					</thead>
					<tbody>
		`;
		data.credit_sales_by_customer.forEach(function(customer) {
			html += `
				<tr>
					<td><strong>${customer.customer}</strong></td>
					<td class="text-right">${format_number(customer.qty)}</td>
					<td class="text-right">${format_currency(customer.amount)}</td>
					<td class="text-right">${customer.count}</td>
				</tr>
			`;
		});
		html += `
					</tbody>
				</table>
			</div>
		`;
	}

	html += `
		</div>
	`;

	return html;
}