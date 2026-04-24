app_name = "smr"
app_title = "SMR"
app_publisher = "SMR"
app_description = "SMR"
app_email = "smr@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "smr",
# 		"logo": "/assets/smr/logo.png",
# 		"title": "SMR",
# 		"route": "/smr",
# 		"has_permission": "smr.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/smr/css/smr.css"
# app_include_js = "/assets/smr/js/smr.js"

# include js, css files in header of web template
# web_include_css = "/assets/smr/css/smr.css"
# web_include_js = "/assets/smr/js/smr.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "smr/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
doctype_js = {
    "Lead" : "public/js/lead.js"
}

# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "smr/public/icons.svg"

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

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "smr.utils.jinja_methods",
# 	"filters": "smr.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "smr.install.before_install"
# after_install = "smr.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "smr.uninstall.before_uninstall"
# after_uninstall = "smr.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "smr.utils.before_app_install"
# after_app_install = "smr.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "smr.utils.before_app_uninstall"
# after_app_uninstall = "smr.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "smr.notifications.get_notification_config"

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

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events
doc_events = {
    "Quotation": {
        "before_save": "smr.smr.custom_script.quotation.before_save",
        "before_cancel": "smr.smr.custom_script.quotation.before_cancel",
        "on_trash": "smr.smr.custom_script.quotation.on_trash",
    },
    "Sales Invoice":{
        "on_update_after_submit": "smr.smr.custom_script.api.on_update_after_submit",

    }
}
# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"smr.tasks.all"
# 	],
# 	"daily": [
# 		"smr.tasks.daily"
# 	],
# 	"hourly": [
# 		"smr.tasks.hourly"
# 	],
# 	"weekly": [
# 		"smr.tasks.weekly"
# 	],
# 	"monthly": [
# 		"smr.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "smr.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "smr.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "smr.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["smr.utils.before_request"]
# after_request = ["smr.utils.after_request"]

# Job Events
# ----------
# before_job = ["smr.utils.before_job"]
# after_job = ["smr.utils.after_job"]

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
# 	"smr.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

