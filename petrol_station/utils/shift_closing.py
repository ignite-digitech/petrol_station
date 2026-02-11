import frappe
from frappe.model.document import Document
from frappe.utils import flt
from petrol_station.petrol_station.doctype.shift_closing_entry.shift_closing_entry import ShiftClosingEntry
from petrol_station.petrol_station.doctype.pump_meter_reading.pump_meter_reading import (
    create_pump_meter_reading,
    PumpMeterReadingData
)


def prepare_invoices_from_readings(doc: Document | ShiftClosingEntry | str):
    """
    Prepare Sales Invoice data from meter readings.
    Groups readings by attendant and creates invoice data for each group.

    Args:
        doc (Document | ShiftClosingEntry | str): Shift Closing Entry document or name

    Returns:
        list: List of dictionaries containing invoice data
            [
                {
                    "customer": "walk-in",
                    "posting_date": "2026-02-11",
                    "posting_time": "18:00:00",
                    "items": [
                        {
                            "item_code": "Petrol",
                            "qty": 100.5,
                            "rate": 5000.0,
                            "amount": 502500.0
                        }
                    ]
                }
            ]
    """

    if isinstance(doc, str):
        doc = frappe.get_doc("Shift Closing Entry", doc)

    if not doc.meter_readings:
        return []

    # Get walk-in customer
    walk_in_customer = frappe.db.get_single_value("Selling Settings", "customer_for_walk_in") or "Walk-In"

    # Group readings by attendant
    attendant_readings = {}
    for reading in doc.meter_readings:
        attendant = reading.attendant or "No Attendant"
        if attendant not in attendant_readings:
            attendant_readings[attendant] = []
        attendant_readings[attendant].append(reading)

    # Prepare invoice data for each attendant group
    invoices_data = []
    for attendant, readings in attendant_readings.items():
        invoice_data = {
            "customer": walk_in_customer,
            "posting_date": doc.posting_date,
            "posting_time": doc.posting_time,
            "company": doc.company,
            "attendant": attendant if attendant != "No Attendant" else None,
            "items": []
        }

        # Group items by fuel_item to consolidate quantities
        items_dict = {}
        for reading in readings:
            fuel_item = reading.fuel_item
            if fuel_item not in items_dict:
                items_dict[fuel_item] = {
                    "item_code": fuel_item,
                    "qty": 0,
                    "rate": reading.unit_price,
                    "amount": 0,
                    "ref_shift": doc.name,
                    "warehouse": reading.tank
                }
            qty = flt(reading.sales_qty)
            items_dict[fuel_item]["qty"] += qty
            items_dict[fuel_item]["amount"] += flt(reading.total_amount)

        # Convert dict to list
        invoice_data["items"] = list(items_dict.values())
        invoices_data.append(invoice_data)

    return invoices_data


def create_and_submit_sales_invoices(doc: Document | ShiftClosingEntry | str):
    """
    Create and submit Sales Invoices from prepared invoice data.

    Args:
        doc (Document | ShiftClosingEntry | str): Shift Closing Entry document or name

    Returns:
        list: List of created and submitted Sales Invoice documents
            [
                {
                    "name": "SINV-00001",
                    "status": "Submitted",
                    "grand_total": 502500.0
                }
            ]

    Raises:
        frappe.ValidationError: If invoice creation or submission fails
    """
    invoices_data = prepare_invoices_from_readings(doc)

    if not invoices_data:
        return None

    created_invoices = []

    for invoice_data in invoices_data:
        if not invoice_data.get("items"):
            continue

        # Create Sales Invoice
        sales_invoice = frappe.get_doc({
            "doctype": "Sales Invoice",
            "customer": invoice_data["customer"],
            "posting_date": invoice_data["posting_date"],
            "posting_time": invoice_data["posting_time"],
            "set_posting_time": 1,
            "company": invoice_data["company"],
            "attendant": invoice_data["attendant"],
            "items": []
        })

        # Add items
        for item in invoice_data["items"]:
            sales_invoice.append("items", {
                "item_code": item["item_code"],
                "qty": item["qty"],
                "rate": item["rate"],
                "ref_shift": item["ref_shift"],
            })

        # Insert and submit
        sales_invoice.flags.ignore_permissions = True
        sales_invoice.insert()
        sales_invoice.submit()

        created_invoices.append({
            "name": sales_invoice.name,
            "status": sales_invoice.status,
            "grand_total": sales_invoice.grand_total
        })

    return created_invoices


def create_pump_meter_readings_from_closing(doc: Document | ShiftClosingEntry | str):
    """
    Create Pump Meter Reading documents from Shift Closing Entry meter readings.

    Args:
        doc (Document | ShiftClosingEntry | str): Shift Closing Entry document or name

    Returns:
        list: List of created Pump Meter Reading documents

    Raises:
        frappe.ValidationError: If no meter readings exist
    """
    if isinstance(doc, str):
        doc = frappe.get_doc("Shift Closing Entry", doc)

    if not doc.meter_readings:
        frappe.throw(
            "No meter readings found to create Pump Meter Readings.",
            frappe.ValidationError
        )

    created_readings = []

    for reading in doc.meter_readings:
        # Get pump from nozzle
        nozzle_doc = frappe.get_doc("Pump Nozzle", reading.nozzle)
        pump = nozzle_doc.pump

        # Create PumpMeterReadingData dataclass instance
        reading_data = PumpMeterReadingData(
            pump=pump,
            nozzle=reading.nozzle,
            fuel_item=reading.fuel_item,
            opening_expected=reading.opening or 0,
            physical_opening=reading.closing,
            sales_qty=reading.sales_qty,
            posting_date=doc.posting_date,
            posting_time=doc.posting_time,
            employee=reading.attendant,
            tank=reading.tank,
            voucher_type="Shift Closing Entry",
            voucher_no=doc.name,
            voucher_detail_no=reading.name,
            selling_price=reading.unit_price
        )

        # Create the Pump Meter Reading
        pump_meter_reading = create_pump_meter_reading(reading_data)
        created_readings.append(pump_meter_reading)

    return created_readings

