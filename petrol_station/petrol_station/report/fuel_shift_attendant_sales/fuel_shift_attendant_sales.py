# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters: dict | None = None):
	"""Return columns and data for the Fuel Shift Attendant Sales report.

	Shows sales per attendant per shift, with a credit balance column
	from the Shift Credit Sale child table.
	"""
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns() -> list[dict]:
	"""Return columns for the report."""
	return [
		# ── Shift Info ──
		{
			"label": _("Date"),
			"fieldname": "posting_date",
			"fieldtype": "Date",
			"width": 110,
		},
		{
			"label": _("Shift Closing Entry"),
			"fieldname": "shift_closing_entry",
			"fieldtype": "Link",
			"options": "Shift Closing Entry",
			"width": 180,
		},
		# ── Attendant ──
		{
			"label": _("Attendant"),
			"fieldname": "attendant",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 140,
		},
		{
			"label": _("Attendant Name"),
			"fieldname": "attendant_name",
			"fieldtype": "Data",
			"width": 160,
		},
		# ── Sales ──
		{
			"label": _("Fuel Item"),
			"fieldname": "fuel_item",
			"fieldtype": "Link",
			"options": "Item",
			"width": 130,
		},
		{
			"label": _("Sales Qty (L)"),
			"fieldname": "sales_qty",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": _("Sales Amount"),
			"fieldname": "sales_amount",
			"fieldtype": "Currency",
			"width": 130,
		},
		# ── Credit Balance ──
		{
			"label": _("Credit Balance"),
			"fieldname": "credit_balance",
			"fieldtype": "Currency",
			"width": 140,
		},
	]


def get_data(filters) -> list[dict]:
	"""Build report data from Shift Closing Entry child tables."""
	conditions = get_conditions(filters)

	# 1) Fetch submitted Shift Closing Entries in the date range
	shift_entries = frappe.db.sql(
		"""
		SELECT
			sce.name,
			sce.posting_date
		FROM `tabShift Closing Entry` sce
		WHERE sce.docstatus = 1
			{conditions}
		ORDER BY sce.posting_date, sce.name
		""".format(conditions=conditions),
		filters,
		as_dict=True,
	)

	if not shift_entries:
		return []

	entry_names = [e.name for e in shift_entries]

	# 2) Meter sales grouped by (parent, attendant, fuel_item)
	meter_sales = frappe.db.sql(
		"""
		SELECT
			cmr.parent,
			cmr.attendant,
			cmr.fuel_item,
			SUM(cmr.sales_qty) AS sales_qty,
			SUM(cmr.total_amount) AS sales_amount
		FROM `tabClosing Meter Reading` cmr
		WHERE cmr.parent IN %(entries)s
		GROUP BY cmr.parent, cmr.attendant, cmr.fuel_item
		ORDER BY cmr.parent, cmr.attendant, cmr.fuel_item
		""",
		{"entries": entry_names},
		as_dict=True,
	)

	# 3) Credit sales grouped by (parent, attendant)
	credit_sales = frappe.db.sql(
		"""
		SELECT
			scs.parent,
			scs.attendant,
			SUM(scs.amount) AS credit_balance
		FROM `tabShift Credit Sale` scs
		WHERE scs.parent IN %(entries)s
		GROUP BY scs.parent, scs.attendant
		""",
		{"entries": entry_names},
		as_dict=True,
	)

	# ── Index data ──
	entries_by_name = {e.name: e for e in shift_entries}

	# meter sales by (parent, attendant) → list of per-fuel-item rows
	sales_by_key = {}
	for row in meter_sales:
		key = (row.parent, row.attendant)
		sales_by_key.setdefault(key, []).append(row)

	# credit balance by (parent, attendant) → total amount
	credit_by_key = {}
	for row in credit_sales:
		credit_by_key[(row.parent, row.attendant)] = flt(row.credit_balance)

	# 4) Collect all unique attendant IDs for name lookup
	attendant_ids = set()
	for row in meter_sales:
		if row.attendant:
			attendant_ids.add(row.attendant)
	for row in credit_sales:
		if row.attendant:
			attendant_ids.add(row.attendant)

	attendant_names = {}
	if attendant_ids:
		for emp in frappe.get_all(
			"Employee",
			filters={"name": ("in", list(attendant_ids))},
			fields=["name", "employee_name"],
		):
			attendant_names[emp.name] = emp.employee_name

	# 5) Build all (parent, attendant) keys — union from meter sales and credit sales
	all_keys = set(sales_by_key.keys()) | set(credit_by_key.keys())

	# Apply attendant filter if provided
	if filters and filters.get("attendant"):
		all_keys = {k for k in all_keys if k[1] == filters.get("attendant")}

	# Sort by posting_date then entry name then attendant
	sorted_keys = sorted(
		all_keys,
		key=lambda k: (entries_by_name[k[0]].posting_date, k[0], k[1] or ""),
	)

	# 6) Build rows
	data = []
	for parent, attendant in sorted_keys:
		entry = entries_by_name[parent]
		fuel_rows = sales_by_key.get((parent, attendant), [])
		credit = credit_by_key.get((parent, attendant), 0)

		if fuel_rows:
			# One row per fuel item; credit balance shown once on first row
			is_first = True
			for fr in fuel_rows:
				row = {
					"posting_date": entry.posting_date,
					"shift_closing_entry": entry.name,
					"attendant": attendant,
					"attendant_name": attendant_names.get(attendant, ""),
					"fuel_item": fr.fuel_item,
					"sales_qty": flt(fr.sales_qty),
					"sales_amount": flt(fr.sales_amount),
				}
				if is_first:
					row["credit_balance"] = credit
					is_first = False
				data.append(row)
		else:
			# Attendant has credit sales but no meter readings
			data.append({
				"posting_date": entry.posting_date,
				"shift_closing_entry": entry.name,
				"attendant": attendant,
				"attendant_name": attendant_names.get(attendant, ""),
				"credit_balance": credit,
			})

	return data


def get_conditions(filters) -> str:
	"""Build SQL WHERE clause fragments from filters."""
	conditions = []

	if filters.get("from_date"):
		conditions.append("AND sce.posting_date >= %(from_date)s")

	if filters.get("to_date"):
		conditions.append("AND sce.posting_date <= %(to_date)s")

	if filters.get("company"):
		conditions.append("AND sce.company = %(company)s")

	if filters.get("shift_closing_entry"):
		conditions.append("AND sce.name = %(shift_closing_entry)s")

	if filters.get("fuel_item"):
		conditions.append(
			"AND sce.name IN ("
			"  SELECT DISTINCT cmr2.parent"
			"  FROM `tabClosing Meter Reading` cmr2"
			"  WHERE cmr2.fuel_item = %(fuel_item)s"
			")"
		)

	return "\n".join(conditions)
