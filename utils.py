"""Utility functions for date and time conversion, handling config files etc."""

from datetime import date, timedelta, time, datetime
import icalendar
import os
import random
import yaml
import os


def loadYAML(path: str) -> list:
    """Load the YAML config."""
    if not os.path.exists(path):
        return []
    with open(path, 'r') as yamlfile:
        data = yaml.load(yamlfile, Loader=yaml.FullLoader)        
    return data


def saveYAML(path: str, config: list):
    """Save the YAML config."""
    with open(path, 'w') as yamlfile:
        yaml.dump(config, yamlfile)


def loadWasteEvents(path: str, selected_trash_cans: list) -> dict:
    """Load an ics file and return a dict with the events."""
    e = open(path, 'rb')
    ecal = icalendar.Calendar.from_ical(e.read())

    events = {}        
    for component in ecal.walk():
        if not component.name == 'VEVENT':
            continue
        description = component.get('description')[:3]
        if description not in selected_trash_cans:
            continue            
        events[component.get('dtstart').dt] = description
            
    return events


def toTime(time: str) -> time:
    """Convert a string to datetime.time."""
    return datetime.strptime(time, '%H:%M:%S').time()


def toTimeDelta(time: str) -> timedelta:
    """Convert a string to datetime.timedelta."""
    tmp = toTime(time)
    return timedelta(days=0,seconds=tmp.hour * 3600 + tmp.minute * 60 + tmp.second)
            

def toDate(date: str) -> date:
    """Convert a string to datetime.date."""
    return datetime.strptime(date, '%d/%m/%Y').date()


def getRandomAnimalEmoji():
    """Return a random animal emoji."""
    animal_emojis = ["🐶", "🐱", "🐭", "🐹", "🐰", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐒", "🐔", "🐧", "🐦", "🐤", "🐣", "🐥"]

    return random.choice(animal_emojis)        


def toGermanWeekday(dt: datetime.date) -> str:
    """Return the german weekday for the given english one."""
    lut = {
        "Monday":"Montag",
        "Tuesday":"Dienstag",
        "Wednesday":"Mittwoch",
        "Thursday":"Donnerstag",
        "Friday":"Freitag",
        "Saturday":"Samstag",
        "Sunday":"Sonntag"
            }
    en = dt.strftime("%A")
    return lut[en]