import frappe
from frappe.utils import today, nowtime
from frappe.model.document import Document
from petrol_station.petrol_station.doctype.shift_opening_entry.shift_opening_entry import ShiftOpeningEntry
from petrol_station.petrol_station.doctype.tank_dip_log.tank_dip_log import TankDipLog


def create_purchase_receipts_from_deliveries(doc: Document | ShiftOpeningEntry | TankDipLog, ignore_create_fuel_ledger=False):
    """
    Create Purchase Receipt documents from deliveries table.
    Each delivery row creates a Purchase Receipt Item with the tank as warehouse
    and opening_shift reference.

    Returns:
        list: List of created Purchase Receipt documents
    """
    if not doc.deliveries:
        return []

    # Group deliveries by supplier
    supplier_deliveries = {}
    for delivery in doc.deliveries:
        if delivery.supplier not in supplier_deliveries:
            supplier_deliveries[delivery.supplier] = []
        supplier_deliveries[delivery.supplier].append(delivery)

    created_receipts = []

    for supplier, deliveries in supplier_deliveries.items():
        # Create Purchase Receipt for each supplier
        pr = frappe.new_doc("Purchase Receipt")
        pr.supplier = supplier
        pr.posting_date = today()
        pr.posting_time = nowtime()
        pr.set_posting_time = 1
        pr.flags.ignore_create_fuel_ledger = ignore_create_fuel_ledger

        # Add items from deliveries
        for delivery in deliveries:
            item = {
                "item_code": delivery.fuel_item,
                "qty": delivery.qty,
                "rate": delivery.rate,
                "warehouse": delivery.tank,
            }

            if doc.doctype == "Tank Dip Log":
                item["ref_tank_dip_log"] = doc.name

            if doc.doctype == "Shift Closing Entry":
                item["opening_shift"] = doc.name

            pr.append("items", item)

        pr.insert()
        pr.submit()
        created_receipts.append(pr)

    return created_receipts


def cancel_purchase_receipts(doc: Document | ShiftOpeningEntry | TankDipLog):
    """
    Cancel all Purchase Receipts linked to this Shift Opening Entry.
    Finds and cancels all Purchase Receipts with items referencing this opening shift.

    Returns:
        int: Number of Purchase Receipts cancelled
    """
    # Find all Purchase Receipt Items linked to this Shift Opening Entry
    filters = {"docstatus": 1}
    if doc.doctype == "Shift Closing Entry":
        filters["opening_shift"] = doc.name
    if doc.doctype == "Tank Dip Log":
        filters["ref_tank_dip_log"] = doc.name

    pr_items = frappe.get_all(
        "Purchase Receipt Item",
        filters=filters,
        fields=["parent"],
        distinct=True
    )

    if not pr_items:
        return 0

    # Get unique Purchase Receipt names
    pr_names = list(set([item.parent for item in pr_items]))

    # Cancel each Purchase Receipt
    for pr_name in pr_names:
        pr = frappe.get_doc("Purchase Receipt", pr_name)
        if pr.docstatus == 1:
            pr.cancel()

    return len(pr_names)