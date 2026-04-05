import json
import logging
from typing import Dict, Any, List, Optional
from shared.models.cv_models import CVData, PersonalInfo, Education, Experience, Project, Certification

logger = logging.getLogger(__name__)

class CollectorStep:
    PERSONAL = 1
    EDUCATION = 2
    EXPERIENCE = 3
    SKILLS = 4
    PROJECTS = 5
    CERTIFICATIONS = 6
    COMPLETE = 7

class CollectorManager:
    """Manages the 6-step CV information collection process."""

    SKILL_SUGGESTIONS = {
        "frontend": ["React", "Vue.js", "TypeScript", "CSS/SCSS", "Jest", "Webpack"],
        "backend": ["Node.js", "Python", "Java", "SQL", "REST API", "Docker"],
        "fullstack": ["React", "Node.js", "PostgreSQL", "Docker", "Git"],
        "devops": ["Docker", "Kubernetes", "CI/CD", "AWS", "Terraform", "Linux"],
        "data": ["Python", "SQL", "Pandas", "Spark", "AWS", "PostgreSQL"],
        "qa": ["Selenium", "Jest", "CI/CD", "Linux", "API Testing", "Git"],
        "architect": ["Microservices", "Design Patterns", "AWS", "Docker", "Kubernetes"],
        "default": ["Git", "SQL", "REST API", "Linux", "Docker"],
    }

    STEP_PROMPTS = {
        CollectorStep.PERSONAL: "Hãy bắt đầu với thông tin cá nhân của bạn. Vui lòng cung cấp Họ tên, Email, Số điện thoại, Địa chỉ và Vị trí ứng tuyển mong muốn (ví dụ: Frontend Developer).",
        CollectorStep.EDUCATION: "Tuyệt vời! Bây giờ hãy cho mình biết về quá trình học tập của bạn. Bạn đã học trường nào, chuyên ngành gì và tốt nghiệp năm bao nhiêu?",
        CollectorStep.EXPERIENCE: "Tiếp theo là kinh nghiệm làm việc. Bạn đã từng làm ở những công ty nào, vị trí gì và những công việc chính bạn đảm nhận là gì?",
        CollectorStep.SKILLS: "Bạn có những kỹ năng chuyên môn nào? (Ví dụ: React, Node.js, AWS, SQL...). Dựa trên kinh nghiệm của bạn, mình gợi ý thêm một số kỹ năng: {suggestions}",
        CollectorStep.PROJECTS: "Bạn có dự án cá nhân hoặc dự án thực tế nào tiêu biểu không? Hãy mô tả ngắn gọn về tên dự án, công nghệ sử dụng và vai trò của bạn.",
        CollectorStep.CERTIFICATIONS: "Cuối cùng, bạn có chứng chỉ hoặc bằng cấp nào khác không? (Ví dụ: IELTS, AWS Certified, v.v.)",
    }

    def __init__(self):
        pass

    def get_skill_suggestions(self, cv_data: CVData) -> str:
        """Get relevant skill suggestions based on the job title and experience."""
        title = (cv_data.personal_info.title or "").lower()

        # Check against skill suggestion keywords
        for keyword, skills in self.SKILL_SUGGESTIONS.items():
            if keyword != "default" and keyword in title:
                return ", ".join(skills[:5])

        # Default suggestions
        return ", ".join(self.SKILL_SUGGESTIONS["default"])

    def get_system_prompt(self, step: int, cv_data: CVData) -> str:
        """Generate a system prompt for the Smart CV Consultant."""
        step_name = self._get_step_name(step)
        collected = self._summarize_collected(cv_data)

        # Smart Consultant Persona
        prompt = f"""Bạn là một Chuyên gia tư vấn tuyển dụng cao cấp (Senior Recruitment Consultant). 
Nhiệm vụ của bạn là thu thập thông tin và tư vấn cho người dùng để tạo ra một bản CV chuyên nghiệp, thu hút nhà tuyển dụng.

TRẠNG THÁI HIỆN TẠI:
- Bước mục tiêu: {step}/6 ({step_name})
- {collected}

QUY TẮC CỐT LÕI:
1. TRÍCH XUẤT TOÀN CẦU: Luôn trích xuất TẤT CẢ thông tin người dùng cung cấp vào thẻ extracted_data.
2. KHÔNG HỎI TRÙNG LẶP: Tuyệt đối KHÔNG hỏi lại những thông tin đã có trong phần "DỮ LIỆU ĐÃ CÓ" của summary. Nếu Summary ghi "Email: ...", đừng bao giờ hỏi xin email nữa.
3. PHONG THÁI CHUYÊN GIA: Nói chuyện chuyên nghiệp, lịch sự. Nhận xét về các công nghệ (như .NET 9, IoT, AI) để thể hiện sự am hiểu.
4. ƯU TIÊN THÔNG TIN THIẾU: Hãy nhìn vào "DỮ LIỆU ĐÃ CÓ" để xác định mục nào đang ghi "Thiếu". Hãy ưu tiên hỏi các mục đó.
5. GIAI ĐOẠN HOÀN THIỆN (Step 7): Khi ở bước 7 (Hoàn tất), hãy chuyển sang vai trò "Người soát lỗi". Đừng hỏi thông tin cơ bản nữa.
6. QUY TẮC TRÍCH XUẤT NGHIÊM NGẶT: CHỈ trích xuất dữ liệu khi người dùng cung cấp. CẤM tuyệt đối việc điền các câu hỏi, yêu cầu hoặc mô tả như "Vui lòng cung cấp..." vào các trường dữ liệu.
7. PHẢN HỒI VĂN BẢN TRƯỚC: Luôn luôn bắt đầu bằng lời thoại dành cho người dùng, sau đó mới đến thẻ <extracted_data> ở cuối cùng. KHÔNG bao giờ để trống phần văn bản nói chuyện.

ĐỊNH DẠNG TRÍCH XUẤT (extracted_data):
<extracted_data>
{{
  "step": [Số bước tiếp theo bạn gợi ý, 7 nếu đã đủ hết], 
  "data": {{ ... }}
}}
</extracted_data>

LƯU Ý: AI Engineer là mục tiêu của người dùng, hãy ưu tiên các dự án/kỹ năng liên quan nếu người dùng nhắc tới. 

Hãy bắt đầu tư vấn dựa trên tin nhắn mới nhất.
"""
        return prompt

    def _summarize_collected(self, cv_data: CVData) -> str:
        """Summarize exactly what fields are collected and what are missing."""
        parts = []
        info = cv_data.personal_info
        
        # Personal Info
        p_status = []
        if info.full_name: p_status.append(f"Tên: {info.full_name}")
        else: p_status.append("Thiếu Tên")
        
        if info.email: p_status.append(f"Email: {info.email}")
        else: p_status.append("Thiếu Email")
        
        if info.phone: p_status.append(f"SĐT: {info.phone}")
        else: p_status.append("Thiếu SĐT")
        
        if info.title: p_status.append(f"Vị trí: {info.title}")
        else: p_status.append("Thiếu Vị trí ứng tuyển")
        
        parts.append("CÁ NHÂN: " + ", ".join(p_status))
        
        # Lists
        parts.append(f"HỌC VẤN: {len(cv_data.education)} mục")
        parts.append(f"KINH NGHIỆM: {len(cv_data.experience)} mục")
        
        skills_count = len(cv_data.skills)
        parts.append(f"KỸ NĂNG: {skills_count} kỹ năng ({', '.join(cv_data.skills[:3])}...)")
        
        parts.append(f"DỰ ÁN: {len(cv_data.projects)} mục")
        parts.append(f"CHỨNG CHỈ: {len(cv_data.certifications)} mục")

        return "DỮ LIỆU ĐÃ CÓ: " + " | ".join(parts)

    def _get_step_name(self, step: int) -> str:
        names = {
            1: "Thông tin cá nhân",
            2: "Học vấn",
            3: "Kinh nghiệm làm việc",
            4: "Kỹ năng",
            5: "Dự án",
            6: "Chứng chỉ",
            7: "Hoàn tất"
        }
        return names.get(step, "Unknown")

    def extract_json_from_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract the hidden <extracted_data> JSON block from LLM response."""
        try:
            json_str = ""
            start_tag = "<extracted_data>"
            end_tag = "</extracted_data>"

            # Primary method: look for exact tags
            if start_tag in response and end_tag in response:
                start_idx = response.find(start_tag) + len(start_tag)
                end_idx = response.find(end_tag)
                json_str = response[start_idx:end_idx].strip()
            else:
                # Fallback: look for JSON block at the end of response
                import re
                # Match {..data..} pattern near the end
                matches = list(re.finditer(r'\{"step":\s*\d+.*?\}', response, re.DOTALL))
                if matches:
                    json_str = matches[-1].group(0)  # Get last match

            if json_str:
                # Remove any leading/trailing non-json garbage that might have been included
                json_str = json_str.strip()
                if not json_str.startswith("{"):
                    start = json_str.find("{")
                    if start != -1: json_str = json_str[start:]
                if not json_str.endswith("}"):
                    end = json_str.rfind("}")
                    if end != -1: json_str = json_str[:end+1]

                data = json.loads(json_str)
                # Validate structure
                if isinstance(data, dict) and ("step" in data and "data" in data):
                    return data
                # Also accept if data dict is present directly
                elif isinstance(data, dict) and any(k in data for k in ["personal_info", "education", "experience", "skills"]):
                    return {"step": 1, "data": data}
        except Exception as e:
            logger.debug(f"JSON extraction failed: {e}")
        return None

    def _is_valid_value(self, value: Any) -> bool:
        """Check if a value is real data and not an AI hallucinated instruction."""
        if not isinstance(value, str):
            return True
        
        # Blacklist common phrases the AI might hallucinate into fields
        blacklist = ["vui lòng cung cấp", "hãy cung cấp", "thiếu thông tin", "chưa có", "không được cung cấp"]
        val_lower = value.lower()
        if any(phrase in val_lower for phrase in blacklist):
            return False
        
        # If it's a long sentence asking a question (ending in ?), it's probably not a name/email
        if len(value) > 20 and value.strip().endswith("?"):
            return False
            
        return True

    def update_cv_data(self, current_data: CVData, extracted: Dict[str, Any]) -> CVData:
        """Merge newly extracted data globally into the main CVData object."""
        data = extracted.get("data", {})
        if not data:
            return current_data

        # 1. Helper to update only with valid values
        def set_if_valid(target, field, new_val):
            if new_val and self._is_valid_value(new_val):
                setattr(target, field, new_val)

        # --- PERSONAL INFO ---
        personal = data.get("personal_info")
        if not personal and extracted.get("step") == CollectorStep.PERSONAL:
            personal = data # Legacy flat format
        
        if personal:
            set_if_valid(current_data.personal_info, "full_name", personal.get("full_name"))
            set_if_valid(current_data.personal_info, "email", personal.get("email"))
            set_if_valid(current_data.personal_info, "phone", personal.get("phone"))
            set_if_valid(current_data.personal_info, "location", personal.get("location"))
            set_if_valid(current_data.personal_info, "title", personal.get("title"))
        
        # --- EDUCATION ---
        edu_list = data.get("education")
        if not edu_list and extracted.get("step") == CollectorStep.EDUCATION:
            edu_list = data if isinstance(data, list) else [data]
            
        if edu_list:
            try:
                for item in (edu_list if isinstance(edu_list, list) else [edu_list]):
                    if isinstance(item, dict) and item.get("school"):
                        # Basic deduplication: don't add the same school twice if fields match
                        exists = any(e.school == item["school"] for e in current_data.education)
                        if not exists:
                            current_data.education.append(Education(**item))
            except Exception as e:
                logger.error(f"Error updating Education: {e}")

        # --- EXPERIENCE ---
        exp_list = data.get("experience")
        if not exp_list and extracted.get("step") == CollectorStep.EXPERIENCE:
            exp_list = data if isinstance(data, list) else [data]
            
        if exp_list:
            try:
                for item in (exp_list if isinstance(exp_list, list) else [exp_list]):
                    if isinstance(item, dict) and item.get("company"):
                        if "description" in item and isinstance(item["description"], str):
                            item["description"] = [item["description"]]
                        
                        # Deduplication
                        exists = any(e.company == item["company"] and e.position == item.get("position") for e in current_data.experience)
                        if not exists:
                            current_data.experience.append(Experience(**item))
            except Exception as e:
                logger.error(f"Error updating Experience: {e}")

        # --- SKILLS ---
        skills = data.get("skills")
        if not skills and extracted.get("step") == CollectorStep.SKILLS:
            skills = data.get("skills", data) if isinstance(data, list) else data.get("skills")

        if skills and isinstance(skills, list):
            for s in skills:
                # Handle both string and dict formats from LLM
                skill_name = s.get("name") if isinstance(s, dict) else str(s)
                if skill_name and skill_name not in current_data.skills:
                    current_data.skills.append(skill_name)
        
        # --- PROJECTS ---
        proj_list = data.get("projects")
        if not proj_list and extracted.get("step") == CollectorStep.PROJECTS:
            proj_list = data if isinstance(data, list) else [data]
            
        if proj_list:
            try:
                for item in (proj_list if isinstance(proj_list, list) else [proj_list]):
                    if isinstance(item, dict) and item.get("name"):
                        if "technologies" in item and isinstance(item["technologies"], str):
                            item["technologies"] = [t.strip() for t in item["technologies"].split(",")]
                        
                        exists = any(p.name == item["name"] for p in current_data.projects)
                        if not exists:
                            current_data.projects.append(Project(**item))
            except Exception as e:
                logger.error(f"Error updating Projects: {e}")

        # --- CERTIFICATIONS ---
        cert_list = data.get("certifications")
        if not cert_list and extracted.get("step") == CollectorStep.CERTIFICATIONS:
            cert_list = data if isinstance(data, list) else [data]
            
        if cert_list:
            try:
                for item in (cert_list if isinstance(cert_list, list) else [cert_list]):
                    if isinstance(item, dict) and item.get("name"):
                        exists = any(c.name == item["name"] for c in current_data.certifications)
                        if not exists:
                            current_data.certifications.append(Certification(**item))
            except Exception as e:
                logger.error(f"Error updating Certifications: {e}")

        return current_data

    def get_next_incomplete_step(self, current_step: int, cv_data: CVData) -> int:
        """Analyze CVData and return the first step that needs more information.
        Allows jumping forward if a large block of text fulfilled later requirements."""
        
        # 1. Personal Info (Mandatory: Name, Title)
        if not (cv_data.personal_info.full_name and cv_data.personal_info.title):
            return CollectorStep.PERSONAL
            
        # 2. Education (Mandatory: 1 entry)
        if not cv_data.education:
            return CollectorStep.EDUCATION
            
        # 3. Experience (Mandatory: 1 entry)
        if not cv_data.experience:
            return CollectorStep.EXPERIENCE
            
        # 4. Skills (Should have some skills)
        if len(cv_data.skills) < 3:
            return CollectorStep.SKILLS
            
        # 5. Projects (Optional, but consult if empty)
        if not cv_data.projects and current_step <= CollectorStep.PROJECTS:
            return CollectorStep.PROJECTS
            
        # 6. Certifications (Optional)
        if not cv_data.certifications and current_step <= CollectorStep.CERTIFICATIONS:
            return CollectorStep.CERTIFICATIONS
            
        # If we reached here, and we're at least at step 6, we might be done
        # But if current_step was already 7, stay at 7
        if current_step >= CollectorStep.COMPLETE:
            return CollectorStep.COMPLETE
            
        # Otherwise, stay at whatever step the LLM thinks or move to complete
        return current_step
