# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PumpNozzle(Document):
	def autoname(self):
		"""Generate unique nozzle name in format: {pump}-{number}"""
		if not self.pump:
			frappe.throw("Pump is required to generate nozzle name")

		# Count existing nozzles for this pump
		nozzle_count = frappe.db.count("Pump Nozzle", filters={"pump": self.pump})

		# Generate next number (count + 1)
		next_number = nozzle_count + 1

		# Set the name
		self.name = f"{self.pump}-{next_number}"
