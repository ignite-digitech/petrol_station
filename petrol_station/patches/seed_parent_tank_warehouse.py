import frappe

def execute():
    if not frappe.db.exists("Warehouse", "Fuel Tanks"):
        doc = frappe.new_doc("Warehouse")
        doc.warehouse_name = "Fuel Tanks"
        doc.warehouse_type = "Fuel Tank"
        doc.is_group = 1
        doc.insert()