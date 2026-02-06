import frappe


def execute():
    """Seed initial fuel items: PMS and AGO."""
    fuel_items = [
        {
            "item_code": "PMS",
            "item_name": "PMS",
            "item_group": "Fuel",
            "stock_uom": "Litre",
            "is_stock_item": 1
        },
        {
            "item_code": "AGO",
            "item_name": "AGO",
            "item_group": "Fuel",
            "stock_uom": "Litre",
            "is_stock_item": 1
        }
    ]

    for item_data in fuel_items:
        if not frappe.db.exists("Item", item_data["item_code"]):
            doc = frappe.get_doc({
                "doctype": "Item",
                **item_data
            })
            doc.insert()

    frappe.db.commit()
