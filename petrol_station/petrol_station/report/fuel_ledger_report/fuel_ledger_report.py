# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.query_builder.functions import Sum
from frappe.utils import cint, flt, get_datetime


def execute(filters: dict | None = None):
	"""Return columns and data for the report.

	This is the main entry point for the report. It accepts the filters as a
	dictionary and should return columns and data. It is called by the framework
	every time the report is refreshed or a filter is updated.
	"""
	columns = get_columns()
	fuel_items = get_fuel_items(filters)
	fuel_ledger_entries = get_fuel_ledger_entries(filters, fuel_items)
	opening_row = get_opening_balance(filters, fuel_ledger_entries)

	precision = cint(frappe.db.get_single_value("System Settings", "float_precision"))

	data = []
	if opening_row:
		data.append(opening_row)

	# Track running balance
	closing_balance = opening_row.get("closing_book_balance", 0) if opening_row else 0

	for entry in fuel_ledger_entries:
		# Calculate balance after transaction
		closing_balance = (
			closing_balance + flt(entry.liters_in, precision)
			- flt(entry.liters_out, precision)
			+ flt(entry.return_to_tank, precision)
		)

		entry["balance_liters"] = closing_balance

		data.append(entry)

	return columns, data


def get_columns() -> list[dict]:
	"""Return columns for the report.

	Similar to Stock Ledger report structure.
	"""
	return [
		{
			"label": _("Date"),
			"fieldname": "posting_datetime",
			"fieldtype": "Datetime",
			"width": 150,
		},
		{
			"label": _("Fuel Item"),
			"fieldname": "fuel_item",
			"fieldtype": "Link",
			"options": "Item",
			"width": 120,
		},
		{
			"label": _("Fuel Tank"),
			"fieldname": "fuel_tank",
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": 150,
		},
		{
			"label": _("Liters In"),
			"fieldname": "liters_in",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Liters Out"),
			"fieldname": "liters_out",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": _("Return to Tank"),
			"fieldname": "return_to_tank",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Balance (Liters)"),
			"fieldname": "balance_liters",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Opening Balance"),
			"fieldname": "opening_book_balance",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("Physical Reading (L)"),
			"fieldname": "physical_dip_reading_liters",
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"label": _("Closing Balance"),
			"fieldname": "closing_book_balance",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("Physical Reading (mm)"),
			"fieldname": "physical_dip_reading_mm",
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"label": _("Water Level (mm)"),
			"fieldname": "water_level_mm",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": _("Variation (L)"),
			"fieldname": "variation_liters",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": _("Variation %"),
			"fieldname": "variation_percentage",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": _("Variation Value"),
			"fieldname": "variation_value",
			"fieldtype": "Currency",
			"width": 130,
		},
		{
			"label": _("Shortage Status"),
			"fieldname": "shortage_status",
			"fieldtype": "Data",
			"width": 130,
		},
		{
			"label": _("Voucher Type"),
			"fieldname": "voucher_type",
			"fieldtype": "Link",
			"options": "DocType",
			"width": 150,
		},
		{
			"label": _("Voucher #"),
			"fieldname": "voucher_no",
			"fieldtype": "Dynamic Link",
			"options": "voucher_type",
			"width": 150,
		},
		{
			"label": _("Is Cancelled"),
			"fieldname": "is_cancelled",
			"fieldtype": "Check",
			"width": 100,
		},
	]


def get_fuel_ledger_entries(filters, fuel_items):
	"""Get Fuel Ledger entries based on filters.

	Args:
		filters (dict): Report filters
		fuel_items (list): List of fuel items to filter

	Returns:
		list: List of Fuel Ledger entries
	"""
	from_date = get_datetime(filters.from_date + " 00:00:00")
	to_date = get_datetime(filters.to_date + " 23:59:59")

	fl = frappe.qb.DocType("Fuel Ledger")
	query = (
		frappe.qb.from_(fl)
		.select(
			fl.name,
			fl.posting_date,
			fl.posting_time,
			fl.posting_datetime,
			fl.fuel_item,
			fl.fuel_tank,
			fl.opening_book_balance,
			fl.liters_in,
			fl.liters_out,
			fl.return_to_tank,
			fl.closing_book_balance,
			fl.physical_dip_reading_mm,
			fl.conversion_factor,
			fl.physical_dip_reading_liters,
			fl.water_level_mm,
			fl.variation_liters,
			fl.variation_percentage,
			fl.variation_value,
			fl.shortage_status,
			fl.voucher_type,
			fl.voucher_no,
			fl.voucher_detail_no,
			fl.is_cancelled,
		)
		.where(fl.posting_datetime[from_date:to_date])
		.orderby(fl.posting_datetime)
		.orderby(fl.creation)
	)

	# Filter by cancelled status
	if not filters.get("show_cancelled"):
		query = query.where(fl.is_cancelled == 0)

	# Filter by fuel items
	if fuel_items:
		query = query.where(fl.fuel_item.isin(fuel_items))

	# Filter by fuel tanks
	if filters.get("fuel_tank"):
		query = query.where(fl.fuel_tank.isin(filters.get("fuel_tank")))

	# Filter by voucher type
	if filters.get("voucher_type"):
		query = query.where(fl.voucher_type == filters.get("voucher_type"))

	# Filter by voucher number
	if filters.get("voucher_no"):
		query = query.where(fl.voucher_no == filters.get("voucher_no"))

	return query.run(as_dict=True)


def get_fuel_items(filters):
	"""Get fuel items based on filters.

	Args:
		filters (dict): Report filters

	Returns:
		list: List of fuel item codes
	"""
	if fuel_items := filters.get("fuel_item"):
		return fuel_items

	return []


def get_opening_balance(filters, fuel_ledger_entries):
	"""Get opening balance for the report.

	Similar to Stock Ledger opening balance logic.

	Args:
		filters (dict): Report filters
		fuel_ledger_entries (list): List of Fuel Ledger entries

	Returns:
		dict: Opening balance row
	"""
	if not (filters.get("fuel_item") and filters.get("fuel_tank") and filters.get("from_date")):
		return None

	# Get the last entry before the from_date
	fl = frappe.qb.DocType("Fuel Ledger")

	# Build filter conditions
	query = (
		frappe.qb.from_(fl)
		.select(
			fl.closing_book_balance,
			fl.fuel_item,
			fl.fuel_tank,
		)
		.where(fl.posting_date < filters.from_date)
		.where(fl.is_cancelled == 0)
		.orderby(fl.posting_date, order=frappe.qb.desc)
		.orderby(fl.posting_time, order=frappe.qb.desc)
		.limit(1)
	)

	# Apply fuel item filter
	if filters.get("fuel_item"):
		query = query.where(fl.fuel_item.isin(filters.get("fuel_item")))

	# Apply fuel tank filter
	if filters.get("fuel_tank"):
		query = query.where(fl.fuel_tank.isin(filters.get("fuel_tank")))

	last_entry = query.run(as_dict=True)

	if not last_entry:
		return None

	last_entry = last_entry[0]

	return {
		"posting_datetime": filters.from_date,
		"fuel_item": _("'Opening'"),
		"fuel_tank": last_entry.get("fuel_tank"),
		"closing_book_balance": last_entry.get("closing_book_balance", 0),
		"balance_liters": last_entry.get("closing_book_balance", 0),
		"liters_in": 0,
		"liters_out": 0,
		"return_to_tank": 0,
		"opening_book_balance": 0,
	}
