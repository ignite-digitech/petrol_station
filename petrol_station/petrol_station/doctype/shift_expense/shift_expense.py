# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class ShiftExpense(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amount: DF.Currency
		employee: DF.Link | None
		expense: DF.Link
		mode_of_payment: DF.Link
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		remarks: DF.SmallText
	# end: auto-generated types

	pass
