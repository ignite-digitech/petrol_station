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

	def on_submit(self):
		self.create_pump_meter_readings_from_opening_readings()


	def validate(self):
		self.validate_dip_logs_existence()

	def on_cancel(self):
		self.cancel_pump_meter_readings()

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


