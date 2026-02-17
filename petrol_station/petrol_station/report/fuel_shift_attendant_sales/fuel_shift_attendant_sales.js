// Copyright (c) 2026, Ignite Digital and contributors
// For license information, please see license.txt

frappe.query_reports["Fuel Shift Attendant Sales"] = {
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
			fieldname: "shift_closing_entry",
			label: __("Shift Closing Entry"),
			fieldtype: "Link",
			options: "Shift Closing Entry",
		},
		{
			fieldname: "attendant",
			label: __("Attendant"),
			fieldtype: "Link",
			options: "Employee",
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
};
