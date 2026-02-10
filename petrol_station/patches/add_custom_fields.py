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
    ],
    "Stock Entry Detail": [
        {
            "fieldname": "ref_tank_dip_log",
            "insert_after": "reference_purchase_receipt",
            "label": "Reference Tank Dip Log",
            "fieldtype": "Link",
            "options": "Tank Dip Log",
            "read_only": 1,
        }
    ],
    "Stock Reconciliation": [
        {
            "fieldname": "ref_tank_dip_log",
            "insert_after": "cost_center",
            "label": "Tank Dip Log",
            "fieldtype": "Link",
            "options": "Tank Dip Log",
            "read_only": 1,
            "hidden": 1,
        }
    ],
    "Purchase Receipt Item": [
        {
            "fieldname": "opening_shift",
            "insert_after": "project",
            "label": "Reference Opening Shift",
            "fieldtype": "Link",
            "options": "Shift Opening Entry",
            "read_only": 1,
        }
    ]
}

def execute():
    create_custom_fields(custom_fields)