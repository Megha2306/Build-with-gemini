# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
import urllib.parse
import urllib.request
import uuid
from typing import Optional
from zoneinfo import ZoneInfo

from pathlib import Path
import google.auth
from google import genai
from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.cloud import firestore, storage
from google.genai import types

from .a2ui_utils import a2ui_callback

# Hardcoded project ID and bucket name
PROJECT_ID = "qwiklabs-gcp-02-1b731aa11332"
BUCKET_NAME = "endurance-pulse-media-qwiklabs-gcp-02-1b731aa11332"

credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
db = firestore.Client(project=PROJECT_ID, credentials=credentials)
storage_client = storage.Client(project=PROJECT_ID, credentials=credentials)


def get_workout_catalog(category: Optional[str] = None) -> str:
    """Retrieves available structured workouts from the workout catalog.

    Args:
        category: Optional category filter (e.g. 'Running', 'Cycling', 'Swimming').

    Returns:
        A JSON string listing matching workout routines from Firestore.
    """
    ref = db.collection("workout_catalog")
    docs = ref.stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        if category:
            if data.get("category", "").lower() == category.lower():
                results.append(data)
        else:
            results.append(data)
    return json.dumps(results, indent=2)


def log_workout(
    activity: str,
    workout_name: str,
    distance_km: float,
    duration_mins: int,
    rpe: int,
    notes: str = "",
) -> str:
    """Logs a completed workout entry to the user's workout history in Firestore.

    Args:
        activity: The type of sport/activity (e.g. 'Running', 'Cycling', 'Swimming').
        workout_name: Name or description of the workout (e.g. 'Zone 2 Base Run').
        distance_km: Distance covered in kilometers.
        duration_mins: Duration of workout in minutes.
        rpe: Rate of Perceived Exertion (scale 1-10).
        notes: Optional comments or observations from the workout.

    Returns:
        A confirmation message with the generated log entry ID.
    """
    log_id = f"log-{uuid.uuid4().hex[:6]}"
    now_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry = {
        "log_id": log_id,
        "activity": activity,
        "workout_name": workout_name,
        "distance_km": float(distance_km),
        "duration_mins": int(duration_mins),
        "rpe": int(rpe),
        "notes": notes,
        "logged_at": now_str,
    }
    db.collection("workout_logs").document(log_id).set(entry)
    return f"Successfully recorded workout log '{log_id}' for {activity}: {workout_name} ({distance_km} km, {duration_mins} mins, RPE {rpe})."


def get_workout_history(activity: Optional[str] = None) -> str:
    """Retrieves logged workouts from the user's training history in Firestore.

    Args:
        activity: Optional activity type filter (e.g. 'Running', 'Cycling').

    Returns:
        A JSON string listing the user's recorded workout logs from Firestore.
    """
    ref = db.collection("workout_logs")
    docs = ref.stream()
    results = []
    for doc in docs:
        data = doc.to_dict()
        if activity:
            if data.get("activity", "").lower() == activity.lower():
                results.append(data)
        else:
            results.append(data)
    return json.dumps(results, indent=2)


def calculate_training_zones(resting_hr: int, max_hr: int) -> str:
    """Calculates personalized heart rate training zones (Zones 1-5) using the Karvonen formula.

    Args:
        resting_hr: Resting heart rate in beats per minute (BPM).
        max_hr: Maximum heart rate in beats per minute (BPM).

    Returns:
        A JSON string containing the target heart rate ranges for Zones 1 through 5.
    """
    hrr = max_hr - resting_hr
    zones = {
        "Zone 1 (Active Recovery)": f"{round(resting_hr + 0.50 * hrr)} - {round(resting_hr + 0.60 * hrr)} BPM",
        "Zone 2 (Aerobic Base)": f"{round(resting_hr + 0.60 * hrr)} - {round(resting_hr + 0.70 * hrr)} BPM",
        "Zone 3 (Tempo / Aerobic)": f"{round(resting_hr + 0.70 * hrr)} - {round(resting_hr + 0.80 * hrr)} BPM",
        "Zone 4 (Threshold)": f"{round(resting_hr + 0.80 * hrr)} - {round(resting_hr + 0.90 * hrr)} BPM",
        "Zone 5 (VO2 Max)": f"{round(resting_hr + 0.90 * hrr)} - {max_hr} BPM",
    }
    return json.dumps({"resting_hr": resting_hr, "max_hr": max_hr, "hrr": hrr, "zones": zones}, indent=2)


