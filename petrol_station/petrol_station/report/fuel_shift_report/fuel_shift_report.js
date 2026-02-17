// Copyright (c) 2026, Ignite Digital and contributors
// For license information, please see license.txt

frappe.query_reports["Fuel Shift Report"] = {
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
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
		},
		{
			fieldname: "fuel_item",
			label: __("Fuel Item"),
			fieldtype: "Link",
			options: "Item",
			get_query: function () {
				return {
					filters: { item_group: "Fuel" },
				};
			},
		},
	],
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (!data) return value;

		// Highlight negative variations in red
		if (column.fieldname === "variation" && data.variation) {
			if (data.variation < 0) {
				value = "<span style='color:red; font-weight:bold'>" + value + "</span>";
			} else if (data.variation > 0) {
				value = "<span style='color:orange'>" + value + "</span>";
			}
		}

		// Highlight payment shortage
		if (column.fieldname === "payment_shortage" && data.payment_shortage) {
			if (data.payment_shortage > 0) {
				value = "<span style='color:red; font-weight:bold'>" + value + "</span>";
			} else if (data.payment_shortage < 0) {
				value = "<span style='color:green'>" + value + "</span>";
			}
		}

		return value;
	},
};
