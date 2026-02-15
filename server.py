import datetime

import flask

app = flask.Flask(__name__)

SAMPLE_SCHEDULE = {
    "2026-02-15": [
        {"title": "Morning workout", "start": "06:45", "duration_minutes": 45, "notes": "Strength + mobility"},
        {"title": "Team standup", "start": "09:00", "duration_minutes": 30, "notes": "Daily priorities"},
        {"title": "Client planning session", "start": "11:30", "duration_minutes": 90, "notes": "Roadmap review"},
        {"title": "Deep work block", "start": "14:00", "duration_minutes": 120, "notes": "Feature implementation"},
        {"title": "Dinner with family", "start": "18:30", "duration_minutes": 75, "notes": "No devices at the table"},
    ]
}


def format_day_label(day_string):
    parsed_day = datetime.datetime.strptime(day_string, "%Y-%m-%d")
    # Avoid %-d because it is unsupported by strftime on Windows.
    return f"{parsed_day.strftime('%A, %B')} {parsed_day.day}, {parsed_day.year}"


@app.route("/")
def home():
    return flask.render_template("index.html", featured_day="2026-02-15")


@app.route("/schedule/<day>")
def day_schedule(day):
    events = SAMPLE_SCHEDULE.get(day)
    if events is None:
        flask.abort(404)

    total_minutes = sum(event["duration_minutes"] for event in events)
    return flask.render_template(
        "day_schedule.html",
        day=day,
        day_label=format_day_label(day),
        events=events,
        total_minutes=total_minutes,
    )


if __name__ == '__main__':
    app.run(debug=False)
