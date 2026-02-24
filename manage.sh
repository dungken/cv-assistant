#!/bin/bash
# manage.sh - Interactive Service Manager for CV Assistant

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color
BOLD='\033[1m'

# Helpers
show_banner() {
    clear
    echo -e "${BLUE}${BOLD}================================================${NC}"
    echo -e "${BLUE}${BOLD}         CV ASSISTANT - SERVICE MANAGER         ${NC}"
    echo -e "${BLUE}${BOLD}================================================${NC}"
}

show_status() {
    echo -e "\n${BOLD}📊 Current Service Status:${NC}"
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
    echo -e "  ${YELLOW}1)${NC} Start Infrastructure (DB/Chroma)"
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
    echo -e "  ${YELLOW}s)${NC} Start Label Studio"
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
        1) echo -e "${YELLOW}Tailing logs for postgres & chromadb...${NC}"; docker compose logs -f postgres chromadb ;;
        2) echo -e "${YELLOW}Tailing logs for api_gateway...${NC}"; docker compose logs -f api_gateway ;;
        3) echo -e "${YELLOW}Tailing logs for chatbot_service...${NC}"; docker compose logs -f chatbot_service ;;
        4) echo -e "${YELLOW}Tailing logs for skill_service...${NC}"; docker compose logs -f skill_service ;;
        5) echo -e "${YELLOW}Tailing logs for ner_service...${NC}"; docker compose logs -f ner_service ;;
        6) echo -e "${YELLOW}Tailing logs for career_service...${NC}"; docker compose logs -f career_service ;;
        7) echo -e "${YELLOW}Tailing logs for frontend...${NC}"; docker compose logs -f frontend ;;
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
        1) ./scripts/run_infra.sh ;;
        2) ./scripts/run_gateway.sh ;;
        3) ./scripts/run_chatbot.sh ;;
        4) ./scripts/run_skill.sh ;;
        5) ./scripts/run_ner.sh ;;
        6) ./scripts/run_career.sh ;;
        7) ./scripts/run_frontend.sh ;;
        8) ./scripts/run_project.sh ;;
        l) view_logs_menu ;;
        c) ./scripts/cleanup_docker.sh ;;
        d) echo -e "${RED}Stopping all services and cleaning orphans...${NC}" && docker compose down --remove-orphans ;;
        s) ./scripts/run_label_studio.sh ;;
        q) echo -e "${BLUE}Goodbye!${NC}" && exit 0 ;;
        *) echo -e "${RED}Invalid option!${NC}" ;;
    esac

    echo -ne "\n${YELLOW}Press ENTER to continue...${NC}"
    read
done
