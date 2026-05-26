#!/bin/bash
# dev_native.sh — DATN scope service manager
# Scope: 2 trụ cột (Multi-criteria CV Freshness + Market Intelligence Dashboard)
# Routes: /cv-health, /market-intel
# Services cần thiết: API Gateway, NER, Skill, Frontend

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'
BOLD='\033[1m'

# Setup env vars & paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."
cd "$PROJECT_ROOT"

# Load .env if exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}Loading configuration from .env...${NC}"
    export $(grep -v '^#' .env | xargs)
fi

# Determine Python exec
export SYSTEM_PYTHON="python3"
if ! command -v python3 &> /dev/null; then
    export SYSTEM_PYTHON="python"
fi

# Setup virtual environment logic
VENV_DIR="$PROJECT_ROOT/.venv"
if [ -d "$VENV_DIR" ]; then
    export PYTHON_EXEC="$VENV_DIR/bin/python"
    export PIP_EXEC="$VENV_DIR/bin/pip"
else
    export PYTHON_EXEC="$SYSTEM_PYTHON"
    export PIP_EXEC="$SYSTEM_PYTHON -m pip"
fi

show_banner() {
    clear
    echo -e "${PURPLE}${BOLD}=========================================================${NC}"
    echo -e "${PURPLE}${BOLD}    CV HEALTH INTELLIGENCE — DATN DEV RUNNER             ${NC}"
    echo -e "${PURPLE}${BOLD}=========================================================${NC}"
    echo -e "${CYAN}Scope: Multi-criteria Freshness + Market Intelligence${NC}"
    if [ -d "$VENV_DIR" ]; then
        echo -e "${GREEN}Env: Virtual Environment (.venv) ACTIVE${NC}"
    else
        echo -e "${YELLOW}Env: Global Python (Recommended: option 'i' để setup venv)${NC}"
    fi
}

check_container() {
    if docker ps --format '{{.Names}}' | grep -q "$1"; then
        echo -e "${GREEN}ONLINE${NC}"
    else
        echo -e "${RED}OFFLINE${NC}"
    fi
}

show_status() {
    echo -e "\n${BOLD}Infrastructure Status:${NC}"
    echo -e "  Main Postgres (5433):     $(check_container "postgres_main")"
    echo -e "  Skill Postgres (5434):    $(check_container "skill_postgres")"
    echo -e "  Skill ChromaDB (8003):    $(check_container "skill_chromadb")"
}

show_menu() {
    echo -e "\n${BOLD}Management Options:${NC}"
    echo -e "  ${YELLOW}1)${NC} Start ALL Databases (Postgres + ChromaDB)"
    echo -e "  ${YELLOW}2)${NC} Stop ALL Databases"
    echo -e "  ------------------------------------------------"
    echo -e "  ${YELLOW}3)${NC} Run API Gateway (.NET Core)        — port 5000"
    echo -e "  ${YELLOW}4)${NC} Run NER Service (Python)            — port 5005"
    echo -e "  ${YELLOW}5)${NC} Run Skill Service (Python)          — port 5002"
    echo -e "  ${YELLOW}6)${NC} Run Frontend (React/Vite)           — port 5173"
    echo -e "  ------------------------------------------------"
    echo -e "  ${YELLOW}s)${NC} Seed Knowledge Base (Skill ChromaDB)"
    echo -e "  ${YELLOW}i)${NC} Setup Venv & Install ALL Dependencies"
    echo -e "  ${YELLOW}q)${NC} Quit"
    echo -ne "\n${BOLD}Select option [1-6, s, i, q]: ${NC}"
}

# Main loop
while true; do
    show_banner
    show_status
    show_menu
    read opt

    case $opt in
        1)
            echo -e "${BLUE}Starting databases (Postgres × 2 + Skill ChromaDB)...${NC}"
            docker compose up -d postgres_main skill_postgres skill_chromadb
            echo -e "${GREEN}Infrastructure online. Wait 5-10s for Postgres ready.${NC}"
            sleep 2
            ;;
        2)
            echo -e "${RED}Stopping all DATN databases...${NC}"
            docker compose stop postgres_main skill_postgres skill_chromadb
            ;;
        3)
            echo -e "${GREEN}Starting API Gateway (.NET) on :5000...${NC}"
            export ConnectionStrings__DefaultConnection="Host=localhost;Port=5433;Database=cv_assistant;Username=postgres;Password=postgres"
            cd services/api_gateway/CvAssistant.ApiGateway.API && dotnet run
            cd ../../../
            ;;
        4)
            echo -e "${GREEN}Starting NER Service on :5005 (parse CV PDF cho /cv-health upload)...${NC}"
            export PYTHONPATH=$PYTHONPATH:$(pwd)
            cd services/ner_service && $PYTHON_EXEC -m uvicorn main:app --port 5005 --reload
            cd ../..
            ;;
        5)
            echo -e "${GREEN}Starting Skill Service on :5002 (Multi-criteria Freshness + Market Intel)...${NC}"
            export PYTHONPATH=$PYTHONPATH:$(pwd)
            export DATABASE_URL="postgresql://skill_user:skill_password@localhost:5434/skill_data"
            export CHROMA_HOST="localhost"
            export CHROMA_PORT="8003"
            cd services/skill_service && $PYTHON_EXEC -m uvicorn main:app --port 5002 --reload
            cd ../..
            ;;
        6)
            echo -e "${GREEN}Starting Frontend on :5173 (/cv-health + /market-intel)...${NC}"
            cd frontend && npm run dev
            cd ..
            ;;
        s)
            echo -e "${BLUE}Seeding Skill ChromaDB (8003) — required cho semantic search...${NC}"
            export PYTHONPATH=$PYTHONPATH:$(pwd)
            $PYTHON_EXEC scripts/ingest_onet_skills.py --port 8003
            $PYTHON_EXEC scripts/setup_knowledge_base.py --port 8003
            echo -e "${GREEN}Seeding done.${NC}"
            ;;
        i)
            echo -e "${BLUE}Setting up virtual environment...${NC}"
            $SYSTEM_PYTHON -m venv .venv
            if [ $? -ne 0 ]; then
                echo -e "${RED}Failed to create venv. Make sure python3-venv is installed.${NC}"
                echo -e "Try: sudo apt install python3-venv"
            else
                export PYTHON_EXEC="$VENV_DIR/bin/python"
                export PIP_EXEC="$VENV_DIR/bin/pip"
                echo -e "${GREEN}Venv created.${NC}"
                echo -e "${BLUE}Installing dependencies (NER + Skill service only)...${NC}"
                $PIP_EXEC install --upgrade pip
                $PIP_EXEC install python-dotenv pydantic-settings uvicorn fastapi
                # Only install for services trong DATN scope
                for svc in ner_service skill_service crawler_service; do
                    req="services/$svc/requirements.txt"
                    if [ -f "$req" ]; then
                        echo -e "${CYAN}Installing from $req...${NC}"
                        $PIP_EXEC install -r "$req"
                    fi
                done
                echo -e "${GREEN}Setup complete. .venv ready.${NC}"
            fi
            ;;
        q)
            echo -e "${PURPLE}Goodbye.${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option!${NC}"
            ;;
    esac

    echo -ne "\n${YELLOW}Service stopped. Press ENTER để quay lại menu...${NC}"
    read
done
