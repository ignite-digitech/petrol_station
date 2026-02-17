import frappe

def execute():
	frappe.db.sql("UPDATE `tabMode of Payment` SET enabled = 0 where `name` in ('Cash', 'Credit Card', 'Wire Transfer', 'Bank Draft', 'Cheque')")
