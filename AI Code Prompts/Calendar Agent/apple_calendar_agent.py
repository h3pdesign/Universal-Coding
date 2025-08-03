# apple_calendar_agent.py

import asyncio
import datetime
from apple_calendar import AppleCalendar
from calendar_tools import categorize, write_brief, summarize_events

def create_calendar_server():
    """Connect to the local Apple Calendar with permissions"""
    calendar = AppleCalendar(calendar_name="hp")
    calendar.request_access()
    return calendar

def create_calendar_agent(calendar):
    """Define the agent behavior for calendar interaction"""

    async def process_week():
        print("Fetching events...")
        events = await calendar.get_events_for_this_week()

        for event in events:
            event['category'] = categorize(event)
            event['brief'] = write_brief(event)
            print(f"✓ Processed: {event['title']}")

        summary = summarize_events(events)
        return summary

    return {'process_week': process_week}

async def launch_agent():
    """Initialize and launch the calendar agent"""
    print("🚀 Launching calendar agent...")
    calendar = create_calendar_server()
    agent = create_calendar_agent(calendar)
    summary = await agent['process_week']()
    print("✅ Week organized!\n", summary)
    return summary

if __name__ == "__main__":
    asyncio.run(launch_agent())