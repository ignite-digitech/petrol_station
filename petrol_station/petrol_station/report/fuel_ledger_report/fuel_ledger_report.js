// Copyright (c) 2026, Ignite Digital and contributors
// For license information, please see license.txt

frappe.query_reports["Fuel Ledger Report"] = {
	filters: [
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1,
		},
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1,
		},
		{
			fieldname: "fuel_tank",
			label: __("Fuel Tanks"),
			fieldtype: "MultiSelectList",
			options: "Warehouse",
			get_data: function (txt) {
				return frappe.db.get_link_options("Warehouse", txt, {
					warehouse_type: "Fuel Tank",
					is_group: 0
				});
			},
		},
		{
			fieldname: "fuel_item",
			label: __("Fuel Items"),
			fieldtype: "MultiSelectList",
			options: "Item",
			get_data: async function (txt) {
				let { message: data } = await frappe.call({
					method: "frappe.desk.search.search_link",
					args: {
						doctype: "Item",
						txt: txt,
						page_length: 10,
					},
				});
				data = data.map(({ value, description }) => {
					return {
						value: value,
						description: description,
					};
				});

				return data || [];
			},
		},
		{
			fieldname: "voucher_type",
			label: __("Voucher Type"),
			fieldtype: "Link",
			options: "DocType",
		},
		{
			fieldname: "voucher_no",
			label: __("Voucher #"),
			fieldtype: "Data",
		},
		{
			fieldname: "show_cancelled",
			label: __("Show Cancelled"),
			fieldtype: "Check",
			default: 0,
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		// Highlight positive and negative values
		if (column.fieldname == "liters_out" && data && data.liters_out < 0) {
			value = "<span style='color:red'>" + value + "</span>";
		} else if (column.fieldname == "liters_in" && data && data.liters_in > 0) {
			value = "<span style='color:green'>" + value + "</span>";
		}

		// Highlight variations
		if (column.fieldname == "variation_liters" && data && data.variation_liters) {
			if (data.variation_liters > 0) {
				value = "<span style='color:orange'>" + value + "</span>";
			} else if (data.variation_liters < 0) {
				value = "<span style='color:red'>" + value + "</span>";
			}
		}

		// Highlight shortage status
		if (column.fieldname == "shortage_status" && data) {
			if (data.shortage_status === "High Loss") {
				value = "<span style='color:red; font-weight:bold'>" + value + "</span>";
			} else if (data.shortage_status === "High Gain") {
				value = "<span style='color:orange; font-weight:bold'>" + value + "</span>";
			}
		}

		return value;
	},
};
