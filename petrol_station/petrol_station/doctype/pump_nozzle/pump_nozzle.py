# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class PumpNozzle(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		fuel_item: DF.Link | None
		pump: DF.Link
	# end: auto-generated types

	def autoname(self):
		"""Generate unique nozzle name in format: {pump}-{number}"""
		if not self.pump:
			frappe.throw(_("Pump is required to generate nozzle name"))

		# Count existing nozzles for this pump
		nozzle_count = frappe.db.count("Pump Nozzle", filters={"pump": self.pump})

		# Generate next number (count + 1)
		next_number = nozzle_count + 1

		# Set the name
		self.name = f"{self.pump}-{next_number}"

	def get_tank(self):
		if self.pump:
			return frappe.db.get_value("Fuel Pump", {"name": self.pump}, "tank")
		else:
			frappe.throw(msg=_("Please configure pump first, attach tank"))
			return None


@frappe.whitelist()
def get_tank(nozzle: str | Document | PumpNozzle):
	if isinstance(nozzle, str):
		nozzle = frappe.get_doc("Pump Nozzle", nozzle)

	return nozzle.get_tank()

