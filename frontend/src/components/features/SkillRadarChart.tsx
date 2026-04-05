import React from 'react';
import { 
  Radar, RadarChart, PolarGrid, 
  PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend 
} from 'recharts';

interface RadarData {
  subject: string;
  A: number; // CV
  B: number; // JD
  fullMark: number;
}

interface SkillRadarChartProps {
  data: RadarData[];
}

/**
 * Premium Radar Chart with glowing effects and refined HSL colors.
 * Subject names are truncated for cleaner presentation.
 */
export default function SkillRadarChart({ data }: SkillRadarChartProps) {
  if (!data || data.length === 0) return null;

  return (
    <div className="w-full h-[300px] md:h-[350px] relative">
      {/* Decorative background glow */}
      <div className="absolute inset-0 bg-accent-primary/5 blur-[60px] rounded-full" />
      
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
          <PolarGrid 
            stroke="rgba(255, 255, 255, 0.05)" 
            radialLines={true}
          />
          <PolarAngleAxis 
            dataKey="subject" 
            tick={{ fill: '#94a3b8', fontSize: 10, fontWeight: 700, letterSpacing: '0.05em' }}
          />
          <PolarRadiusAxis 
            angle={30} 
            domain={[0, 100]} 
            tick={false}
            axisLine={false}
          />
          
          {/* JD Requirements - Blue Glow */}
          <Radar
            name="JD Requirements"
            dataKey="B"
            stroke="#3b82f6"
            strokeWidth={2}
            fill="#3b82f6"
            fillOpacity={0.15}
            animationBegin={300}
            animationDuration={1500}
          />
          
          {/* User Skills - Emerald Glow */}
          <Radar
            name="Your Arsenal"
            dataKey="A"
            stroke="#10b981"
            strokeWidth={3}
            fill="#10b981"
            fillOpacity={0.4}
            dot={{ r: 3, fill: '#10b981', strokeWidth: 1, stroke: '#fff' }}
            animationBegin={600}
            animationDuration={1500}
          />
          
          <Legend 
            wrapperStyle={{ paddingTop: '20px' }}
            formatter={(value) => <span className="text-[10px] font-black uppercase tracking-widest text-text-muted">{value}</span>}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
