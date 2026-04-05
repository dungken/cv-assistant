import React from 'react';
import { 
  Calendar, CheckCircle2, ChevronRight, 
  Layers, Lightbulb, Map, Star, Clock 
} from 'lucide-react';
import { Course } from './CourseCard';

export interface LearningPhase {
  phase: string;
  weeks: string;
  skills: string[];
  courses: Course[];
  estimated_hours: number;
}

export interface Roadmap {
  total_weeks: number;
  phases: LearningPhase[];
  current_progress?: number;
}

interface RoadmapProps {
  roadmap: Roadmap;
  onCourseClick?: (course: Course) => void;
}

export default function LearningRoadmap({ roadmap, onCourseClick }: RoadmapProps) {
  if (!roadmap || !roadmap.phases.length) return null;

  return (
    <div className="bg-overlay p-10 rounded-[3rem] border border-white/10 relative overflow-hidden group/container">
      {/* Background decoration */}
      <div className="absolute top-0 right-0 p-10 opacity-5 group-hover/container:opacity-20 transition-opacity">
        <Map className="w-48 h-48 text-accent-primary" />
      </div>

      <div className="flex items-center justify-between mb-12 flex-wrap gap-6 relative z-10">
        <div className="flex items-center gap-5">
          <div className="p-5 rounded-[2rem] bg-accent-primary/20 text-accent-primary border border-accent-primary/20 shadow-xl">
            <Calendar className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-3xl font-black tracking-tight text-white">Learning Ascension</h3>
            <p className="text-sm text-text-muted font-medium flex items-center gap-2">
              <Layers className="w-4 h-4 text-accent-primary" />
              Strategic skill-building roadmap for full role alignment
            </p>
          </div>
        </div>
        <div className="flex flex-col items-end">
          <div className="flex items-center gap-3">
             <div className="flex flex-col items-end">
                <span className="text-[10px] font-black text-text-muted uppercase tracking-[0.2em] mb-1">Total Estimated Path</span>
                <span className="text-3xl font-black text-transparent bg-clip-text bg-gradient-to-br from-white to-white/60">
                   ~{roadmap.total_weeks} WEEKS
                </span>
             </div>
          </div>
          
          <div className="mt-4 flex items-center gap-2">
             <div className="w-32 h-1.5 bg-white/5 rounded-full overflow-hidden">
                <div 
                  className="h-full bg-accent-primary" 
                  style={{ width: `${roadmap.current_progress || 0}%` }} 
                />
             </div>
             <span className="text-[10px] font-black text-accent-primary uppercase tracking-widest">
                {Math.floor(roadmap.current_progress || 0)}% READY
             </span>
          </div>
        </div>
      </div>

      <div className="space-y-12 relative before:absolute before:left-8 before:top-4 before:bottom-4 before:w-0.5 before:bg-gradient-to-b before:from-accent-primary/50 before:via-white/10 before:to-transparent">
        {roadmap.phases.map((phase, idx) => (
          <div key={idx} className="relative pl-24 group">
            {/* Timeline indicator circle */}
            <div className="absolute left-[26px] top-2 w-4 h-4 rounded-full bg-surface border-2 border-accent-primary z-10 shadow-[0_0_15px_rgba(37,99,235,0.4)] group-hover:scale-125 group-hover:shadow-[0_0_25px_rgba(37,99,235,0.6)] transition-all duration-500" />
            
            <div className="flex flex-col lg:flex-row gap-8">
              {/* Info Column */}
              <div className="lg:w-1/3 space-y-4">
                <div className="flex items-center gap-3">
                  <span className="text-[11px] font-black py-1.5 px-4 rounded-xl bg-accent-primary/10 text-accent-primary border border-accent-primary/10 tracking-widest uppercase">
                    Phase {idx + 1}
                  </span>
                  <span className="text-sm font-bold text-text-muted">Weeks {phase.weeks}</span>
                </div>
                
                <h4 className="text-xl font-black text-white group-hover:translate-x-2 transition-transform">
                   Focus on {phase.skills.join(" & ")}
                </h4>
                
                {/* Micro-learning tip */}
                <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 flex items-start gap-3">
                   <Lightbulb className="w-4 h-4 text-yellow-500/60 mt-1 flex-shrink-0" />
                   <p className="text-[11px] font-medium text-text-muted leading-relaxed">
                      Master the fundamentals first. We recommend dedicating ~{Math.round(phase.estimated_hours / 2)}h weekly.
                   </p>
                </div>
              </div>

              {/* Course Reference Column */}
              <div className="lg:w-2/3">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {phase.courses.map((course, cIdx) => (
                    <div 
                      key={cIdx} 
                      onClick={() => onCourseClick?.(course)}
                      className="p-5 rounded-[2rem] bg-white/[0.03] border border-white/5 hover:bg-white/[0.07] hover:border-accent-primary/30 transition-all cursor-pointer group/course"
                    >
                      <div className="flex items-start justify-between gap-3 mb-3">
                        <div className="p-2 rounded-xl bg-accent-primary/20 text-accent-primary">
                           <Clock className="w-4 h-4" />
                        </div>
                        <div className="text-[10px] font-black text-text-muted opacity-50 bg-white/5 px-2 py-0.5 rounded-lg">{course.platform}</div>
                      </div>
                      <h5 className="text-xs font-bold text-white mb-4 line-clamp-2 leading-relaxed">
                         {course.title}
                      </h5>
                      <div className="flex items-center justify-between mt-auto">
                         <div className="flex items-center gap-1.5 text-[10px] font-bold text-text-muted">
                            <Star className="w-3 h-3 text-yellow-500 fill-yellow-500/20" />
                            {course.rating}
                         </div>
                         <div className="text-accent-primary group-hover/course:translate-x-1 transition-transform">
                            <ChevronRight className="w-4 h-4" />
                         </div>
                      </div>
                    </div>
                  ))}

                  {/* Empty state/placeholder if no course matched */}
                  {phase.courses.length === 0 && (
                    <div className="col-span-full py-6 px-10 rounded-[2rem] bg-rose-500/5 border border-rose-500/10 flex items-center gap-4 italic text-xs text-rose-400">
                       <CheckCircle2 className="w-5 h-5 opacity-50" />
                       No specific course matched yet. Browse our library for {phase.skills[0]} resources.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="mt-12 flex items-center justify-between p-6 rounded-[2rem] bg-accent-primary/10 border border-accent-primary/10">
         <div className="flex items-center gap-4">
            <CheckCircle2 className="w-6 h-6 text-accent-primary" />
            <span className="text-sm font-bold">You are {roadmap.total_weeks} weeks away from the target role.</span>
         </div>
         <button className="px-8 py-3 rounded-xl bg-accent-primary text-white font-black text-[11px] uppercase tracking-widest hover:shadow-[0_10px_30px_rgba(37,99,235,0.3)] transition-all">
            Download Roadmap as PDF
         </button>
      </div>
    </div>
  );
}
