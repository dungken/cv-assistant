import React from 'react';
import { Mail, Phone, MapPin, Briefcase, GraduationCap, Trophy, Code2, Rocket } from 'lucide-react';
import { CVData } from '../../services/api';

interface CVPreviewProps {
    data: CVData;
}

const CVPreview: React.FC<CVPreviewProps> = ({ data }) => {
    if (!data) return <div className="p-8 text-text-muted italic">Đang tải dữ liệu CV...</div>;

    const { 
        personal_info = { full_name: '', title: '', email: '', phone: '', location: '' }, 
        education = [], 
        experience = [], 
        skills = [], 
        projects = [], 
        certifications = [] 
    } = data;

    return (
        <div className="w-full h-full bg-white text-slate-800 p-8 shadow-2xl overflow-y-auto font-sans leading-relaxed">
            {/* Header / Personal Info */}
            <header className="border-b-4 border-accent-primary pb-6 mb-8">
                <h1 className="text-4xl font-black text-slate-900 uppercase tracking-tight mb-2">
                    {personal_info.full_name || "HỌ TÊN CỦA BẠN"}
                </h1>
                <h2 className="text-xl font-bold text-accent-primary mb-4 italic">
                    {personal_info.title || "Vị trí ứng tuyển"}
                </h2>
                <div className="grid grid-cols-2 gap-y-2 text-sm text-slate-600">
                    <div className="flex items-center gap-2">
                        <Mail className="w-4 h-4 text-accent-primary" />
                        {personal_info.email || "email@example.com"}
                    </div>
                    <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4 text-accent-primary" />
                        {personal_info.phone || "0123 456 789"}
                    </div>
                    <div className="flex items-center gap-2 col-span-2">
                        <MapPin className="w-4 h-4 text-accent-primary" />
                        {personal_info.location || "Địa chỉ, Thành phố"}
                    </div>
                </div>
            </header>

            {/* Experience */}
            {experience.length > 0 && (
                <section className="mb-8">
                    <div className="flex items-center gap-2 mb-4">
                        <Briefcase className="w-5 h-5 text-accent-primary" />
                        <h3 className="text-lg font-black uppercase tracking-widest text-slate-900">Kinh nghiệm làm việc</h3>
                    </div>
                    <div className="space-y-6">
                        {experience.map((exp, idx) => (
                            <div key={idx} className="relative pl-4 border-l-2 border-slate-200">
                                <div className="absolute -left-[9px] top-1.5 w-4 h-4 rounded-full bg-accent-primary border-4 border-white shadow-sm" />
                                <div className="flex justify-between items-start mb-1">
                                    <h4 className="font-bold text-slate-900">{exp.position}</h4>
                                    <span className="text-xs font-bold text-slate-500 bg-slate-100 px-2 py-1 rounded">
                                        {exp.start_date} - {exp.end_date || "Hiện tại"}
                                    </span>
                                </div>
                                <div className="text-sm font-bold text-accent-primary mb-2">{exp.company}</div>
                                <ul className="list-disc list-inside text-sm text-slate-600 space-y-1">
                                    {exp.description.map((bullet: string, bIdx: number) => (
                                        <li key={bIdx}>{bullet}</li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>
                </section>
            )}

            {/* Education */}
            {education.length > 0 && (
                <section className="mb-8">
                    <div className="flex items-center gap-2 mb-4">
                        <GraduationCap className="w-5 h-5 text-accent-primary" />
                        <h3 className="text-lg font-black uppercase tracking-widest text-slate-900">Học vấn</h3>
                    </div>
                    <div className="space-y-4">
                        {education.map((edu, idx) => (
                            <div key={idx} className="flex justify-between items-start">
                                <div>
                                    <h4 className="font-bold text-slate-900">{edu.school}</h4>
                                    <div className="text-sm text-slate-600">{edu.degree} - {edu.major}</div>
                                </div>
                                <span className="text-xs font-bold text-slate-500">{edu.start_date} - {edu.end_date}</span>
                            </div>
                        ))}
                    </div>
                </section>
            )}

            {/* Skills */}
            {skills.length > 0 && (
                <section className="mb-8">
                    <div className="flex items-center gap-2 mb-4">
                        <Code2 className="w-5 h-5 text-accent-primary" />
                        <h3 className="text-lg font-black uppercase tracking-widest text-slate-900">Kỹ năng</h3>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {skills.map((skill, idx) => (
                            <span key={idx} className="px-3 py-1 bg-slate-900 text-white text-xs font-bold rounded-full lowercase tracking-tighter">
                                {skill}
                            </span>
                        ))}
                    </div>
                </section>
            )}

            {/* Projects */}
            {projects.length > 0 && (
                <section className="mb-8">
                    <div className="flex items-center gap-2 mb-4">
                        <Rocket className="w-5 h-5 text-accent-primary" />
                        <h3 className="text-lg font-black uppercase tracking-widest text-slate-900">Dự án</h3>
                    </div>
                    <div className="space-y-4">
                        {projects.map((proj, idx) => (
                            <div key={idx}>
                                <h4 className="font-bold text-slate-900 lowercase tracking-tight"># {proj.name}</h4>
                                <ul className="list-disc list-inside text-sm text-slate-600 space-y-1 mb-2">
                                    {(proj.description || []).map((bullet: string, bIdx: number) => (
                                        <li key={bIdx}>{bullet}</li>
                                    ))}
                                </ul>
                                <div className="flex flex-wrap gap-1">
                                    {proj.technologies?.map((tech: string, tIdx: number) => (
                                        <span key={tIdx} className="text-[10px] font-bold text-accent-primary lowercase">
                                            {tech}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </section>
            )}

            {/* Certifications */}
            {certifications.length > 0 && (
                <section>
                    <div className="flex items-center gap-2 mb-4">
                        <Trophy className="w-5 h-5 text-accent-primary" />
                        <h3 className="text-lg font-black uppercase tracking-widest text-slate-900">Chứng chỉ</h3>
                    </div>
                    <ul className="space-y-2">
                        {certifications.map((cert, idx) => (
                            <li key={idx} className="flex justify-between items-center text-sm">
                                <span className="font-bold text-slate-800">{cert.name}</span>
                                <span className="text-xs text-slate-500 italic">{cert.organization} ({cert.issue_date})</span>
                            </li>
                        ))}
                    </ul>
                </section>
            )}
        </div>
    );
};

export default CVPreview;
