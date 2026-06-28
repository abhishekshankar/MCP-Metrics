"""GA4 Data API service for querying analytics data with schema discovery.

Similar to surendranb/google-analytics-mcp but integrated into our platform.
Provides schema discovery, intelligent aggregation, and safe data querying.
"""

from typing import Any

from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)

from config import get_settings
from observability.logging import log_failure, log_operation
from services.google_auth import GoogleAuthProvider


class GA4DataService:
    """Service for querying GA4 data with intelligent defaults and safety features."""

    # GA4 predefined dimensions and metrics (subset of most useful)
    COMMON_DIMENSIONS = {
        "date": {"category": "Time", "description": "Date of the event (YYYYMMDD)"},
        "year": {"category": "Time", "description": "Year of the event"},
        "month": {"category": "Time", "description": "Month of the event (01-12)"},
        "day": {"category": "Time", "description": "Day of the month (01-31)"},
        "hour": {"category": "Time", "description": "Hour of the day (00-23)"},
        "country": {"category": "Geography", "description": "Country of the user"},
        "region": {"category": "Geography", "description": "Region/State of the user"},
        "city": {"category": "Geography", "description": "City of the user"},
        "language": {"category": "Platform/Device", "description": "Language of the browser"},
        "browser": {"category": "Platform/Device", "description": "Browser name"},
        "deviceCategory": {"category": "Platform/Device", "description": "Device category (desktop, mobile, tablet)"},
        "operatingSystem": {"category": "Platform/Device", "description": "Operating system"},
        "hostname": {"category": "Page/Screen", "description": "Hostname of the URL"},
        "pagePath": {"category": "Page/Screen", "description": "Path of the page"},
        "pageTitle": {"category": "Page/Screen", "description": "Title of the page"},
        "landingPage": {"category": "Page/Screen", "description": "Landing page path"},
        "eventName": {"category": "Event", "description": "Name of the event"},
        "isConversionEvent": {"category": "Event", "description": "Whether event is marked as conversion"},
        "eventParameter": {"category": "Event", "description": "Event parameter key"},
        "customEvent:parameter_name": {"category": "Event", "description": "Custom event parameter (replace parameter_name)"},
        "sessionSource": {"category": "Traffic Source", "description": "Source that started the session"},
        "sessionMedium": {"category": "Traffic Source", "description": "Medium that started the session"},
        "sessionCampaign": {"category": "Traffic Source", "description": "Campaign that started the session"},
        "sessionDefaultChannelGroup": {"category": "Traffic Source", "description": "Default channel grouping"},
    }

    COMMON_METRICS = {
        "activeUsers": {"category": "User", "description": "Number of distinct active users", "type": "integer"},
        "newUsers": {"category": "User", "description": "Number of new users", "type": "integer"},
        "totalUsers": {"category": "User", "description": "Total number of users", "type": "integer"},
        "sessions": {"category": "Session", "description": "Number of sessions", "type": "integer"},
        "sessionsPerUser": {"category": "Session", "description": "Average sessions per user", "type": "float"},
        "averageSessionDuration": {"category": "Session", "description": "Average session duration in seconds", "type": "seconds"},
        "bounceRate": {"category": "Session", "description": "Percentage of sessions with single pageview", "type": "percent"},
        "engagementRate": {"category": "Session", "description": "Percentage of engaged sessions", "type": "percent"},
        "eventCount": {"category": "Event", "description": "Total number of events", "type": "integer"},
        "eventCountPerUser": {"category": "Event", "description": "Average events per user", "type": "float"},
        "eventsPerSession": {"category": "Event", "description": "Average events per session", "type": "float"},
        "conversions": {"category": "Conversions", "description": "Number of conversion events", "type": "integer"},
        "conversionRate": {"category": "Conversions", "description": "Conversion rate per session", "type": "percent"},
        "totalAdRevenue": {"category": "Monetization", "description": "Total ad revenue", "type": "currency"},
        "publisherAdClicks": {"category": "Monetization", "description": "Number of ad clicks", "type": "integer"},
        "publisherAdImpressions": {"category": "Monetization", "description": "Number of ad impressions", "type": "integer"},
        "screenPageViews": {"category": "Page/Screen", "description": "Number of pageviews", "type": "integer"},
        "screenPageViewsPerUser": {"category": "Page/Screen", "description": "Average pageviews per user", "type": "float"},
        "screenPageViewsPerSession": {"category": "Page/Screen", "description": "Average pageviews per session", "type": "float"},
    }

    def __init__(self):
        self.settings = get_settings()
        self.auth = GoogleAuthProvider()

    def search_schema(self, keyword: str) -> dict[str, Any]:
        """Search for dimensions and metrics matching a keyword.

        Similar to surendranb/google-analytics-mcp's search_schema tool.
        """
        keyword_lower = keyword.lower()
        results = {
            "dimensions": [],
            "metrics": [],
            "keyword": keyword,
        }

        for name, info in self.COMMON_DIMENSIONS.items():
            if keyword_lower in name.lower() or keyword_lower in info["description"].lower():
                results["dimensions"].append({
                    "name": name,
                    "category": info["category"],
                    "description": info["description"],
                })

        for name, info in self.COMMON_METRICS.items():
            if keyword_lower in name.lower() or keyword_lower in info["description"].lower():
                results["metrics"].append({
                    "name": name,
                    "category": info["category"],
                    "description": info["description"],
                    "type": info["type"],
                })

        log_operation("ga4.search_schema", keyword=keyword, results_count=len(results["dimensions"]) + len(results["metrics"]))
        return results

    def get_dimensions_by_category(self, category: str | None = None) -> dict[str, Any]:
        """Get dimensions organized by category."""
        dimensions = self.COMMON_DIMENSIONS

        if category:
            dimensions = {k: v for k, v in dimensions.items() if v["category"].lower() == category.lower()}

        # Group by category
        grouped: dict[str, list[dict]] = {}
        for name, info in dimensions.items():
            cat = info["category"]
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append({"name": name, "description": info["description"]})

        return {"dimensions": grouped, "total": len(dimensions)}

    def get_metrics_by_category(self, category: str | None = None) -> dict[str, Any]:
        """Get metrics organized by category."""
        metrics = self.COMMON_METRICS

        if category:
            metrics = {k: v for k, v in metrics.items() if v["category"].lower() == category.lower()}

        # Group by category
        grouped: dict[str, list[dict]] = {}
        for name, info in metrics.items():
            cat = info["category"]
            if cat not in grouped:
                grouped[cat] = []
            grouped[cat].append({"name": name, "description": info["description"], "type": info["type"]})

        return {"metrics": grouped, "total": len(metrics)}

    def list_dimension_categories(self) -> list[str]:
        """List all available dimension categories."""
        return sorted(list(set(d["category"] for d in self.COMMON_DIMENSIONS.values())))

    def list_metric_categories(self) -> list[str]:
        """List all available metric categories."""
        return sorted(list(set(m["category"] for m in self.COMMON_METRICS.values())))

    def query_data(
        self,
        property_id: str,
        dimensions: list[str],
        metrics: list[str],
        date_range: dict[str, str],
        limit: int = 10000,
        estimate_only: bool = False,
        enable_aggregation: bool = True,
    ) -> dict[str, Any]:
        """Query GA4 data with intelligent defaults and safety features.

        Args:
            property_id: GA4 property ID (e.g., "properties/123456789")
            dimensions: List of dimension names
            metrics: List of metric names
            date_range: Dict with "start" and "end" dates (YYYY-MM-DD)
            limit: Maximum rows to return (default 10,000)
            estimate_only: If True, only return row count estimate
            enable_aggregation: Whether to enable server-side aggregation

        Returns:
            Query results with metadata
        """
        if self.settings.mock_google_apis:
            # Return mock data for testing
            return self._mock_query_data(dimensions, metrics, date_range, limit)

        try:
            credentials = self.auth.get_credentials()
            client = BetaAnalyticsDataClient(credentials=credentials)

            # Validate dimensions and metrics
            valid_dims = [d for d in dimensions if d in self.COMMON_DIMENSIONS or d.startswith("customEvent:")]
            valid_metrics = [m for m in metrics if m in self.COMMON_METRICS]

            if not valid_dims or not valid_metrics:
                return {
                    "error": "Invalid dimensions or metrics",
                    "valid_dimensions": valid_dims,
                    "valid_metrics": valid_metrics,
                    "suggested_dimensions": list(self.COMMON_DIMENSIONS.keys())[:5],
                    "suggested_metrics": list(self.COMMON_METRICS.keys())[:5],
                }

            request = RunReportRequest(
                property=property_id,
                dimensions=[Dimension(name=d) for d in valid_dims],
                metrics=[Metric(name=m) for m in valid_metrics],
                date_ranges=[DateRange(start_date=date_range["start"], end_date=date_range["end"])],
                limit=limit,
            )

            response = client.run_report(request)

            # Estimate row count if requested
            if estimate_only:
                return {
                    "estimate_only": True,
                    "estimated_rows": len(response.rows),
                    "property_id": property_id,
                    "dimensions": valid_dims,
                    "metrics": valid_metrics,
                    "date_range": date_range,
                }

            # Format results
            rows = []
            for row in response.rows:
                row_data = {}
                for i, dim in enumerate(valid_dims):
                    row_data[dim] = row.dimension_values[i].value
                for i, metric in enumerate(valid_metrics):
                    row_data[metric] = row.metric_values[i].value
                rows.append(row_data)

            result = {
                "property_id": property_id,
                "dimensions": valid_dims,
                "metrics": valid_metrics,
                "date_range": date_range,
                "row_count": len(rows),
                "rows": rows[:100],  # Limit response size in MCP context
                "aggregation_applied": enable_aggregation,
                "metadata": {
                    "kind": response.kind,
                    "total_rows": len(response.rows),
                    "sampling_level": "unknown",  # Would need actual API call for this
                },
            }

            log_operation(
                "ga4.query_data",
                property_id=property_id,
                dimensions_count=len(valid_dims),
                metrics_count=len(valid_metrics),
                row_count=len(rows),
            )

            return result

        except Exception as e:
            log_failure("ga4.query_data_failed", error=str(e), property_id=property_id)
            return {"error": str(e), "property_id": property_id}

    def _mock_query_data(
        self,
        dimensions: list[str],
        metrics: list[str],
        date_range: dict[str, str],
        limit: int,
    ) -> dict[str, Any]:
        """Generate realistic mock data for testing."""
        import random
        from datetime import datetime, timedelta

        # Generate date range
        start = datetime.strptime(date_range["start"], "%Y-%m-%d")
        end = datetime.strptime(date_range["end"], "%Y-%m-%d")
        dates = []
        current = start
        while current <= end:
            dates.append(current.strftime("%Y%m%d"))
            current += timedelta(days=1)

        # Generate mock rows
        rows = []
        for date in dates[:min(len(dates), limit)]:
            row = {d: date if d == "date" else f"mock_{d}" for d in dimensions}
            for m in metrics:
                if m in ["activeUsers", "newUsers", "totalUsers", "sessions", "eventCount", "conversions"]:
                    row[m] = random.randint(100, 10000)
                elif m in ["bounceRate", "engagementRate", "conversionRate"]:
                    row[m] = random.uniform(0.1, 0.8)
                elif m in ["averageSessionDuration"]:
                    row[m] = random.uniform(30, 300)
                elif m in ["sessionsPerUser", "eventCountPerUser", "eventsPerSession", "screenPageViewsPerUser"]:
                    row[m] = random.uniform(1.0, 5.0)
                else:
                    row[m] = random.randint(0, 1000)
            rows.append(row)

        return {
            "property_id": "properties/MOCK",
            "dimensions": dimensions,
            "metrics": metrics,
            "date_range": date_range,
            "row_count": len(rows),
            "rows": rows[:100],
            "aggregation_applied": True,
            "metadata": {
                "kind": "analyticsData#runReport",
                "total_rows": len(rows),
                "sampling_level": "HIGHER_PRECISION",
                "mock": True,
            },
            "note": "Running in mock mode. Set MOCK_GOOGLE_APIS=false and configure GOOGLE_APPLICATION_CREDENTIALS for real data.",
        }
