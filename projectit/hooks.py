app_name = "projectit"
app_title = "Projectit"
app_publisher = "frappe.dev@arus.co.in"
app_description = "Project Cost Tracking Tool"
app_email = "frappe.dev@arus.co.in"
app_license = "gpl-3.0"
required_apps = ["frappe","erpnext","hrms"]

fixtures = [
    {"dt" : "Custom Field", "filters" : [["module" , "=" , "Projectit"]] },
    {"dt" : "Property Setter", "filters" : [["module" , "=" , "Projectit"]] },
    {"dt" : "DocType Link", "filters" : [["name" , "=" , "v8sdmt8hqv"]] },
    {"dt" : "Mobile Module Item" }
    ]

# include js in doctype views
# doctype_js removed — project.js was ManageIT/WorkIT only

# Document Events
doc_events = {
    "Timesheet" : {
        "on_submit" : "projectit.projectit.timesheet.on_submit_of_timesheet"
    }
}

website_route_rules = [ {'from_route': '/projectit/<path:app_path>', 'to_route': 'projectit'},]
