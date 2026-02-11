# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

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
		from petrol_station.petrol_station.doctype.shift_tank_dip.shift_tank_dip import ShiftTankDip
		from petrol_station.petrol_station.doctype.shift_credit_sale.shift_credit_sale import ShiftCreditSale

		amended_from: DF.Link | None
		company: DF.Link
		credit_sales: DF.Table[ShiftCreditSale]
		dip_readings: DF.Table[ShiftTankDip]
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
		total_meter_sales: DF.Currency
		total_qty: DF.Float
		total_returns: DF.Float
		total_shift_revenue: DF.Currency
		total_variation_l: DF.Float
	# end: auto-generated types

	def on_submit(self):
		pass
