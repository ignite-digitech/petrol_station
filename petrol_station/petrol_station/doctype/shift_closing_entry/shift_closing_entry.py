# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt
import frappe
from frappe import _
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
	# end: auto-generated types

	def on_submit(self):
		from petrol_station.utils import (create_meter_sales,
		                                  create_meter_readings,
		                                  create_credit_sales_invoices,
			                                  create_fuel_ledger,
		                                  create_journal_entries_for_expenses)
		from petrol_station.utils.shift_closing import create_sales_invoices_from_item_sales
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
			create_sales_invoices_from_item_sales(self)
		except FrappeException as e:
			frappe.log_error(message=frappe.get_traceback(), title="Shift Closing Entry Submission Error")
			frappe.throw(msg=_(str(e)))

	def on_cancel(self):
		from petrol_station.utils import (cancel_invoices_from_shift_closing,
		                                  cancel_fuel_ledgers,
		                                  cancel_pump_meter_readings,
		                                  cancel_journal_entries_for_expenses)
		from petrol_station.utils.shift_closing import cancel_sales_invoices_from_item_sales
		cancel_invoices_from_shift_closing(self)
		cancel_fuel_ledgers(self)
		cancel_pump_meter_readings(self)
		cancel_journal_entries_for_expenses(self)
		cancel_sales_invoices_from_item_sales(self)

	@frappe.whitelist()
	def get_summary_data(self):
		"""Generate comprehensive summary data for the shift closing entry"""
		from collections import defaultdict

		summary = {
			# Key Performance Indicators
			'kpis': {
				'total_fuel_sales': self.total_meter_sales or 0,
				'total_credit_sales': self.total_credit_sales or 0,
				'total_item_sales': self.total_items_sales or 0,
				'total_expenses': self.total_expenses or 0,
				'total_qty': self.total_qty or 0,
				'total_returns': self.total_returns or 0,
			},

			# Sales per fuel item
			'fuel_sales_by_item': self._get_fuel_sales_by_item(),

			# Sales per attendant
			'sales_by_attendant': self._get_sales_by_attendant(),

			# Tank variations
			'tank_variations': self._get_tank_variations(),

			# Expenses grouped by type
			'expenses_by_type': self._get_expenses_by_type(),

			# Item sales grouped by item group
			'item_sales_by_group': self._get_item_sales_by_group(),

			# Payment reconciliation summary
			'payment_summary': self._get_payment_summary(),

			# Credit sales by customer
			'credit_sales_by_customer': self._get_credit_sales_by_customer(),
		}

		return summary

	def _get_fuel_sales_by_item(self):
		"""Aggregate fuel sales by fuel item"""
		from collections import defaultdict
		fuel_data = defaultdict(lambda: {'qty': 0, 'amount': 0, 'count': 0})

		for row in self.meter_readings:
			fuel_item = row.fuel_item or 'Unknown'
			fuel_data[fuel_item]['qty'] += row.sales_qty or 0
			fuel_data[fuel_item]['amount'] += row.total_amount or 0
			fuel_data[fuel_item]['count'] += 1

		# Add credit sales fuel
		for row in self.credit_sales:
			fuel_item = row.fuel_item or 'Unknown'
			fuel_data[fuel_item]['qty'] += row.qty or 0
			fuel_data[fuel_item]['amount'] += row.amount or 0

		return [{'fuel_item': k, **v} for k, v in fuel_data.items()]

	def _get_sales_by_attendant(self):
		"""Aggregate sales by attendant across all sale types"""
		from collections import defaultdict
		attendant_data = defaultdict(lambda: {
			'fuel_qty': 0, 'fuel_amount': 0,
			'credit_qty': 0, 'credit_amount': 0,
			'item_amount': 0,
			'total_amount': 0
		})

		# Meter readings (fuel sales)
		for row in self.meter_readings:
			attendant = row.attendant or 'Unknown'
			attendant_data[attendant]['fuel_qty'] += row.sales_qty or 0
			attendant_data[attendant]['fuel_amount'] += row.total_amount or 0
			attendant_data[attendant]['total_amount'] += row.total_amount or 0

		# Credit sales
		for row in self.credit_sales:
			attendant = row.attendant or 'Unknown'
			attendant_data[attendant]['credit_qty'] += row.qty or 0
			attendant_data[attendant]['credit_amount'] += row.amount or 0
			# attendant_data[attendant]['total_amount'] += row.amount or 0

		# Item sales
		for row in self.items_sales:
			attendant = row.attendant or 'Unknown'
			attendant_data[attendant]['item_amount'] += row.amount or 0
			attendant_data[attendant]['total_amount'] += row.amount or 0

		# Get employee names
		result = []
		for attendant_id, data in attendant_data.items():
			employee_name = frappe.db.get_value('Employee', attendant_id, 'employee_name') or attendant_id
			result.append({
				'attendant': attendant_id,
				'employee_name': employee_name,
				**data
			})

		return sorted(result, key=lambda x: x['total_amount'], reverse=True)

	def _get_tank_variations(self):
		"""Get tank variation details"""
		variations = []

		for row in self.dip_readings:
			variations.append({
				'tank': row.tank,
				'fuel_item': row.fuel_item,
				'opening': row.opening or 0,
				'physical_liters': row.physical_liters or 0,
				'book_stock': row.book_stock or 0,
				'variation': row.variation or 0,
				'stock_in': row.stock_in or 0,
			})

		return variations

	def _get_expenses_by_type(self):
		"""Group expenses by expense account"""
		from collections import defaultdict
		expense_data = defaultdict(lambda: {'amount': 0, 'count': 0, 'details': []})

		for row in self.expenses:
			expense_type = row.expense or 'Unknown'
			expense_data[expense_type]['amount'] += row.amount or 0
			expense_data[expense_type]['count'] += 1
			expense_data[expense_type]['details'].append({
				'employee': row.employee,
				'amount': row.amount or 0,
				'mode_of_payment': row.mode_of_payment,
				'remarks': row.remarks
			})

		return [{'expense_type': k, **v} for k, v in expense_data.items()]

	def _get_item_sales_by_group(self):
		"""Group item sales by item group"""
		from collections import defaultdict
		group_data = defaultdict(lambda: {'qty': 0, 'amount': 0, 'count': 0})

		for row in self.items_sales:
			item_group = frappe.db.get_value('Item', row.item_code, 'item_group') or 'Unknown'
			group_data[item_group]['qty'] += row.qty or 0
			group_data[item_group]['amount'] += row.amount or 0
			group_data[item_group]['count'] += 1

		return [{'item_group': k, **v} for k, v in group_data.items()]

	def _get_payment_summary(self):
		"""Get payment reconciliation summary"""
		payments = []

		for row in self.payment_reconciliation:
			payments.append({
				'mode_of_payment': row.mode_of_payment,
				'opening_amount': row.opening_amount or 0,
				'expected_amount': row.expected_amount or 0,
				'closing_amount': row.closing_amount or 0,
				'difference': row.difference or 0,
			})

		return payments

	def _get_credit_sales_by_customer(self):
		"""Group credit sales by customer"""
		from collections import defaultdict
		customer_data = defaultdict(lambda: {'qty': 0, 'amount': 0, 'count': 0})

		for row in self.credit_sales:
			customer = row.customer or 'Unknown'
			customer_data[customer]['qty'] += row.qty or 0
			customer_data[customer]['amount'] += row.amount or 0
			customer_data[customer]['count'] += 1

		return [{'customer': k, **v} for k, v in customer_data.items()]


