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
        },
        {
            "fieldname": "ref_fuel_ledger",
            "insert_after": "reference_purchase_receipt",
            "label": "Reference Fuel Ledger",
            "fieldtype": "Link",
            "options": "Fuel Ledger",
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
        },
        {
            "fieldname": "ref_fuel_ledger",
            "insert_after": "cost_center",
            "label": "Reference Fuel Ledger",
            "fieldtype": "Link",
            "options": "Fuel Ledger",
            "read_only": 1,
        }
    ],
    "Stock Reconciliation Item": [
        {
            "fieldname": "ref_fuel_ledger",
            "insert_after": "batch_no",
            "label": "Reference Fuel Ledger",
            "fieldtype": "Link",
            "options": "Fuel Ledger",
            "read_only": 1,
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
    ],
    "Customer": [
        {
            "fieldname": "vehicle_reg_no",
            "label": "Vehicle Registration No",
            "insert_after": "customer_type",
            "fieldtype": "Data"
        }
    ],
    "Selling Settings": [
        {
            "fieldname": "customer_for_walk_in",
            "insert_after": "territory",
            "fieldtype": "Link",
            "options": "Customer",
            "label": "Customer For Walk In",
        }
    ],
    "Sales Invoice": [
        {
            "fieldname": "attendant",
            "insert_after": "customer",
            "label": "Attendant",
            "fieldtype": "Link",
            "options": "Employee",
        }
    ],
    "Sales Invoice Item": [
        {
            "fieldname": "ref_shift",
            "insert_after": "pos_invoice_item",
            "label": "Reference Shift",
            "fieldtype": "Link",
            "options": "Shift Closing Entry",
        }
    ]
}

def execute():
    create_custom_fields(custom_fields)