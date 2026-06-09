"""
Vehicle Maintenance Scheduler Microservice
===========================================
Solves the vehicle maintenance scheduling problem using the 0/1 Knapsack 
algorithm with Dynamic Programming. Fetches depot and vehicle data from 
the evaluation server APIs and determines the optimal subset of vehicles 
to service within the daily mechanic-hour budget to maximise total 
operational impact score.

Usage:
    uvicorn main:app --reload --port 8001
"""

import sys
import os
import math
from typing import Any

import requests
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# Add parent directory to path so logging_middleware is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from logging_middleware import Log
from logging_middleware.config import get_token, BASE_URL

# =============================================================================
# FastAPI Application
# =============================================================================
app = FastAPI(
    title="Vehicle Maintenance Scheduler",
    description="Optimises daily vehicle maintenance scheduling using 0/1 Knapsack DP",
    version="1.0.0",
)

# =============================================================================
# API Endpoints on the Test Server
# =============================================================================
DEPOTS_URL = f"{BASE_URL}/depots"
VEHICLES_URL = f"{BASE_URL}/vehicles"


def _get_auth_headers() -> dict:
    """Build authorization headers with a valid Bearer token."""
    token = get_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def fetch_depots() -> list[dict]:
    """
    Fetch all depot data from the evaluation server.
    
    Returns:
        list[dict]: List of depot objects with mechanic-hour budgets.
    """
    Log("backend", "info", "service", "Fetching depot data from evaluation server")

    try:
        response = requests.get(DEPOTS_URL, headers=_get_auth_headers(), timeout=15)
        response.raise_for_status()
        data = response.json()
        Log("backend", "info", "service", f"Successfully fetched depot data: {len(data) if isinstance(data, list) else 'object'} entries")
        return data
    except requests.exceptions.RequestException as e:
        Log("backend", "error", "service", f"Failed to fetch depots: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch depots: {e}")


def fetch_vehicles() -> list[dict]:
    """
    Fetch all vehicle/task data from the evaluation server.
    
    Returns:
        list[dict]: List of vehicle objects with duration and importance scores.
    """
    Log("backend", "info", "service", "Fetching vehicle data from evaluation server")

    try:
        response = requests.get(VEHICLES_URL, headers=_get_auth_headers(), timeout=15)
        response.raise_for_status()
        data = response.json()
        Log("backend", "info", "service", f"Successfully fetched vehicle data: {len(data) if isinstance(data, list) else 'object'} entries")
        return data
    except requests.exceptions.RequestException as e:
        Log("backend", "error", "service", f"Failed to fetch vehicles: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Failed to fetch vehicles: {e}")


# =============================================================================
# Knapsack Algorithm (0/1 Dynamic Programming)
# =============================================================================

