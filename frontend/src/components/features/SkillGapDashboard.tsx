import React, { useMemo, useState } from 'react';
import { 
  CheckCircle2, XCircle, PlusCircle, 
  TrendingUp, BookOpen, 
  Award, Briefcase, GraduationCap,
  ArrowRight, Sparkles, AlertCircle,
  Target, Zap, Compass, Map,
  BookMarked,
  LayoutGrid
} from 'lucide-react';
import { SkillMatchResponse, courseApi, Course } from '../../services/api';
import SkillRadarChart from './SkillRadarChart';
import CourseCard from './learning/CourseCard';
import LearningRoadmap from './learning/LearningRoadmap';

interface Props {
  data: SkillMatchResponse;
  onRefresh?: () => void;
}

/**
 * High-end Circular Gauge for the match score.
 */
function MatchGauge({ score }: { score: number }) {
  const radius = 90;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center group">
      <svg className="w-48 h-48 -rotate-90">
        {/* Background track */}
        <circle
          cx="96"
          cy="96"
          r={radius}
          stroke="rgba(255, 255, 255, 0.03)"
          strokeWidth="12"
          fill="transparent"
        />
        {/* Progress gauge */}
        <circle
          cx="96"
          cy="96"
          r={radius}
          stroke="url(#gauge-gradient)"
          strokeWidth="12"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          fill="transparent"
          className="transition-all duration-1000 ease-out"
        />
        <defs>
          <linearGradient id="gauge-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#10b981" />
            <stop offset="100%" stopColor="#3b82f6" />
          </linearGradient>
        </defs>
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-5xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-br from-white to-white/60">
          {score}
        </span>
        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400/80 mt-1">Match Index</span>
      </div>
      
      {/* Outer decorative ring */}
      <div className="absolute -inset-4 border border-white/5 rounded-full blur-[1px] group-hover:scale-105 transition-transform duration-700" />
    </div>
  );
}

