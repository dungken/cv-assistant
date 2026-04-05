import re
import logging
from typing import List, Dict, Tuple, Optional
from shared.models.cv_models import CVData
from services.skill_service.models.schemas import ATSScoreResponse, ATSIssue
from services.skill_service.services.matcher import SkillMatcher

logger = logging.getLogger(__name__)

ACTION_VERBS = {
    "spearheaded", "orchestrated", "optimized", "developed", "led", "managed",
    "implemented", "designed", "engineered", "accelerated", "achieved", "administered",
    "analyzed", "authored", "automated", "built", "collaborated", "conceived",
    "constructed", "coordinated", "created", "delivered", "deployed", "directed",
    "enhanced", "established", "executed", "expanded", "expedited", "fabricated",
    "facilitated", "formulated", "generated", "guided", "improved", "increased",
    "influenced", "initiated", "innovated", "inspected", "installed", "integrated",
    "introduced", "invented", "launched", "maintained", "masterminded", "mediated",
    "mentored", "modified", "monitored", "negotiated", "operated", "overhauled",
    "oversaw", "performed", "pioneered", "planned", "produced", "programmed",
    "projected", "promoted", "proposed", "provided", "publicized", "published",
    "purchased", "recorded", "recruited", "redesigned", "reduced", "regulated",
    "rehabilitated", "remodeled", "repaired", "replaced", "reported", "represented",
    "researched", "restored", "revised", "revitalized", "scheduled", "screened",
    "selected", "serviced", "shaped", "simplified", "solved", "sparked",
    "standardized", "stimulated", "strategized", "streamlined", "strengthened",
    "supervised", "supported", "surpassed", "synthesized", "systematized",
    "tabulated", "tailored", "taught", "tested", "trained", "transformed",
    "translated", "upgraded", "utilized", "validated", "visualized", "wrote"
}

