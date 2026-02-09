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

frappe.ui.form.on("Shift Opening Meter Reading", {
	nozzle(frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		if (row.nozzle) {
			// Auto-fetch the last closing qty for this nozzle
			frappe.call({
				method: 'petrol_station.petrol_station.doctype.pump_meter_reading.pump_meter_reading.auto_fetch_nozzle_opening_reading',
				args: {
					nozzle: row.nozzle,
					posting_date: frm.doc.posting_date,
					posting_time: frm.doc.posting_time
				},
				freeze: true,
				freeze_message: __('Fetching last closing reading for {0}', [row.nozzle]),
				callback: function(r) {
					if (r.message) {
						frappe.model.set_value(cdt, cdn, 'opening_reading', r.message.opening_reading);
						frappe.model.set_value(cdt, cdn, 'expected_reading', r.message.expected_reading);
					}
				}
			});
		}
	}
});
