# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class FuelLedger(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		closing_book_balance: DF.Float
		conversion_factor: DF.Float
		fuel_item: DF.Link | None
		fuel_tank: DF.Link | None
		liters_in: DF.Float
		liters_our: DF.Float
		opening_book_balance: DF.Float
		physical_dip_reading_liters: DF.Float
		physical_dip_reading_mm: DF.Float
		posting_date: DF.Date | None
		posting_datetime: DF.Datetime | None
		posting_time: DF.Time | None
		return_to_tank: DF.Float
		shortage_status: DF.Literal["Normal", "High Loss", "High Gain"]
		variation_liters: DF.Float
		variation_percentage: DF.Float
		variation_value: DF.Currency
		voucher_detail_no: DF.Data | None
		voucher_no: DF.DynamicLink | None
		voucher_type: DF.Link | None
		water_level_mm: DF.Float
	# end: auto-generated types

	pass
