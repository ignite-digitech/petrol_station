# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class FuelPump(Document):
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
