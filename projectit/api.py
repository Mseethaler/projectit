import frappe
from datetime import date, datetime, timedelta


# ---------------------------------------------------------------------------
# Original ProjectIT endpoints
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_employee_id(user_id):
    employee = frappe.db.get_value(
        "Employee",
        {"user_id": user_id},
        ["name", "employee_name", "company"],
        as_dict=True,
    )
    if employee:
        return employee


@frappe.whitelist()
def get_project_allocation(employee_id):
    if frappe.has_permission("Project", ptype="read"):
        project_list = frappe.db.sql("""
            select pai.project_name
            from `tabProject Allocation and Instrucions` as pai
            left join `tabEmployee Allocation Instruction` as eai on eai.parent = pai.name
            left join tabProject as p on p.name = pai.project
            where eai.employee = %(employee_id)s and p.status = 'Open'
            """, {"employee_id": employee_id}, as_dict=True)
        return project_list
    else:
        return []


@frappe.whitelist()
def upload_base64_file(content, filename, dt=None, dn=None, fieldname=None):
    import base64
    import io
    from mimetypes import guess_type

    from PIL import Image, ImageOps
    from frappe.handler import ALLOWED_MIMETYPES

    decoded_content = base64.b64decode(content)
    content_type = guess_type(filename)[0]
    if content_type not in ALLOWED_MIMETYPES:
        frappe.throw(_("You can only upload JPG, PNG, PDF, TXT or Microsoft documents."))

    if content_type.startswith("image/jpeg"):
        with Image.open(io.BytesIO(decoded_content)) as image:
            transpose_img = ImageOps.exif_transpose(image)
            file_content = io.BytesIO()
            transpose_img.save(file_content, format="JPEG")
            file_content = file_content.getvalue()
    else:
        file_content = decoded_content

    return frappe.get_doc({
        "doctype": "File",
        "attached_to_doctype": dt,
        "attached_to_name": dn,
        "attached_to_field": fieldname,
        "folder": "Home",
        "file_name": filename,
        "content": file_content,
        "is_private": 0,
    }).insert()


@frappe.whitelist()
def get_work_time_settings():
    return frappe.get_single("Work Time Settings")


@frappe.whitelist(allow_guest=True)
def get_header_info():
    app_logo = frappe.get_single("Navbar Settings").app_logo
    company = frappe.get_single("Global Defaults").default_company
    return app_logo, company


@frappe.whitelist()
def get_instructions(project_name, employee_id):
    if frappe.has_permission("Project", ptype="read"):
        data = frappe.db.sql("""
            SELECT pai.work_instruction, eai.instructions
            FROM `tabProject Allocation and Instrucions` as pai
            LEFT JOIN `tabEmployee Allocation Instruction` as eai
                ON eai.employee = %(employee)s and eai.parent = pai.name
            WHERE pai.project_name = %(project_name)s
            ORDER BY eai.modified DESC
            LIMIT 1
            """, {"employee": employee_id, "project_name": project_name}, as_dict=True)
        return data
    else:
        return []


@frappe.whitelist()
def get_team_members(project_name):
    if frappe.has_permission("Project", ptype="read"):
        data = frappe.db.sql("""
            select project_name,
            CONCAT('[',GROUP_CONCAT(JSON_OBJECT("employee_name",employee_name,"activity" , activity)),']') as members
            from(
                select eai.employee_name, pai.project_name, case when t.start_date then 'active' else 'inactive' end as activity
                from `tabProject Allocation and Instrucions` as pai
                left join `tabEmployee Allocation Instruction` as eai on eai.parent = pai.name
                left join `tabTimesheet` as t
                    on
                        t.employee = eai.employee
                        and t.parent_project = pai.project
                        and t.start_date = %(today)s
                        and t.docstatus = 0
                where pai.project_name = %(project_name)s
                ) as ts
            """, {"today": date.today(), "project_name": project_name}, as_dict=True)
        return data
    else:
        return []


@frappe.whitelist()
def get_employee_schedule(date, employee_id):
    if frappe.has_permission("Project", ptype="read"):
        project_list = frappe.db.sql("""
            select pai.project_name
            from `tabEmployee Allocation Instruction` as eai
            left join `tabProject Allocation and Instrucions` as pai on eai.parent = pai.name
            where eai.employee = %(employee_id)s
            """, {"employee_id": employee_id}, as_dict=True)
        return project_list

    frappe.throw(msg="You Don't have enough Permission", exc=PermissionError)