class ATSScoringEngine:
    """Comprehensive ATS Scoring Engine based on 8 core criteria."""

    def __init__(self, matcher: SkillMatcher):
        self.matcher = matcher

    def calculate_score(self, cv_data: CVData, jd_text: Optional[str] = None) -> ATSScoreResponse:
        issues = []
        breakdown = {}

        # 1. Keywords Match (25%)
        kw_score, kw_issues = self._score_keywords(cv_data, jd_text)
        breakdown["keywords"] = kw_score
        issues.extend(kw_issues)

        # 2. Format & Structure (15%)
        fmt_score, fmt_issues = self._score_format(cv_data)
        breakdown["format"] = fmt_score
        issues.extend(fmt_issues)

        # 3. Contact Info (10%)
        contact_score, contact_issues = self._score_contact(cv_data)
        breakdown["contact"] = contact_score
        issues.extend(contact_issues)

        # 4. Experience Detail (15%)
        exp_score, exp_issues = self._score_experience(cv_data)
        breakdown["experience"] = exp_score
        issues.extend(exp_issues)

        # 5. Education (5%)
        edu_score, edu_issues = self._score_education(cv_data)
        breakdown["education"] = edu_score
        issues.extend(edu_issues)

        # 6. Skills Section (10%)
        skills_sec_score, skills_sec_issues = self._score_skills_section(cv_data)
        breakdown["skills_section"] = skills_sec_score
        issues.extend(skills_sec_issues)

        # 7. Action Verbs (10%)
        verb_score, verb_issues = self._score_action_verbs(cv_data)
        breakdown["action_verbs"] = verb_score
        issues.extend(verb_issues)

        # 8. Quantified Results (10%)
        metric_score, metric_issues = self._score_metrics(cv_data)
        breakdown["metrics"] = metric_score
        issues.extend(metric_issues)

        # Final Weighted Score
        total_score = (
            kw_score * 0.25 +
            fmt_score * 0.15 +
            contact_score * 0.10 +
            exp_score * 0.15 +
            edu_score * 0.05 +
            skills_sec_score * 0.10 +
            verb_score * 0.10 +
            metric_score * 0.10
        )

        return ATSScoreResponse(
            cv_id="cv-temp", # Placeholder
            total_score=round(total_score, 1),
            breakdown=breakdown,
            issues=issues
        )

    def _score_keywords(self, cv_data: CVData, jd_text: Optional[str]) -> Tuple[float, List[ATSIssue]]:
        if not jd_text:
            return 70.0, [ATSIssue(category="keywords", severity="medium", message="Chưa cung cấp JD để đối sánh từ khóa.", suggestion="Tải lên JD để nhận điểm chính xác hơn.")]

        # Extract skills from JD if not provided
        jd_skills = self.matcher.extract_skills_from_jd(jd_text)
        match_res = self.matcher.match_comprehensive(
            cv_skills=cv_data.skills,
            jd_required=jd_skills,
            jd_preferred=[]
        )
        
        score = match_res["breakdown"]["skills"]
        issues = []
        if score < 70:
            missing = [s.skill for s in match_res["skills"]["missing"][:3]]
            issues.append(ATSIssue(
                category="keywords",
                severity="high",
                message=f"Thiếu {len(match_res['skills']['missing'])} từ khóa quan trọng.",
                suggestion=f"Cân nhắc thêm các kỹ năng: {', '.join(missing)}."
            ))
        
        return score, issues

    def _score_format(self, cv_data: CVData) -> Tuple[float, List[ATSIssue]]:
        score = 100.0
        issues = []
        
        required_sections = ["experience", "education", "skills"]
        present_sections = []
        if cv_data.experience: present_sections.append("experience")
        if cv_data.education: present_sections.append("education")
        if cv_data.skills: present_sections.append("skills")
        
        missing = set(required_sections) - set(present_sections)
        if missing:
            score -= len(missing) * 30
            issues.append(ATSIssue(
                category="format",
                severity="high",
                message=f"Thiếu các phần quan trọng: {', '.join(missing)}",
                suggestion="Đảm bảo CV có đầy đủ các phần Kinh nghiệm, Học vấn và Kỹ năng."
            ))
            
        return max(0, score), issues

    def _score_contact(self, cv_data: CVData) -> Tuple[float, List[ATSIssue]]:
        info = cv_data.personal_info
        score = 0
        issues = []
        
        if info.full_name: score += 25
        if info.email and re.match(r"[^@]+@[^@]+\.[^@]+", info.email): score += 25
        else: issues.append(ATSIssue(category="contact", severity="high", message="Email thiếu hoặc không hợp lệ.", suggestion="Thêm địa chỉ email chuyên nghiệp."))
        
        if info.phone: score += 25
        if info.location: score += 25
        
        return float(score), issues

    def _score_experience(self, cv_data: CVData) -> Tuple[float, List[ATSIssue]]:
        if not cv_data.experience:
            return 0.0, [ATSIssue(category="experience", severity="high", message="Không có thông tin kinh nghiệm.", suggestion="Thêm lịch sử làm việc để ATS có thể đánh giá.")]
        
        score = 100.0
        issues = []
        
        for exp in cv_data.experience:
            if not exp.description or len(exp.description) < 3:
                score -= 10
                issues.append(ATSIssue(
                    category="experience",
                    severity="medium",
                    message=f"Mô tả tại {exp.company} quá ngắn.",
                    suggestion="Thêm ít nhất 3-5 bullet points cho mỗi vị trí."
                ))
                break # Only one issue per category for brevity
                
        return max(0, score), issues

    def _score_education(self, cv_data: CVData) -> Tuple[float, List[ATSIssue]]:
        if not cv_data.education:
            return 0.0, [ATSIssue(category="education", severity="medium", message="Thiếu thông tin học vấn.", suggestion="Thêm bằng cấp cao nhất của bạn.")]
        
        score = 100.0
        for edu in cv_data.education:
            if not edu.school or not edu.degree:
                score -= 50
                return 50.0, [ATSIssue(category="education", severity="low", message="Thông tin học vấn chưa đầy đủ.", suggestion="Đảm bảo có tên trường và bằng cấp.")]
                
        return 100.0, []

    def _score_skills_section(self, cv_data: CVData) -> Tuple[float, List[ATSIssue]]:
        if not cv_data.skills:
            return 0.0, [ATSIssue(category="skills_section", severity="high", message="Thiếu danh sách kỹ năng.", suggestion="Tạo một phần 'Kỹ năng' riêng biệt.")]
        
        count = len(cv_data.skills)
        if count < 5:
            return 50.0, [ATSIssue(category="skills_section", severity="medium", message="Danh sách kỹ năng quá ít.", suggestion="Thêm ít nhất 5-10 kỹ năng chuyên môn.")]
            
        return 100.0, []

    def _score_action_verbs(self, cv_data: CVData) -> Tuple[float, List[ATSIssue]]:
        all_bullets = []
        for exp in cv_data.experience: 
            desc = exp.description or []
            all_bullets.extend(desc if isinstance(desc, list) else [str(desc)])
        for proj in cv_data.projects: 
            desc = proj.description or []
            all_bullets.extend(desc if isinstance(desc, list) else [str(desc)])
        
        # Filter out empty or non-string bullets
        all_bullets = [str(b) for b in all_bullets if b]

            
        verb_count = 0
        for bullet in all_bullets:
            if not bullet.strip(): continue
            first_word = bullet.strip().split(' ')[0].lower().strip(',.')
            if first_word in ACTION_VERBS:
                verb_count += 1
                
        percentage = (verb_count / len(all_bullets)) * 100

        issues = []
        if percentage < 60:
            issues.append(ATSIssue(
                category="action_verbs",
                severity="medium",
                message=f"Chỉ {round(percentage)}% bullet points bắt đầu bằng động từ hành động.",
                suggestion="Sử dụng các động từ mạnh như 'Developed', 'Led', 'Optimized' ở đầu mỗi dòng."
            ))
            
        return float(min(100, percentage * 1.5)), issues

    def _score_metrics(self, cv_data: CVData) -> Tuple[float, List[ATSIssue]]:
        all_text_list = []
        for exp in cv_data.experience:
            desc = exp.description or []
            all_text_list.append(" ".join(desc) if isinstance(desc, list) else str(desc))
        for proj in cv_data.projects:
            desc = proj.description or []
            all_text_list.append(" ".join(desc) if isinstance(desc, list) else str(desc))
        
        all_text = " ".join(all_text_list)
        
        if not all_text.strip(): return 0.0, []

        # Look for numbers, percentages, currency
        metrics = re.findall(r"\d+%|\$\d+|\d+ users|\d+ employees|\d+ months", all_text)

        
        score = min(100, len(metrics) * 20)
        issues = []
        if score < 60:
            issues.append(ATSIssue(
                category="metrics",
                severity="medium",
                message="CV thiếu các số liệu định lượng kết quả.",
                suggestion="Thêm các con số cụ thể (ví dụ: 'Tăng 20% doanh thu', 'Quản lý 5 nhân sự')."
            ))
            
        return float(score), issues
