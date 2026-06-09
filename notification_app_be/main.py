"""
Notification App Backend — Stage 6: Priority Inbox
====================================================
Fetches notifications from the evaluation server and computes the 
top-N most important unread notifications using a min-heap algorithm.

Priority is determined by a combination of:
- Type weight: Placement (3) > Result (2) > Event (1)
- Recency: newer notifications score higher

Priority Formula:
    priority_score = type_weight × (1 / (1 + hours_since_creation))

Usage:
    uvicorn main:app --reload --port 8002

Endpoints:
    GET /                       — Health check
    GET /notifications          — Raw notifications from evaluation server
    GET /priority-inbox         — Top 10 priority notifications
    GET /priority-inbox?top=15  — Top N priority notifications
"""

import sys
import os
import heapq
from datetime import datetime, timezone
from typing import Any

import requests
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

# Add parent directory to path so logging_middleware is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from logging_middleware import Log
from logging_middleware.config import get_token, BASE_URL

# =============================================================================
# FastAPI Application
# =============================================================================
app = FastAPI(
    title="Notification App — Priority Inbox",
    description="Computes top-N priority notifications using a min-heap algorithm",
    version="1.0.0",
)

# =============================================================================
# Constants
# =============================================================================
NOTIFICATIONS_URL = f"{BASE_URL}/notifications"

# Type weights — higher weight = higher priority
TYPE_WEIGHTS = {
    "Placement": 3,
    "placement": 3,
    "Result": 2,
    "result": 2,
    "Event": 1,
    "event": 1,
}

DEFAULT_TOP_N = 10


# =============================================================================
# Helper Functions
# =============================================================================

