from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

custom_fields = {
    "Warehouse": [
        {
            "fieldname": "fuel_item",
            "insert_after": "is_rejected_warehouse",
            "label": "Fuel Item",
            "fieldtype": "Link",
            "options": "Item"
        }
    ]
}

def execute():
    create_custom_fields(custom_fields)