"""
Macro Event Calendar — tracks recurring economic events and their historical impact on gold.
"""

from datetime import datetime, timedelta, timezone


# Known FOMC meeting dates for 2026 (approximate, 2-day meetings end on these dates)
FOMC_2026 = [
    "2026-01-29", "2026-03-19", "2026-05-07", "2026-06-18",
    "2026-07-30", "2026-09-17", "2026-11-05", "2026-12-17",
]

# CPI release dates are usually around the 10-14th of each month
# NFP is the first Friday of each month — computed dynamically


class MacroEventCalendar:
    def get_upcoming_events(self, days_ahead: int = 7) -> list[dict]:
        """Return economic events in the next N days."""
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days_ahead)
        events = []

        # Check FOMC
        for date_str in FOMC_2026:
            dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
            if now <= dt <= end:
                events.append({
                    "type": "FOMC",
                    "name": "FOMC Meeting Decision",
                    "date": date_str,
                    "impact": "high",
                    "note": "Fed rate decision — high volatility expected for gold",
                })

        # Check NFP (first Friday of next months)
        for month_offset in range(2):
            nfp = self._first_friday(now.year, now.month + month_offset)
            if nfp and now <= nfp <= end:
                events.append({
                    "type": "NFP",
                    "name": "Non-Farm Payrolls",
                    "date": nfp.strftime("%Y-%m-%d"),
                    "impact": "high",
                    "note": "Employment data — strong USD = bearish gold",
                })

        # Check CPI (approx 10-14th of each month)
        for month_offset in range(2):
            m = now.month + month_offset
            y = now.year + (m - 1) // 12
            m = ((m - 1) % 12) + 1
            cpi_approx = datetime(y, m, 12, tzinfo=timezone.utc)
            if now <= cpi_approx <= end:
                events.append({
                    "type": "CPI",
                    "name": "CPI Release",
                    "date": cpi_approx.strftime("%Y-%m-%d"),
                    "impact": "high",
                    "note": "Inflation data — high CPI = bullish gold",
                })

        events.sort(key=lambda e: e["date"])
        return events

    def _first_friday(self, year: int, month: int) -> datetime | None:
        """Get first Friday of a given month."""
        if month > 12:
            year += (month - 1) // 12
            month = ((month - 1) % 12) + 1
        try:
            dt = datetime(year, month, 1, tzinfo=timezone.utc)
            days_until_friday = (4 - dt.weekday()) % 7
            return dt + timedelta(days=days_until_friday)
        except ValueError:
            return None

    def is_near_event(self, hours_before: int = 4) -> dict | None:
        """Check if we're within hours_before of a high-impact event."""
        events = self.get_upcoming_events(days_ahead=1)
        now = datetime.now(timezone.utc)
        for event in events:
            event_dt = datetime.fromisoformat(event["date"]).replace(
                hour=13, minute=30, tzinfo=timezone.utc  # Most US data at 13:30 UTC
            )
            if timedelta(0) <= (event_dt - now) <= timedelta(hours=hours_before):
                return event
        return None
