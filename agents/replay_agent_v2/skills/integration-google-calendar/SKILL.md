---
name: "integration-google-calendar"
description: "Use the Google Calendar declarative plugin through the plugin gateway."
---

# Google Calendar Plugin Skill

Use the Google Calendar plugin by calling the gateway at `http://workbench:3000/plugins/invoke` with:

- `agentId`: the current agent id
- `pluginKey`: `com.google.calendar`
- `actionKey`: one of the actions listed below
- `connectionKey`: optional, defaults to `default`
- `params`: action input parameters

## Available Actions

1. **getProfile**: Verify the connected Google account email.
2. **listCalendars**: List accessible calendars.
3. **listEvents**: List events from a calendar within an optional time range.
4. **getEvent**: Read one event by `eventId`.
5. **createEvent**: Create a timed event with title, description, location, start, and end.
6. **updateEvent**: Update those same event fields for an existing event.
7. **deleteEvent**: Delete an event.
8. **freeBusyQuery**: Query busy blocks for a calendar across a time window.

## Usage Notes

- Use `primary` as `calendarId` for the connected user's main calendar.
- Datetimes should be passed in RFC3339 format such as `2026-06-01T09:00:00+08:00`.
- `createEvent` and `updateEvent` are designed for straightforward timed events. If you later need attendees, conference links, or recurring rules, those can be added in a follow-up version.

## Examples

### Example: List Events This Week
```json
{
  "agentId": "123",
  "pluginKey": "com.google.calendar",
  "actionKey": "listEvents",
  "connectionKey": "default",
  "params": {
    "calendarId": "primary",
    "timeMin": "2026-06-01T00:00:00+08:00",
    "timeMax": "2026-06-08T00:00:00+08:00",
    "singleEvents": true,
    "orderBy": "startTime"
  }
}
```

### Example: Create Event
```json
{
  "agentId": "123",
  "pluginKey": "com.google.calendar",
  "actionKey": "createEvent",
  "params": {
    "calendarId": "primary",
    "summary": "Weekly planning",
    "description": "Review roadmap and blockers",
    "location": "Meeting Room A",
    "startDateTime": "2026-06-03T10:00:00+08:00",
    "endDateTime": "2026-06-03T10:30:00+08:00",
    "timeZone": "Asia/Shanghai"
  }
}
```

### Example: Free Busy Query
```json
{
  "agentId": "123",
  "pluginKey": "com.google.calendar",
  "actionKey": "freeBusyQuery",
  "params": {
    "calendarId": "primary",
    "timeMin": "2026-06-03T00:00:00+08:00",
    "timeMax": "2026-06-04T00:00:00+08:00",
    "timeZone": "Asia/Shanghai"
  }
}
```

If the plugin is not authorized yet, ask the user to enable the Google Calendar plugin and complete OAuth before invoking actions.
