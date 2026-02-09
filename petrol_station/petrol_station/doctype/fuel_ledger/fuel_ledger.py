# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from erpnext.stock.get_item_details import get_valuation_rate
from frappe.model.document import Document
from dataclasses import dataclass
from typing import Optional



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
		shortage_status: DF.Literal["Normal", "High Loss", "High Gain"]
		variation_liters: DF.Float
		variation_percentage: DF.Float
		variation_value: DF.Currency
		voucher_detail_no: DF.Data | None
		voucher_no: DF.DynamicLink | None
		voucher_type: DF.Link | None
		water_level_mm: DF.Float
	# end: auto-generated types

	pass


@dataclass
class FuelLedgerData:
	"""Data class for creating Fuel Ledger."""
	fuel_item: str
	fuel_tank: str
	opening_book_balance: float
	physical_dip_reading_liters: float
	posting_date: str
	posting_time: str
	liters_in: float = 0
	liters_out: float = 0
	return_to_tank: float = 0
	physical_dip_reading_mm: Optional[float] = None
	conversion_factor: Optional[float] = None
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
		data.physical_dip_reading_liters + data.liters_in
	) - data.return_to_tank - data.liters_out

	# Calculate variation_liters
	variation_liters = data.opening_book_balance - data.physical_dip_reading_liters

	# Calculate variation_percentage
	if data.opening_book_balance > 0:
		variation_percentage = (variation_liters / data.opening_book_balance) * 100
	else:
		variation_percentage = 0

	# Get valuation rate for the fuel item
	valuation_rate = get_item_valuation_rate(data.fuel_item, data.fuel_tank)

	# Calculate variation_value
	variation_value = valuation_rate * variation_liters

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
		"shortage_status": data.shortage_status,
		"voucher_type": data.voucher_type,
		"voucher_no": data.voucher_no,
		"voucher_detail_no": data.voucher_detail_no
	})

	fuel_ledger.insert()

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
