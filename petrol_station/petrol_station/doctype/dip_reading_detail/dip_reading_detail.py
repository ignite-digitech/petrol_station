# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class DipReadingDetail(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		dip_log_id: DF.Link | None
		opening_reading: DF.Float
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		physical_reading: DF.Float
		tank: DF.Link | None
	# end: auto-generated types

	pass
