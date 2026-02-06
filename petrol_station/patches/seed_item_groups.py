import frappe


def execute():
    """Seed initial Item Groups for petrol station items."""
    item_groups = ["Fuel", "Lubricants", "Air Filters", "Oil Filters", "Fuel Filters"]

    for item_group_name in item_groups:
        if not frappe.db.exists("Item Group", item_group_name):
            doc = frappe.get_doc({
                "doctype": "Item Group",
                "item_group_name": item_group_name,
                "is_group": 0,
                "parent_item_group": "All Item Groups"
            })
            doc.insert()

    frappe.db.commit()