app_name = "petrol_station"
app_title = "Petrol Station"
app_publisher = "Ignite Digital"
app_description = "Petrol Station Management app"
app_email = "hello@igniteug.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "petrol_station",
# 		"logo": "/assets/petrol_station/logo.png",
# 		"title": "Petrol Station",
# 		"route": "/petrol_station",
# 		"has_permission": "petrol_station.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/petrol_station/css/petrol_station.css"
app_include_js = "/assets/petrol_station/js/petrol_station.bundle.js"

# include js, css files in header of web template
# web_include_css = "/assets/petrol_station/css/petrol_station.css"
# web_include_js = "/assets/petrol_station/js/petrol_station.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "petrol_station/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "petrol_station/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "petrol_station.utils.jinja_methods",
# 	"filters": "petrol_station.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "petrol_station.install.before_install"
# after_install = "petrol_station.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "petrol_station.uninstall.before_uninstall"
# after_uninstall = "petrol_station.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "petrol_station.utils.before_app_install"
# after_app_install = "petrol_station.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "petrol_station.utils.before_app_uninstall"
# after_app_uninstall = "petrol_station.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "petrol_station.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

doc_events = {
	"Purchase Receipt": {
		"on_submit": "petrol_station.overrides.purchase_receipt.on_submit",
		"on_cancel": "petrol_station.overrides.purchase_receipt.on_cancel"
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"petrol_station.tasks.all"
# 	],
# 	"daily": [
# 		"petrol_station.tasks.daily"
# 	],
# 	"hourly": [
# 		"petrol_station.tasks.hourly"
# 	],
# 	"weekly": [
# 		"petrol_station.tasks.weekly"
# 	],
# 	"monthly": [
# 		"petrol_station.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "petrol_station.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "petrol_station.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "petrol_station.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["petrol_station.utils.before_request"]
# after_request = ["petrol_station.utils.after_request"]

# Job Events
# ----------
# before_job = ["petrol_station.utils.before_job"]
# after_job = ["petrol_station.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"petrol_station.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

