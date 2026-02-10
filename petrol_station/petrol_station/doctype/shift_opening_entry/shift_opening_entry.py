# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today
from petrol_station.petrol_station.doctype.tank_dip_log.tank_dip_log import get_tank_dip_logs_by_date
from petrol_station.petrol_station.doctype.pump_meter_reading.pump_meter_reading import (
	create_pump_meter_reading,
	PumpMeterReadingData
)


class ShiftOpeningEntry(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from erpnext.accounts.doctype.pos_opening_entry_detail.pos_opening_entry_detail import POSOpeningEntryDetail
		from frappe.types import DF
		from petrol_station.petrol_station.doctype.fuel_delivery.fuel_delivery import FuelDelivery
		from petrol_station.petrol_station.doctype.shift_opening_fuel_price.shift_opening_fuel_price import ShiftOpeningFuelPrice
		from petrol_station.petrol_station.doctype.shift_opening_meter_reading.shift_opening_meter_reading import ShiftOpeningMeterReading

		amended_from: DF.Link | None
		company: DF.Link
		deliveries: DF.Table[FuelDelivery]
		opening_balances: DF.Table[POSOpeningEntryDetail]
		opening_meter_readings: DF.Table[ShiftOpeningMeterReading]
		posting_date: DF.Date
		posting_datetime: DF.Datetime
		posting_time: DF.Time
		selling_prices: DF.Table[ShiftOpeningFuelPrice]
		shift_type: DF.Literal["Day", "Night"]
		status: DF.Literal["Draft", "Open", "Closed", "Cancelled"]
		supervisor: DF.Link
	# end: auto-generated types

	def onload(self):
		pass
		# date = today()
		# if self.posting_date:
		# 	date = self.posting_date
		#
		# try:
		# 	tank_reading = get_tank_dip_logs_by_date(date)
		# 	self.dip_readings = []
		# 	for tank in tank_reading:
		# 		self.append("dip_readings", {
		# 			"tank": tank.get("tank"),
		# 			"dip_log_id": tank.get("name"),
		# 			"opening_reading": tank.get("opening_dip"),
		# 			"physical_reading": tank.get("physical_liters")
		# 		})
		#
		# except Exception as e:
		# 	frappe.log_error(title="Error in fetching tank dip logs", message=e)

	def on_submit(self):
		self.status = "Open"
		self.create_pump_meter_readings_from_opening_readings()
		self.create_purchase_receipts_from_deliveries()

	def validate(self):
		self.validate_dip_logs_existence()

	def on_cancel(self):
		self.cancel_pump_meter_readings()
		self.cancel_purchase_receipts()

	def validate_dip_logs_existence(self):
		tank_readings = get_tank_dip_logs_by_date(self.posting_date)
		if not tank_readings or len(tank_readings) == 0:
			frappe.throw("No tank dip logs found for the selected date")

	def create_pump_meter_readings_from_opening_readings(self):
		"""
		Create Pump Meter Reading documents from opening_meter_readings table.
		Validates that opening_meter_readings exist before creating.

		Returns:
			list: List of created Pump Meter Reading documents

		Raises:
			frappe.ValidationError: If no opening meter readings exist
		"""
		if not self.opening_meter_readings:
			frappe.throw(
				"No opening meter readings found to create Pump Meter Readings.",
				frappe.ValidationError
			)

		created_readings = []

		for reading in self.opening_meter_readings:
			# Get pump and fuel item from nozzle
			nozzle_doc = frappe.get_doc("Pump Nozzle", reading.nozzle)
			pump = nozzle_doc.pump

			# Get fuel item and tank from pump
			pump_doc = frappe.get_doc("Fuel Pump", pump)
			fuel_item = pump_doc.fuel_item
			tank = reading.tank or pump_doc.tank

			# Create PumpMeterReadingData dataclass instance
			reading_data = PumpMeterReadingData(
				pump=pump,
				nozzle=reading.nozzle,
				fuel_item=fuel_item,
				opening_expected=reading.expected_reading or 0,
				physical_opening=reading.opening_reading,
				sales_qty=0,  # Opening reading, no sales yet
				posting_date=self.posting_date,
				posting_time=self.posting_time,
				employee=self.supervisor or self.attendant,
				tank=tank,
				voucher_type="Shift Opening Entry",
				voucher_no=self.name,
				voucher_detail_no=reading.name
			)

			# Create the Pump Meter Reading
			pump_meter_reading = create_pump_meter_reading(reading_data)
			created_readings.append(pump_meter_reading)

		return created_readings

	def cancel_pump_meter_readings(self):
		"""
		Mark all Pump Meter Readings linked to this Shift Opening Entry as cancelled.
		Sets is_cancelled = 1 for all related Pump Meter Readings.

		Returns:
			int: Number of Pump Meter Readings marked as cancelled
		"""
		# Find all Pump Meter Readings linked to this Shift Opening Entry
		pump_meter_readings = frappe.get_all(
			"Pump Meter Reading",
			filters={
				"voucher_type": "Shift Opening Entry",
				"voucher_no": self.name,
				"is_cancelled": 0
			},
			pluck="name"
		)

		if not pump_meter_readings:
			return 0

		# Mark each reading as cancelled
		for reading_name in pump_meter_readings:
			frappe.db.set_value("Pump Meter Reading", reading_name, "is_cancelled", 1)

		frappe.db.commit()

		return len(pump_meter_readings)

	def create_purchase_receipts_from_deliveries(self):
		"""
		Create Purchase Receipt documents from deliveries table.
		Each delivery row creates a Purchase Receipt Item with the tank as warehouse
		and opening_shift reference.

		Returns:
			list: List of created Purchase Receipt documents
		"""
		if not self.deliveries:
			return []

		# Group deliveries by supplier
		supplier_deliveries = {}
		for delivery in self.deliveries:
			if delivery.supplier not in supplier_deliveries:
				supplier_deliveries[delivery.supplier] = []
			supplier_deliveries[delivery.supplier].append(delivery)

		created_receipts = []

		for supplier, deliveries in supplier_deliveries.items():
			# Create Purchase Receipt for each supplier
			pr = frappe.new_doc("Purchase Receipt")
			pr.supplier = supplier
			pr.posting_date = self.posting_date
			pr.posting_time = self.posting_time
			pr.set_posting_time = 1

			# Add items from deliveries
			for delivery in deliveries:
				pr.append("items", {
					"item_code": delivery.fuel_item,
					"qty": delivery.qty,
					"rate": delivery.rate,
					"warehouse": delivery.tank,
					"opening_shift": self.name
				})

			pr.insert()
			pr.submit()
			created_receipts.append(pr)

		return created_receipts

	def cancel_purchase_receipts(self):
		"""
		Cancel all Purchase Receipts linked to this Shift Opening Entry.
		Finds and cancels all Purchase Receipts with items referencing this opening shift.

		Returns:
			int: Number of Purchase Receipts cancelled
		"""
		# Find all Purchase Receipt Items linked to this Shift Opening Entry
		pr_items = frappe.get_all(
			"Purchase Receipt Item",
			filters={
				"opening_shift": self.name,
				"docstatus": 1
			},
			fields=["parent"],
			distinct=True
		)

		if not pr_items:
			return 0

		# Get unique Purchase Receipt names
		pr_names = list(set([item.parent for item in pr_items]))

		# Cancel each Purchase Receipt
		for pr_name in pr_names:
			pr = frappe.get_doc("Purchase Receipt", pr_name)
			if pr.docstatus == 1:
				pr.cancel()

		return len(pr_names)


@frappe.whitelist()
def get_item_price_from_shift(item_code, shift_opening_entry=None, posting_date=None):
	"""
	Get item price from Shift Opening Entry's selling prices list.
	Falls back to the latest Item Price if not found in shift.

	Args:
		item_code (str): Item code
		shift_opening_entry (str, optional): Shift Opening Entry name
		posting_date (str, optional): Posting date for finding active shift

	Returns:
		dict: Contains price and source information
			{
				"price": float,
				"source": "Shift Opening Entry" | "Item Price",
				"shift_name": str (if from shift)
			}
	"""
	price_info = {
		"price": 0,
		"source": None,
		"shift_name": None
	}

	if not item_code:
		return price_info

	# Try to get price from Shift Opening Entry
	if shift_opening_entry:
		# Get price from specific shift
		price = get_price_from_shift_entry(shift_opening_entry, item_code)
		if price:
			price_info["price"] = price
			price_info["source"] = "Shift Opening Entry"
			price_info["shift_name"] = shift_opening_entry
			return price_info

	elif posting_date:
		# Find active shift for the posting date
		active_shift = get_active_shift_for_date(posting_date)
		if active_shift:
			price = get_price_from_shift_entry(active_shift, item_code)
			if price:
				price_info["price"] = price
				price_info["source"] = "Shift Opening Entry"
				price_info["shift_name"] = active_shift
				return price_info

	# Fallback to latest Item Price
	from petrol_station.petrol_station.doctype.pump_meter_reading.pump_meter_reading import get_selling_price

	price = get_selling_price(item_code)
	if price:
		price_info["price"] = price
		price_info["source"] = "Item Price"

	return price_info


def get_price_from_shift_entry(shift_name, item_code):
	"""
	Get price for an item from a specific Shift Opening Entry's selling prices.

	Args:
		shift_name (str): Shift Opening Entry name
		item_code (str): Item code

	Returns:
		float: Price or None if not found
	"""
	price = frappe.db.get_value(
		"Shift Opening Fuel Price",
		{
			"parent": shift_name,
			"parenttype": "Shift Opening Entry",
			"fuel_item": item_code
		},
		"rate"
	)

	return price


def get_active_shift_for_date(posting_date):
	"""
	Get the active (Open) Shift Opening Entry for a given date.

	Args:
		posting_date (str): Date to find active shift

	Returns:
		str: Shift Opening Entry name or None
	"""
	shift = frappe.db.get_value(
		"Shift Opening Entry",
		{
			"posting_date": posting_date,
			"docstatus": 1,
			"status": "Open"
		},
		"name",
		order_by="posting_datetime desc"
	)

	return shift


@frappe.whitelist()
def get_opening_balances_with_expected(shift_opening_entry, total_sales=None, payments=None, credit_sales=None):
	"""
	Get opening balances from Shift Opening Entry with optional expected cash calculation.

	Args:
		shift_opening_entry (str): Shift Opening Entry name
		total_sales (float, optional): Total sales amount for calculating expected cash
		payments (dict/str, optional): Dictionary of other payment modes and amounts
			Example: {"mtn": 1000, "airtel": 1200, "credit": 6000}

	Returns:
		list: Opening balances with additional 'expected' field for cash
			[
				{
					"mode_of_payment": "Cash",
					"opening_amount": 5000.00,
					"expected": 8800.00  # Only for cash if total_sales provided
				},
				{
					"mode_of_payment": "MTN Mobile Money",
					"opening_amount": 0.00
				}
			]
	"""
	from frappe.utils import flt
	import json

	if credit_sales is None:
		credit_sales = 0

	if not shift_opening_entry:
		frappe.throw("Shift Opening Entry is required")

	# Parse payments if it's a JSON string
	if payments and isinstance(payments, str):
		payments = json.loads(payments)

	# Fetch the shift document
	shift_doc = frappe.get_doc("Shift Opening Entry", shift_opening_entry)

	if not shift_doc.opening_balances:
		return []

	# Convert opening balances to list of dicts
	balances = []
	for balance in shift_doc.opening_balances:
		balance_dict = {
			"mode_of_payment": balance.mode_of_payment,
			"opening_amount": flt(balance.opening_amount)
		}

		# Calculate expected cash if total_sales is provided
		if total_sales and payments:
			# Check if this is a cash mode of payment
			mode_lower = balance.mode_of_payment.lower()
			if "cash" in mode_lower:
				# Calculate expected cash
				# expected_cash = total_sales - sum(all other payments)
				total_other_payments = sum(flt(amount) for amount in payments.values())
				expected_cash = flt(total_sales) - total_other_payments - flt(credit_sales)

				balance_dict["expected"] = expected_cash

		if total_sales and payments == {}:
			balance_dict["expected"] = flt(total_sales) - flt(credit_sales)

		balances.append(balance_dict)

		return balances


@frappe.whitelist()
def get_opening_balances(shift_opening_entry):
	"""
	Simple method to get opening balances from Shift Opening Entry.

	Args:
		shift_opening_entry (str): Shift Opening Entry name

	Returns:
		list: Opening balances
			[
				{
					"mode_of_payment": "Cash",
					"opening_amount": 5000.00
				}
			]
	"""
	return get_opening_balances_with_expected(shift_opening_entry)


