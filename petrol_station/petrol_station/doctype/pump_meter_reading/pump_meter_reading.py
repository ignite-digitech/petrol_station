# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from erpnext.stock.get_item_details import get_price_list_rate
from dataclasses import dataclass
from typing import Optional


class PumpMeterReading(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		closing_qty: DF.Float
		employee: DF.Link | None
		fuel_item: DF.Link
		is_opening: DF.Check
		nozzle: DF.Link
		opening_expected: DF.Float
		physical_opening: DF.Float
		posting_date: DF.Date
		posting_time: DF.Time
		pump: DF.Link
		sales_amount: DF.Currency
		sales_qty: DF.Float
		selling_price: DF.Currency
		tank: DF.Link | None
		variation: DF.Float
		voucher_detail_no: DF.Data | None
		voucher_no: DF.DynamicLink | None
		voucher_type: DF.Link | None
	# end: auto-generated types

	pass


@dataclass
class PumpMeterReadingData:
	"""Data class for creating Pump Meter Reading."""
	pump: str
	nozzle: str
	fuel_item: str
	opening_expected: float
	physical_opening: float
	sales_qty: float
	posting_date: str
	posting_time: str
	employee: Optional[str] = None
	tank: Optional[str] = None
	voucher_type: Optional[str] = None
	voucher_no: Optional[str] = None
	voucher_detail_no: Optional[str] = None
	is_opening: int = 0


def create_pump_meter_reading(data: PumpMeterReadingData):
	"""
	Create a PumpMeterReading document with calculated fields.

	Args:
		data (PumpMeterReadingData): Dataclass containing pump meter reading data

	Returns:
		PumpMeterReading: Created PumpMeterReading document
	"""
	# Calculate variation
	variation = abs(data.opening_expected - data.physical_opening)

	# Get selling price from Item Price
	selling_price = get_selling_price(data.fuel_item)

	# Calculate sales amount
	sales_amount = data.sales_qty * selling_price

	# Calculate closing quantity
	closing_qty = data.physical_opening - data.sales_qty

	# Create the document
	pump_meter_reading = frappe.get_doc({
		"doctype": "Pump Meter Reading",
		"pump": data.pump,
		"nozzle": data.nozzle,
		"fuel_item": data.fuel_item,
		"tank": data.tank,
		"employee": data.employee,
		"posting_date": data.posting_date,
		"posting_time": data.posting_time,
		"opening_expected": data.opening_expected,
		"physical_opening": data.physical_opening,
		"sales_qty": data.sales_qty,
		"selling_price": selling_price,
		"sales_amount": sales_amount,
		"closing_qty": closing_qty,
		"variation": variation,
		"voucher_type": data.voucher_type,
		"voucher_no": data.voucher_no,
		"voucher_detail_no": data.voucher_detail_no,
		"is_opening": data.is_opening
	})

	pump_meter_reading.insert()

	return pump_meter_reading


def get_selling_price(item_code, price_list=None, customer=None):
	"""
	Get selling price for an item from Item Price.

	Args:
		item_code (str): Item code
		price_list (str, optional): Price List name. Defaults to standard selling price list.
		customer (str, optional): Customer name for customer-specific pricing

	Returns:
		float: Selling price or 0 if not found
	"""
	if not item_code:
		return 0

	# Get default price list if not provided
	if not price_list:
		price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")

	try:
		# Use ERPNext utility to get price
		price_list_rate = get_price_list_rate(item_code, price_list, customer)
		return price_list_rate or 0
	except Exception:
		# Fallback: Query Item Price directly
		price = frappe.db.get_value(
			"Item Price",
			{
				"item_code": item_code,
				"selling": 1,
				"price_list": price_list
			},
			"price_list_rate"
		)
		return price or 0


