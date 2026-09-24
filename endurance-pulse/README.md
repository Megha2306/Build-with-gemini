# Endurance Pulse ⚡

> Dedicated AI Fitness and Endurance Coach powered by Google Agent Development Kit (ADK) and Vertex AI.

![Endurance Pulse Demo](./demo.gif)

---

## 📌 Overview

**Endurance Pulse** is an intelligent fitness and endurance coaching agent designed for runners, cyclists, swimmers, and triathletes. Built with Google's **Agent Development Kit (ADK)** and running on **Gemini 2.5 Flash**, Endurance Pulse combines real-time tool execution, structured Agent-to-User Interface (A2UI) component rendering, long-term session memory, database persistence, and multimodal AI asset generation.

---

## ⚡ Implemented Capabilities & Architecture

Based directly on the codebase (`app/agent.py` and `agents-cli-manifest.yaml`), Endurance Pulse implements the following core features and Google Cloud integrations:

### 🧠 1. Long-Term Cross-Session Memory (Vertex AI Memory Bank)
- **Service**: `VertexAiMemoryBankService` (Location: `us-east4`)
- **Tool & Callbacks**: Integrated via `PreloadMemoryTool` and `after_agent_callback` to store and recall athlete profiles, physical stats, resting/max heart rates, injury history, dietary constraints, and personal fitness goals across sessions.

### 🗄️ 2. Database Persistence (Google Cloud Firestore)
- **Database**: Google Cloud Firestore (`workouts` collection)
- **Tools**:
  - `log_workout`: Records completed athlete workouts with sport type, duration, distance, heart rate, and training notes into Firestore.
  - `get_workout_history`: Queries recent training logs from Firestore ordered chronologically to analyze athlete progression.

### ☁️ 3. Media Artifact Storage (Google Cloud Storage)
- **Bucket**: Public Cloud Storage bucket (`endurance-pulse-media-*`)
- **Integration**: Direct GCS blob upload for generated images and video clips to provide public HTTPS media URLs rendered directly within chat interface components.

### 🎨 4. AI Image Generation (`generate_workout_badge`)
- **Model**: Gemini Image Generation (`imagen-3.0-generate-002`)
- **Capability**: Dynamically generates custom milestone badges (e.g. 10K completion, marathon badges) saved to Playground Artifacts and uploaded to GCS.

### 🎬 5. AI Video Generation (`generate_workout_video`)
- **Model**: Google Omni Model (`gemini-omni-flash-preview` in region `global`)
- **Capability**: Generates short workout demonstration video clips via the Interactions API, saved to Playground Artifacts and stored in GCS.

### 🌤️ 6. Workout Tools & Weather Integration
- **`get_workout_catalog`**: Provides structured exercise & workout routines across running, cycling, swimming, and strength training.
- **`calculate_training_zones`**: Computes 5 target heart rate zones (Recovery, Endurance, Tempo, Threshold, Anaerobic) based on age and resting heart rate.
- **`get_workout_weather`**: Advises on outdoor weather conditions (temperature, wind, precipitation) for planned training sessions.

### 🎨 7. Agent-to-User Interface (A2UI v0.8)
- **UI Engine**: `A2uiSchemaManager` with `BasicCatalog`
- **Output**: Generates flat, responsive A2UI card layouts (Cards, Columns, Rows, Text, Images) rendered dynamically by the web frontend.

### 🌐 8. Web Frontend & Proxy
- **Stack**: FastAPI proxy backend serving a custom, responsive HTML5/CSS3 dark-themed athletic interface.
- **Protocol**: A2A (Agent-to-Agent) client communication.

---

## 🛠️ Project Structure

```
.
├── app/
│   └── agent.py              # Core ADK agent, tools, system prompt, and A2UI schema setup
├── frontend/
│   ├── main.py               # FastAPI proxy server connecting web UI to Agent Engine
│   └── static/
│       └── index.html        # Rebranded athletic dark-mode chat interface
├── agents-cli-manifest.yaml  # Agents CLI deployment manifest
├── pyproject.toml            # Dependencies and Python package definitions
├── demo.gif                  # Recorded inline demo recording
└── README.md                 # Project documentation
```

---

## 🚀 Setup & Local Execution

### 1. Prerequisites
- Python 3.11+
- `uv` package manager (`pip install uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
- Google Cloud SDK (`gcloud`) authenticated with access to Firestore, Cloud Storage, and Vertex AI APIs.

### 2. Installation & Environment Setup
Clone the repository and install dependencies using `uv`:

```bash
uv sync
```

Set required environment variables:

```bash
export GOOGLE_GENAI_USE_VERTEXAI=true
export LOCATION=us-east4
export AGENT_ENGINE_RESOURCE_NAME=<your-agent-engine-resource-name>
export AGENT_DIRECTORY=app
```

### 3. Running the Agent Backend Locally
You can test the agent framework locally via ADK CLI:

```bash
agents-cli run
```

### 4. Running the Web Frontend Locally
Start the FastAPI proxy server locally:

```bash
uv run python -m frontend.main
```

The server will start locally on port 8080. Access it in your web browser at the local port specified by the server output.
