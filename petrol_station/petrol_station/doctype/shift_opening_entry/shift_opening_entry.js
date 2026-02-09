// Copyright (c) 2026, Ignite Digital and contributors
// For license information, please see license.txt

frappe.ui.form.on("Shift Opening Entry", {
	refresh(frm) {
        if (frappe.model.can_create('Tank Dip Log')){
            frm.add_custom_button(__('Create Ta     nk Dip Log'), function() {
                frm.trigger('create_tank_dip_log');
            }, 'Create');
        }
	},

	onload(frm) {
		frm.trigger('check_tank_dip_logs');
	},

	check_tank_dip_logs(frm) {
		frappe.call({
			method: 'petrol_station.petrol_station.doctype.tank_dip_log.tank_dip_log.get_tank_dip_logs_by_date',
			callback: function(r) {
				if (r.message && r.message.length === 0) {
					// Check if user has permission to create Tank Dip Log
					if (frappe.model.can_create('Tank Dip Log')) {
						frappe.msgprint({
							title: __('Warning'),
							indicator: 'orange',
							message: __('No Tank Dip Logs found for today.'),
							primary_action: {
								label: __('Create Tank Dip Log'),
								action: function() {
									frm.trigger('create_tank_dip_log');
								}
							}
						});
					} else {
						frappe.msgprint({
							title: __('Warning'),
							indicator: 'orange',
							message: __('No Tank Dip Logs found for today.')
						});
					}
				}
			}
		});
	},

    create_tank_dip_log: function(frm) {
        frappe.new_doc('Tank Dip Log', {
            posting_date: frm.doc.posting_date || frappe.datetime.get_today(),
            posting_time: frm.doc.posting_time || frappe.datetime.now_time(),
            posting_datetime: frm.doc.posting_datetime || frappe.datetime.now_datetime()
        });
    }
});