def get_workout_weather(city: str = "San Francisco") -> str:
    """Fetches real-time weather conditions for an outdoor training location from Open-Meteo public API.

    Args:
        city: City name for the outdoor workout location (e.g. 'San Francisco', 'Boston', 'London').

    Returns:
        A JSON string with real weather data (temperature, humidity, wind speed) and outdoor suitability.
    """
    try:
        api_key = os.getenv("WEATHER_API_KEY", "")
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={urllib.parse.quote(city)}&count=1"
        req = urllib.request.Request(geo_url, headers={"User-Agent": "EndurancePulseAgent/1.0"})
        with urllib.request.urlopen(req) as resp:
            geo_data = json.loads(resp.read().decode())

        if not geo_data.get("results"):
            return json.dumps({"error": f"Could not find location coordinates for city: {city}"})

        loc = geo_data["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]
        place_name = f"{loc['name']}, {loc.get('admin1', loc.get('country', ''))}"

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,wind_speed_10m"
        if api_key:
            weather_url += f"&apikey={api_key}"

        req_w = urllib.request.Request(weather_url, headers={"User-Agent": "EndurancePulseAgent/1.0"})
        with urllib.request.urlopen(req_w) as resp_w:
            w_data = json.loads(resp_w.read().decode())

        current = w_data.get("current", {})
        temp_c = current.get("temperature_2m")
        humidity = current.get("relative_humidity_2m")
        wind_kmh = current.get("wind_speed_10m")

        return json.dumps({
            "location": place_name,
            "temperature_celsius": temp_c,
            "temperature_fahrenheit": round(temp_c * 9/5 + 32, 1) if temp_c is not None else None,
            "relative_humidity_percent": humidity,
            "wind_speed_kmh": wind_kmh,
            "data_source": "Open-Meteo Public API"
        }, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch weather: {str(e)}"})


def generate_workout_badge(description: str, tool_context: ToolContext) -> str:
    """Generates a motivational workout milestone badge image using gemini-3.1-flash-lite-image in the global region.
    Saves the image as a Playground Artifact and uploads it to the public Cloud Storage bucket.

    Args:
        description: Description of the workout badge or milestone achievement (e.g. '10K Run Finisher Badge', '100km Cycling Medal').
        tool_context: ToolContext provided by the ADK runtime environment.

    Returns:
        The public HTTPS URL of the uploaded image in Cloud Storage (https://storage.googleapis.com/<bucket>/<filename>).
    """
    try:
        genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )
        prompt = f"A high quality graphic design of a motivational sports achievement badge for: {description}. Endurance pulse theme."

        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )

        part = response.candidates[0].content.parts[0]
        image_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type or "image/jpeg"

        ext = "png" if "png" in mime_type else "jpg"
        filename = f"badge-{uuid.uuid4().hex[:8]}.{ext}"

        # 1. Save as Playground Artifact
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload directly to public Cloud Storage bucket
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return public_url
    except Exception as e:
        return f"Error generating image: {str(e)}"


