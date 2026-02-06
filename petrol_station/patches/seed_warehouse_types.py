import frappe


def execute():
    """Seed Fuel Tank warehouse type."""
    if not frappe.db.exists("Warehouse Type", "Fuel Tank"):
        doc = frappe.get_doc({
            "doctype": "Warehouse Type",
            "name": "Fuel Tank",
            "description": "Fuel tank warehouse type for storing fuel"
        })
        doc.insert()
        frappe.db.commit()
