import json
import requests
import os
import time
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:1b"
OUTPUT_DIR = Path("data/raw/synthetic_it")

# IT Roles from O*NET and industry
IT_ROLES = [
    {
        "title": "Software Developer",
        "description": "Develop, create, and modify general computer applications software or specialized utility programs.",
        "skills": ["Python", "JavaScript", "React", "Docker", "PostgreSQL", "Git", "API Design", "Agile"]
    },
    {
        "title": "Data Scientist",
        "description": "Develop and implement algorithms and statistical models to analyze large datasets.",
        "skills": ["Python", "R", "Pandas", "Scikit-learn", "TensorFlow", "SQL", "Tableau", "Statistics"]
    },
    {
        "title": "System Administrator",
        "description": "Install, configure, and maintain computer systems and servers.",
        "skills": ["Linux", "Bash", "AWS", "Nginx", "Kubernetes", "Monitoring", "Security Patching", "Networking"]
    },
    {
        "title": "Frontend Developer",
        "description": "Specialize in the visual and interactive aspects of websites.",
        "skills": ["ReactJS", "TypeScript", "Tailwind CSS", "Redux", "Figma", "HTML5", "CSS3", "Vite"]
    }
]

PROMPT_TEMPLATE = """
Generate a realistic professional curriculum vitae (CV) content for an IT professional in Vietnamese. 
The CV should look like a plain text version of a real resume.

Role: {title}
Objective: {description}
Target Skills: {skills}

Include:
1. Full Name (Fake Vietnamese name)
2. Summary (Professional summary)
3. Experience (At least 2 previous jobs at Vietnamese IT companies like VNG, FPT, Viettel, or startups)
4. Education (Vietnamese universities like Bách Khoa, KHTN, UIT)
5. Technical Skills (The target skills + some extras)

Format: Plain text. Do not include markdown or explanations. Just the CV text.
"""

def generate_cv(role_data):
    prompt = PROMPT_TEMPLATE.format(
        title=role_data["title"],
        description=role_data["description"],
        skills=", ".join(role_data["skills"])
    )
    
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=60)
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    for i, role in enumerate(IT_ROLES):
        print(f"Generating synthetic CV for {role['title']}...")
        for j in range(2): # Generating 2 samples per role for initial test
            content = generate_cv(role)
            if content:
                filename = f"{role['title'].lower().replace(' ', '_')}_{j+1}.txt"
                with open(OUTPUT_DIR / filename, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"  - Saved {filename}")
            else:
                print(f"  - Failed to generate {role['title']}")
            time.sleep(1)

if __name__ == "__main__":
    main()
