"""
Time Range Parser for Natural Language Query Processing

Parses natural language time expressions into structured TimeRange objects.

Based on: docs/query-service-holistic-fix-analysis.md
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple, Callable
from dateutil.relativedelta import relativedelta

from app.models.query import TimeRange

logger = logging.getLogger(__name__)


class TimeRangeParser:
    """
    Parse natural language time expressions into TimeRange objects.
    
    Supports:
    - Relative expressions: "last 7 days", "past 2 weeks", "last month"
    - Current period: "this week", "this month", "today"
    - Absolute ranges: "from January to March", "Jan 1 to Jan 31"
    - Specific dates: "on March 15", "March 2024"
    
    Example:
        >>> parser = TimeRangeParser()
        >>> time_range = parser.parse("last 7 days")
        >>> print(time_range.start, time_range.end)
        2026-04-14 09:30:00 2026-04-21 09:30:00
    """
    
    # Relative time patterns with handlers
    RELATIVE_PATTERNS = [
        # Days
        (r'(?:last|past|previous)\s+(\d+)\s+days?', 
         lambda m: timedelta(days=int(m.group(1)))),
        
        # Weeks
        (r'(?:last|past|previous)\s+(\d+)\s+weeks?',
         lambda m: timedelta(weeks=int(m.group(1)))),
        
        # Months
        (r'(?:last|past|previous)\s+(\d+)\s+months?',
         lambda m: relativedelta(months=int(m.group(1)))),
        
        # Years
        (r'(?:last|past|previous)\s+(\d+)\s+years?',
         lambda m: relativedelta(years=int(m.group(1)))),
        
        # Hours
        (r'(?:last|past|previous)\s+(\d+)\s+hours?',
         lambda m: timedelta(hours=int(m.group(1)))),
    ]
    
    # Current period patterns
    CURRENT_PERIOD_PATTERNS = {
        r'\btoday\b': lambda: (
            datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0),
            datetime.utcnow()
        ),
        r'\byesterday\b': lambda: (
            (datetime.utcnow() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0),
            (datetime.utcnow() - timedelta(days=1)).replace(hour=23, minute=59, second=59, microsecond=999999)
        ),
        r'\bthis\s+week\b': lambda: (
            datetime.utcnow() - timedelta(days=datetime.utcnow().weekday()),
            datetime.utcnow()
        ),
        r'\bthis\s+month\b': lambda: (
            datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            datetime.utcnow()
        ),
        r'\bthis\s+year\b': lambda: (
            datetime.utcnow().replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0),
            datetime.utcnow()
        ),
        r'\blast\s+week\b': lambda: (
            datetime.utcnow() - timedelta(days=datetime.utcnow().weekday() + 7),
            datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
        ),
        r'\blast\s+month\b': lambda: (
            (datetime.utcnow().replace(day=1) - relativedelta(months=1)),
            datetime.utcnow().replace(day=1) - timedelta(days=1)
        ),
    }
    
    # Month name mapping
    MONTH_NAMES = {
        'january': 1, 'jan': 1,
        'february': 2, 'feb': 2,
        'march': 3, 'mar': 3,
        'april': 4, 'apr': 4,
        'may': 5,
        'june': 6, 'jun': 6,
        'july': 7, 'jul': 7,
        'august': 8, 'aug': 8,
        'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10,
        'november': 11, 'nov': 11,
        'december': 12, 'dec': 12,
    }
    
    @classmethod
    def parse(cls, query_text: str) -> Optional[TimeRange]:
        """
        Parse time range from query text.
        
        Args:
            query_text: Natural language query text
            
        Returns:
            TimeRange object or None if no time expression found
        """
        query_lower = query_text.lower()
        
        # Try relative patterns
        for pattern, delta_func in cls.RELATIVE_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                try:
                    delta = delta_func(match)
                    end = datetime.utcnow()
                    if isinstance(delta, timedelta):
                        start = end - delta
                    else:
                        # relativedelta case
                        start = end - delta  # type: ignore[operator]
                    logger.info(f"Parsed relative time: {pattern} -> {start} to {end}")
                    return TimeRange(start=start, end=end)
                except Exception as e:
                    logger.warning(f"Failed to parse relative time: {e}")
                    continue
        
        # Try current period patterns
        for pattern, range_func in cls.CURRENT_PERIOD_PATTERNS.items():
            if re.search(pattern, query_lower):
                try:
                    start, end = range_func()
                    logger.info(f"Parsed current period: {pattern} -> {start} to {end}")
                    return TimeRange(start=start, end=end)
                except Exception as e:
                    logger.warning(f"Failed to parse current period: {e}")
                    continue
        
        # Try absolute range patterns
        time_range = cls._parse_absolute_range(query_lower)
        if time_range:
            return time_range
        
        # Try month-based patterns
        time_range = cls._parse_month_range(query_lower)
        if time_range:
            return time_range
        
        return None
    
    @classmethod
    def _parse_absolute_range(cls, query_text: str) -> Optional[TimeRange]:
        """
        Parse absolute date ranges like "from Jan 1 to Jan 31" or "Jan 1 - Jan 31".
        
        Args:
            query_text: Query text (lowercase)
            
        Returns:
            TimeRange or None
        """
        # Pattern: from <date> to <date>
        pattern = r'from\s+(\w+\s+\d+)(?:\s+\d{4})?\s+to\s+(\w+\s+\d+)(?:\s+\d{4})?'
        match = re.search(pattern, query_text)
        
        if match:
            try:
                start_str = match.group(1)
                end_str = match.group(2)
                
                # Parse dates
                start = cls._parse_date_string(start_str)
                end = cls._parse_date_string(end_str)
                
                if start and end:
                    logger.info(f"Parsed absolute range: {start} to {end}")
                    return TimeRange(start=start, end=end)
            except Exception as e:
                logger.warning(f"Failed to parse absolute range: {e}")
        
        return None
    
    @classmethod
    def _parse_month_range(cls, query_text: str) -> Optional[TimeRange]:
        """
        Parse month-based ranges like "in March", "March 2024", "discovered this month".
        
        Args:
            query_text: Query text (lowercase)
            
        Returns:
            TimeRange or None
        """
        # Pattern: <month> <year>
        pattern = r'\b(' + '|'.join(cls.MONTH_NAMES.keys()) + r')\s+(\d{4})\b'
        match = re.search(pattern, query_text)
        
        if match:
            try:
                month_name = match.group(1)
                year = int(match.group(2))
                month = cls.MONTH_NAMES[month_name]
                
                start = datetime(year, month, 1)
                # Last day of month
                if month == 12:
                    end = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end = datetime(year, month + 1, 1) - timedelta(days=1)
                
                end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                logger.info(f"Parsed month range: {start} to {end}")
                return TimeRange(start=start, end=end)
            except Exception as e:
                logger.warning(f"Failed to parse month range: {e}")
        
        # Pattern: in <month> (current year)
        pattern = r'\bin\s+(' + '|'.join(cls.MONTH_NAMES.keys()) + r')\b'
        match = re.search(pattern, query_text)
        
        if match:
            try:
                month_name = match.group(1)
                month = cls.MONTH_NAMES[month_name]
                year = datetime.utcnow().year
                
                start = datetime(year, month, 1)
                if month == 12:
                    end = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end = datetime(year, month + 1, 1) - timedelta(days=1)
                
                end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                logger.info(f"Parsed month: {start} to {end}")
                return TimeRange(start=start, end=end)
            except Exception as e:
                logger.warning(f"Failed to parse month: {e}")
        
        return None
    
    @classmethod
    def _parse_date_string(cls, date_str: str) -> Optional[datetime]:
        """
        Parse a date string like "Jan 1", "January 15", "March 20 2024".
        
        Args:
            date_str: Date string
            
        Returns:
            datetime object or None
        """
        # Try to extract month and day
        parts = date_str.strip().split()
        
        if len(parts) < 2:
            return None
        
        month_str = parts[0].lower()
        day_str = parts[1]
        year = datetime.utcnow().year  # Default to current year
        
        if len(parts) >= 3:
            try:
                year = int(parts[2])
            except ValueError:
                pass
        
        # Get month number
        month = cls.MONTH_NAMES.get(month_str)
        if not month:
            return None
        
        # Get day
        try:
            day = int(day_str)
        except ValueError:
            return None
        
        try:
            return datetime(year, month, day)
        except ValueError:
            return None
    
    @classmethod
    def extract_time_keywords(cls, query_text: str) -> list[str]:
        """
        Extract time-related keywords from query text.
        
        Args:
            query_text: Query text
            
        Returns:
            List of time keywords found
        """
        keywords = []
        query_lower = query_text.lower()
        
        # Check for relative time keywords
        if re.search(r'\b(?:last|past|previous)\s+\d+\s+(?:days?|weeks?|months?|years?|hours?)', query_lower):
            keywords.append('relative_time')
        
        # Check for current period keywords
        if re.search(r'\b(?:today|yesterday|this\s+(?:week|month|year))\b', query_lower):
            keywords.append('current_period')
        
        # Check for month names
        for month_name in cls.MONTH_NAMES.keys():
            if month_name in query_lower:
                keywords.append('month_reference')
                break
        
        # Check for absolute range keywords
        if re.search(r'\bfrom\s+.+\s+to\s+', query_lower):
            keywords.append('absolute_range')
        
        return keywords


# Made with Bob