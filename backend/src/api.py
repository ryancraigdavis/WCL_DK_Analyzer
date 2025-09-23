import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import sentry_sdk
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentry_sdk.integrations.aws_lambda import AwsLambdaIntegration

from analysis.analyze import analyze
from client import PrivateReport, TemporaryUnavailable, fetch_report

SENTRY_ENABLED = os.environ.get("AWS_EXECUTION_ENV") is not None
if SENTRY_ENABLED:
    sentry_sdk.init(
        dsn="https://d5eb49442a8f433b86952081e5e42bfb@o4504244781711360.ingest.sentry.io/4504244816117760",
        traces_sample_rate=0.05,
        attach_stacktrace=True,
        integrations=[AwsLambdaIntegration()],
    )
app = FastAPI()


async def catch_exceptions_middleware(request, call_next):
    try:
        return await call_next(request)
    except Exception as e:
        logging.exception(e)
        return Response("Internal server error", status_code=500)


# Add this middleware first so 500 errors have CORS headers
app.middleware("http")(catch_exceptions_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://classic.warcraftlogs.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeResponse(BaseModel):
    data: dict


async def save_combat_log(report, report_id: str, fight_id: int, source_id: int):
    """Save combat log data to local JSON file for analysis"""
    try:
        # Create logs directory if it doesn't exist (in the backend root)
        logs_dir = Path("../saved_logs")
        logs_dir.mkdir(exist_ok=True)

        # Create filename with timestamp and metadata
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{report_id}_{fight_id}_{source_id}.json"
        filepath = logs_dir / filename

        # Debug: log the working directory and file path
        logging.info(f"Current working directory: {os.getcwd()}")
        logging.info(f"Attempting to save to: {filepath.absolute()}")

        # Prepare data to save
        log_data = {
            "metadata": {
                "report_id": report_id,
                "fight_id": fight_id,
                "source_id": source_id,
                "source_name": report.source.name,
                "timestamp": timestamp,
                "end_time": report.end_time,
            },
            "events": report._events,
            "combatant_info": report._combatant_info,
            "fights": report._fights,
            "abilities": report._abilities,
            "actors": report._actors,
            "rankings": report._rankings,
        }

        # Save to file
        with open(filepath, "w") as f:
            json.dump(log_data, f, indent=2)

        logging.info(f"Saved combat log to {filepath}")

    except Exception as e:
        logging.error(f"Failed to save combat log: {e}")
        # Don't let this break the main analysis flow


@app.get("/analyze_fight")
async def analyze_fight(
    response: Response, report_id: str, fight_id: int, source_id: int
):
    if report_id == "compare":
        response.status_code = 400
        return {"error": "Can not analyze while using the 'Compare' feature"}

    try:
        report = await fetch_report(report_id, fight_id, source_id)

        # Save the combat log for analysis
        await save_combat_log(report, report_id, fight_id, source_id)

    except PrivateReport:
        response.status_code = 403
        return {"error": "Can not analyze private reports"}
    except TemporaryUnavailable:
        response.status_code = 503
        return {"error": "Bad response from Warcraft Logs, try again"}

    events = analyze(report, fight_id)

    # don't cache reports that are less than a day old
    ended_ago = datetime.now() - datetime.fromtimestamp(report.end_time / 1000)
    if fight_id == -1 and ended_ago < timedelta(days=1):
        response.headers["Cache-Control"] = "no-cache"
    else:
        response.headers["Cache-Control"] = "max-age=86400"
    return {"data": events}