@frappe.whitelist()
def project_with_members(employee_id):
    employee_id = get_employee_id(frappe.session.user)
    if employee_id:
        modules = frappe.get_list(
            "Mobile Module",
            parent_doctype="Employee",
            fields=["module_name"],
            filters={"parent": employee_id.name},
            pluck="module_name",
        )

        if "ManageIT" in modules:
            data = frappe.db.sql("""
                select p.project_name,
                CONCAT('[',GROUP_CONCAT(JSON_OBJECT("employee_name",employee_name,"activity" , activity)),']') as members
                from(
                    select eai.employee_name, pai.project_name, case when t.start_date then 'active' else 'inactive' end as activity
                    from `tabProject Allocation and Instrucions` as pai
                    right join `tabEmployee Allocation Instruction` as eai on eai.parent = pai.name
                    left join `tabTimesheet` as t
                        on
                            t.employee = eai.employee
                            and t.parent_project = pai.project
                            and t.start_date = %(today)s
                            and t.docstatus = 0
                    ) as ts
                RIGHT JOIN tabProject as p ON p.project_name = ts.project_name
                WHERE p.status = 'Open'
                GROUP BY project_name
                """, {"today": date.today()}, as_dict=True)
            return data

    frappe.throw(msg="You Don't have enough Permission", exc=PermissionError)


@frappe.whitelist()
def get_project_list():
    project_list = frappe.get_list("Project", filters={"status": 'Open'}, fields=["project_name"])
    return project_list


@frappe.whitelist()
def get_modules_for_router(user_id):
    employee_id = get_employee_id(user_id)
    modules = frappe.get_list(
        "Mobile Module",
        parent_doctype="Employee",
        fields=["module_name"],
        filters={"parent": employee_id.name},
        pluck="module_name",
    )
    modules.append('home')
    modules = [m.lower() for m in modules]
    return modules


@frappe.whitelist()
def get_employee_with_workit(project_name):
    if frappe.has_permission("Employee", ptype="read"):
        employee = frappe.db.sql("""
            select mm.parent as name, e.employee_name
            from `tabMobile Module` as mm
            left join tabEmployee as e on mm.parent = e.name
            where module_name = "WorkIT"
            except
            select eai.employee as name, eai.employee_name
            from `tabProject Allocation and Instrucions` as pai
            left join `tabEmployee Allocation Instruction` as eai on eai.parent = pai.name
            where pai.project_name = %(project_name)s
            """, {"project_name": project_name}, as_dict=True)
        return employee
    else:
        return []


# ---------------------------------------------------------------------------
# RouteIT — Delivery Trip based field service
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_todays_route(employee_id, selected_date=None):
    """
    Returns the Delivery Trip for the given employee on the selected date.
    Defaults to today if no date provided.
    """
    today = selected_date if selected_date else date.today().strftime("%Y-%m-%d")

    driver = frappe.db.get_value("Driver", {"employee": employee_id}, "name")
    if not driver:
        return None

    trip = frappe.db.get_value(
        "Delivery Trip",
        {
            "driver": driver,
            "departure_time": ["between", [f"{today} 00:00:00", f"{today} 23:59:59"]],
            "docstatus": ["!=", 2],
        },
        ["name", "departure_time", "status"],
        as_dict=True,
    )

    if not trip:
        return None

    stops = frappe.db.get_all(
        "Delivery Stop",
        filters={"parent": trip.name},
        fields=[
            "name",
            "idx",
            "customer",
            "address",
            "customer_address",
            "delivery_note",
            "visited",
            "custom_status",
            "custom_checkin_time",
            "custom_checkout_time",
            "estimated_arrival",
            "grand_total",
            "contact",
            "customer_contact",
            "lat",
            "lng",
        ],
        order_by="idx asc",
    )

    for stop in stops:
        stop["address_display"] = stop.get("customer_address") or ""

        if stop.get("contact"):
            mobile = frappe.db.get_value("Contact", stop["contact"], "mobile_no")
            phone = frappe.db.get_value("Contact", stop["contact"], "phone")
            stop["phone"] = mobile or phone or ""
        elif stop.get("customer"):
            primary_contact = frappe.db.get_value(
                "Dynamic Link",
                {"link_doctype": "Customer", "link_name": stop["customer"], "parenttype": "Contact"},
                "parent",
                order_by="creation asc",
            )
            if primary_contact:
                mobile = frappe.db.get_value("Contact", primary_contact, "mobile_no")
                phone = frappe.db.get_value("Contact", primary_contact, "phone")
                stop["phone"] = mobile or phone or ""
            else:
                stop["phone"] = ""
        else:
            stop["phone"] = ""

        if not stop.get("custom_status"):
            stop["custom_status"] = "Pending"

        # Pull special instructions from Delivery Note
        if stop.get("delivery_note"):
            stop["special_instructions"] = frappe.db.get_value(
                "Delivery Note", stop["delivery_note"], "custom_sales_order_instructions"
            ) or ""
        else:
            stop["special_instructions"] = ""

    trip["stops"] = stops
    return trip


