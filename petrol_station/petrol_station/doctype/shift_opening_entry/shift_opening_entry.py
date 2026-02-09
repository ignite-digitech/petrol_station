# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today
from petrol_station.petrol_station.doctype.tank_dip_log.tank_dip_log import get_tank_dip_logs_by_date


class ShiftOpeningEntry(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from erpnext.accounts.doctype.pos_opening_entry_detail.pos_opening_entry_detail import POSOpeningEntryDetail
		from frappe.types import DF
		from petrol_station.petrol_station.doctype.dip_reading_detail.dip_reading_detail import DipReadingDetail
		from petrol_station.petrol_station.doctype.shift_opening_meter_reading.shift_opening_meter_reading import ShiftOpeningMeterReading

		amended_from: DF.Link | None
		attendant: DF.Link | None
		dip_readings: DF.Table[DipReadingDetail]
		opening_balances: DF.Table[POSOpeningEntryDetail]
		opening_meter_readings: DF.Table[ShiftOpeningMeterReading]
		posting_date: DF.Date
		posting_datetime: DF.Datetime | None
		posting_time: DF.Time
		shift_type: DF.Literal["Day", "Night"]
		supervisor: DF.Link | None
	# end: auto-generated types

	def onload(self):
		date = today()
		if self.posting_date:
			date = self.posting_date

		try:
			tank_reading = get_tank_dip_logs_by_date(date)
			self.dip_readings = []
			for tank in tank_reading:
				self.append("dip_readings", {
					"tank": tank.get("tank"),
					"dip_log_id": tank.get("name"),
					"opening_reading": tank.get("opening_dip"),
					"physical_reading": tank.get("physical_liters")
				})

		except Exception as e:
			frappe.log_error(title="Error in fetching tank dip logs", message=e)


	def validate(self):
		self.validate_dip_logs_existence()

	def validate_dip_logs_existence(self):
		tank_readings = get_tank_dip_logs_by_date(self.posting_date)
		if not tank_readings or len(tank_readings) == 0:
			frappe.throw("No tank dip logs found for the selected date")


