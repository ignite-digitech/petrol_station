import frappe


def execute():
	"""
	Seed Walk-In customer and set customer_for_walk_in in Selling Settings
	"""
	# Create Walk-In customer if it doesn't exist
	if not frappe.db.exists("Customer", "Walk-In"):
		customer = frappe.get_doc({
			"doctype": "Customer",
			"customer_name": "Walk-In",
			"customer_type": "Individual",
			"customer_group": frappe.db.get_single_value("Selling Settings", "customer_group") or "Individual",
			"territory": frappe.db.get_single_value("Selling Settings", "territory") or "All Territories"
		})
		customer.insert(ignore_permissions=True)
		frappe.db.commit()

	# Set customer_for_walk_in in Selling Settings if field exists
	selling_settings = frappe.get_single("Selling Settings")
	selling_settings.customer_for_walk_in = "Walk-In"
	selling_settings.save(ignore_permissions=True)
	frappe.db.commit()