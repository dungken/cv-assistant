import os
import random
from pathlib import Path

# --- Configuration ---
OUTPUT_DIR = Path("data/raw/synthetic_jds")
NUM_JDS = 80

# --- High Fidelity Content Chunks ---
COMPANIES = [
    "TechNova Vietnam", "VNG Corporation", "FPT Software", "Viettel Group", 
    "Tiki Group", "Momo Fintech", "Shopee Vietnam", "ZaloPay", "Kyber Network",
    "Axon Active", "KMS Technology", "NashTech", "TMA Solutions", "Rikkeisoft",
    "Sun*", "Tekexpert", "VNPay", "OneMount Group", "VinAI", "Got It Vietnam"
]

ROLES = {
    "Frontend Developer": {
        "skills": ["ReactJS", "Next.js", "TypeScript", "Tailwind CSS", "Redux Toolkit", "HTML5/CSS3"],
        "desc": "Xây dựng giao diện người dùng hiện đại, hiệu năng cao cho hệ thống thương mại điện tử quy mô lớn.",
        "reqs": ["Có ít nhất 2 năm kinh nghiệm làm việc với ReactJS và hệ sinh thái liên quan.", "Hiểu biết sâu sắc về Responsive Design và tối ưu hóa hiệu suất trình duyệt.", "Kỹ năng làm việc với Git, Webpack hoặc Vite."]
    },
    "Backend Developer (NodeJS)": {
        "skills": ["Node.js", "Express", "NestJS", "PostgreSQL", "Redis", "Microservices", "Docker"],
        "desc": "Phát triển các API mạnh mẽ, có khả năng mở rộng để xử lý hàng triệu giao dịch mỗi phút.",
        "reqs": ["Kinh nghiệm làm việc với NodeJS và các framework như NestJS hoặc Express.", "Thành thạo thiết kế cơ sở dữ liệu quan hệ và NoSQL.", "Am hiểu về kiến trúc Microservices và Messaging Queue (RabbitMQ hoặc Kafka)."]
    },
    "Backend Developer (Java)": {
        "skills": ["Java 17", "Spring Boot", "Hibernate", "Microservices", "MySQL", "Kafka", "Docker"],
        "desc": "Phát triển hệ thống core banking với độ tin cậy và bảo mật cao nhất.",
        "reqs": ["Tốt nghiệp Đại học chuyên ngành CNTT chuyên sâu về hướng đối tượng (OOP).", "Có kinh nghiệm với Spring Framework (Spring Boot, Spring Security, Spring Cloud).", "Kỹ năng tối ưu hóa SQL và xử lý concurrency tốt."]
    },
    "Fullstack Engineer": {
        "skills": ["ReactJS", "Node.js", "TypeScript", "MongoDB", "AWS", "CI/CD"],
        "desc": "Chịu trách nhiệm từ giao diện người dùng đến hạ tầng backend cho các dự án startup tiềm năng.",
        "reqs": ["Khả năng làm việc linh hoạt cả Frontend và Backend.", "Hiểu biết về quy trình triển khai phần mềm (CI/CD pipelines).", "Kỹ năng tư duy giải quyết vấn đề độc lập tốt."]
    },
    "AI/ML Engineer": {
        "skills": ["Python", "PyTorch", "TensorFlow", "NLP", "LLMs", "LangChain", "Vector Databases"],
        "desc": "Nghiên cứu và triển khai các mô hình ngôn ngữ lớn (LLM) để xây dựng trợ lý AI thông minh.",
        "reqs": ["Nắm vững kiến thức toán học, thuật toán Machine Learning và Deep Learning.", "Kinh nghiệm làm việc với các thư viện như PyTorch hoặc TensorFlow.", "Có kiến thức về xử lý ngôn ngữ tự nhiên (NLP) hoặc Computer Vision."]
    },
    "DevOps Engineer": {
        "skills": ["AWS", "Terraform", "Kubernetes (K8s)", "Ansible", "CI/CD", "Monitoring (Prometheus/Grafana)"],
        "desc": "Quản lý hạ tầng đám mây và tự động hóa quy trình triển khai phần mềm cho hệ thống toàn cầu.",
        "reqs": ["Am hiểu về Linux Administration và Shell scripting.", "Kinh nghiệm thực tế với Docker và Kubernetes.", "Có chứng chỉ AWS hoặc CKA là một lợi thế lớn."]
    },
    "QC/QA Automation Engineer": {
        "skills": ["Selenium", "Cypress", "Appium", "Java/Python", "API Testing (Postman)"],
        "desc": "Xây dựng khung kiểm thử tự động để đảm bảo chất lượng phần mềm không tì vết.",
        "reqs": ["Ít nhất 2 năm kinh nghiệm trong lĩnh vực kiểm thử phần mềm.", "Kỹ năng lập trình tốt để viết các script kiểm thử tự động.", "Hiểu biết về quy trình Agile/Scrum."]
    },
    "Mobile Developer (Flutter)": {
        "skills": ["Flutter", "Dart", "BLoC/GetX", "Rest API", "Firebase", "App Store/Play Store"],
        "desc": "Xây dựng ứng dụng di động đa nền tảng với trải nghiệm người dùng mượt mà.",
        "reqs": ["Có kinh nghiệm phát triển ứng dụng bằng Flutter/Dart.", "Thành thạo trong việc tích hợp API và bóc tách giao diện từ Figma.", "Am hiểu về vòng đời ứng dụng di động."]
    }
}