@frappe.whitelist()
def update_stop_status(trip_name, stop_name, status):
    """
    Updates custom_status on a Delivery Stop.
    Sets visited=1 and custom_checkout_time when Complete.
    Sets custom_checkin_time when In Progress.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    trip = frappe.get_doc("Delivery Trip", trip_name)
    for stop in trip.delivery_stops:
        if stop.name == stop_name:
            stop.custom_status = status
            if status == "In Progress":
                stop.custom_checkin_time = now
            elif status == "Complete":
                stop.custom_checkout_time = now
                stop.visited = 1
            break

    trip.flags.ignore_validate_update_after_submit = True
    trip.save(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "ok", "updated_status": status}


@frappe.whitelist()
def route_checkin(employee_id, trip_name, stop_name, latitude, longitude):
    """
    Called when tech taps Check In on a stop.
    1. Creates Employee Checkin IN record (HR)
    2. Adds a time log to today's Timesheet with GPS
    3. Stores GPS on Delivery Stop
    4. Updates stop status to In Progress
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = date.today().strftime("%Y-%m-%d")

    stop = frappe.db.get_value(
        "Delivery Stop",
        stop_name,
        ["customer", "delivery_note"],
        as_dict=True,
    )

    # 1. Employee Checkin IN
    frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": employee_id,
        "time": now,
        "log_type": "IN",
        "latitude": latitude,
        "longitude": longitude,
        "custom_delivery_trip": trip_name,
        "custom_delivery_stop": stop_name,
    }).insert(ignore_permissions=True)

    # 2. Find or create today's Timesheet
    activity_type = frappe.db.get_single_value(
        "Work Time Settings", "regular_time_activity_type"
    )
    company = frappe.db.get_value("Employee", employee_id, "company")

    existing_timesheet = frappe.db.get_value(
        "Timesheet",
        {"employee": employee_id, "start_date": today, "docstatus": 0},
        "name",
    )

    if existing_timesheet:
        timesheet = frappe.get_doc("Timesheet", existing_timesheet)
        timesheet.append("time_logs", {
            "from_time": now,
            "activity_type": activity_type,
            "description": f"Stop: {stop.get('customer', '')} | Trip: {trip_name}",
            "custom_delivery_stop": stop_name,
            "custom_checkin_lat": latitude,
            "custom_checkin_lng": longitude,
        })
        timesheet.save(ignore_permissions=True)
    else:
        timesheet = frappe.get_doc({
            "doctype": "Timesheet",
            "employee": employee_id,
            "start_date": today,
            "company": company,
            "time_logs": [{
                "from_time": now,
                "activity_type": activity_type,
                "description": f"Stop: {stop.get('customer', '')} | Trip: {trip_name}",
                "custom_delivery_stop": stop_name,
                "custom_checkin_lat": latitude,
                "custom_checkin_lng": longitude,
            }]
        })
        timesheet.insert(ignore_permissions=True)

    # 3. Store GPS on Delivery Stop
    frappe.db.set_value("Delivery Stop", stop_name, {
        "custom_checkin_lat": latitude,
        "custom_checkin_lng": longitude,
    }, update_modified=False)

    # 4. Update stop status
    update_stop_status(trip_name, stop_name, "In Progress")

    frappe.db.commit()
    return {"status": "ok", "timesheet": timesheet.name}


