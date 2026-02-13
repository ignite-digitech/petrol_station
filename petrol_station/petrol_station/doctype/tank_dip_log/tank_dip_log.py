# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate, nowtime, get_datetime
from petrol_station.petrol_station.doctype.fuel_ledger.fuel_ledger import create_fuel_ledger, FuelLedgerData, \
	cancel_fuel_ledgers_by_voucher


class TankDipLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from petrol_station.petrol_station.doctype.fuel_delivery.fuel_delivery import FuelDelivery

		amended_from: DF.Link | None
		conversion_factor: DF.Float
		deliveries: DF.Table[FuelDelivery]
		employee: DF.Link | None
		fuel_item: DF.Link
		opening_dip: DF.Float
		physical_dip_reading_mm: DF.Float
		physical_liters: DF.Float
		posting_date: DF.Date
		posting_datetime: DF.Datetime | None
		posting_time: DF.Time | None
		stock_in: DF.Float
		tank: DF.Link
		water_level_mm: DF.Float
	# end: auto-generated types

	def validate(self):
		"""Validate the document before saving."""
		self.set_opening_dip()
		self.validate_posting_date()
		self.calculate_stock_in()

	def set_opening_dip(self):
		"""Set opening_dip from last closing_book_balance."""
		if not self.opening_dip:
			self.opening_dip = get_last_closing_book_balance(self.tank)

	def validate_posting_date(self):
		"""Validate that posting date is not in the future."""
		if self.posting_date and getdate(self.posting_date) > getdate(today()):
			frappe.throw("Posting Date cannot be a future date")

	def calculate_stock_in(self):
		"""Calculate total stock_in from deliveries table."""
		total_stock_in = 0
		if self.deliveries:
			for delivery in self.deliveries:
				if delivery.qty:
					total_stock_in += delivery.qty
		self.stock_in = total_stock_in

	def on_submit(self):
		from petrol_station.utils.deliveries import create_purchase_receipts_from_deliveries
		"""Create Fuel Ledger entry, Stock Entry, and Stock Reconciliation on submit."""
		self.create_fuel_ledger_entry()
		create_purchase_receipts_from_deliveries(doc=self, ignore_create_fuel_ledger=True)

	def on_cancel(self):
		from petrol_station.utils.deliveries import cancel_purchase_receipts
		"""Cancel related Fuel Ledger entry, Stock Entry, and Stock Reconciliation on cancel."""
		cancel_fuel_ledgers_by_voucher(voucher_type=self.doctype, voucher_name=self.name)
		cancel_purchase_receipts(doc=self)

	def create_fuel_ledger_entry(self):
		"""
		Create a Fuel Ledger entry from this Tank Dip Log.

		Returns:
			FuelLedger: Created Fuel Ledger document
		"""
		data = FuelLedgerData(
			fuel_item=self.fuel_item,
			fuel_tank=self.tank,
			opening_book_balance=self.opening_dip,
			physical_dip_reading_liters=self.physical_liters,
			posting_date=today(),
			posting_time=nowtime(),
			liters_in=self.stock_in,
			physical_dip_reading_mm=self.physical_dip_reading_mm,
			conversion_factor=self.conversion_factor,
			water_level_mm=self.water_level_mm,
			posting_datetime=get_datetime(),
			shortage_status="Normal",
			voucher_type="Tank Dip Log",
			voucher_no=self.name
		)

		return create_fuel_ledger(data)


@frappe.whitelist()
def get_last_closing_book_balance(tank: str):
	"""
	Fetch the last closing_book_balance for the tank from Fuel Ledger.

	Returns:
		float: Last closing book balance or 0 if not found
	"""
	last_balance = frappe.db.get_value(
		"Fuel Ledger",
		{
			"fuel_tank": tank,
			"is_cancelled": 0,
			"closing_book_balance": [">", 0]
		},
		"closing_book_balance",
		order_by="posting_date desc, posting_time desc"
	)

	return last_balance or 0


@frappe.whitelist()
def get_tank_dip_logs_by_date(date=None) -> list:
	"""
	Get all Tank Dip Logs created on a particular day.

	Args:
		date (str, optional): Date in YYYY-MM-DD format. Defaults to current date.

	Returns:
		list: List of Tank Dip Log documents
	"""
	if not date:
		date = today()

	tank_dip_logs = frappe.get_all(
		"Tank Dip Log",
		filters={"posting_date": date},
		fields=["*"],
		order_by="posting_time desc"
	)

	return tank_dip_logs


