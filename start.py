#!/usr/bin/python3

from datetime import datetime, timedelta
from configparser import ConfigParser
import time
from ast import literal_eval as make_tuple
from icalendar import Calendar
import requests
import pytz
import recurring_ical_events

def ordinal(n: int):
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    return str(n) + suffix

dtend = []
dtstart = []
priority = []
status = []
location = []
name = []
isimportant = []

def fuckswap(a, b):
    dtstart[a], dtstart[b] = dtstart[b], dtstart[a]
    dtend[a], dtend[b] = dtend[b], dtend[a]
    priority[a], priority[b] = priority[b], priority[a]
    status[a], status[b] = status[b], status[a]
    location[a], location[b] = location[b], location[a]
    name[a], name[b] = name[b], name[a]
    isimportant[a], isimportant[b] = isimportant[b], isimportant[a]

while (True):

    config_object = ConfigParser()
    config_object.read("config.ini")

    readinfo = config_object["CALENDAR"]
    url = make_tuple(str(readinfo["url"]))
    tz_user = pytz.timezone(readinfo["timezone"])
    regenerate_interval = int(readinfo["regenerate_interval"])
    hide_events = str(readinfo["hide_events"])

    readinfo2 = config_object["SITE"]
    if (str(readinfo2["no_unknown"]) == "True"):
        no_unknown = True
    else:
        no_unknown = False
    started_text = str(readinfo2["started_text"])
    ended_text = str(readinfo2["ended_text"])
    confirmed_text = str(readinfo2["confirmed_text"])
    cancelled_text = str(readinfo2["cancelled_text"])
    tentative_text = str(readinfo2["tentative_text"])
    unspecified_text = str(readinfo2["unspecified_text"])
    display_location = str(readinfo2["display_location"])
    refresh_interval = int(readinfo2["refresh_interval"])
    location_link = str(readinfo2["location_link"])
    search_bar = str(readinfo2["search_bar"])
    importance_in_status = str(readinfo2["importance_in_status"])
    important_text = str(readinfo2["important_text"])
    scrolltext = str(readinfo2["scrolltext"])

    dtend = []
    dtstart = []
    priority = []
    status = []
    location = []
    name = []
    isimportant = []
 
    all_count = 0  # all_count is only for debug and display purposes.
    shown_count = 0  # shown_count is only for debug and display purposes.
 
 
    now = datetime.now(tz_user)

    allevents = []
    
    for item in url:
        r = requests.get(item, allow_redirects=True, timeout=10)
        open('data.ics', 'wb').write(r.content)

        e = open('data.ics', 'rb')
        ecal = Calendar.from_ical(e.read())
        e.close()
        filter_mode = str(readinfo["filter_mode"])

        if (filter_mode == "Specific"):
            begindate = make_tuple(str(readinfo["specific_start"]))
            enddate = make_tuple(str(readinfo["specific_end"]))
            if (begindate == enddate):
                allevents = allevents + recurring_ical_events.of(ecal).at(begindate)
            else:
                allevents = allevents + recurring_ical_events.of(
                    ecal).between(begindate, enddate)
        elif (filter_mode == "Relative"):
            begindate = int(readinfo["relative_start"])
            enddate = int(readinfo["relative_end"])
            allevents = allevents + recurring_ical_events.of(ecal).between(datetime(now.year, now.month, now.day) + timedelta(
                begindate), datetime(now.year, now.month, now.day) + timedelta(enddate, 59, 999, 999, 59, 23))
        else:
            allevents = allevents + recurring_ical_events.of(ecal).between(datetime(
                now.year, now.month, now.day), datetime(now.year, now.month, now.day) + timedelta(14))
        for event in recurring_ical_events.of(ecal).between((1969), (2099)):
            all_count += 1
    
    for event in allevents:
        shown_count += 1

        format_datetime = True  # For End Times
        format_datetime2 = True  # For Start Times
        before_today = False
        today_done = False
        ongoing = False

        try:
            timeend = event["DTEND"].dt
        except KeyError:
            timeend = event["DTSTART"].dt

        combine_end = datetime.combine(timeend, datetime.min.time(), tz_user)
        
        if timeend.tzinfo == None: #no timezone (timezone unaware)
            timeend = datetime.combine(timeend.date(), timeend.time(), tz_user)

        try:
            delta: timedelta = timeend - now
        except TypeError:
            format_datetime = False
            delta: timedelta = combine_end - now

        if (format_datetime):
            delta: timedelta = timeend.astimezone(tz_user) - now
            realenddate = timeend.astimezone(tz_user)
        else:
            delta: timedelta = combine_end.astimezone(tz_user) - now
            realenddate = combine_end.astimezone(tz_user)

        if (delta.days < -1 or (delta.days == -1 and realenddate.day != now.day)):
            before_today = True # Event has concluded before today
        elif (delta.days == -1 and realenddate.day == now.day):
            today_done = True # Event has concluded today

        if (hide_events == "All" and (before_today or today_done)):
            continue
        if (hide_events == "Today" and before_today):
            continue

        timestart = event["DTSTART"].dt

        combine_start = datetime.combine(
            timestart, datetime.min.time(), tz_user)

        if timestart.tzinfo == None: #no timezone (timezone unaware)
            timestart = datetime.combine(timestart.date(), timestart.time(), tz_user)

        try:
            delta2: timedelta = timestart - now
        except TypeError:
            format_datetime2 = False
            delta2: timedelta = combine_start - now

        if (format_datetime2):
            delta2: timedelta = timestart.astimezone(tz_user) - now
            realstartdate = timestart.astimezone(tz_user)
        else:
            delta: timedelta = combine_start.astimezone(tz_user) - now
            realstartdate = combine_start.astimezone(tz_user)

        if (delta2.days < 0 and (not today_done) and (not before_today)):
            ongoing = True

        dtend.append(realenddate)
        dtstart.append(realstartdate)

        name.append(event["SUMMARY"])

        try:
            prioritynum = event["PRIORITY"]
        except KeyError:
            prioritynum = 0

        if (prioritynum == 1):
            priority.append("HIGH")
            isimportant.append(True)
        elif (prioritynum == 9):
            priority.append("LOW")
            isimportant.append(False)
        elif (prioritynum == 5 or (no_unknown and prioritynum == 0)):
            priority.append("MID")
            isimportant.append(False)
        else:
            priority.append("N/A")
            isimportant.append(False)

        try:
            stats = event["STATUS"]
        except KeyError:
            stats = "Unspecified"

        if (ongoing and stats != "CANCELLED"):
            status.append("Departed")
        elif ((before_today or today_done) and stats != "CANCELLED"):
            status.append("Arrived")
        elif (stats == "TENTATIVE"):
            status.append("Unknown")
        elif (stats == "CANCELLED"):
            status.append("Cancelled")
        elif (stats == "CONFIRMED" or no_unknown):
            status.append("On Time")
        else:
            status.append("Unspecified")

        try:
            locas = event["LOCATION"]
        except KeyError:
            locas = "None"

        location.append(locas)

    for i in range(len(name)-1):
        mark = False
        for j in range(len(name)-i-1):
            if (dtstart[j+1] < dtstart[j]):
                fuckswap(j, j+1)
                mark = True
        if (not mark):
            break

    f = open("index.html", "w", encoding="utf-8")

    f.write("""<html>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<head>
<meta http-equiv="refresh" content=\"""" + str(refresh_interval) + """\" />
<meta charset="UTF-8">
<title>Test</title>
<link rel="stylesheet" href="style.css" />
</head>
<body>
<br/>""")
    if (str(search_bar) == "True"):
        f.write("""<input type="text" id="inputbox" onkeyup="myFunction()" placeholder="Search for events.." title="Enter event name" />""")
    f.write("""<table align="center" id="timetable">
<tr>
<th>POS&nbsp;&nbsp; </th>
<th>Time&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; </th>""")
    if (str(importance_in_status) == "False"):
        f.write("""<th>PRI&nbsp;&nbsp; </th>""")
    f.write("""<th>Name&nbsp;&nbsp;&nbsp; </th>
<th>Status&nbsp;&nbsp;&nbsp; </th>
</tr>\n\n""")

    for i in range(len(name)):
        f.write("<tr>\n<td>" + str(ordinal(i+1)) + "</td>\n<td>" + str(dtstart[i].strftime(
            '%d/%b/%y %H:%M')) + "</td>\n")
        if (str(importance_in_status) == "False"):
            f.write("<td>" + str(priority[i]) + "</td>\n")
        f.write("<td>" + str(name[i]) + "</td>\n")

        if (str(status[i]) == "Departed"):
            f.write("<td style=\"color: #00d619\">" +
                    started_text + "</td>\n</tr>\n\n")
        elif (str(status[i]) == "Arrived"):
            f.write("<td style=\"color: #c842f5\">" +
                    ended_text + "</td>\n</tr>\n\n")
        elif (str(status[i]) == "Cancelled"):
            f.write("<td style=\"color: #ff1f1f\">" +
                    cancelled_text + "</td>\n</tr>\n\n")
        elif (str(status[i]) == "Unknown"):
            f.write("<td>" + tentative_text + "</td>\n</tr>\n\n")
        elif (str(status[i]) == "Unspecified"):
            f.write("<td>" + unspecified_text + "</td>\n</tr>\n\n")
        elif (str(status[i]) == "On Time" and str(importance_in_status) == "True" and isimportant[i]):
            f.write("<td style=\"color: #fee715\">" + important_text + "</td>\n</tr>\n\n")
        elif (str(status[i]) == "On Time"):
            f.write("<td style=\"color: #00d619\">" +
                    confirmed_text + "</td>\n</tr>\n\n")
        else:
            f.write("<td>" + str(status[i]) + "</td>\n</tr>\n\n")

        if (((display_location == "First" and i == 0) 
      or display_location == "All" 
      or (display_location == "AllAuto" and str(location[i]) != "None") 
      or (display_location == "FirstAuto" and i == 0 and str(location[i]) != "None") 
      or (display_location == "Today" and dtstart[i].day <= now.day and dtend[i].day >= now.day) 
      or (display_location == "TodayAuto" and dtstart[i].day <= now.day and dtend[i].day >= now.day and str(location[i]) != "None")) 
      and ("".join(list(str(location[i]))[0:4]) != "http" or location_link == "True")):
            if (str(importance_in_status) == "False"):
                f.write("<tr>\n<td></td>\n<td style=\"color: #ff1f1f\">Calling at:</td>\n<td></td>\n<td>" +
                    str(location[i]) + "</td>\n<td></td>\n</tr>\n\n")
            else:
                f.write("<tr>\n<td></td>\n<td style=\"color: #ff1f1f\">Calling at:</td>\n<td>" +
                    str(location[i]) + "</td>\n<td></td>\n</tr>\n\n")

    f.write("""</table>
<div id="scroll-container">
<div id="scroll-text">""" + scrolltext + """</div>
</div>
<div id="scroll-container">
<div id="scroll-text-2">Last Updated: """)
    f.write(str(now.strftime('%Y-%m-%d %H:%M:%S.%f')))
    f.write("""</div>
</div>
<br/>
<script>
function myFunction() {
    var input, filter, table, tr, td, td2, i, txtValue, txtValue2;
    input = document.getElementById("inputbox");
    filter = input.value.toUpperCase();
    table = document.getElementById("timetable");
    tr = table.getElementsByTagName("tr");
    for (i = 0; i < tr.length; i++) {\n""")
    if (str(importance_in_status) == "True"):
        f.write("""      td = tr[i].getElementsByTagName("td")[2];""")
    else:
        f.write("""      td = tr[i].getElementsByTagName("td")[3];""")
    f.write("""
      td2 = tr[i].getElementsByTagName("td")[1];
      if (td) {
        txtValue = td.textContent || td.innerText;
        txtValue2 = td2.textContent || td2.innerText;
        if (txtValue2 == "Calling at:" && txtValue.toUpperCase().indexOf(filter) > -1) {
          tr[i-1].style.display = "";
          tr[i].style.display = "";
        }
        else if (txtValue2 == "Calling at:") {
          tr[i].style.display = tr[i-1].style.display;
        }
        else if (txtValue.toUpperCase().indexOf(filter) > -1) {
          tr[i].style.display = "";
        }
        else {
          tr[i].style.display = "none";
        }
      }       
    }
}
</script>
</body>
</html>
""")

    f.close()
    print("\nRefreshed successfully at " + str(now.strftime('%Y-%m-%d %H:%M:%S.%f')) + ".\nRendered " +
          str(len(name)) + " events out of " + str(shown_count) + ", filtered from " + str(all_count) + " fetched.\n")
    try:
        time.sleep(regenerate_interval)
    except KeyboardInterrupt:
        print("Keyboard interruption detected. Program ending.")
        break