@frappe.whitelist()
def route_checkout(employee_id, trip_name, stop_name, latitude, longitude):
    """
    Called when tech taps Check Out on a stop.
    1. Creates Employee Checkin OUT record (HR)
    2. Closes the open Timesheet time log for this stop
    3. Stores GPS on Delivery Stop
    4. Updates stop status to Complete
    SMS is handled by the Vue app via send_route_sms after checkout.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = date.today().strftime("%Y-%m-%d")

    # 1. Employee Checkin OUT
    frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": employee_id,
        "time": now,
        "log_type": "OUT",
        "latitude": latitude,
        "longitude": longitude,
        "custom_delivery_trip": trip_name,
        "custom_delivery_stop": stop_name,
    }).insert(ignore_permissions=True)

    # 2. Close open time log for this stop
    timesheet_name = frappe.db.get_value(
        "Timesheet",
        {"employee": employee_id, "start_date": today, "docstatus": 0},
        "name",
    )

    if timesheet_name:
        timesheet = frappe.get_doc("Timesheet", timesheet_name)
        for log in timesheet.time_logs:
            if (
                getattr(log, "custom_delivery_stop", None) == stop_name
                and not log.to_time
            ):
                log.to_time = now
                from_dt = datetime.strptime(str(log.from_time), "%Y-%m-%d %H:%M:%S")
                to_dt = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
                log.hours = round((to_dt - from_dt).seconds / 3600, 4)
                break
        timesheet.save(ignore_permissions=True)

    # 3. Store GPS on Delivery Stop
    frappe.db.set_value("Delivery Stop", stop_name, {
        "custom_checkout_lat": latitude,
        "custom_checkout_lng": longitude,
    }, update_modified=False)

    # 4. Update stop status to Complete
    update_stop_status(trip_name, stop_name, "Complete")

    frappe.db.commit()
    return {"status": "ok"}


@frappe.whitelist()
def send_route_sms(stop_name, contact_name, template_type, message=None):
    """
    Sends SMS via ERPNext SMS Center.
    template_type: "omw" | "complete"
    message: if provided by the Vue app, uses this directly instead of template.
    """
    mobile = frappe.db.get_value("Contact", contact_name, "mobile_no")
    phone = frappe.db.get_value("Contact", contact_name, "phone")
    phone = mobile or phone
    if not phone:
        frappe.log_error(f"No phone for contact {contact_name}", "RouteIT SMS")
        return {"status": "no_phone"}

    # Use the message passed from the Vue app if provided
    if not message:
        try:
            settings = frappe.get_single("Field Service Settings")
            if template_type == "omw":
                message = getattr(settings, "omw_sms_template", None) or \
                    "Your technician is on the way. Thank you for your business!"
            else:
                message = getattr(settings, "complete_sms_template", None) or \
                    "Your service has been completed. Thank you for your business!"
        except Exception:
            message = "Your technician is on the way." if template_type == "omw" \
                else "Your service has been completed."

    try:
        from frappe.core.doctype.sms_settings.sms_settings import send_sms
        send_sms([phone], message)
        return {"status": "sent", "phone": phone}
    except Exception as e:
        frappe.log_error(str(e), "RouteIT SMS Error")
        return {"status": "error", "message": str(e)}


# ---------------------------------------------------------------------------
# Clock — Start Day / End Day (shared across RouteIT and ServiceIT)
# ---------------------------------------------------------------------------

@frappe.whitelist()
def start_day(employee_id, latitude, longitude):
    """
    Creates an Employee Checkin IN for the work day.
    Allows multiple check-ins per day — no guard against double clock-in.
    ERPNext Auto Attendance uses first IN and last OUT automatically.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    checkin = frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": employee_id,
        "time": now,
        "log_type": "IN",
        "latitude": latitude,
        "longitude": longitude,
    })
    checkin.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "ok", "checkin": checkin.name, "time": now}


