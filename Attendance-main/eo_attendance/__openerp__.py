{
    "name" : "eoAttendance",
    "version" : "1.0",
    "author" : "Elastoffice",
    "category" : "Extra Tools",
    "description": """
eoAttendance
============
Module for Attendance/Wifi/Location/ management. You can manage:

* Attendance logs
* Person
* Check In, Check out
* Location

    """,
    "depends" : ['base', 'crm', 'web'],
    "init_xml" : [],
    "js" : ["static/src/js/show_realtime.js",],
    "qweb" : ["static/src/xml/*.xml",],
    "demo_xml" : [],
    "update_xml" : [
                    "security/eoattendance_security.xml",
                    "security/ir.model.access.csv",
                    "menu.xml",
                    "attendance_view.xml",
                    "report/eoattendance_report.xml",
                    "wizard/wizard_rp.xml",
                    "show_messages.xml", 
    ],
    "installable": True,
    'application': True,
    'css' : ["static/src/css/show_realtime.css"],
}