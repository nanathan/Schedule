import calendar
import datetime

import flask

app = flask.Flask(__name__)

SAMPLE_SCHEDULE = {
    "2026-02-02": [
        {"title": "Project kickoff", "start": "09:00", "duration_minutes": 60, "notes": "Align goals and responsibilities"},
        {"title": "Lunch with mentor", "start": "12:30", "duration_minutes": 60, "notes": "Career growth check-in"},
    ],
    "2026-02-08": [
        {"title": "Grocery run", "start": "10:00", "duration_minutes": 50, "notes": "Stock up for the week"},
    ],
    "2026-02-15": [
        {"title": "Morning workout", "start": "06:45", "duration_minutes": 45, "notes": "Strength + mobility"},
        {"title": "Team standup", "start": "09:00", "duration_minutes": 30, "notes": "Daily priorities"},
        {"title": "Client planning session", "start": "11:30", "duration_minutes": 90, "notes": "Roadmap review"},
        {"title": "Deep work block", "start": "14:00", "duration_minutes": 120, "notes": "Feature implementation"},
        {"title": "Dinner with family", "start": "18:30", "duration_minutes": 75, "notes": "No devices at the table"},
    ],
    "2026-02-20": [
        {"title": "Product demo rehearsal", "start": "15:00", "duration_minutes": 60, "notes": "Run through slide deck"},
    ],
    "2026-03-04": [
        {"title": "Dentist appointment", "start": "08:30", "duration_minutes": 45, "notes": "Semi-annual cleaning"},
    ],
    "2026-03-17": [
        {"title": "Quarterly planning", "start": "10:00", "duration_minutes": 150, "notes": "Set next quarter OKRs"},
    ],
}


def format_day_label(day_string):
    parsed_day = datetime.datetime.strptime(day_string, "%Y-%m-%d")
    # Avoid %-d because it is unsupported by strftime on Windows.
    return f"{parsed_day.strftime('%A, %B')} {parsed_day.day}, {parsed_day.year}"


def parse_day(day_string):
    try:
        datetime.datetime.strptime(day_string, "%Y-%m-%d")
    except ValueError:
        return False
    return True


def parse_duration(duration_input):
    try:
        duration_minutes = int(duration_input)
        if duration_minutes <= 0:
            raise ValueError
    except ValueError:
        return None
    return duration_minutes


def add_event(day, event):
    SAMPLE_SCHEDULE.setdefault(day, []).append(event)
    SAMPLE_SCHEDULE[day].sort(key=lambda saved_event: saved_event["start"])


def remove_event(day, event_index):
    events = SAMPLE_SCHEDULE.get(day, [])
    if event_index < 0 or event_index >= len(events):
        return None
    removed_event = events.pop(event_index)
    if not events and day in SAMPLE_SCHEDULE:
        del SAMPLE_SCHEDULE[day]
    return removed_event


def get_calendar_context(year, month):
    cal = calendar.Calendar(firstweekday=6)
    month_name = datetime.date(year, month, 1).strftime("%B %Y")

    days = []
    for date_value in cal.itermonthdates(year, month):
        day_key = date_value.isoformat()
        events = SAMPLE_SCHEDULE.get(day_key, [])
        searchable_text = " ".join(
            f"{event['title']} {event['notes']}".lower() for event in events
        )
        days.append(
            {
                "date": day_key,
                "day": date_value.day,
                "in_month": date_value.month == month,
                "has_events": bool(events),
                "event_count": len(events),
                "search_text": searchable_text,
            }
        )

    previous_month = (datetime.date(year, month, 1) - datetime.timedelta(days=1)).replace(day=1)
    next_month = (datetime.date(year, month, calendar.monthrange(year, month)[1]) + datetime.timedelta(days=1)).replace(day=1)

    return {
        "days": days,
        "month_label": month_name,
        "previous_year": previous_month.year,
        "previous_month": previous_month.month,
        "next_year": next_month.year,
        "next_month": next_month.month,
    }


@app.route("/")
def home():
    today = datetime.date.today()
    year = flask.request.args.get("year", type=int) or today.year
    month = flask.request.args.get("month", type=int) or today.month

    if month < 1 or month > 12:
        flask.abort(400)

    return flask.render_template("index.html", **get_calendar_context(year, month))


@app.route("/schedule/<day>", methods=["GET", "POST"])
def day_schedule(day):
    if not parse_day(day):
        flask.abort(404)

    error_message = None
    form_values = {"title": "", "start": "", "duration_minutes": "", "notes": ""}

    if flask.request.method == "POST":
        action = flask.request.form.get("action", "add")

        if action == "delete":
            event_index = flask.request.form.get("event_index", type=int)
            if event_index is None or remove_event(day, event_index) is None:
                error_message = "Unable to delete that event."
            else:
                return flask.redirect(flask.url_for("day_schedule", day=day))

        elif action == "update":
            event_index = flask.request.form.get("event_index", type=int)
            title = flask.request.form.get("title", "").strip()
            start = flask.request.form.get("start", "").strip()
            duration_input = flask.request.form.get("duration_minutes", "").strip()
            notes = flask.request.form.get("notes", "").strip()
            target_day = flask.request.form.get("target_day", day).strip()

            duration_minutes = parse_duration(duration_input)

            if not title or not start:
                error_message = "Please fill in both title and start time."
            elif duration_minutes is None:
                error_message = "Duration must be a positive number of minutes."
            elif not parse_day(target_day):
                error_message = "Please choose a valid date for this event."
            else:
                updated_event = {
                    "title": title,
                    "start": start,
                    "duration_minutes": duration_minutes,
                    "notes": notes,
                }
                removed_event = remove_event(day, event_index) if event_index is not None else None
                if removed_event is None:
                    error_message = "Unable to update that event."
                else:
                    add_event(target_day, updated_event)
                    return flask.redirect(flask.url_for("day_schedule", day=target_day))

        else:
            title = flask.request.form.get("title", "").strip()
            start = flask.request.form.get("start", "").strip()
            duration_input = flask.request.form.get("duration_minutes", "").strip()
            notes = flask.request.form.get("notes", "").strip()

            form_values = {
                "title": title,
                "start": start,
                "duration_minutes": duration_input,
                "notes": notes,
            }

            duration_minutes = parse_duration(duration_input)

            if not title or not start:
                error_message = "Please fill in both title and start time."
            elif duration_minutes is None:
                error_message = "Duration must be a positive number of minutes."

            if not error_message:
                add_event(
                    day,
                    {
                        "title": title,
                        "start": start,
                        "duration_minutes": duration_minutes,
                        "notes": notes,
                    },
                )
                return flask.redirect(flask.url_for("day_schedule", day=day))

    events = SAMPLE_SCHEDULE.get(day, [])
    total_minutes = sum(event["duration_minutes"] for event in events)
    return flask.render_template(
        "day_schedule.html",
        day=day,
        day_label=format_day_label(day),
        events=events,
        total_minutes=total_minutes,
        error_message=error_message,
        form_values=form_values,
    )


if __name__ == '__main__':
    app.run(debug=False)