@frappe.whitelist()
def end_day(employee_id, latitude, longitude):
    """
    Creates an Employee Checkin OUT for the work day.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    checkin = frappe.get_doc({
        "doctype": "Employee Checkin",
        "employee": employee_id,
        "time": now,
        "log_type": "OUT",
        "latitude": latitude,
        "longitude": longitude,
    })
    checkin.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "ok", "checkin": checkin.name, "time": now}


@frappe.whitelist()
def get_clock_status(employee_id):
    """
    Returns today's clock status and total billed hours for the Clock tab.
    Uses first IN and last OUT of the day.
    currently_in is true if the last checkin action was IN.
    """
    today = date.today().strftime("%Y-%m-%d")

    # First IN of the day
    checkin = frappe.db.get_value(
        "Employee Checkin",
        {
            "employee": employee_id,
            "log_type": "IN",
            "time": ["between", [f"{today} 00:00:00", f"{today} 23:59:59"]],
            "custom_delivery_stop": ["is", "not set"],
        },
        ["name", "time"],
        as_dict=True,
        order_by="time asc",
    )

    # Last OUT of the day
    checkout = frappe.db.get_value(
        "Employee Checkin",
        {
            "employee": employee_id,
            "log_type": "OUT",
            "time": ["between", [f"{today} 00:00:00", f"{today} 23:59:59"]],
            "custom_delivery_stop": ["is", "not set"],
        },
        ["name", "time"],
        as_dict=True,
        order_by="time desc",
    )

    # Most recent checkin to determine current state (IN or OUT)
    last_checkin = frappe.db.get_value(
        "Employee Checkin",
        {
            "employee": employee_id,
            "time": ["between", [f"{today} 00:00:00", f"{today} 23:59:59"]],
            "custom_delivery_stop": ["is", "not set"],
        },
        ["name", "time", "log_type"],
        as_dict=True,
        order_by="time desc",
    )

    timesheet = frappe.db.get_value(
        "Timesheet",
        {"employee": employee_id, "start_date": today, "docstatus": ["!=", 2]},
        ["name", "total_hours"],
        as_dict=True,
    )

    currently_in = last_checkin and last_checkin.log_type == "IN"

    return {
        "clocked_in": bool(checkin),
        "currently_in": currently_in,
        "clocked_out": bool(checkout),
        "checkin_time": checkin.time if checkin else None,
        "checkout_time": checkout.time if checkout else None,
        "total_billed_hours": timesheet.total_hours if timesheet else 0,
        "timesheet": timesheet.name if timesheet else None,
    }


@frappe.whitelist()
def get_attendance_entries(employee_id, days=30):
    """
    Returns clock in/out history for the employee.
    Groups by date, using first IN and last OUT per day.
    Excludes stop-level checkins (custom_delivery_stop is set).
    Returns last N days, most recent first.
    """
    from_date = (datetime.now() - timedelta(days=int(days))).strftime("%Y-%m-%d")

    records = frappe.db.get_all(
        "Employee Checkin",
        filters={
            "employee": employee_id,
            "time": [">=", f"{from_date} 00:00:00"],
            "custom_delivery_stop": ["in", ["", None]],
        },
        fields=["log_type", "time"],
        order_by="time asc",
    )

    # Group by date
    days_map = {}
    for r in records:
        day = str(r.time)[:10]
        if day not in days_map:
            days_map[day] = {"first_in": None, "last_out": None}
        if r.log_type == "IN" and not days_map[day]["first_in"]:
            days_map[day]["first_in"] = r.time
        if r.log_type == "OUT":
            days_map[day]["last_out"] = r.time

    entries = []
    for day, data in sorted(days_map.items(), reverse=True):
        first_in = data["first_in"]
        last_out = data["last_out"]

        if first_in and last_out:
            diff = datetime.strptime(str(last_out)[:19], "%Y-%m-%d %H:%M:%S") - \
                   datetime.strptime(str(first_in)[:19], "%Y-%m-%d %H:%M:%S")
            hours = round(diff.seconds / 3600, 1)
        else:
            hours = None

        entries.append({
            "date": day,
            "clock_in": datetime.strptime(str(first_in)[:19], "%Y-%m-%d %H:%M:%S").strftime("%I:%M %p") if first_in else None,
            "clock_out": datetime.strptime(str(last_out)[:19], "%Y-%m-%d %H:%M:%S").strftime("%I:%M %p") if last_out else None,
            "hours": hours,
        })

    return entries
