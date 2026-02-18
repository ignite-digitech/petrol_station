# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt
import frappe
from frappe.frappeclient import FrappeException
# import frappe
from frappe.model.document import Document


class ShiftClosingEntry(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from erpnext.accounts.doctype.pos_closing_entry_detail.pos_closing_entry_detail import POSClosingEntryDetail
		from frappe.types import DF
		from petrol_station.petrol_station.doctype.closing_meter_reading.closing_meter_reading import ClosingMeterReading
		from petrol_station.petrol_station.doctype.shift_credit_sale.shift_credit_sale import ShiftCreditSale
		from petrol_station.petrol_station.doctype.shift_expense.shift_expense import ShiftExpense
		from petrol_station.petrol_station.doctype.shift_item_sales.shift_item_sales import ShiftItemSales
		from petrol_station.petrol_station.doctype.shift_tank_dip.shift_tank_dip import ShiftTankDip

		amended_from: DF.Link | None
		company: DF.Link
		credit_sales: DF.Table[ShiftCreditSale]
		dip_readings: DF.Table[ShiftTankDip]
		expenses: DF.Table[ShiftExpense]
		items_sales: DF.Table[ShiftItemSales]
		managers_comments: DF.SmallText | None
		meter_readings: DF.Table[ClosingMeterReading]
		payment_reconciliation: DF.Table[POSClosingEntryDetail]
		period_end_date: DF.Datetime
		period_start_date: DF.Datetime
		posting_date: DF.Date
		posting_time: DF.Time
		shift_opening_entry: DF.Link
		supervisor: DF.Link
		total_credit_sales: DF.Currency
		total_expenses: DF.Currency
		total_items_sales: DF.Currency
		total_meter_sales: DF.Currency
		total_qty: DF.Float
		total_returns: DF.Float
		total_shift_revenue: DF.Currency
		total_variation_l: DF.Float
	# end: auto-generated types

	def on_submit(self):
		from petrol_station.utils import (create_meter_sales,
		                                  create_meter_readings,
		                                  create_credit_sales_invoices,
			                                  create_fuel_ledger,
		                                  create_journal_entries_for_expenses)
		try:
			frappe.enqueue(
				method=create_meter_sales,
				queue='long',
				doc=self,
				on_failure=lambda _e: frappe.log_error(message=frappe.get_traceback(), title="Shift Closing Entry Submission Error")
			)

			frappe.enqueue(
				method=create_meter_readings,
				queue='long',
				doc=self,
			)

			frappe.enqueue(
				method=create_credit_sales_invoices,
				queue='long',
				doc=self,
			)

			# frappe.enqueue(
			# 	method=create_fuel_ledger,
			# 	queue='long',
			# 	doc=self,
			# )
			# create_meter_sales(self)
			# create_meter_readings(self)
			# create_credit_sales_invoices(self)
			create_fuel_ledger(self)
			create_journal_entries_for_expenses(self)
		except FrappeException as e:
			frappe.log_error(message=frappe.get_traceback(), title="Shift Closing Entry Submission Error")
			frappe.throw(msg=str(e))

	def on_cancel(self):
		from petrol_station.utils import (cancel_invoices_from_shift_closing,
		                                  cancel_fuel_ledgers,
		                                  cancel_pump_meter_readings,
		                                  cancel_journal_entries_for_expenses)
		cancel_invoices_from_shift_closing(self)
		cancel_fuel_ledgers(self)
		cancel_pump_meter_readings(self)
		cancel_journal_entries_for_expenses(self)


