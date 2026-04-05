#!/bin/bash
# dev_native.sh - PRO Native/Hybrid Service Manager for Resume Assistant
# Updated for Microservice Isolation & Virtual Environment Support

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' 
BOLD='\033[1m'

# Setup Env Vars & Paths
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."
cd "$PROJECT_ROOT"

# Load .env if exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}Loading configuration from .env...${NC}"
    export $(grep -v '^#' .env | xargs)
fi

# Determine Python Exec
export SYSTEM_PYTHON="python3"
if ! command -v python3 &> /dev/null; then
    export SYSTEM_PYTHON="python"
fi

# Setup Virtual Environment logic
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
    echo -e "${PURPLE}${BOLD}================================================${NC}"
    echo -e "${PURPLE}${BOLD}    🚀 RESUME ASSISTANT - PRO NATIVE RUNNER 🚀    ${NC}"
    echo -e "${PURPLE}${BOLD}================================================${NC}"
    echo -e "${CYAN}Mode: Microservice Isolation (Hybrid Docker Infra)${NC}"
    if [ -d "$VENV_DIR" ]; then
        echo -e "${GREEN}Env: Virtual Environment (.venv) ACTIVE${NC}"
    else
        echo -e "${YELLOW}Env: Global Python (Recommended: run 'i' to setup venv)${NC}"
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
    echo -e "\n${BOLD}📊 Infrastructure Status:${NC}"
    echo -e "  Main Postgres (Port 5433):    $(check_container "postgres_main")"
    echo -e "  Skill Postgres (Port 5434):   $(check_container "skill_postgres")"
    echo -e "  Skill Chroma (Port 8003):     $(check_container "skill_chromadb")"
    echo -e "  Career Chroma (Port 8004):    $(check_container "career_chromadb")"
    echo -e "  Chatbot Chroma (Port 8005):   $(check_container "chatbot_chromadb")"
}

show_menu() {
    echo -e "\n${BOLD}🛠️  Management Options:${NC}"
    echo -e "  ${YELLOW}1)${NC} Start ALL Databases (Docker Infra)"
    echo -e "  ------------------------------------------------"
    echo -e "  ${YELLOW}2)${NC} Run API Gateway (.NET Core)"
    echo -e "  ${YELLOW}3)${NC} Run NER Service (Python)"
    echo -e "  ${YELLOW}4)${NC} Run Skill Service (Python + Postgres 5434)"
    echo -e "  ${YELLOW}5)${NC} Run Career Service (Python + Chroma 8004)"
    echo -e "  ${YELLOW}6)${NC} Run Chatbot Service (Python + Chroma 8005)"
    echo -e "  ${YELLOW}7)${NC} Run Frontend (React/Vite)"
    echo -e "  ------------------------------------------------"
    echo -e "  ${YELLOW}8)${NC} Stop ALL Databases"
    echo -e "  ${YELLOW}s)${NC} Seed ALL Vector Stores (KB Initialization)"
    echo -e "  ${YELLOW}i)${NC} Setup Venv & Install ALL Dependencies"
    echo -e "  ${YELLOW}q)${NC} Quit"
    echo -ne "\n${BOLD}Select an option [1-8, s, i, q]: ${NC}"
}

