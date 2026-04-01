#!/bin/bash
# dev_native.sh - Epic Native/Hybrid Service Manager for CV Assistant

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' 
BOLD='\033[1m'

# Setup Env Vars
export ConnectionStrings__DefaultConnection="Host=localhost;Port=5433;Database=cv_assistant;Username=postgres;Password=postgres"
export CHROMA_HOST="localhost"
export CHROMA_PORT="8002"
export CHAT_OLLAMA_URL="http://localhost:11434"
export CHAT_NER_URL="http://localhost:5001"

# Prepare Venv
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

show_banner() {
    clear
    echo -e "${PURPLE}${BOLD}================================================${NC}"
    echo -e "${PURPLE}${BOLD}       🚀 CV ASSISTANT - NATIVE RUNNER 🚀       ${NC}"
    echo -e "${PURPLE}${BOLD}================================================${NC}"
    echo -e "${CYAN}Mode: Hybrid (Docker DBs + Native services)${NC}"
}

show_status() {
    echo -e "\n${BOLD}📊 Infrastructure Status:${NC}"
    if docker ps | grep -q "cv_assistant-postgres"; then
        echo -e "  Postgres:  [${GREEN}ONLINE${NC}] (Port 5433)"
    else
        echo -e "  Postgres:  [${RED}OFFLINE${NC}]"
    fi
    
    if docker ps | grep -q "cv_assistant-chromadb"; then
        echo -e "  ChromaDB:  [${GREEN}ONLINE${NC}] (Port 8002)"
    else
        echo -e "  ChromaDB:  [${RED}OFFLINE${NC}]"
    fi
}

show_menu() {
    echo -e "\n${BOLD}🛠️  Management Options:${NC}"
    echo -e "  ${YELLOW}1)${NC} Start ALL Databases (Docker Infra)"
    echo -e "  ------------------------------------------------"
    echo -e "  ${YELLOW}2)${NC} Run API Gateway (.NET)"
    echo -e "  ${YELLOW}3)${NC} Run NER Service (Python)"
    echo -e "  ${YELLOW}4)${NC} Run Skill Service (Python)"
    echo -e "  ${YELLOW}5)${NC} Run Career Service (Python)"
    echo -e "  ${YELLOW}6)${NC} Run Chatbot Service (Python)"
    echo -e "  ${YELLOW}7)${NC} Run Frontend (React/Vite)"
    echo -e "  ------------------------------------------------"
    echo -e "  ${YELLOW}8)${NC} Stop Databases"
    echo -e "  ${YELLOW}v)${NC} Update Virtual Env (.venv)"
    echo -e "  ${YELLOW}q)${NC} Quit"
    echo -ne "\n${BOLD}Select an option to RUN [1-7]: ${NC}"
}

# Main Loop
while true; do
    show_banner
    show_status
    show_menu
    read opt

    case $opt in
        1) 
            echo -e "${BLUE}Starting Postgres & Chromadb...${NC}"
            docker compose up -d postgres chromadb
            ;;
        2) 
            echo -e "${GREEN}Starting API Gateway...${NC}"
            cd services/api_gateway/CvAssistant.ApiGateway.API && dotnet run
            cd ../../../
            ;;
        3) 
            echo -e "${GREEN}Starting NER Service...${NC}"
            uvicorn services.ner_service.main:app --port 5001 --reload
            ;;
        4) 
            echo -e "${GREEN}Starting Skill Service...${NC}"
            uvicorn services.skill_service.main:app --port 5002 --reload
            ;;
        5) 
            echo -e "${GREEN}Starting Career Service...${NC}"
            uvicorn services.career_service.main:app --port 5003 --reload
            ;;
        6) 
            echo -e "${GREEN}Starting Chatbot Service...${NC}"
            uvicorn services.chatbot_service.main:app --port 5004 --reload
            ;;
        7) 
            echo -e "${GREEN}Starting Frontend...${NC}"
            cd frontend && npm run dev
            cd ..
            ;;
        8) 
            echo -e "${RED}Stopping Databases...${NC}"
            docker compose stop postgres chromadb
            ;;
        v)
            echo -e "${BLUE}Updating .venv...${NC}"
            python3 -m venv .venv
            source .venv/bin/activate
            pip install -r requirements.txt
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
