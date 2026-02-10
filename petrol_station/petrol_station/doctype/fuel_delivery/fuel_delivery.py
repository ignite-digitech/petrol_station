# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FuelDelivery(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		fuel_item: DF.Link
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		qty: DF.Float
		rate: DF.Currency
		supplier: DF.Link
		tank: DF.Link
	# end: auto-generated types

	pass