def solve_knapsack(
    tasks: list[dict],
    capacity: float,
    weight_key: str = "duration",
    value_key: str = "importance",
) -> dict:
    """
    Solve the 0/1 Knapsack problem using Dynamic Programming.
    
    Selects the subset of tasks that maximises total importance score 
    without exceeding the mechanic-hour capacity.
    
    Args:
        tasks: List of task dicts, each with weight_key and value_key fields.
        capacity: Maximum available mechanic-hours (knapsack capacity).
        weight_key: Key in task dict for the duration/weight.
        value_key: Key in task dict for the importance/value.
    
    Returns:
        dict: {
            "selected_tasks": [...],
            "total_importance": float,
            "total_duration": float,
            "capacity": float,
            "tasks_considered": int,
            "tasks_selected": int,
        }
    """
    n = len(tasks)
    Log("backend", "info", "service",
        f"Starting knapsack solver: {n} tasks, capacity={capacity} hours")

    if n == 0:
        Log("backend", "warn", "service", "No tasks provided to knapsack solver")
        return {
            "selected_tasks": [],
            "total_importance": 0,
            "total_duration": 0,
            "capacity": capacity,
            "tasks_considered": 0,
            "tasks_selected": 0,
        }

    # Extract weights and values
    weights = []
    values = []
    for task in tasks:
        w = float(task.get(weight_key, 0))
        v = float(task.get(value_key, 0))
        weights.append(w)
        values.append(v)

    # Handle fractional weights by scaling to integers
    # Find the smallest granularity (e.g., 0.5 hours -> scale by 2)
    all_weights = weights + [capacity]
    # Determine decimal places needed
    max_decimals = 0
    for w in all_weights:
        decimal_str = str(w).split(".")[-1] if "." in str(w) else "0"
        max_decimals = max(max_decimals, len(decimal_str))

    scale_factor = 10 ** min(max_decimals, 2)  # Cap at 2 decimal places
    scaled_weights = [int(round(w * scale_factor)) for w in weights]
    scaled_capacity = int(round(capacity * scale_factor))

    Log("backend", "debug", "service",
        f"Scale factor: {scale_factor}, Scaled capacity: {scaled_capacity}")

    # DP Table — optimised 1D array (rolling)
    # dp[w] = maximum value achievable with capacity w
    dp = [0.0] * (scaled_capacity + 1)

    # Track which items are selected (for backtracking)
    # keep[i][w] = True if item i is included in optimal solution for capacity w
    keep = [[False] * (scaled_capacity + 1) for _ in range(n)]

    for i in range(n):
        # Traverse in reverse to avoid using an item more than once
        for w in range(scaled_capacity, scaled_weights[i] - 1, -1):
            new_val = dp[w - scaled_weights[i]] + values[i]
            if new_val > dp[w]:
                dp[w] = new_val
                keep[i][w] = True

        if (i + 1) % 100 == 0:
            Log("backend", "debug", "service",
                f"Knapsack DP progress: processed {i + 1}/{n} tasks")

    # Backtrack to find selected items
    selected_indices = []
    remaining_capacity = scaled_capacity
    for i in range(n - 1, -1, -1):
        if keep[i][remaining_capacity]:
            selected_indices.append(i)
            remaining_capacity -= scaled_weights[i]

    selected_indices.reverse()
    selected_tasks = [tasks[i] for i in selected_indices]
    total_importance = sum(values[i] for i in selected_indices)
    total_duration = sum(weights[i] for i in selected_indices)

    Log("backend", "info", "service",
        f"Knapsack solved: selected {len(selected_tasks)}/{n} tasks, "
        f"total importance={total_importance}, "
        f"total duration={total_duration}/{capacity} hours")

    return {
        "selected_tasks": selected_tasks,
        "total_importance": total_importance,
        "total_duration": total_duration,
        "capacity": capacity,
        "tasks_considered": n,
        "tasks_selected": len(selected_tasks),
    }


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/")
async def root():
    """Health check endpoint."""
    Log("backend", "info", "route", "Health check endpoint accessed")
    return {"status": "ok", "service": "Vehicle Maintenance Scheduler"}


@app.get("/depots")
async def get_depots():
    """Fetch and return raw depot data from the evaluation server."""
    Log("backend", "info", "handler", "GET /depots — fetching depot data")
    data = fetch_depots()
    Log("backend", "info", "handler", f"GET /depots — returning depot data")
    return data


@app.get("/vehicles")
async def get_vehicles():
    """Fetch and return raw vehicle data from the evaluation server."""
    Log("backend", "info", "handler", "GET /vehicles — fetching vehicle data")
    data = fetch_vehicles()
    Log("backend", "info", "handler", f"GET /vehicles — returning vehicle data")
    return data


