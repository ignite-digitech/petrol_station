# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import get_datetime
from frappe.model.document import Document
from petrol_station.petrol_station.doctype.fuel_ledger.fuel_ledger import (
	create_fuel_ledger,
	FuelLedgerData
)
from petrol_station.petrol_station.doctype.tank_dip_log.tank_dip_log import (
	get_last_closing_book_balance
)


def on_submit(doc, method=None):
	"""
	Hook method called when a Purchase Receipt is submitted.
	Creates Fuel Ledger entries for items with opening_shift reference.

	Args:
		doc: Purchase Receipt document
		method: Hook method (unused)
	"""
	if doc.flags.ignore_create_fuel_ledger:
		return

	create_fuel_ledger_entries_from_purchase_receipt(doc)


def on_cancel(doc, method=None):
	"""
	Hook method called when a Purchase Receipt is cancelled.
	Marks related Fuel Ledger entries as cancelled.

	Args:
		doc: Purchase Receipt document
		method: Hook method (unused)
	"""
	cancel_fuel_ledger_entries(doc)


def create_fuel_ledger_entries_from_purchase_receipt(pr_doc: str | Document):
	"""
	Create Fuel Ledger entries from Purchase Receipt items that have opening_shift reference.
	Each item with opening_shift creates a Fuel Ledger entry with liters_in.

	Args:
		pr_doc: Purchase Receipt document

	Returns:
		list: List of created Fuel Ledger documents
	"""
	if isinstance(pr_doc, str):
		pr_doc = frappe.get_doc("Purchase Receipt", pr_doc)

	if not pr_doc.items:
		return []

	created_ledgers = []
	posting_datetime = get_datetime(f"{pr_doc.posting_date} {pr_doc.posting_time}")

	for item in pr_doc.items:
		# Only process items with opening_shift reference
		if not item.get("opening_shift"):
			continue

		# Get the last closing book balance for the tank
		opening_balance = get_last_closing_book_balance(item.warehouse)

		# Get physical dip reading (same as opening balance for deliveries)
		physical_dip = opening_balance

		# Create FuelLedgerData
		ledger_data = FuelLedgerData(
			fuel_item=item.item_code,
			fuel_tank=item.warehouse,
			opening_book_balance=opening_balance,
			physical_dip_reading_liters=physical_dip,
			posting_date=pr_doc.posting_date,
			posting_time=pr_doc.posting_time,
			posting_datetime=posting_datetime,
			liters_in=item.qty,  # Delivery quantity as liters_in
			liters_out=0,
			return_to_tank=0,
			voucher_type="Purchase Receipt",
			voucher_no=pr_doc.name,
			voucher_detail_no=item.name
		)

		# Create Fuel Ledger entry
		fuel_ledger = create_fuel_ledger(ledger_data)
		created_ledgers.append(fuel_ledger)

	return created_ledgers


def cancel_fuel_ledger_entries(pr_doc):
	"""
	Mark all Fuel Ledger entries linked to this Purchase Receipt as cancelled.

	Args:
		pr_doc: Purchase Receipt document

	Returns:
		int: Number of Fuel Ledger entries marked as cancelled
	"""
	# Find all Fuel Ledger entries linked to this Purchase Receipt
	fuel_ledgers = frappe.get_all(
		"Fuel Ledger",
		filters={
			"voucher_type": "Purchase Receipt",
			"voucher_no": pr_doc.name,
			"is_cancelled": 0
		},
		pluck="name"
	)

	if not fuel_ledgers:
		return 0

	# Mark each ledger as cancelled
	for ledger_name in fuel_ledgers:
		frappe.db.set_value("Fuel Ledger", ledger_name, "is_cancelled", 1)

	# nosemgrep We are commiting since we want to mark all ledgers as cancelled immediately
	frappe.db.commit()

	return len(fuel_ledgers)