LOCATIONS = ["Hồ Chí Minh (Quận 1, Quận 7)", "Hà Nội (Cầu Giấy, Nam Từ Liêm)", "Đà Nẵng", "Remote", "Hybrid"]

BENEFITS = [
    "Mức lương cạnh tranh lên đến $3000 + thưởng tháng 13.",
    "Gói chăm sóc sức khỏe cao cấp (PVI/BaoViet) cho bản thân và gia đình.",
    "Môi trường làm việc năng động với nhiều hoạt động Team Building, Happy Hour hàng tuần.",
    "Cơ hội được đào tạo chuyên sâu và tham gia các hội thảo công nghệ quốc tế.",
    "Trang bị Macbook Pro/Laptop cấu hình cao cho nhân viên.",
    "Hỗ trợ phí gửi xe và ăn trưa tại công ty."
]

def generate_jd_content(role_name, role_data, index):
    company = random.choice(COMPANIES)
    location = random.choice(LOCATIONS)
    skills_str = ", ".join(random.sample(role_data["skills"], k=min(5, len(role_data["skills"]))))
    
    jd_text = f"""
{company} - {role_name}
{location}
{random.randint(10, 60)} minutes ago

Skills: {skills_str}
Job Expertise: {role_name.split()[0]}
Job Domain: IT Development

Top 3 lý do gia nhập
- {random.choice(["Dẫn đầu thị trường công nghệ", "Công nghệ mới nhất (AI, Cloud)", "Cơ hội thăng tiến nhanh"])}
- {random.choice(["Môi trường quốc tế, chuyên nghiệp", "Chế độ đãi ngộ hàng đầu", "Văn hóa startup trẻ trung"])}
- {random.choice(["Làm việc trực tiếp với chuyên gia", "Thử thách bản thân với dự án lớn", "Sản phẩm triệu người dùng"])}

Mô tả công việc
- {role_data["desc"]}
- {random.choice(role_data["reqs"])}
- Tham gia báo cáo tiến độ công việc hàng ngày qua daily stand-up.
- Phối hợp chặt chẽ với team Design và Product Manager.

Yêu cầu ứng viên
- {role_data["reqs"][0]}
- {role_data["reqs"][1]}
- {role_data["reqs"][len(role_data["reqs"])-1]}
- Khả năng đọc hiểu tài liệu tiếng Anh tốt (TOEIC 600+ hoặc tương đương).
- Tốt nghiệp Đại học chuyên ngành CNTT hoặc liên quan.

Phúc lợi
- {random.choice(BENEFITS)}
- {random.choice(BENEFITS)}
- {random.choice(BENEFITS)}
- Du lịch hàng năm và các hoạt động teambuilding.

Working hours: Monday - Friday (08:30 - 17:30)
""".strip()
    return jd_text

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Clean previous failed LLM files if any
    for f in OUTPUT_DIR.glob("llm_jd_*.txt"):
        f.unlink()
        
    print(f"Generating {NUM_JDS} high-fidelity JDs...")
    
    for i in range(1, NUM_JDS + 1):
        role_name = random.choice(list(ROLES.keys()))
        content = generate_jd_content(role_name, ROLES[role_name], i)
        
        filename = f"llm_jd_{i:02d}.txt"
        (OUTPUT_DIR / filename).write_text(content, encoding="utf-8")
        
    print(f"Successfully generated {NUM_JDS} JDs in {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
