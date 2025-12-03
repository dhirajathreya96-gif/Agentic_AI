# Outlook Calendar ReAct Agent

A **ReAct agent** built with **LangGraph** and **OpenAI GPT-4o-mini** to manage your Outlook calendar.
This agent can **check availability** and **schedule meetings** using Microsoft Graph API. It’s production-ready, modular, and designed for deployment.

---

## Features

* ✅ Check calendar availability for a given date/time.
* ✅ Schedule new meetings with multiple attendees.
* ✅ ReAct architecture: LLM decides when to call tools.
* ✅ Fully modular: tools are lazy-loaded, no auth import at module load.
* ✅ FastAPI backend for API requests.
* ✅ Optional Streamlit frontend for interactive chat.
* ✅ Works with Device Code Flow or OAuth2 (Azure).

---

## Screen recording



https://github.com/user-attachments/assets/15032ffb-6c1d-42dc-ab43-68e7d3f368af



## Folder Structure

```
.
├── tools.py                 # Tool functions for calendar management
├── main.py                  # Agent executor with LLM & LangGraph
├── auth.py                  # Outlook authentication (Device Code Flow)
├── fastapi_app.py           # FastAPI server wrapper (optional)
├── streamlit_app.py         # Streamlit UI (optional)
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker setup for containerized deployment
└── README.md                # Project documentation
```

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/outlook-react-agent.git
cd outlook-react-agent
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file:

```env
CLIENT_ID=<your_azure_app_client_id>
TENANT_ID=<your_tenant_id>        # e.g., "organizations" or your tenant GUID
CLIENT_SECRET=<your_client_secret> # if using Authorization Code Flow
```

For Device Code Flow, `CLIENT_SECRET` is optional.

---

## Usage

### Run the agent in terminal

```bash
python main.py
```

Type your messages, e.g.:

```
You: Check if I am free on 2025-12-05 at 09:00 for 60 minutes
You: Schedule a meeting on 2025-12-05 at 14:00 with alice@example.com and bob@example.com titled "Project Sync"
```

### Run FastAPI backend

```bash
uvicorn fastapi_app:app --reload
```

POST to `/chat`:

```json
POST http://127.0.0.1:8000/chat
{
  "session_id": "123",
  "prompt": "Schedule a meeting tomorrow at 10am with alice@example.com"
}
```

### Optional Streamlit frontend

```bash
streamlit run streamlit_app.py
```

---

## Tools

1. **check_calendar_availability**
   Checks if a specific date/time is free.
   Input JSON:

   ```json
   {"date": "2025-12-05", "time": "09:00:00", "duration_minutes": 60}
   ```

2. **schedule_new_meeting**
   Schedules a meeting.
   Input JSON:

   ```json
   {
       "date": "2025-12-05",
       "time": "14:00:00",
       "duration_minutes": 60,
       "attendees": ["alice@example.com", "bob@example.com"],
       "subject": "Project S

---

## Notes

* The agent uses **LangGraph ReAct** to decide when to call tools.
* Tools are **lazy-loaded**, so the project can run even without authentication, useful for development.
* The authentication system supports both **Device Code Flow** and **Authorization Code Flow** for Microsoft Graph.

---

## License

MIT License – free to use and modify.

---

## Author



Dhiraj Athreya – (https://github.com/dhirajathreya96)
Contact: (mailto:dhirajathreya96@gmail.com)

