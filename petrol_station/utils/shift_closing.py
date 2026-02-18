import frappe
from frappe.model.document import Document
from frappe.utils import flt, today, nowtime, now, get_datetime
from petrol_station.petrol_station.doctype.shift_closing_entry.shift_closing_entry import ShiftClosingEntry
from petrol_station.petrol_station.doctype.pump_meter_reading.pump_meter_reading import (
    create_pump_meter_reading,
    PumpMeterReadingData
)
from petrol_station.petrol_station.doctype.fuel_ledger.fuel_ledger import (
    create_fuel_ledger,
    FuelLedgerData, cancel_fuel_ledgers_by_voucher
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
            "posting_date": today(),
            "posting_time": nowtime(),
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
            posting_date=today(),
            posting_time=nowtime(),
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


def create_sales_invoices_from_credit_sales(doc: Document | ShiftClosingEntry | str):
    """
    Create Sales Invoices from credit sales entries in Shift Closing Entry.

    Args:
        doc (Document | ShiftClosingEntry | str): Shift Closing Entry document or name

    Returns:
        list: List of created and submitted Sales Invoice documents
            [
                {
                    "name": "SINV-00001",
                    "customer": "Customer Name",
                    "grand_total": 10000.0
                }
            ]

    Raises:
        frappe.ValidationError: If no credit sales exist
    """
    if isinstance(doc, str):
        doc = frappe.get_doc("Shift Closing Entry", doc)


    if not doc.credit_sales:
        return []

    created_invoices = []

    # Group credit sales by customer and attendant
    customer_attendant_sales = {}
    for sale in doc.credit_sales:
        key = (sale.customer, sale.attendant)
        if key not in customer_attendant_sales:
            customer_attendant_sales[key] = []
        customer_attendant_sales[key].append(sale)

    # Create a Sales Invoice for each customer-attendant combination
    for (customer, attendant), sales in customer_attendant_sales.items():
        # Prepare invoice data
        invoice_data = {
            "doctype": "Sales Invoice",
            "customer": customer,
            "posting_date": today(),
            "posting_time": nowtime(),
            "set_posting_time": 1,
            "company": doc.company,
            "items": [],
            "attendant": attendant
        }

        # Add items for this customer-attendant combination
        for sale in sales:
            invoice_data["items"].append({
                "item_code": sale.fuel_item,
                "qty": sale.qty,
                "rate": sale.rate,
                "amount": sale.amount,
                "ref_shift": doc.name,
            })

        # Create Sales Invoice
        sales_invoice = frappe.get_doc(invoice_data)
        sales_invoice.flags.ignore_permissions = True
        sales_invoice.insert()
        sales_invoice.submit()

        created_invoices.append({
            "name": sales_invoice.name,
            "customer": sales_invoice.customer,
            "grand_total": sales_invoice.grand_total
        })

    return created_invoices


def create_fuel_ledgers_from_dip_readings(doc: Document | ShiftClosingEntry | str):
    """
    Create Fuel Ledger documents from Shift Closing Entry dip readings.

    Args:
        doc (Document | ShiftClosingEntry | str): Shift Closing Entry document or name

    Returns:
        list: List of created Fuel Ledger documents

    Raises:
        frappe.ValidationError: If no dip readings exist
    """
    if isinstance(doc, str):
        doc = frappe.get_doc("Shift Closing Entry", doc)

    if not doc.dip_readings:
        frappe.throw(
            "No dip readings found to create Fuel Ledgers.",
            frappe.ValidationError
        )

    created_ledgers = []

    def get_tank_sales(tank):
        return sum(dip.sales_qty for dip in doc.meter_readings if dip.tank == tank)

    def get_tank_returns(tank):
        return sum(dip.return_to_tank for dip in doc.meter_readings if dip.tank == tank)

    for dip_reading in doc.dip_readings:
        # Create FuelLedgerData dataclass instance
        ledger_data = FuelLedgerData(
            fuel_item=dip_reading.fuel_item,
            fuel_tank=dip_reading.tank,
            opening_book_balance=dip_reading.opening or 0,
            physical_dip_reading_liters=dip_reading.physical_liters,
            posting_date=today(),
            posting_time=nowtime(),
            posting_datetime=get_datetime(),
            liters_in=0,
            liters_out=get_tank_sales(dip_reading.tank),
            return_to_tank=get_tank_returns(dip_reading.tank),
            physical_dip_reading_mm=dip_reading.physical_dip_mm,
            conversion_factor=None,
            water_level_mm=None,
            voucher_type="Shift Closing Entry",
            voucher_no=doc.name,
            voucher_detail_no=dip_reading.name,
            shortage_status="Normal"
        )

        # Create the Fuel Ledger
        fuel_ledger = create_fuel_ledger(ledger_data)
        created_ledgers.append(fuel_ledger)

    return created_ledgers


def cancel_invoices_from_shift_closing(doc: Document | ShiftClosingEntry | str):
    """
    Cancel all Sales Invoices created from a Shift Closing Entry.

    Args:
        doc (Document | ShiftClosingEntry | str): Shift Closing Entry document or name

    Returns:
        list: List of cancelled Sales Invoice names
            ["SINV-00001", "SINV-00002"]
    """
    if isinstance(doc, str):
        doc = frappe.get_doc("Shift Closing Entry", doc)

    # Find all Sales Invoices linked to this shift closing entry
    invoice_items = frappe.get_all(
        "Sales Invoice Item",
        filters={
            "ref_shift": doc.name
        },
        pluck="parent",
    )

    cancelled_invoices = []

    for invoice in invoice_items:
        # Check if any item in this invoice has ref_shift matching this shift closing entry
        invoice_doc = frappe.get_doc("Sales Invoice", invoice)

        try:
            invoice_doc.flags.ignore_permissions = True
            if invoice_doc.docstatus == 1:
                invoice_doc.cancel()
                cancelled_invoices.append(invoice_doc.name)
        except Exception as e:
            frappe.log_error(
                title=f"Error Cancelling Invoice {invoice_doc.name}",
                message=str(e)
            )

    return cancelled_invoices

def cancel_pump_meter_readings(doc: Document | ShiftClosingEntry | str):
    """
    Cancel all Pump Meter Reading entries linked to a Shift Closing Entry.
    Marks pump meter readings as cancelled (is_cancelled = 1).

    Args:
        doc (Document | ShiftClosingEntry | str): Shift Closing Entry document or name

    Returns:
        int: Number of Pump Meter Readings cancelled
    """
    if isinstance(doc, str):
        doc = frappe.get_doc("Shift Closing Entry", doc)

    # Find all Pump Meter Readings linked to this shift closing entry
    pump_readings = frappe.get_all(
        "Pump Meter Reading",
        filters={
            "voucher_type": "Shift Closing Entry",
            "voucher_no": doc.name,
            "is_cancelled": 0
        },
        pluck="name"
    )

    if not pump_readings:
        return 0

    # Mark each reading as cancelled
    for reading_name in pump_readings:
        reading = frappe.get_doc("Pump Meter Reading", reading_name)
        reading.is_cancelled = 1
        reading.save(ignore_permissions=True)

    frappe.db.commit()

    return len(pump_readings)


def cancel_fuel_ledgers(doc: Document | ShiftClosingEntry | str):
    """
    Cancel all Fuel Ledger entries linked to a Shift Closing Entry.
    Marks fuel ledgers as cancelled (is_cancelled = 1).
    """
    if isinstance(doc, str):
        doc = frappe.get_doc("Shift Closing Entry", doc)

    cancel_fuel_ledgers_by_voucher(doc.doctype, doc.name)


def create_journal_entries_for_expenses(doc: Document | ShiftClosingEntry | str):
    """
    Create Journal Entry documents from expenses in a Shift Closing Entry.
    Expenses are grouped by mode_of_payment so one Journal Entry is created
    per payment method.

    Each Journal Entry contains:
    - A debit row for each expense account
    - A credit row for each expense against the mode of payment's default account

    Args:
        doc (Document | ShiftClosingEntry | str): Shift Closing Entry document or name

    Returns:
        list: List of created Journal Entry names
    """
    if isinstance(doc, str):
        doc = frappe.get_doc("Shift Closing Entry", doc)

    if not doc.expenses:
        return []

    # Group expenses by mode_of_payment
    expenses_by_mop = {}
    for expense in doc.expenses:
        mop = expense.mode_of_payment
        if mop not in expenses_by_mop:
            expenses_by_mop[mop] = []
        expenses_by_mop[mop].append(expense)

    created_journals = []

    for mode_of_payment, expenses in expenses_by_mop.items():
        # Get the default account for this mode of payment and company
        payment_account = frappe.db.get_value(
            "Mode of Payment Account",
            {"parent": mode_of_payment, "company": doc.company},
            "default_account"
        )

        if not payment_account:
            frappe.throw(
                f"No default account found for Mode of Payment '{mode_of_payment}' "
                f"and Company '{doc.company}'. Please set it up in Mode of Payment master.",
                frappe.ValidationError
            )

        # Build journal entry
        journal_entry = frappe.get_doc({
            "doctype": "Journal Entry",
            "posting_date": doc.posting_date,
            "company": doc.company,
            "voucher_type": "Journal Entry",
            "accounts": []
        })

        for expense in expenses:
            # Debit the expense account
            journal_entry.append("accounts", {
                "account": expense.expense,
                "debit_in_account_currency": flt(expense.amount),
                "credit_in_account_currency": 0,
                "reference_type": "Shift Closing Entry",
                "reference_name": doc.name,
                "reference_detail_no": expense.name,
                "user_remark": expense.remarks or ""
            })

            # Credit the mode of payment account
            journal_entry.append("accounts", {
                "account": payment_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": flt(expense.amount),
                "reference_type": "Shift Closing Entry",
                "reference_name": doc.name,
                "reference_detail_no": expense.name,
                "user_remark": expense.remarks or ""
            })

        journal_entry.flags.ignore_permissions = True
        journal_entry.insert()
        journal_entry.submit()

        created_journals.append(journal_entry.name)

    return created_journals


def cancel_journal_entries_for_expenses(doc: Document | ShiftClosingEntry | str):
    """
    Cancel all Journal Entries created from a Shift Closing Entry's expenses.

    Args:
        doc (Document | ShiftClosingEntry | str): Shift Closing Entry document or name

    Returns:
        list: List of cancelled Journal Entry names
    """
    if isinstance(doc, str):
        doc = frappe.get_doc("Shift Closing Entry", doc)

    # Find all Journal Entry Account rows referencing this Shift Closing Entry
    journal_entries = frappe.get_all(
        "Journal Entry Account",
        filters={
            "reference_type": "Shift Closing Entry",
            "reference_name": doc.name,
            "docstatus": 1
        },
        pluck="parent",
        distinct=True
    )

    cancelled_journals = []

    for je_name in journal_entries:
        try:
            je_doc = frappe.get_doc("Journal Entry", je_name)
            if je_doc.docstatus == 1:
                je_doc.flags.ignore_permissions = True
                je_doc.cancel()
                cancelled_journals.append(je_name)
        except Exception as e:
            frappe.log_error(
                title=f"Error Cancelling Journal Entry {je_name}",
                message=str(e)
            )

    return cancelled_journals
