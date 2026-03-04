import sys
from pathlib import Path
import logging

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from shared.db.chroma_client import get_chroma_client
from services.chatbot_service.services.normalizer import SkillNormalizer

logging.basicConfig(level=logging.INFO)

def test_normalization():
    client = get_chroma_client()
    collection = client.get_collection("onet_skills")
    normalizer = SkillNormalizer(collection, threshold=0.1) # Low threshold for testing

    test_skills = [
        "Python 3",
        "Machine Learning",
        "ReactJS",
        "Financial Analysis",
        "Communication skills",
        "Deep learning",
        "AWS Cloud"
    ]

    print("\n--- Skill Normalization Test ---")
    for skill in test_skills:
        result = normalizer.normalize(skill)
        if result:
            print(f"Raw: '{skill}' -> Canonical: '{result['canonical']}' (Confidence: {result['confidence']:.2f})")
        else:
            print(f"Raw: '{skill}' -> [No match found]")

if __name__ == "__main__":
    test_normalization()
