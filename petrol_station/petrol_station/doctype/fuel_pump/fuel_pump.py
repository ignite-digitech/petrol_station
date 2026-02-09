# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today, now_datetime
from petrol_station.petrol_station.doctype.pump_meter_reading.pump_meter_reading import (
	create_pump_meter_reading,
	PumpMeterReadingData
)


class FuelPump(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF
		from petrol_station.petrol_station.doctype.shift_opening_meter_reading.shift_opening_meter_reading import ShiftOpeningMeterReading

		company: DF.Link
		fuel_item: DF.Link
		initial_readings: DF.Table[ShiftOpeningMeterReading]
		nozzles: DF.Int
		pump_name: DF.Data
		tank: DF.Link
	# end: auto-generated types

	def validate(self):
		"""Set is_opening flag for initial readings"""
		self.set_opening_flag_for_initial_readings()

	def after_insert(self):
		"""Create nozzles after pump is created"""
		self.create_nozzles()

	def on_update(self):
		"""Update nozzles if the number of nozzles has changed"""
		if self.has_value_changed("nozzles"):
			self.create_nozzles()

		if self.initial_readings:
			if self.has_value_changed("initial_readings"):
				self.create_pump_meter_readings_from_initial_readings()

	def set_opening_flag_for_initial_readings(self):
		"""Set is_opening to 1 for all initial readings"""
		if self.initial_readings:
			for reading in self.initial_readings:
				reading.is_opening = 1

	def create_nozzles(self):
		"""Create or adjust nozzles based on the nozzles field"""
		if not self.nozzles or self.nozzles < 1:
			return

		# Get existing nozzles for this pump
		existing_nozzles = frappe.get_all(
			"Pump Nozzle",
			filters={"pump": self.name},
			pluck="name",
			order_by="name"
		)

		existing_count = len(existing_nozzles)
		required_count = int(self.nozzles)

		# If we need to create more nozzles
		if required_count > existing_count:
			for i in range(existing_count + 1, required_count + 1):
				nozzle = frappe.get_doc({
					"doctype": "Pump Nozzle",
					"pump": self.name
				})
				nozzle.insert()

		# If we need to delete excess nozzles
		elif required_count < existing_count:
			# Delete the extra nozzles (from the end)
			for i in range(required_count, existing_count):
				if i < len(existing_nozzles):
					frappe.delete_doc("Pump Nozzle", existing_nozzles[i])

	def create_pump_meter_readings_from_initial_readings(self):
		"""
		Create Pump Meter Reading documents from initial_readings table.
		Validates that no Pump Meter Readings exist for the pump before creating.

		Returns:
			list: List of created Pump Meter Reading documents

		Raises:
			frappe.ValidationError: If Pump Meter Readings already exist for this pump
		"""
		# Validate that no pump meter readings exist for this pump
		created_readings = []
		posting_date = today()
		posting_time = now_datetime().strftime("%H:%M:%S")

		for reading in self.initial_readings:
			existing_readings = frappe.db.exists("Pump Meter Reading", {"pump": self.name, "is_opening": 1, "nozzle": reading.nozzle})
			if existing_readings:
				continue

			# Create PumpMeterReadingData dataclass instance
			reading_data = PumpMeterReadingData(
				pump=reading.pump or self.name,
				nozzle=reading.nozzle,
				fuel_item=self.fuel_item,
				opening_expected=reading.expected_reading or 0,
				physical_opening=reading.opening_reading,
				sales_qty=0,  # Initial reading, no sales yet
				posting_date=posting_date,
				posting_time=posting_time,
				employee=None,
				tank=reading.tank or self.tank,
				voucher_type=None,
				voucher_no=None,
				voucher_detail_no=None,
				is_opening=1
			)

			# Create the Pump Meter Reading
			pump_meter_reading = create_pump_meter_reading(reading_data)
			created_readings.append(pump_meter_reading)

		return created_readings


