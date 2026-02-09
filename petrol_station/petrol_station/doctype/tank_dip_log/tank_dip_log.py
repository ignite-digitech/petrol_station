# Copyright (c) 2026, Ignite Digital and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import today


class TankDipLog(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		amended_from: DF.Link | None
		conversion_factor: DF.Float
		employee: DF.Link | None
		fuel_item: DF.Link
		opening_dip: DF.Float
		physical_dip_reading_mm: DF.Float
		physical_liters: DF.Float
		posting_date: DF.Date
		posting_datetime: DF.Datetime | None
		posting_time: DF.Time | None
		tank: DF.Link
		water_level_mm: DF.Float
	# end: auto-generated types

	pass


@frappe.whitelist()
def get_tank_dip_logs_by_date(date=None) -> list:
	"""
	Get all Tank Dip Logs created on a particular day.

	Args:
		date (str, optional): Date in YYYY-MM-DD format. Defaults to current date.

	Returns:
		list: List of Tank Dip Log documents
	"""
	if not date:
		date = today()

	tank_dip_logs = frappe.get_all(
		"Tank Dip Log",
		filters={"posting_date": date},
		fields=["*"],
		order_by="posting_time desc"
	)

	return tank_dip_logs
