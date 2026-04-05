import React from 'react';
import { 
  Star, Clock, Tag, ExternalLink, 
  Bookmark, BookmarkCheck, PlayCircle,
  BarChart, Globe
} from 'lucide-react';

export interface Course {
  id: string;
  title: string;
  platform: string;
  url: string;
  rating: number;
  duration_hours: number;
  price: number;
  level: string;
  skills: string[];
  is_bookmarked?: boolean;
  progress?: number;
}

interface CourseCardProps {
  course: Course;
  onBookmark?: (id: string) => void;
  onStartLearning?: (url: string) => void;
}

export default function CourseCard({ course, onBookmark, onStartLearning }: CourseCardProps) {
  const isFree = course.price === 0;

  return (
    <div className="group relative bg-white/[0.03] backdrop-blur-md border border-white/10 rounded-[2rem] overflow-hidden hover:bg-white/[0.06] hover:border-accent-primary/30 transition-all duration-500 flex flex-col h-full">
      {/* Platform Tag */}
      <div className="absolute top-4 left-4 z-10">
        <div className="px-3 py-1 rounded-full bg-surface/80 backdrop-blur-md border border-white/10 text-[10px] font-black text-text-muted uppercase tracking-widest flex items-center gap-1.5 shadow-xl">
          <Globe className="w-3 h-3" />
          {course.platform}
        </div>
      </div>

      {/* Bookmark Button */}
      <button 
        onClick={() => onBookmark?.(course.id)}
        className="absolute top-4 right-4 z-10 p-2.5 rounded-xl bg-surface/80 backdrop-blur-md border border-white/10 text-text-muted hover:text-accent-primary hover:scale-110 transition-all group/bookmark shadow-xl"
      >
        {course.is_bookmarked ? (
          <BookmarkCheck className="w-4 h-4 text-accent-primary fill-accent-primary/20" />
        ) : (
          <Bookmark className="w-4 h-4" />
        )}
      </button>

      {/* Course Info */}
      <div className="p-6 pt-16 space-y-4 flex-grow">
        <h4 className="font-bold text-text-primary leading-tight group-hover:text-accent-primary transition-colors line-clamp-2 min-h-[3rem]">
          {course.title}
        </h4>

        <div className="flex flex-wrap gap-1.5">
          {course.skills.slice(0, 3).map((skill, idx) => (
            <span key={idx} className="px-2 py-0.5 rounded-lg bg-white/5 border border-white/5 text-[9px] font-bold text-text-muted">
              {skill}
            </span>
          ))}
          {course.skills.length > 3 && (
            <span className="px-2 py-0.5 rounded-lg bg-white/5 border border-white/5 text-[9px] font-bold text-text-muted">
              +{course.skills.length - 3}
            </span>
          )}
        </div>

        <div className="grid grid-cols-2 gap-4 pt-2">
          <div className="flex items-center gap-2 text-xs font-medium text-text-muted">
            <Star className="w-3.5 h-3.5 text-yellow-500 fill-yellow-500/20" />
            {course.rating} Rating
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-text-muted">
            <Clock className="w-3.5 h-3.5 text-blue-400" />
            {course.duration_hours}h
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-text-muted">
            <BarChart className="w-3.5 h-3.5 text-purple-400" />
            {course.level}
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-xs font-black px-2 py-0.5 rounded-md ${isFree ? 'bg-emerald-500/20 text-emerald-400' : 'bg-accent-primary/20 text-accent-primary'}`}>
              {isFree ? 'FREE' : `$${course.price}`}
            </span>
          </div>
        </div>
      </div>

      {/* Progress Bar (if exists) */}
      {course.progress !== undefined && course.progress > 0 && (
        <div className="px-6 pb-2">
          <div className="h-1 w-full bg-white/5 rounded-full overflow-hidden">
            <div 
              className="h-full bg-accent-primary transition-all duration-1000" 
              style={{ width: `${course.progress * 100}%` }} 
            />
          </div>
        </div>
      )}

      {/* Footer / Action */}
      <div className="p-6 pt-2">
        <button 
          onClick={() => onStartLearning?.(course.url)}
          className="w-full py-3 rounded-xl bg-white/5 border border-white/20 group-hover:bg-accent-primary group-hover:border-accent-primary transition-all duration-300 flex items-center justify-center gap-2 font-black text-[11px] uppercase tracking-widest text-text-muted group-hover:text-white"
        >
          <PlayCircle className="w-4 h-4" />
          {course.progress && course.progress > 0 ? 'Continue' : 'Start Education'}
        </button>
      </div>
    </div>
  );
}
