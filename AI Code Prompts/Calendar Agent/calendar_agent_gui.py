# calendar_agent_gui.py

import rumps
import asyncio
import threading
from apple_calendar_agent import launch_agent

class CalendarAgentApp(rumps.App):
    def __init__(self):
        super().__init__("HP Calendar Agent", icon="icon.png", menu=["Show Summary", "Refresh"])
        self.summary = "Calendar agent not yet run."

    @rumps.clicked("Show Summary")
    def show_summary(self, _):
        rumps.alert(title="Weekly Summary", message=self.summary)

    @rumps.clicked("Refresh")
    def manual_refresh(self, _):
        self.run_agent()

    @rumps.timer(3600)
    def auto_refresh(self, _):
        self.run_agent()

    def run_agent(self):
        def runner():
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            summary = loop.run_until_complete(launch_agent())
            self.summary = summary
        threading.Thread(target=runner).start()

if __name__ == "__main__":
    CalendarAgentApp().run()