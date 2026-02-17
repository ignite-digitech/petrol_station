# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt


def execute(filters: dict | None = None):
	"""Return columns and data for the Fuel Shift Report.

	This report aggregates shift closing data to show:
	  - Sales per pump/nozzle
	  - Sales per fuel item
	  - Tank dip variations
	  - Payment shortages
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
		{
			"label": _("Supervisor"),
			"fieldname": "supervisor",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 140,
		},
		# ── Sales per Pump ──
		{
			"label": _("Pump Nozzle"),
			"fieldname": "nozzle",
			"fieldtype": "Link",
			"options": "Pump Nozzle",
			"width": 130,
		},
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
		# ── Total Sales per Fuel Item ──
		{
			"label": _("Fuel Item Total Qty (L)"),
			"fieldname": "fuel_item_total_qty",
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"label": _("Fuel Item Total Sales"),
			"fieldname": "fuel_item_total_sales",
			"fieldtype": "Currency",
			"width": 150,
		},
		# ── Tank Variations ──
		{
			"label": _("Tank"),
			"fieldname": "tank",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 140,
		},
		{
			"label": _("Book Stock (L)"),
			"fieldname": "book_stock",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Physical Dip (L)"),
			"fieldname": "physical_liters",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("Variation (L)"),
			"fieldname": "variation",
			"fieldtype": "Float",
			"width": 110,
		},
		# ── Payment Shortage ──
		{
			"label": _("Total Meter Sales"),
			"fieldname": "total_meter_sales",
			"fieldtype": "Currency",
			"width": 140,
		},
		{
			"label": _("Total Payments Received"),
			"fieldname": "total_payments_received",
			"fieldtype": "Currency",
			"width": 170,
		},
		{
			"label": _("Payment Shortage"),
			"fieldname": "payment_shortage",
			"fieldtype": "Currency",
			"width": 140,
		},
	]


def get_data(filters) -> list[dict]:
	"""Build report data from Shift Closing Entry and its child tables."""
	conditions = get_conditions(filters)

	# 1) Fetch submitted Shift Closing Entries in the date range
	shift_entries = frappe.db.sql(
		"""
		SELECT
			sce.name,
			sce.posting_date,
			sce.supervisor,
			sce.total_meter_sales,
			sce.total_credit_sales
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

	# 2) Closing Meter Readings (sales per nozzle)
	meter_readings = frappe.db.sql(
		"""
		SELECT
			cmr.parent,
			cmr.nozzle,
			cmr.fuel_item,
			cmr.sales_qty,
			cmr.total_amount,
			cmr.tank
		FROM `tabClosing Meter Reading` cmr
		WHERE cmr.parent IN %(entries)s
		ORDER BY cmr.parent, cmr.idx
		""",
		{"entries": entry_names},
		as_dict=True,
	)

	# 3) Shift Tank Dips (tank variations)
	tank_dips = frappe.db.sql(
		"""
		SELECT
			std.parent,
			std.tank,
			std.fuel_item,
			std.book_stock,
			std.physical_liters,
			std.variation
		FROM `tabShift Tank Dip` std
		WHERE std.parent IN %(entries)s
		ORDER BY std.parent, std.idx
		""",
		{"entries": entry_names},
		as_dict=True,
	)

	# 4) Payment Reconciliation (sum of payments per shift)
	payments = frappe.db.sql(
		"""
		SELECT
			pcd.parent,
			SUM(pcd.closing_amount) AS total_collected
		FROM `tabPOS Closing Entry Detail` pcd
		WHERE pcd.parent IN %(entries)s
		GROUP BY pcd.parent
		""",
		{"entries": entry_names},
		as_dict=True,
	)

	# ── Index helper data by parent ──
	readings_by_parent = {}
	for r in meter_readings:
		readings_by_parent.setdefault(r.parent, []).append(r)

	dips_by_parent = {}
	for d in tank_dips:
		dips_by_parent.setdefault(d.parent, []).append(d)

	payments_by_parent = {p.parent: flt(p.total_collected) for p in payments}

	# ── Aggregate sales per fuel item per shift ──
	fuel_item_totals_by_parent = {}
	for r in meter_readings:
		key = (r.parent, r.fuel_item)
		if key not in fuel_item_totals_by_parent:
			fuel_item_totals_by_parent[key] = {"qty": 0, "amount": 0}
		fuel_item_totals_by_parent[key]["qty"] += flt(r.sales_qty)
		fuel_item_totals_by_parent[key]["amount"] += flt(r.total_amount)

	# ── Index tank dips by (parent, tank) for dedup ──
	dip_by_key = {}
	for d in tank_dips:
		dip_by_key[(d.parent, d.tank)] = d

	# ── Build rows ──
	data = []
	for entry in shift_entries:
		readings = readings_by_parent.get(entry.name, [])
		total_payments = payments_by_parent.get(entry.name, 0)
		expected_revenue = flt(entry.total_meter_sales) + flt(entry.total_credit_sales)
		shortage = flt(expected_revenue) - flt(total_payments)

		# Track which fuel items and tanks we've already shown for this shift
		shown_fuel_items = set()
		shown_tanks = set()
		is_first_row = True

		if not readings:
			# No meter readings — still show shift-level info
			dips = dips_by_parent.get(entry.name, [])
			row = {
				"posting_date": entry.posting_date,
				"shift_closing_entry": entry.name,
				"supervisor": entry.supervisor,
				"total_meter_sales": entry.total_meter_sales,
				"total_payments_received": total_payments,
				"payment_shortage": shortage,
			}
			if dips:
				d = dips[0]
				row.update({
					"tank": d.tank,
					"book_stock": d.book_stock,
					"physical_liters": d.physical_liters,
					"variation": d.variation,
				})
			data.append(row)
			continue

		for r in readings:
			row = {}

			# Show shift info only on first row per entry
			if is_first_row:
				row["posting_date"] = entry.posting_date
				row["shift_closing_entry"] = entry.name
				row["supervisor"] = entry.supervisor
				row["total_meter_sales"] = entry.total_meter_sales
				row["total_payments_received"] = total_payments
				row["payment_shortage"] = shortage
				is_first_row = False

			# Per-nozzle sales
			row["nozzle"] = r.nozzle
			row["fuel_item"] = r.fuel_item
			row["sales_qty"] = r.sales_qty
			row["sales_amount"] = r.total_amount

			# Fuel item totals (show once per fuel item per shift)
			fi_key = (entry.name, r.fuel_item)
			if r.fuel_item and fi_key not in shown_fuel_items:
				totals = fuel_item_totals_by_parent.get(fi_key, {})
				row["fuel_item_total_qty"] = totals.get("qty", 0)
				row["fuel_item_total_sales"] = totals.get("amount", 0)
				shown_fuel_items.add(fi_key)

			# Tank variation (show once per tank per shift)
			tank_key = (entry.name, r.tank)
			if r.tank and tank_key not in shown_tanks:
				dip = dip_by_key.get(tank_key)
				if dip:
					row["tank"] = dip.tank
					row["book_stock"] = dip.book_stock
					row["physical_liters"] = dip.physical_liters
					row["variation"] = dip.variation
				shown_tanks.add(tank_key)

			data.append(row)

		# Remaining tank dips not associated with any meter reading tank
		for d in dips_by_parent.get(entry.name, []):
			if (entry.name, d.tank) not in shown_tanks:
				data.append({
					"tank": d.tank,
					"book_stock": d.book_stock,
					"physical_liters": d.physical_liters,
					"variation": d.variation,
				})
				shown_tanks.add((entry.name, d.tank))

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

	if filters.get("fuel_item"):
		conditions.append(
			"AND sce.name IN ("
			"  SELECT DISTINCT cmr2.parent"
			"  FROM `tabClosing Meter Reading` cmr2"
			"  WHERE cmr2.fuel_item = %(fuel_item)s"
			")"
		)

	return "\n".join(conditions)