@app.get("/schedule")
async def get_optimal_schedule():
    """
    Compute the optimal maintenance schedule.
    
    Fetches depots (for mechanic-hour budget) and vehicles (for tasks),
    then runs the 0/1 Knapsack DP algorithm to find the subset of 
    vehicles that maximises total importance within the budget.
    
    Returns:
        JSON response with optimal schedule per depot.
    """
    Log("backend", "info", "handler",
        "GET /schedule — computing optimal maintenance schedule")

    # Fetch data from evaluation server
    depots_data = fetch_depots()
    vehicles_data = fetch_vehicles()

    Log("backend", "info", "controller",
        f"Data fetched — Depots: {type(depots_data).__name__}, "
        f"Vehicles: {type(vehicles_data).__name__}")

    # Handle different possible response structures
    # The API might return a list of depots or a single depot object
    results = []

    # Try to extract depot information
    if isinstance(depots_data, dict):
        depots_list = depots_data.get("depots", [depots_data])
    elif isinstance(depots_data, list):
        depots_list = depots_data
    else:
        Log("backend", "error", "controller",
            f"Unexpected depots data format: {type(depots_data)}")
        depots_list = []

    # Try to extract vehicle/task information
    if isinstance(vehicles_data, dict):
        vehicles_list = vehicles_data.get("vehicles", [vehicles_data])
    elif isinstance(vehicles_data, list):
        vehicles_list = vehicles_data
    else:
        Log("backend", "error", "controller",
            f"Unexpected vehicles data format: {type(vehicles_data)}")
        vehicles_list = []

    Log("backend", "info", "controller",
        f"Parsed {len(depots_list)} depots and {len(vehicles_list)} vehicles/tasks")

    # If we have depots with capacity info, solve per depot
    # Otherwise, solve with a global capacity
    if depots_list and len(depots_list) > 0:
        for depot in depots_list:
            depot_name = depot.get("name", depot.get("depotName", depot.get("ID", depot.get("id", "unknown"))))
            
            # Look for capacity field — could be named differently
            capacity = (
                depot.get("MechanicHours", None)
                or depot.get("mechanicHours", None)
                or depot.get("mechanic_hours", None)
                or depot.get("capacity", None)
                or depot.get("dailyBudget", None)
                or depot.get("budget", None)
            )

            if capacity is None:
                Log("backend", "warn", "controller",
                    f"Depot '{depot_name}' has no recognizable capacity field. "
                    f"Keys: {list(depot.keys())}. Skipping.")
                results.append({
                    "depot": depot,
                    "error": "Could not determine mechanic-hour capacity",
                    "available_keys": list(depot.keys()),
                })
                continue

            capacity = float(capacity)
            Log("backend", "info", "controller",
                f"Processing depot '{depot_name}' with capacity={capacity} hours")

            # Filter vehicles for this depot if there's a depot reference
            depot_id = depot.get("ID", depot.get("id", depot.get("depotId", None)))
            if depot_id:
                depot_vehicles = [
                    v for v in vehicles_list
                    if v.get("depotId", v.get("depot_id", v.get("depot", None))) == depot_id
                ]
                if not depot_vehicles:
                    # If no vehicles match this depot, use all vehicles
                    Log("backend", "warn", "controller",
                        f"No vehicles matched depot '{depot_name}' by ID. Using all vehicles.")
                    depot_vehicles = vehicles_list
            else:
                depot_vehicles = vehicles_list

            # Detect weight and value keys from vehicle data
            sample = depot_vehicles[0] if depot_vehicles else {}
            weight_key = next(
                (k for k in ["Duration", "duration", "serviceDuration", "service_duration",
                             "estimatedTime", "time", "hours"]
                 if k in sample),
                "Duration"
            )
            value_key = next(
                (k for k in ["Impact", "importance", "impactScore", "impact_score",
                             "operationalImpact", "score", "priority"]
                 if k in sample),
                "Impact"
            )

            Log("backend", "debug", "controller",
                f"Using weight_key='{weight_key}', value_key='{value_key}' "
                f"from sample keys: {list(sample.keys())}")

            # Solve knapsack for this depot
            result = solve_knapsack(
                tasks=depot_vehicles,
                capacity=capacity,
                weight_key=weight_key,
                value_key=value_key,
            )
            result["depot_name"] = depot_name
            result["depot_info"] = depot
            results.append(result)
    else:
        Log("backend", "warn", "controller",
            "No depots found. Cannot determine capacity.")
        results.append({
            "error": "No depot data available to determine mechanic-hour budget",
            "raw_depots_data": depots_data,
            "raw_vehicles_data_sample": vehicles_list[:3] if vehicles_list else [],
        })

    Log("backend", "info", "handler",
        f"GET /schedule — returning {len(results)} depot schedules")

    return JSONResponse(content={
        "schedules": results,
        "summary": {
            "total_depots_processed": len(results),
            "total_vehicles_available": len(vehicles_list),
        },
    })


# =============================================================================
# Entry Point
# =============================================================================
if __name__ == "__main__":
    import uvicorn

    Log("backend", "info", "config",
        "Starting Vehicle Maintenance Scheduler on port 8001")
    uvicorn.run(app, host="0.0.0.0", port=8001)
