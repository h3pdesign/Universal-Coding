# calendar_tools.py

def categorize(event):
    title = event.get("title", "").lower()
    if "meeting" in title:
        return "Work Meeting"
    elif "call" in title:
        return "Call"
    elif "doctor" in title or "appointment" in title:
        return "Health"
    elif "gym" in title or "run" in title:
        return "Fitness"
    else:
        return "General"

def write_brief(event):
    return f"{event['title']} from {event['start']} to {event['end']}"

def summarize_events(events):
    summary = "Weekly Calendar Summary:\n"
    categories = {}
    for event in events:
        cat = event["category"]
        categories.setdefault(cat, []).append(event)

    for category, items in categories.items():
        summary += f"\n{category} ({len(items)} events):\n"
        for e in items:
            summary += f"- {e['brief']}\n"

    return summary