def generate_workout_video(description: str, tool_context: ToolContext) -> str:
    """Generates a short workout or fitness video clip using Google's Omni model (gemini-omni-flash-preview) in the global region.
    Saves the video as a Playground Artifact and uploads it to the public Cloud Storage bucket.

    Args:
        description: Description of the workout or exercise motion to generate a short video for (e.g. 'Sprinting technique video', 'Cycling cadence demo').
        tool_context: ToolContext provided by the ADK runtime environment.

    Returns:
        The public HTTPS URL of the uploaded video in Cloud Storage (https://storage.googleapis.com/<bucket>/<filename>).
    """
    try:
        genai_client = genai.Client(
            vertexai=True,
            project=PROJECT_ID,
            location="global",
        )
        prompt = f"Generate a short video clip illustrating: {description}. Endurance pulse theme."

        response = genai_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
            generation_config={
                "response_modalities": ["VIDEO"]
            }
        )

        video_bytes = None
        mime_type = "video/mp4"

        if hasattr(response, "output_video") and response.output_video:
            out_vid = response.output_video
            if hasattr(out_vid, "data") and out_vid.data:
                video_bytes = out_vid.data
                mime_type = getattr(out_vid, "mime_type", "video/mp4") or "video/mp4"
            elif hasattr(out_vid, "content") and out_vid.content:
                for item in out_vid.content:
                    if hasattr(item, "inline_data") and item.inline_data:
                        video_bytes = item.inline_data.data
                        mime_type = getattr(item.inline_data, "mime_type", "video/mp4") or "video/mp4"
                        break

        if not video_bytes:
            return "Error: No video bytes returned from gemini-omni-flash-preview."

        ext = "mp4" if "mp4" in mime_type else "webm"
        filename = f"video-{uuid.uuid4().hex[:8]}.{ext}"

        # 1. Save as Playground Artifact
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

        # 2. Upload directly to public Cloud Storage bucket
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
        return public_url
    except Exception as e:
        return f"Error generating video: {str(e)}"


# Check deployment_metadata.json or environment for Agent Engine resource name
metadata_file = Path(__file__).parent.parent / "deployment_metadata.json"
agent_engine_resource_name = None

if metadata_file.exists():
    try:
        with open(metadata_file, "r") as f:
            meta_data = json.load(f)
            agent_engine_resource_name = meta_data.get("agent_engine_resource_name") or meta_data.get("resource_name")
    except Exception:
        pass

if not agent_engine_resource_name:
    agent_engine_resource_name = os.getenv("AGENT_ENGINE_RESOURCE_NAME")

if agent_engine_resource_name:
    sandbox_code_executor = AgentEngineSandboxCodeExecutor(agent_engine_resource_name=agent_engine_resource_name)
else:
    sandbox_code_executor = AgentEngineSandboxCodeExecutor()


# Memory Bank callback to persist session memories after each turn
async def generate_memories_callback(callback_context: CallbackContext):
    try:
        await callback_context.add_session_to_memory()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Could not add session to memory: {e}")
    return None


MEMORY_BANK_ID = "4213825536893386752"


def memory_bank_service_builder():
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location="us-east4",
        agent_engine_id=MEMORY_BANK_ID,
    )


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are Endurance Pulse, a dedicated AI fitness and endurance coach. "
        "Help athletes plan workouts, check outdoor workout weather conditions, calculate heart rate training zones, "
        "generate motivational workout milestone badges, generate short workout demonstration videos, record completed training logs, "
        "and review their training history stored in Firestore. "
        "You are equipped with long-term cross-session memory via Vertex AI Memory Bank (PreloadMemoryTool). "
        "Pay strict attention to remembering and recalling ALL user details and preferences across sessions, including: "
        "user name, age, physical stats, resting & max heart rates, fitness goals, sport preferences, "
        "preferred workout schedules, injuries, dietary constraints, and explicit instructions. "
        "Use these remembered details to continuously personalize every response. "
        "Always be encouraging, technical, and precise."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=sandbox_code_executor,
    tools=[
        PreloadMemoryTool(),
        get_workout_catalog,
        log_workout,
        get_workout_history,
        calculate_training_zones,
        get_workout_weather,
        generate_workout_badge,
        generate_workout_video,
    ],
    after_agent_callback=generate_memories_callback,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

