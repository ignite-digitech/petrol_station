# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ShiftTankDip(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		book_stock: DF.Float
		fuel_item: DF.Link
		opening: DF.Float
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		physical_dip_mm: DF.Float
		physical_liters: DF.Float
		tank: DF.Link
		variation: DF.Float
	# end: auto-generated types

	pass
