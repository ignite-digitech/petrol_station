# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, getdate
from petrol_station.petrol_station.doctype.fuel_ledger.fuel_ledger import create_fuel_ledger, FuelLedgerData, \
	get_item_valuation_rate


class TankDipLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		conversion_factor: DF.Float
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

	def set_opening_dip(self):
		"""Set opening_dip from last closing_book_balance."""
		if not self.opening_dip:
			self.opening_dip = self.get_last_closing_book_balance()

	def validate_posting_date(self):
		"""Validate that posting date is not in the future."""
		if self.posting_date and getdate(self.posting_date) > getdate(today()):
			frappe.throw("Posting Date cannot be a future date")

	def on_submit(self):
		"""Create Fuel Ledger entry, Stock Entry, and Stock Reconciliation on submit."""
		self.create_fuel_ledger_entry()
		if self.stock_in and self.stock_in > 0:
			self.create_stock_entry()
		if abs(self.opening_dip - self.physical_liters) > 0:
			self.create_stock_reconciliation()

	def on_cancel(self):
		"""Cancel related Fuel Ledger entry, Stock Entry, and Stock Reconciliation on cancel."""
		self.cancel_fuel_ledger_entry()
		self.cancel_stock_entry()
		self.cancel_stock_reconciliation()

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
			posting_date=self.posting_date,
			posting_time=self.posting_time,
			liters_in=self.stock_in,
			physical_dip_reading_mm=self.physical_dip_reading_mm,
			conversion_factor=self.conversion_factor,
			water_level_mm=self.water_level_mm,
			posting_datetime=self.posting_datetime,
			shortage_status="Normal",
			voucher_type="Tank Dip Log",
			voucher_no=self.name
		)

		return create_fuel_ledger(data)

	def cancel_fuel_ledger_entry(self):
		"""
		Cancel the Fuel Ledger entry linked to this Tank Dip Log by setting is_cancelled = 1.
		"""
		frappe.db.set_value(
			"Fuel Ledger",
			{"voucher_type": "Tank Dip Log", "voucher_no": self.name},
			"is_cancelled",
			1
		)

	def cancel_stock_entry(self):
		"""
		Cancel the Stock Entry linked to this Tank Dip Log using ref_tank_dip_log reference.
		"""
		stock_entries = frappe.get_all(
			"Stock Entry Detail",
			filters={"ref_tank_dip_log": self.name},
			fields=["parent"]
		)

		for entry in stock_entries:
			stock_entry = frappe.get_doc("Stock Entry", entry.parent)
			if stock_entry.docstatus == 1:
				stock_entry.cancel()

	def cancel_stock_reconciliation(self):
		"""
		Cancel the Stock Reconciliation linked to this Tank Dip Log using ref_tank_dip_log reference.
		"""
		stock_reconciliation = frappe.db.get_value(
			"Stock Reconciliation",
			filters={"ref_tank_dip_log": self.name},
			fieldname=["name"]
		)

		if stock_reconciliation:
			doc = frappe.get_doc("Stock Reconciliation", stock_reconciliation)
			doc.flags.ignore_permissions = True
			if doc.docstatus == 1:
				doc.cancel()





	def create_stock_entry(self):
		"""
		Create a Stock Entry of type Material Receipt if stock_in > 0.

		Returns:
			StockEntry: Created Stock Entry document
		"""
		stock_entry = frappe.get_doc({
			"doctype": "Stock Entry",
			"stock_entry_type": "Material Receipt",
			"posting_date": self.posting_date,
			"posting_time": self.posting_time,
			"items": [{
				"item_code": self.fuel_item,
				"qty": self.stock_in,
				"t_warehouse": self.tank,
				"conversion_factor": 1,
				"allow_zero_valuation_rate": 1,
				"ref_tank_dip_log": self.name
			}]
		})

		stock_entry.flags.ignore_permissions = True
		stock_entry.insert()
		stock_entry.submit()

		return stock_entry


	def create_stock_reconciliation(self):
		"""
		Create a Stock Reconciliation when there's a difference between opening_dip and physical_liters.

		Returns:
			StockReconciliation: Created Stock Reconciliation document
		"""
		valuation_rate = get_item_valuation_rate(item_code=self.fuel_item, warehouse=self.tank)

		qty = self.physical_liters + float(self.stock_in)
		stock_reconciliation = frappe.get_doc({
			"doctype": "Stock Reconciliation",
			"purpose": "Stock Reconciliation",
			"posting_date": self.posting_date,
			"posting_time": self.posting_time,
			"ref_tank_dip_log": self.name,
			"items": [{
				"item_code": self.fuel_item,
				"warehouse": self.tank,
				"qty": qty,
				"valuation_rate": valuation_rate,
				"allow_zero_valuation_rate": 1,
				"ref_tank_dip_log": self.name
			}]
		})

		stock_reconciliation.flags.ignore_permissions = True
		stock_reconciliation.insert(ignore_permissions=True)
		stock_reconciliation.submit()

		return stock_reconciliation

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
			"is_cancelled": 0
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
