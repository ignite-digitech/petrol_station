// Copyright (c) 2026, Ignite Digital and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fuel Pump", {
	refresh(frm) {
        frm.add_custom_button(__("Create Tank"), function() {
            createTank(frm);
        })

        frm.set_query("nozzle", "initial_readings", function(doc, cdt, cdn) {
            return {
                filters: {
                    "pump": doc.name
                }
            }
        })

        if (frm.is_new()){
            frm.set_df_property("initial_readings", "hidden", 1)
        }
	},
});

function createTank(frm){
    let dialog = new frappe.ui.Dialog({
                    title: __("Create Fuel Tank"),
                    fields: [
                        {
                            label: __("Tank Name"),
                            fieldname: "tank_name",
                            fieldtype: "Data",
                            reqd: 1
                        },
                        {
                            label: __("Fuel Item"),
                            fieldname: "fuel_item",
                            fieldtype: "Link",
                            options: "Item",
                            reqd: 1,
                            get_query: () => {
                                return {
                                    filters: {
                                        item_group: "Fuel"
                                    }
                                };
                            }
                        }
                    ],
                    size: "medium",
                    primary_action_label: __("Create"),
                    primary_action(values) {
                        // Get company and its abbreviation
                        let company = frm.doc.company || frappe.defaults.get_default("company");

                        frappe.db.get_value("Company", company, "abbr", (r) => {
                            if (r && r.abbr) {
                                let parent_warehouse = `Fuel Tanks - ${r.abbr}`;

                                frappe.call({
                                    method: "frappe.client.insert",
                                    args: {
                                        doc: {
                                            doctype: "Warehouse",
                                            warehouse_name: values.tank_name,
                                            warehouse_type: "Fuel Tank",
                                            is_group: 0,
                                            company: company,
                                            parent_warehouse: parent_warehouse,
                                            fuel_item: values.fuel_item
                                        }
                                    },
                                    callback: (r) => {
                                        if (r.message) {
                                            frappe.msgprint(__("Fuel Tank {0} created successfully", [r.message.name]));
                                            frm.set_value("tank", r.message.name);
                                            dialog.hide();
                                        }
                                    }
                                });
                            }
                        });
                    }
        });
    dialog.show();
}
