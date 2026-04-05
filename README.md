# CV Assistant

CV Assistant is a multi-service project for CV analysis, ATS optimization, skill matching, career guidance, and chatbot-assisted resume editing.

This README is intentionally written for team onboarding.

Goal:

- configure the machine once
- run one script
- choose menu options
- start coding without remembering every service command

## What is in this repo

- `frontend`: React + Vite UI
- `services/api_gateway`: .NET 9 API Gateway
- `services/ner_service`: FastAPI NER service
- `services/skill_service`: FastAPI skill matching service
- `services/career_service`: FastAPI career recommendation service
- `services/chatbot_service`: FastAPI chatbot service
- `scripts/dev_native.sh`: hybrid runner
- `manage.sh`: Docker runner

## Prerequisites

Install these first:

- Docker + Docker Compose
- Node.js `20+`
- npm
- Python `3.10+`
- `python3-venv`
- .NET SDK `9.0`

Quick checks:

```bash
docker --version
docker compose version
node -v
npm -v
python3 --version
dotnet --version
```

## Local assets you still need

Some large runtime assets are intentionally not always kept in Git.

Before expecting the full app to work, make sure these exist locally:

- `models/ner/final`
- `models/ner/jd_final`
- `knowledge_base/onet/db_28_1_text`

If these are missing, ask a teammate for the shared project assets.

## Environment

You usually do not need much config to start locally.

Optional `.env` example:

```env
APP_ENV=development
DEBUG=true
VITE_API_BASE_URL=http://localhost:8081/api
CHAT_USE_GROQ=false
```

## The two supported ways to run

### 1. Full Docker mode

Use this when:

- you want the fastest full-stack startup
- you do not need hot reload for every backend service
- you just want to smoke test the whole app

Main script:

```bash
./manage.sh
```

Recommended menu flow:

- `8`: Start ALL
- `l`: View logs
- `d`: Stop all containers
- `q`: Quit script

Important note:

- `manage.sh` is useful for full-stack Docker startup.
- Some older infra-specific options in this script are not as up to date as the main `Start ALL` flow.
- For team usage, prefer `8` to boot the stack instead of trying to compose infra manually inside this script.

### 2. Hybrid mode

Use this when:

- databases should run in Docker
- API Gateway, Python services, and frontend should run locally
- you want easier debugging and hot reload

Main script:

```bash
./scripts/dev_native.sh
```

Recommended menu flow:

- `i`: Setup venv and install dependencies
- `1`: Start all databases in Docker
- `s`: Seed vector stores if needed
- `2`: Run API Gateway
- `3`: Run NER service
- `4`: Run Skill service
- `5`: Run Career service
- `6`: Run Chatbot service
- `7`: Run Frontend
- `8`: Stop all databases
- `q`: Quit script

Important note:

- options `2` to `7` are foreground processes
- that means you usually open the script in multiple terminal tabs and start one service per tab

---

## Fastest team setup

If you are new to the project, do this once:

```bash
chmod +x manage.sh
chmod +x scripts/dev_native.sh
```

Then choose one path below.

---

## Option A: Quick full-stack run with Docker

### Step 1

From project root:

```bash
./manage.sh
```

### Step 2

Choose:

```text
8
```

This runs:

- frontend
- api gateway
- ner service
- skill service
- career service
- chatbot service
- postgres
- chroma services

### Step 3

Wait until containers are healthy, then open:

- Frontend: `http://localhost:5173`
- API Gateway Swagger: `http://localhost:8081/swagger-ui.html`

### Step 4

If chatbot or skill/career features return empty context, seed data manually from the project root:

```bash
python3 scripts/ingest_onet_skills.py --port 8003
python3 scripts/setup_knowledge_base.py --port 8003
python3 scripts/setup_knowledge_base.py --port 8004
python3 scripts/ingest_onet_skills.py --port 8005
python3 scripts/setup_knowledge_base.py --port 8005
```

### Step 5

When done, stop everything:

- inside script: choose `d`
- or outside script:

```bash
docker compose down --remove-orphans
```

---

## Option B: Recommended development flow with script

This is the best choice for most team members.

### Step 1

From project root:

```bash
./scripts/dev_native.sh
```

### Step 2

Choose:

```text
i
```

This does the setup work for you:

- creates `.venv`
- upgrades `pip`
- installs Python dependencies from service requirement files

### Step 3

Run the script again:

```bash
./scripts/dev_native.sh
```

Choose:

```text
1
```

This starts:

- `postgres_main`
- `skill_postgres`
- `skill_chromadb`
- `career_chromadb`
- `chatbot_chromadb`

### Step 4

If this is your first local setup, seed the vector stores:

Run the script again and choose:

```text
s
```

### Step 5

Now start services in separate terminals.

Terminal 1:

```bash
./scripts/dev_native.sh
```

Choose:

```text
2
```

This starts the API Gateway.

Terminal 2:

```bash
./scripts/dev_native.sh
```

Choose:

```text
3
```

This starts the NER service.

Terminal 3:

```bash
./scripts/dev_native.sh
```

Choose:

```text
4
```

This starts the Skill service.

Terminal 4:

```bash
./scripts/dev_native.sh
```

Choose:

```text
5
```

This starts the Career service.

Terminal 5:

```bash
./scripts/dev_native.sh
```

Choose:

```text
6
```

This starts the Chatbot service.

Terminal 6:

```bash
./scripts/dev_native.sh
```

Choose:

```text
7
```

This starts the frontend.

### Step 6

Open:

- Frontend: `http://localhost:5173`
- API Gateway Swagger: `http://localhost:8081/swagger-ui.html`

### Step 7

When done, stop DB containers:

```bash
./scripts/dev_native.sh
```

Choose:

```text
8
```

---

## Ports

Useful local ports:

- Frontend: `5173`
- API Gateway: `8081`
- NER: `5005`
- Skill: `5002`
- Career: `5003`
- Chatbot: `5004`
- Main Postgres: `5433`
- Skill Postgres: `5434`
- Skill Chroma: `8003`
- Career Chroma: `8004`
- Chatbot Chroma: `8005`

## Health checks

Use these after startup:

- `http://localhost:5005/health`
- `http://localhost:5002/health`
- `http://localhost:5003/health`
- `http://localhost:5004/health`
- `http://localhost:8081/swagger-ui.html`

## Common issues

### `./scripts/dev_native.sh` says venv creation failed

Install:

```bash
sudo apt install python3-venv
```

### Frontend runs but cannot talk to backend

Check that the frontend is pointing to:

```env
VITE_API_BASE_URL=http://localhost:8081/api
```

### NER service fails at startup

The fine-tuned model folders are missing:

- `models/ner/final`
- `models/ner/jd_final`

### Chatbot service starts but answers fail

Likely causes:

- NER service is not running
- Skill or Career service is not running
- Chroma stores were never seeded
- local Ollama is unavailable

If your team uses Groq instead of Ollama, set in `.env`:

```env
CHAT_USE_GROQ=true
CHAT_GROQ_API_KEY=your_key_here
```

### Docker mode starts but some features still do not work

That usually means runtime data is missing:

- models are missing
- O*NET data is missing
- vector stores were not seeded

## Recommended team usage

For daily development:

- use `./scripts/dev_native.sh`

For quick end-to-end smoke tests:

- use `./manage.sh`
- choose `8`

That is the intended low-friction workflow for this repository.
