# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from erpnext.stock.get_item_details import get_valuation_rate
from frappe import DoesNotExistError, _
from frappe.model.document import Document
from dataclasses import dataclass
from typing import Optional

from frappe.utils import flt


class FuelLedger(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		closing_book_balance: DF.Float
		conversion_factor: DF.Float
		fuel_item: DF.Link | None
		fuel_tank: DF.Link | None
		is_cancelled: DF.Check
		liters_in: DF.Float
		liters_out: DF.Float
		opening_book_balance: DF.Float
		physical_dip_reading_liters: DF.Float
		physical_dip_reading_mm: DF.Float
		posting_date: DF.Date | None
		posting_datetime: DF.Datetime | None
		posting_time: DF.Time | None
		return_to_tank: DF.Float
		shortage_status: DF.Literal["Normal", "High Loss", "High Gain", "Loss", "Gain"]
		variation_liters: DF.Float
		variation_percentage: DF.Float
		variation_value: DF.Currency
		voucher_detail_no: DF.Data | None
		voucher_no: DF.DynamicLink | None
		voucher_type: DF.Link | None
		water_level_mm: DF.Float
	# end: auto-generated types

	def on_update(self):
		if self.has_value_changed("is_cancelled") and self.is_cancelled == 1:
			cancel_stock_reconciliation(self)


@dataclass
class FuelLedgerData:
	"""Data class for creating Fuel Ledger."""
	fuel_item: str
	fuel_tank: str
	posting_date: str
	posting_time: str
	opening_book_balance: float
	physical_dip_reading_liters: float = 0
	liters_in: float = 0
	liters_out: float = 0
	return_to_tank: Optional[float] = 0
	physical_dip_reading_mm: Optional[float] = None
	conversion_factor: Optional[float] = 1
	water_level_mm: Optional[float] = None
	posting_datetime: Optional[str] = None
	voucher_type: Optional[str] = None
	voucher_no: Optional[str] = None
	voucher_detail_no: Optional[str] = None
	shortage_status: Optional[str] = "Normal"


def create_fuel_ledger(data: FuelLedgerData):
	"""
	Create a Fuel Ledger document with calculated fields.

	Args:
		data (FuelLedgerData): Dataclass containing fuel ledger data

	Returns:
		FuelLedger: Created Fuel Ledger document

	Calculations:
		- closing_book_balance = (physical_dip_reading_liters + liters_in) - return_to_tank - liters_out
		- variation_liters = opening_book_balance - physical_dip_reading_liters
		- variation_percentage = (variation_liters / opening_book_balance) * 100 if opening_book_balance > 0
		- variation_value = valuation_rate * variation_liters
	"""
	# Calculate closing_book_balance
	closing_book_balance = (
		flt(data.opening_book_balance) + flt(data.liters_in)
	) - flt(data.liters_out) - flt(data.return_to_tank)

	variation_liters, variation_percentage, variation_value = 0, 0, 0
	shortage_status = "Normal"
	if data.physical_dip_reading_liters:
		closing_book_balance = data.physical_dip_reading_liters + flt(data.liters_in)

		# Calculate variation_liters
		variation_liters = flt(data.opening_book_balance) - flt(data.physical_dip_reading_liters) - flt(data.liters_out)

		variation_liters = variation_liters * -1

		# Calculate variation_percentage
		if data.opening_book_balance > 0:
			variation_percentage = (variation_liters / data.opening_book_balance) * 100
		else:
			variation_percentage = 0

		# Get valuation rate for the fuel item
		valuation_rate = get_item_valuation_rate(data.fuel_item, data.fuel_tank)

		# Calculate variation_value
		variation_value = valuation_rate * variation_liters

		# Set shortage_status based on variation_liters
		if variation_liters < 0:
			shortage_status = "Loss"
		elif variation_liters > 0:
			shortage_status = "Gain"
		else:
			shortage_status = data.shortage_status

	# Create the document
	fuel_ledger = frappe.get_doc({
		"doctype": "Fuel Ledger",
		"fuel_item": data.fuel_item,
		"fuel_tank": data.fuel_tank,
		"posting_date": data.posting_date,
		"posting_time": data.posting_time,
		"posting_datetime": data.posting_datetime,
		"opening_book_balance": data.opening_book_balance,
		"liters_in": data.liters_in,
		"liters_out": data.liters_out,
		"return_to_tank": data.return_to_tank,
		"closing_book_balance": closing_book_balance,
		"physical_dip_reading_mm": data.physical_dip_reading_mm,
		"conversion_factor": data.conversion_factor,
		"physical_dip_reading_liters": data.physical_dip_reading_liters,
		"water_level_mm": data.water_level_mm,
		"variation_liters": variation_liters,
		"variation_percentage": variation_percentage,
		"variation_value": variation_value,
		"shortage_status": shortage_status,
		"voucher_type": data.voucher_type,
		"voucher_no": data.voucher_no,
		"voucher_detail_no": data.voucher_detail_no
	})

	fuel_ledger.insert()

	if abs(flt(fuel_ledger.get("variation_liters"))) > 0:
		if flt(fuel_ledger.get("physical_dip_reading_liters"), 2) != flt(fuel_ledger.get("opening_book_balance"), 2):
			create_stock_reconciliation(fuel_ledger)

	return fuel_ledger


def get_item_valuation_rate(item_code: str, warehouse: str):
	"""
	Get valuation rate for an item in a specific warehouse using ERPNext utilities.

	Args:
		item_code (str): Item code
		warehouse (str): Warehouse name

	Returns:
		float: Valuation rate or 0 if not found
	"""
	if not item_code or not warehouse:
		return 0

	try:
		# Use ERPNext utility to get valuation rate
		valuation_rate = get_valuation_rate(item_code, warehouse)
		return valuation_rate.get("valuation_rate") or 0
	except Exception:
		# Fallback: Query Stock Ledger Entry for the last valuation rate
		valuation_rate = frappe.db.get_value(
			"Stock Ledger Entry",
			{
				"item_code": item_code,
				"warehouse": warehouse,
				"is_cancelled": 0
			},
			"valuation_rate",
			order_by="posting_date desc, posting_time desc"
		)
		return valuation_rate or 0


def create_stock_reconciliation(fuel_ledger: FuelLedger | Document | str):
	if isinstance(fuel_ledger, str):
		try:
			fuel_ledger = frappe.get_doc("Fuel Ledger", fuel_ledger)
		except DoesNotExistError:
			return None

	valuation_rate = get_item_valuation_rate(item_code=fuel_ledger.fuel_item, warehouse=fuel_ledger.fuel_tank)

	qty = flt(fuel_ledger.physical_dip_reading_liters)

	try:
		stock_reconciliation = frappe.get_doc({
			"doctype": "Stock Reconciliation",
			"purpose": "Stock Reconciliation",
			"posting_date": fuel_ledger.posting_date,
			"posting_time": fuel_ledger.posting_time,
			"ref_fuel_ledger": fuel_ledger.name,
			"items": [{
				"item_code": fuel_ledger.fuel_item,
				"warehouse": fuel_ledger.fuel_tank,
				"qty": qty,
				"valuation_rate": valuation_rate,
				"allow_zero_valuation_rate": 1,
				"ref_fuel_ledger": fuel_ledger.name
			}]
		})

		stock_reconciliation.flags.ignore_permissions = True
		stock_reconciliation.insert(ignore_permissions=True)
		stock_reconciliation.submit()
	except Exception as e:
		frappe.log_error(title=_("Fuel Ledger Reconciliation Error"), message=_(str(e)))
		frappe.throw(msg=_(str(e)), title=_("Stock Reconciliation Error"))
	return None

def cancel_stock_reconciliation(fuel_ledger: FuelLedger | Document):
	stock_reconciliation = frappe.db.get_value(
		"Stock Reconciliation",
		filters={"ref_fuel_ledger": fuel_ledger.name},
		fieldname=["name"]
	)

	if stock_reconciliation:
		doc = frappe.get_doc("Stock Reconciliation", stock_reconciliation)
		doc.flags.ignore_permissions = True
		if doc.docstatus == 1:
			doc.cancel()


def cancel_fuel_ledgers_by_voucher(voucher_type: str, voucher_name: str):
	"""
	Cancel all Fuel Ledger entries linked to a specific voucher.
	Marks fuel ledgers as cancelled (is_cancelled = 1) and cancels their stock reconciliations.

	Args:
		voucher_type (str): The type of voucher (e.g., "Shift Opening Entry")
		voucher_name (str): The name/ID of the voucher

	Returns:
		int: Number of Fuel Ledgers cancelled
	"""
	# Find all Fuel Ledgers linked to this voucher
	fuel_ledgers = frappe.get_all(
		"Fuel Ledger",
		filters={
			"voucher_type": voucher_type,
			"voucher_no": voucher_name,
			"is_cancelled": 0
		},
		pluck="name"
	)

	if not fuel_ledgers:
		return 0

	# Mark each ledger as cancelled
	for ledger_name in fuel_ledgers:
		ledger = frappe.get_doc("Fuel Ledger", ledger_name)
		ledger.is_cancelled = 1
		ledger.save(ignore_permissions=True)

		# cancel_stock_reconciliation is automatically called in on_update hook

	# nosemgrep Update the ledger immediately
	frappe.db.commit()

	return len(fuel_ledgers)


@frappe.whitelist()
def get_all_tanks_with_closing_balance():
	"""
	Get the latest closing_book_balance for all fuel tanks.

	Returns:
		list: List of dictionaries with tank and closing_balance
			[
				{
					"tank": "Tank-001",
					"closing_balance": 5000.50
				},
				...
			]
	"""
	# Query to get the latest closing_book_balance per tank
	query = """
		SELECT
			fl.fuel_tank as tank,
			fl.closing_book_balance as closing_balance,
			fl.fuel_item
		FROM `tabFuel Ledger` fl
		INNER JOIN (
			SELECT
				fuel_tank,
				MAX(posting_date) as max_date,
				MAX(posting_time) as max_time
			FROM `tabFuel Ledger`
			WHERE is_cancelled = 0
			GROUP BY fuel_tank
		) latest ON fl.fuel_tank = latest.fuel_tank
			AND fl.posting_date = latest.max_date
			AND fl.posting_time = latest.max_time
		WHERE fl.is_cancelled = 0
		ORDER BY fl.fuel_tank
	"""

	results = frappe.db.sql(query, as_dict=True)

	return results