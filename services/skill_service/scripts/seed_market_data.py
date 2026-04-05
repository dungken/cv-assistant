import sys
import os
from pathlib import Path
import random
import uuid
import json
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from shared.db.chroma_client import get_chroma_client
from services.skill_service.services.ontology import SkillOntology, SKILL_ONTOLOGY
from sentence_transformers import SentenceTransformer

def generate_synthetic_jds(count=500):
    ontology = SkillOntology()
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client = get_chroma_client()
    
    # Use a separate collection for market data to avoid polluting onet_jobs
    collection_name = "market_jds"
    try:
        client.delete_collection(collection_name)
    except:
        pass
    collection = client.create_collection(collection_name)
    
    industries = list(SKILL_ONTOLOGY.keys())
    locations = ["Hà Nội", "TP.HCM", "Đà Nẵng", "Remote"]
    exp_levels = ["Junior (1-3y)", "Middle (3-5y)", "Senior (5y+)", "Freshman (0-1y)"]
    
    print(f"Generating {count} synthetic JDs for market analysis...")
    
    documents = []
    metadatas = []
    ids = []
    
    for i in range(count):
        industry = random.choice(industries)
        # Get subcategories and skills for this industry
        subcats = SKILL_ONTOLOGY[industry]
        subcat = random.choice(list(subcats.keys()))
        industry_skills = subcats[subcat]
        
        # Pick 3-8 skills
        selected_skills = random.sample(industry_skills, min(len(industry_skills), random.randint(3, 8)))
        
        location = random.choice(locations)
        exp_level = random.choice(exp_levels)
        
        # Salary estimation (USD)
        base_salary = {
            "Freshman (0-1y)": (500, 800),
            "Junior (1-3y)": (800, 1500),
            "Middle (3-5y)": (1500, 2500),
            "Senior (5y+)": (2500, 4500)
        }[exp_level]
        
        # Boost for certain industries
        if industry in ["Machine Learning & AI", "Blockchain"]:
            base_salary = (base_salary[0] * 1.2, base_salary[1] * 1.3)
            
        min_sal = round(random.uniform(base_salary[0], base_salary[1] / 1.2), -1)
        max_sal = round(random.uniform(min_sal * 1.2, base_salary[1]), -1)
        
        jd_id = str(uuid.uuid4())
        
        # Mock JD content
        content = f"Looking for {exp_level} {subcat} Specialist in {industry}.\n"
        content += f"Skills required: {', '.join(selected_skills)}.\n"
        content += f"Location: {location}. We offer a competitive salary between {min_sal}-{max_sal} USD."
        
        # Create metadata
        metadata = {
            "industry": industry,
            "subcategory": subcat,
            "skills": json.dumps(selected_skills),
            "location": location,
            "exp_level": exp_level,
            "min_salary": float(min_sal),
            "max_salary": float(max_sal),
            "currency": "USD",
            "posted_at": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat()
        }
        
        documents.append(content)
        metadatas.append(metadata)
        ids.append(jd_id)
        
        if (i + 1) % 100 == 0:
            print(f"Prepared {i + 1} records...")

    # Generate embeddings and add to collection
    print("Generating embeddings (this may take a minute)...")
    embeddings = model.encode(documents).tolist()
    
    # Add to ChromaDB in batches
    batch_size = 100
    for i in range(0, count, batch_size):
        end = min(i + batch_size, count)
        collection.add(
            ids=ids[i:end],
            embeddings=embeddings[i:end],
            metadatas=metadatas[i:end],
            documents=documents[i:end]
        )
        print(f"Uploaded batch {i // batch_size + 1}")

    print(f"Successfully seeded {count} JDs to collection '{collection_name}'")

if __name__ == "__main__":
    generate_synthetic_jds(600) # Seeding 600 JDs
