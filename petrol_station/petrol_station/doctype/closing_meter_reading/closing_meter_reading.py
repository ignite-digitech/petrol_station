# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ClosingMeterReading(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		attendant: DF.Link
		closing: DF.Float
		fuel_item: DF.Link | None
		nozzle: DF.Link
		opening: DF.Float
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		return_to_tank: DF.Float
		sales_qty: DF.Float
		total_amount: DF.Currency
		unit_price: DF.Currency
	# end: auto-generated types

	pass
