#!/bin/bash
# manage.sh - Interactive Service Manager for Resume Assistant (Docker Mode)

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' 
BOLD='\033[1m'

# Ensure BuildKit is used
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1

show_banner() {
    clear
    echo -e "${BLUE}${BOLD}================================================${NC}"
    echo -e "${BLUE}${BOLD}         Resume Assistant - DOCKER MANAGER          ${NC}"
    echo -e "${BLUE}${BOLD}================================================${NC}"
}

show_status() {
    echo -e "\n${BOLD}📊 Current Service Status (Docker):${NC}"
    docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" | sed '1d' | while read line; do
        if echo "$line" | grep -q "Up"; then
            echo -e "  [${GREEN}RUNNING${NC}] $line"
        else
            echo -e "  [${RED}STOPPED${NC}] $line"
        fi
    done
}

show_menu() {
    echo -e "\n${BOLD}🛠️  Management Options:${NC}"
    echo -e "  ${YELLOW}1)${NC} Start Infrastructure (Postgres/Chroma)"
    echo -e "  ${YELLOW}2)${NC} Start API Gateway"
    echo -e "  ${YELLOW}3)${NC} Start Chatbot Service"
    echo -e "  ${YELLOW}4)${NC} Start Skill Service"
    echo -e "  ${YELLOW}5)${NC} Start NER Service"
    echo -e "  ${YELLOW}6)${NC} Start Career Service"
    echo -e "  ${YELLOW}7)${NC} Start Frontend"
    echo -e "  ${YELLOW}8)${NC} Start ALL (Normal run)"
    echo -e "  ${YELLOW}l)${NC} View Logs (interactive)"
    echo -e "  ${YELLOW}c)${NC} Cleanup Docker (Aggressive)"
    echo -e "  ${YELLOW}d)${NC} Down (Stop all containers)"
    echo -e "  ${YELLOW}q)${NC} Quit"
    echo -ne "\n${BOLD}Select an option: ${NC}"
}

view_logs_menu() {
    echo -e "\n${BOLD}📜 Select service to view logs:${NC}"
    echo -e "  (Press ${YELLOW}Ctrl+C${NC} to stop viewing and return to menu)"
    echo -e "  ------------------------------------------------"
    echo -e "  1) Infrastructure (DB/Chroma)"
    echo -e "  2) API Gateway"
    echo -e "  3) Chatbot"
    echo -e "  4) Skill"
    echo -e "  5) NER"
    echo -e "  6) Career"
    echo -e "  7) Frontend"
    echo -e "  b) Back to main menu"
    echo -ne "\nOption: "
    read log_opt
    
    case $log_opt in
        1) docker compose logs -f postgres chromadb ;;
        2) docker compose logs -f api_gateway ;;
        3) docker compose logs -f chatbot_service ;;
        4) docker compose logs -f skill_service ;;
        5) docker compose logs -f ner_service ;;
        6) docker compose logs -f career_service ;;
        7) docker compose logs -f frontend ;;
        *) return ;;
    esac
}

# Main Loop
while true; do
    show_banner
    show_status
    show_menu
    read opt

    case $opt in
        1) docker compose up -d postgres chromadb ;;
        2) docker compose up --build -d api_gateway ;;
        3) docker compose up --build -d chatbot_service ;;
        4) docker compose up --build -d skill_service ;;
        5) docker compose up --build -d ner_service ;;
        6) docker compose up --build -d career_service ;;
        7) docker compose up --build -d frontend ;;
        8) docker compose up --build -d ;;
        l) view_logs_menu ;;
        c) 
            echo -e "${RED}Cleaning up unused Docker resources...${NC}"
            docker system prune -f 
            docker volume prune -f
            ;;
        d) 
            echo -e "${RED}Stopping all services and cleaning orphans...${NC}"
            docker compose down --remove-orphans 
            ;;
        q) exit 0 ;;
        *) echo -e "${RED}Invalid option!${NC}" ;;
    esac

    echo -ne "\n${YELLOW}Press ENTER to continue...${NC}"
    read
done