export default function SkillGapDashboard({ data, onRefresh }: Props) {
  const [localCourses, setLocalCourses] = useState<Course[]>(data.course_recommendations || []);

  const handleBookmark = async (id: string) => {
    try {
      const resp = await courseApi.bookmark(id);
      if (resp.data.status === 'success') {
        setLocalCourses(prev => prev.map(c => 
          c.id === id ? { ...c, is_bookmarked: resp.data.is_bookmarked } : c
        ));
      }
    } catch (err) {
      console.error("Failed to toggle bookmark", err);
    }
  };

  const handleStartEducation = async (course: Course) => {
    window.open(course.url, '_blank');
    // Track initiation
    try {
      await courseApi.updateProgress(course.id, 0.1);
    } catch (err) {
      console.error("Failed to track progress", err);
    }
  };

  // Transform data for Radar Chart
  const radarData = useMemo(() => {
    const categories = [
      'Frontend', 'Backend', 'Data', 'DevOps', 'QA', 'Mobile'
    ];
    return categories.map(cat => ({
      subject: cat,
      A: Math.floor(Math.random() * 40) + 50, // Simulated CV
      B: 85, // JD Target
      fullMark: 100,
    }));
  }, []);

  return (
    <div className="space-y-16 animate-in fade-in slide-in-from-bottom-8 duration-1000 pb-20">
      
      {/* Executive Summary Header */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
        {/* Match Index Gauge Container */}
        <div className="lg:col-span-4 bg-overlay/40 backdrop-blur-2xl border border-white/10 rounded-[3rem] p-10 flex flex-col items-center justify-center relative overflow-hidden group min-h-[450px]">
          <div className="absolute top-0 right-0 w-64 h-64 bg-accent-primary/10 blur-[100px] -translate-y-1/2 translate-x-1/2" />
          <MatchGauge score={data.overall_score} />
          
          <div className="mt-8 text-center space-y-2">
             <p className="text-text-secondary text-sm font-medium italic opacity-80 max-w-[200px]">
                "{data.skill_gap_explanation?.score_interpretation || "Highly compatible for this role."}"
             </p>
             <div className="flex gap-2 justify-center pt-4">
                <div className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-black text-emerald-400 uppercase tracking-widest">Low Risk</div>
                <div className="px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-[10px] font-black text-blue-400 uppercase tracking-widest">Tier 1 Fit</div>
             </div>
          </div>
        </div>

        {/* Detailed Attribute Breakdown */}
        <div className="lg:col-span-5 bg-surface/30 backdrop-blur-xl border border-white/5 rounded-[3rem] p-10 space-y-10 flex flex-col justify-center">
           <div className="space-y-8">
              <div className="group">
                 <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                       <Award className="w-5 h-5 text-emerald-400" />
                       <span className="font-bold text-sm tracking-tight text-white/90">Semantic Skill Alignment</span>
                    </div>
                    <span className="text-xs font-black text-text-muted">{data.breakdown.skills}%</span>
                 </div>
                 <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden shadow-inner p-[1px]">
                    <div className="h-full bg-gradient-to-r from-emerald-600 to-emerald-400 group-hover:opacity-80 transition-all rounded-full" style={{ width: `${data.breakdown.skills}%` }} />
                 </div>
              </div>

              <div className="group">
                 <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                       <Briefcase className="w-5 h-5 text-accent-primary" />
                       <span className="font-bold text-sm tracking-tight text-white/90">Seniority & Tenure Fit</span>
                    </div>
                    <span className="text-xs font-black text-text-muted">{data.breakdown.experience}%</span>
                 </div>
                 <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden shadow-inner p-[1px]">
                    <div className="h-full bg-gradient-to-r from-blue-600 to-blue-400 group-hover:opacity-80 transition-all rounded-full" style={{ width: `${data.breakdown.experience}%` }} />
                 </div>
              </div>

              <div className="group">
                 <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                       <GraduationCap className="w-5 h-5 text-purple-400" />
                       <span className="font-bold text-sm tracking-tight text-white/90">Educational Pedigree</span>
                    </div>
                    <span className="text-xs font-black text-text-muted">{data.breakdown.education}%</span>
                 </div>
                 <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden shadow-inner p-[1px]">
                    <div className="h-full bg-gradient-to-r from-purple-600 to-purple-400 group-hover:opacity-80 transition-all rounded-full" style={{ width: `${data.breakdown.education}%` }} />
                 </div>
              </div>
           </div>

           <div className="pt-6 border-t border-white/5 text-xs text-text-muted leading-relaxed font-medium">
              Your profile shows exceptional strength in <span className="text-text-primary">Engineering Leadership</span> and <span className="text-text-primary">Cloud Architecture</span>. 
              Address the identified <span className="text-rose-400/80">Skill Gaps</span> below for the optimal competitive edge.
           </div>
        </div>

        {/* Dynamic Radar Visualization */}
        <div className="lg:col-span-3 bg-surface/30 backdrop-blur-md border border-white/5 rounded-[3rem] p-8 flex items-center justify-center">
           <SkillRadarChart data={radarData} />
        </div>
      </div>

      {/* Skills Matrix: Matched | Missing | Extra */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
         {/* Matched Skills - Emerald Glass */}
         <div className="bg-emerald-500/[0.03] backdrop-blur-sm border border-emerald-500/10 rounded-[2.5rem] p-8 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-6 opacity-10">
               <CheckCircle2 className="w-16 h-16 text-emerald-500" />
            </div>
            <h3 className="text-lg font-black text-emerald-500/80 mb-8 uppercase tracking-widest flex items-center gap-2">
               Verified Strengths
            </h3>
            <div className="flex flex-wrap gap-2">
               {data.skills.matched.map((s, i) => (
                  <div key={i} className="px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/10 text-xs font-bold text-emerald-400/90 group hover:border-emerald-500/40 transition-all cursor-default">
                     {s.skill}
                     <span className="ml-2 opacity-30 group-hover:opacity-100 uppercase text-[8px] tracking-tighter">{s.match_type}</span>
                  </div>
               ))}
            </div>
         </div>

         {/* Missing Skills - Rose Glass */}
         <div className="bg-rose-500/[0.03] backdrop-blur-sm border border-rose-500/10 rounded-[2.5rem] p-8 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-6 opacity-10 text-rose-500">
               <Target className="w-16 h-16 fill-rose-500" />
            </div>
            <h3 className="text-lg font-black text-rose-500/80 mb-8 uppercase tracking-widest flex items-center gap-2">
               Critical Gaps
            </h3>
            <div className="flex flex-wrap gap-2">
               {data.skills.missing.map((s, i) => (
                  <div key={i} className="px-4 py-2 rounded-xl bg-rose-500/10 border border-rose-500/10 text-xs font-bold text-rose-400 group hover:border-rose-500/40 transition-all cursor-help relative">
                     {s.skill}
                     {s.priority === 'high' && <div className="absolute -top-1 -right-1 w-2 h-2 rounded-full bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.8)]" />}
                  </div>
               ))}
            </div>
         </div>

         {/* Extra Skills - Premium Accent Glass */}
         <div className="bg-accent-primary/[0.03] backdrop-blur-sm border border-accent-primary/10 rounded-[2.5rem] p-8 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-6 opacity-10 text-accent-primary">
               <Zap className="w-16 h-16 fill-accent-primary" />
            </div>
            <h3 className="text-lg font-black text-accent-primary/80 mb-8 uppercase tracking-widest flex items-center gap-2 text-blue-400">
               Unclaimed Value
            </h3>
            <div className="flex flex-wrap gap-2">
               {data.skills.extra.map((s, i) => (
                  <div key={i} className="px-4 py-2 rounded-xl bg-accent-primary/10 border border-accent-primary/10 text-xs font-bold text-blue-400/90 group hover:border-accent-primary/40 transition-all cursor-default">
                     {s.skill}
                     <Sparkles className="inline-block w-3 h-3 ml-2 text-accent-primary/50" />
                  </div>
               ))}
            </div>
         </div>
      </div>

      {/* US-12 Section: Strategic Education & Recommendations */}
      <div className="space-y-12">
        <div className="flex items-end justify-between border-b border-white/5 pb-6">
           <div className="space-y-2">
              <h2 className="text-4xl font-black tracking-tight text-white flex items-center gap-4">
                 <BookMarked className="w-10 h-10 text-accent-primary" />
                 Skill Gap Remediation
              </h2>
              <p className="text-text-muted font-medium">Curated education paths to eliminate your competitive gaps</p>
           </div>
           <div className="flex items-center gap-3">
              <div className="px-5 py-2 rounded-2xl bg-white/5 border border-white/10 text-xs font-bold text-text-muted flex items-center gap-2 h-fit">
                 <LayoutGrid className="w-4 h-4" />
                 Grid View
              </div>
           </div>
        </div>

        {/* Course Recommendations Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
           {(localCourses.length > 0 ? localCourses : data.course_recommendations || []).map((course, idx) => (
              <CourseCard 
                key={course.id || idx} 
                course={course} 
                onBookmark={handleBookmark}
                onStartLearning={() => handleStartEducation(course)}
              />
           ))}
           {(!localCourses || localCourses.length === 0) && (
              <div className="col-span-full py-20 bg-white/[0.02] border border-dashed border-white/10 rounded-[3rem] flex flex-col items-center justify-center text-center space-y-4">
                 <AlertCircle className="w-12 h-12 text-text-muted" />
                 <div>
                    <h4 className="text-xl font-bold text-white">No specific recommendations found</h4>
                    <p className="text-sm text-text-muted">Try refining your skill search or uploading a more detailed JD.</p>
                 </div>
              </div>
           )}
        </div>

        {/* Smart Roadmap Section */}
        {data.learning_roadmap && (
          <div className="pt-8">
            <LearningRoadmap 
              roadmap={data.learning_roadmap} 
              onCourseClick={(c) => window.open(c.url, '_blank')}
            />
          </div>
        )}
      </div>

      {/* Floating Action Bar / Mobile Sticky Meta */}
      <div className="fixed bottom-10 left-1/2 -translate-x-1/2 z-50 w-full max-w-2xl px-6 pointer-events-none">
         <div className="bg-overlay/80 backdrop-blur-3xl border border-white/10 rounded-[2.5rem] p-4 shadow-2xl pointer-events-auto flex items-center justify-between gap-6 overflow-hidden relative">
            <div className="absolute inset-0 bg-gradient-to-r from-accent-primary/10 to-transparent pointer-events-none" />
            
            <div className="flex items-center gap-4 pl-4">
               <div className="flex flex-col">
                  <span className="text-[10px] font-black text-accent-primary uppercase tracking-widest">Readiness Score</span>
                  <div className="flex items-baseline gap-1">
                     <span className="text-2xl font-black text-white">{data.overall_score}%</span>
                     <TrendingUp className="w-4 h-4 text-emerald-400" />
                  </div>
               </div>
            </div>

            <button className="flex-grow py-5 rounded-[1.5rem] bg-accent-primary text-white font-black text-sm flex items-center justify-center gap-3 hover:shadow-[0_20px_50px_rgba(37,99,235,0.4)] hover:scale-[1.02] transition-all group relative overflow-hidden active:scale-95">
               <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover:translate-x-full duration-1000 transition-transform" />
               Generate AI-Optimized Resume
               <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
         </div>
      </div>
    </div>
  );
}
