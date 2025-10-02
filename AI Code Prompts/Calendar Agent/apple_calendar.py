# apple_calendar.py

import datetime
from Foundation import NSDate
from EventKit import EKEventStore, EKEntityTypeEvent
import asyncio

class AppleCalendar:
    def __init__(self, calendar_name="hp"):
        self.store = EKEventStore.alloc().init()
        self.calendar_name = calendar_name
        self.calendar = None

    def request_access(self):
        sem = asyncio.Semaphore(0)
        granted = False

        def handler(grant, err):
            nonlocal granted
            granted = grant
            sem.release()

        self.store.requestAccessToEntityType_completion_(EKEntityTypeEvent, handler)
        asyncio.run(sem.acquire())

        if not granted:
            raise PermissionError("Calendar access not granted")

        # Locate the calendar
        for cal in self.store.calendarsForEntityType_(EKEntityTypeEvent):
            if cal.title() == self.calendar_name:
                self.calendar = cal
                break

        if self.calendar is None:
            raise ValueError(f"Calendar '{self.calendar_name}' not found")

    async def get_events_for_this_week(self):
        now = NSDate.date()
        week_later = now.dateByAddingTimeInterval_(7 * 24 * 60 * 60)  # 7 days

        predicate = self.store.predicateForEventsWithStartDate_endDate_calendars_(
            now, week_later, [self.calendar]
        )

        events = self.store.eventsMatchingPredicate_(predicate)
        events = sorted(events, key=lambda e: e.startDate())

        # Convert to dicts
        return [
            {
                "title": str(e.title()),
                "start": e.startDate().description(),
                "end": e.endDate().description(),
                "notes": str(e.notes()) if e.notes() else "",
            }
            for e in events
        ]