# Main Loop
while true; do
    show_banner
    show_status
    show_menu
    read opt

    case $opt in
        1) 
            echo -e "${BLUE}Starting All Isolated Databases...${NC}"
            docker compose up -d postgres_main skill_postgres skill_chromadb career_chromadb chatbot_chromadb
            echo -e "${GREEN}Infrastructure is coming online. Please wait 5-10s for Postgres to be ready.${NC}"
            sleep 2
            ;;
        2) 
            echo -e "${GREEN}Starting API Gateway (.NET)...${NC}"
            export ConnectionStrings__DefaultConnection="Host=localhost;Port=5433;Database=cv_assistant;Username=postgres;Password=postgres"
            cd services/api_gateway/CvAssistant.ApiGateway.API && dotnet run
            cd ../../../
            ;;
        3) 
            echo -e "${GREEN}Starting NER Service...${NC}"
            export PYTHONPATH=$PYTHONPATH:$(pwd)
            cd services/ner_service && $PYTHON_EXEC -m uvicorn main:app --port 5005 --reload
            cd ../..
            ;;
        4) 
            echo -e "${GREEN}Starting Skill Service (Isolated DB 5434)...${NC}"
            export PYTHONPATH=$PYTHONPATH:$(pwd)
            export DATABASE_URL="postgresql://skill_user:skill_password@localhost:5434/skill_data"
            export CHROMA_HOST="localhost"
            export CHROMA_PORT="8003"
            cd services/skill_service && $PYTHON_EXEC -m uvicorn main:app --port 5002 --reload
            cd ../..
            ;;
        5) 
            echo -e "${GREEN}Starting Career Service (Isolated Chroma 8004)...${NC}"
            export PYTHONPATH=$PYTHONPATH:$(pwd)
            export CHROMA_HOST="localhost"
            export CHROMA_PORT="8004"
            cd services/career_service && $PYTHON_EXEC -m uvicorn main:app --port 5003 --reload
            cd ../..
            ;;
        6) 
            echo -e "${GREEN}Starting Chatbot Service (Isolated Chroma 8005)...${NC}"
            export PYTHONPATH=$PYTHONPATH:$(pwd)
            export CHROMA_HOST="localhost"
            export CHROMA_PORT="8005"
            export CHAT_NER_URL="http://localhost:5005"
            export CHAT_SKILL_SERVICE_URL="http://localhost:5002"
            export CHAT_CAREER_SERVICE_URL="http://localhost:5003"
            cd services/chatbot_service && $PYTHON_EXEC -m uvicorn main:app --port 5004 --reload
            cd ../..
            ;;
        7) 
            echo -e "${GREEN}Starting Frontend...${NC}"
            cd frontend && npm run dev
            cd ..
            ;;
        8) 
            echo -e "${RED}Stopping All Databases...${NC}"
            docker compose stop postgres_main skill_postgres skill_chromadb career_chromadb chatbot_chromadb
            ;;
        s)
            echo -e "${BLUE}🌱 Seeding Knowledge Base to ALL Vector Stores...${NC}"
            export PYTHONPATH=$PYTHONPATH:$(pwd)
            # Skill Service Store (8003)
            $PYTHON_EXEC scripts/ingest_onet_skills.py --port 8003
            $PYTHON_EXEC scripts/setup_knowledge_base.py --port 8003
            # Career Service Store (8004)
            $PYTHON_EXEC scripts/setup_knowledge_base.py --port 8004
            # Chatbot Service Store (8005)
            $PYTHON_EXEC scripts/ingest_onet_skills.py --port 8005
            $PYTHON_EXEC scripts/setup_knowledge_base.py --port 8005
            echo -e "${GREEN}✅ Seeding Complete!${NC}"
            ;;

        i)
            echo -e "${BLUE}Setting up Virtual Environment...${NC}"
            $SYSTEM_PYTHON -m venv .venv
            if [ $? -ne 0 ]; then
                echo -e "${RED}Failed to create venv. Make sure python3-venv is installed.${NC}"
                echo -e "Try: sudo apt install python3-venv"
            else
                export PYTHON_EXEC="$VENV_DIR/bin/python"
                export PIP_EXEC="$VENV_DIR/bin/pip"
                echo -e "${GREEN}Venv created successfully.${NC}"
                echo -e "${BLUE}Installing Dependencies into Venv...${NC}"
                $PIP_EXEC install --upgrade pip
                $PIP_EXEC install python-dotenv pydantic-settings uvicorn fastapi
                for req in services/*/requirements.txt; do
                    echo -e "${CYAN}Installing from $req...${NC}"
                    $PIP_EXEC install -r "$req"
                done
                echo -e "${GREEN}Setup complete! You are now using .venv.${NC}"
            fi
            ;;
        q) 
            echo -e "${PURPLE}Happy coding! Goodbye.${NC}"
            exit 0 
            ;;
        *) 
            echo -e "${RED}Invalid option!${NC}" 
            ;;
    esac

    echo -ne "\n${YELLOW}Service stopped. Press ENTER to return to menu...${NC}"
    read
done