def _get_auth_headers() -> dict:
    """Build authorization headers with a valid Bearer token."""
    token = get_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def fetch_notifications() -> list[dict]:
    """
    Fetch all notifications from the evaluation server.
    
    Returns:
        list[dict]: List of notification objects.
    """
    Log("backend", "info", "service",
        "Fetching notifications from evaluation server")

    try:
        response = requests.get(
            NOTIFICATIONS_URL,
            headers=_get_auth_headers(),
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        # Handle different response structures
        if isinstance(data, list):
            notifications = data
        elif isinstance(data, dict):
            # Could be wrapped in a key like "notifications" or "data"
            notifications = (
                data.get("notifications", None)
                or data.get("data", None)
                or data.get("items", None)
                or [data]
            )
        else:
            notifications = []

        Log("backend", "info", "service",
            f"Fetched {len(notifications)} notifications successfully")
        return notifications

    except requests.exceptions.RequestException as e:
        Log("backend", "error", "service",
            f"Failed to fetch notifications: {str(e)}")
        raise


def compute_priority_score(notification: dict) -> float:
    """
    Compute the priority score for a notification.
    
    Priority Formula:
        priority_score = type_weight × recency_score
    
    Where:
        type_weight: Placement=3, Result=2, Event=1
        recency_score: 1 / (1 + hours_since_creation)
    
    Args:
        notification: Notification dict with type and timestamp fields.
    
    Returns:
        float: Computed priority score (higher = more important).
    """
    # Extract notification type (API returns "Type" in PascalCase)
    notif_type = (
        notification.get("Type", None)
        or notification.get("notificationType", None)
        or notification.get("notification_type", None)
        or notification.get("type", "Event")
    )
    type_weight = TYPE_WEIGHTS.get(notif_type, 1)

    # Extract creation timestamp (API returns "Timestamp" in PascalCase)
    created_at_str = (
        notification.get("Timestamp", None)
        or notification.get("createdAt", None)
        or notification.get("created_at", None)
        or notification.get("timestamp", None)
        or notification.get("date", None)
    )

    # Compute recency score
    if created_at_str:
        try:
            # Handle various timestamp formats
            if isinstance(created_at_str, (int, float)):
                created_at = datetime.fromtimestamp(created_at_str, tz=timezone.utc)
            else:
                # Try ISO format first
                created_at_str = created_at_str.replace("Z", "+00:00")
                created_at = datetime.fromisoformat(created_at_str)
                if created_at.tzinfo is None:
                    created_at = created_at.replace(tzinfo=timezone.utc)

            hours_since = (datetime.now(timezone.utc) - created_at).total_seconds() / 3600
            recency_score = 1.0 / (1.0 + max(0, hours_since))
        except (ValueError, TypeError):
            Log("backend", "warn", "utils",
                f"Could not parse timestamp: {created_at_str}. Using default recency.")
            recency_score = 0.5
    else:
        recency_score = 0.5

    priority_score = type_weight * recency_score
    return priority_score


def find_top_n_priority(notifications: list[dict], n: int = 10) -> list[dict]:
    """
    Find the top-N highest priority notifications using a min-heap.
    
    Algorithm:
        1. Maintain a min-heap of size N.
        2. For each notification, compute priority_score.
        3. If heap size < N: push.
        4. If priority_score > heap minimum: replace and heapify.
        5. Extract and sort the heap in descending order.
    
    Time Complexity: O(M log N) where M = total notifications
    Space Complexity: O(N)
    
    Args:
        notifications: List of all notification dicts.
        n: Number of top notifications to return.
    
    Returns:
        list[dict]: Top-N notifications sorted by priority (highest first).
    """
    Log("backend", "info", "service",
        f"Computing top-{n} priority notifications from {len(notifications)} total")

    if not notifications:
        Log("backend", "warn", "service", "No notifications to process")
        return []

    # Min-heap: stores (priority_score, index, notification)
    # We use index as tiebreaker to avoid comparing dicts
    min_heap = []

    for idx, notification in enumerate(notifications):
        score = compute_priority_score(notification)

        # Add score to notification for display
        notification["_priority_score"] = round(score, 6)
        notification["_type_weight"] = TYPE_WEIGHTS.get(
            notification.get("Type",
                notification.get("notificationType",
                    notification.get("notification_type",
                        notification.get("type", "Event")))), 1
        )

        if len(min_heap) < n:
            # Heap not full yet — just push
            heapq.heappush(min_heap, (score, idx, notification))
        elif score > min_heap[0][0]:
            # New notification has higher priority than current minimum
            # Replace the minimum
            heapq.heapreplace(min_heap, (score, idx, notification))

    # Extract from heap and sort by priority (highest first)
    top_notifications = []
    while min_heap:
        score, idx, notification = heapq.heappop(min_heap)
        top_notifications.append(notification)

    # Reverse to get highest priority first
    top_notifications.reverse()

    Log("backend", "info", "service",
        f"Top-{n} priority inbox computed. "
        f"Highest score: {top_notifications[0]['_priority_score'] if top_notifications else 'N/A'}, "
        f"Lowest score: {top_notifications[-1]['_priority_score'] if top_notifications else 'N/A'}")

    return top_notifications


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    Log("backend", "info", "route", "Health check endpoint accessed")
    return {"status": "ok", "service": "Notification App — Priority Inbox"}


@app.get("/notifications")
async def get_notifications():
    """
    Fetch and return raw notifications from the evaluation server.
    Useful for debugging and verifying the data source.
    """
    Log("backend", "info", "handler", "GET /notifications — fetching raw notifications")

    try:
        notifications = fetch_notifications()
        Log("backend", "info", "handler",
            f"GET /notifications — returning {len(notifications)} notifications")
        return {
            "total": len(notifications),
            "notifications": notifications,
        }
    except Exception as e:
        Log("backend", "error", "handler",
            f"GET /notifications — error: {str(e)}")
        return JSONResponse(
            status_code=502,
            content={"error": f"Failed to fetch notifications: {str(e)}"},
        )


@app.get("/priority-inbox")
async def get_priority_inbox(top: int = Query(default=DEFAULT_TOP_N, ge=1, le=100)):
    """
    Get the top-N highest priority unread notifications.
    
    Priority is computed as: type_weight × recency_score
    Where:
        - type_weight: Placement=3, Result=2, Event=1
        - recency_score: 1 / (1 + hours_since_creation)
    
    Uses a min-heap of size N for efficient O(M log N) computation.
    
    Query Parameters:
        top (int): Number of top notifications to return (default: 10, max: 100)
    
    Returns:
        JSON with top-N priority notifications ranked by score.
    """
    Log("backend", "info", "handler",
        f"GET /priority-inbox?top={top} — computing priority inbox")

    try:
        # Fetch all notifications
        notifications = fetch_notifications()

        # Compute top-N using min-heap algorithm
        top_notifications = find_top_n_priority(notifications, n=top)

        Log("backend", "info", "handler",
            f"GET /priority-inbox — returning top-{top} notifications")

        return {
            "top_n": top,
            "total_notifications": len(notifications),
            "priority_inbox": [
                {
                    "rank": i + 1,
                    "priority_score": notif.get("_priority_score", 0),
                    "type_weight": notif.get("_type_weight", 1),
                    "notification": {
                        k: v for k, v in notif.items()
                        if not k.startswith("_")
                    },
                }
                for i, notif in enumerate(top_notifications)
            ],
            "algorithm": {
                "name": "Min-Heap Top-N Selection",
                "formula": "priority_score = type_weight × (1 / (1 + hours_since_creation))",
                "weights": {"Placement": 3, "Result": 2, "Event": 1},
                "time_complexity": f"O(M log {top})",
                "space_complexity": f"O({top})",
            },
        }

    except Exception as e:
        Log("backend", "error", "handler",
            f"GET /priority-inbox — error: {str(e)}")
        return JSONResponse(
            status_code=502,
            content={"error": f"Failed to compute priority inbox: {str(e)}"},
        )


# =============================================================================
# Entry Point
# =============================================================================
if __name__ == "__main__":
    import uvicorn

    Log("backend", "info", "config",
        "Starting Notification App — Priority Inbox on port 8002")
    
    print("\n" + "=" * 60)
    print("  Notification App — Priority Inbox")
    print("  Endpoints:")
    print("    GET /                  — Health check")
    print("    GET /notifications     — Raw notifications")
    print("    GET /priority-inbox    — Top 10 priority notifications")
    print("    GET /priority-inbox?top=15 — Top N priority notifications")
    print("=" * 60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8002)
