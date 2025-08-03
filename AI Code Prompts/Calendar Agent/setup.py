# setup.py

from setuptools import setup

APP = ['calendar_agent_gui.py']
DATA_FILES = ['icon.png']
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'icon.png',
    'packages': ['rumps', 'EventKit', 'Foundation'],
}

setup(
    app=APP,
    name="HP Calendar Agent",
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)