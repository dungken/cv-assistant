import { memo, useMemo, useState, useEffect, Fragment } from "react";
import { useNavigate } from "react-router-dom";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { ExternalLink, HelpCircle, Info, X, Sigma, Database, Lightbulb, Compass, CheckCircle2, AlertTriangle, XCircle } from "lucide-react";
import { BlockMath } from "react-katex";
import "katex/dist/katex.min.css";
import ReactMarkdown from "react-markdown";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../../ui/Card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "../../ui/Dialog";
import { Badge } from "../../ui/Badge";
import { GaugeSkeleton } from "../../ui/Skeleton";
import type { HealthScoreResponse } from "../../../services/api";

interface Props {
  data: HealthScoreResponse | null;
  originalData?: HealthScoreResponse | null;
  loading?: boolean;
}

const DIM_LABELS: Record<string, string> = {
  skill: "Skill",
  experience: "Experience",
  project: "Project",
  education: "Education",
  achievement: "Achievement",
  language: "Language",
  completeness: "Completeness",
  market_alignment: "Market Align",
};

function scoreColor(score: number): string {
  if (score >= 75) return "#10b981"; // green-500
  if (score >= 50) return "#6366f1"; // indigo-500
  if (score >= 30) return "#f59e0b"; // amber-500
  return "#f43f5e"; // rose-500
}

type InsightKind = "good" | "warn" | "bad" | "info";

function parseInsight(text: string): { kind: InsightKind; body: string } {
  const t = text.trimStart();
  if (t.startsWith("✓")) return { kind: "good", body: t.slice(1).trim() };
  if (t.startsWith("⚠")) return { kind: "warn", body: t.slice(1).trim() };
  if (t.startsWith("✗")) return { kind: "bad", body: t.slice(1).trim() };
  if (t.startsWith("ℹ")) return { kind: "info", body: t.slice(1).trim() };
  return { kind: "info", body: t };
}

const INSIGHT_STYLE: Record<InsightKind, { icon: typeof Info; color: string; bg: string; border: string }> = {
  good: { icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-500/[0.06]", border: "border-emerald-500/20" },
  warn: { icon: AlertTriangle, color: "text-amber-400", bg: "bg-amber-500/[0.06]", border: "border-amber-500/20" },
  bad: { icon: XCircle, color: "text-rose-400", bg: "bg-rose-500/[0.06]", border: "border-rose-500/20" },
  info: { icon: Info, color: "text-indigo-400", bg: "bg-white/[0.02]", border: "border-white/[0.06]" },
};

function scoreLabel(score: number): string {
  if (score >= 85) return "Xuất sắc";
  if (score >= 70) return "Tốt";
  if (score >= 50) return "Trung bình";
  if (score >= 30) return "Cần cải thiện";
  return "Lỗi thời";
}

function FreshnessGaugeInner({ data, originalData, loading }: Props) {
  const navigate = useNavigate();
  const [showAllMissingSkills, setShowAllMissingSkills] = useState(false);
  const [showCriteriaModal, setShowCriteriaModal] = useState(false);
  const [detailDimName, setDetailDimName] = useState<string | null>(null);
  const safeData = data && typeof data.score === "number" ? data : null;
  const detailDim = useMemo(() => {
    if (!detailDimName || !safeData?.dimensions) return null;
    return safeData.dimensions.find((d) => d.name === detailDimName) || null;
  }, [detailDimName, safeData]);

  // Check if simulation is currently active
  const isSimulated = useMemo(() => {
    if (!originalData || !safeData) return false;
    return Math.abs(safeData.score - originalData.score) > 0.05;
  }, [safeData, originalData]);

  const radarData = useMemo(() => {
    if (!safeData?.dimensions || safeData.dimensions.length === 0) return [];

    // Map original scores to dimensions
    const originalMap = new Map<string, number>();
    if (originalData?.dimensions) {
      originalData.dimensions.forEach((d) => {
        originalMap.set(d.name, d.score);
      });
    }

    return safeData.dimensions.map((d) => {
      const hasOrig = originalMap.has(d.name);
      const originalVal = hasOrig ? originalMap.get(d.name)! : d.score;
      return {
        axis: DIM_LABELS[d.name] ?? d.name,
        name: d.name,
        score: d.score,
        originalScore: originalVal,
        weight: d.weight,
        detail: d.detail?.summary || "",
      };
    });
  }, [safeData, originalData]);

  const hasMulti = radarData.length > 0;

  return (
    <Fragment>
      <Card className="bg-surface border border-white/5 shadow-lg overflow-hidden relative group">
        <CardHeader className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-white/5 pb-4">
          <div>
            <CardTitle className="text-xl font-extrabold font-outfit tracking-tight flex items-center gap-2">
              Multi-criteria CV Freshness
              <button
                type="button"
                onClick={() => setShowCriteriaModal(true)}
                className="text-text-muted hover:text-accent-primary transition-colors cursor-pointer"
                title="Xem tiêu chí chấm điểm"
              >
                <Info className="w-5 h-5" />
              </button>
              {isSimulated && (
                <Badge className="bg-violet-500/10 text-violet-400 border border-violet-500/20 px-2 py-0.5 animate-pulse text-[10px] font-bold">
                  Simulated Mode
                </Badge>
              )}
            </CardTitle>
            <CardDescription className="text-xs">
              Đánh giá CV 8 chiều được tối ưu và cân đối trọng số theo xu hướng
              thị trường IT Việt Nam
            </CardDescription>
          </div>
        </CardHeader>

        <CardContent className="pt-6">
          {loading ? (
            <GaugeSkeleton />
          ) : !safeData ? (
            <div className="h-64 flex items-center justify-center text-text-secondary/50 text-sm italic">
              Chưa có dữ liệu phân tích sức khỏe.
            </div>
          ) : (
            <div className="animate-in fade-in duration-500">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-start">
                {/* Left Column */}
                <div className="flex flex-col gap-6">
                  {/* Total score header */}
                  <div className="flex items-end justify-between p-4 rounded-2xl bg-white/[0.02] border border-white/5 relative overflow-hidden">
                    <div>
                      <div className="flex items-baseline gap-2">
                        <div
                          className="text-5xl font-black font-outfit tracking-tight tabular-nums transition-colors duration-500"
                          style={{ color: scoreColor(safeData.score) }}
                        >
                          {safeData.score.toFixed(1)}
                        </div>
                        {isSimulated && originalData && (
                          <div className="text-sm font-semibold text-text-muted line-through tabular-nums pb-1">
                            {originalData.score.toFixed(1)}
                          </div>
                        )}
                        {isSimulated && originalData && (
                          <div
                            className={`text-sm font-bold pb-1 flex items-center ${safeData.score >= originalData.score ? "text-emerald-400" : "text-rose-400"}`}
                          >
                            {safeData.score >= originalData.score ? "+" : ""}
                            {(safeData.score - originalData.score).toFixed(1)}đ
                          </div>
                        )}
                      </div>
                      <div className="text-[10px] font-bold uppercase tracking-widest text-text-muted mt-1.5">
                        Weighted Sum 8 chiều / 100
                      </div>
                    </div>

                    <div className="flex flex-col items-end gap-1.5">
                      <Badge
                        variant="outline"
                        className="font-bold text-xs px-3 py-1 border transition-all duration-500"
                        style={{
                          color: scoreColor(safeData.score),
                          borderColor: `${scoreColor(safeData.score)}30`,
                          backgroundColor: `${scoreColor(safeData.score)}08`,
                        }}
                      >
                        {scoreLabel(safeData.score)}
                      </Badge>
                      {safeData.seniority && (
                        <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                          {safeData.role} ·{" "}
                          <span className="text-text-secondary">
                            {safeData.seniority}
                          </span>
                        </span>
                      )}
                    </div>
                  </div>

                  {hasMulti ? (
                    <div className="w-full h-[300px] flex items-center justify-center bg-white/[0.01] rounded-2xl border border-white/5 relative p-4">
                      <ResponsiveContainer width="100%" height="100%">
                        <RadarChart
                          data={radarData}
                          margin={{ top: 15, right: 30, bottom: 15, left: 30 }}
                        >
                          <PolarGrid stroke="rgba(255,255,255,0.06)" />
                          <PolarAngleAxis
                            dataKey="axis"
                            tick={{
                              fill: "rgba(255,255,255,0.7)",
                              fontSize: 10,
                              fontWeight: 600,
                            }}
                          />
                          <PolarRadiusAxis
                            domain={[0, 100]}
                            angle={90}
                            tick={{ fill: "rgba(255,255,255,0.3)", fontSize: 8 }}
                            stroke="rgba(255,255,255,0.03)"
                          />

                          <Tooltip
                            cursor={false}
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                const dp = payload[0].payload;
                                const currentVal = dp.score;
                                const originalVal = dp.originalScore;
                                const hasDiff =
                                  Math.abs(currentVal - originalVal) > 0.05;
                                return (
                                  <div className="bg-surface/95 border border-white/10 backdrop-blur-xl rounded-xl p-3 shadow-2xl text-[11px] space-y-1.5 min-w-[150px] animate-in fade-in zoom-in-95 duration-100">
                                    <div className="font-extrabold text-text-primary border-b border-white/5 pb-1 flex items-center gap-1.5">
                                      <div
                                        className="w-1.5 h-1.5 rounded-full"
                                        style={{
                                          backgroundColor: scoreColor(currentVal),
                                        }}
                                      />
                                      {dp.axis}
                                    </div>
                                    <div className="flex items-center justify-between gap-4">
                                      <span className="text-text-muted">
                                        Trọng số (ω):
                                      </span>
                                      <span className="font-bold text-text-primary tabular-nums">
                                        {dp.weight.toFixed(2)}
                                      </span>
                                    </div>
                                    <div className="space-y-1 pt-0.5">
                                      {hasDiff ? (
                                        <>
                                          <div className="flex items-center justify-between gap-4">
                                            <span className="text-text-muted">
                                              Điểm gốc:
                                            </span>
                                            <span className="font-semibold text-text-secondary tabular-nums">
                                              {originalVal.toFixed(0)}
                                            </span>
                                          </div>
                                          <div className="flex items-center justify-between gap-4">
                                            <span className="text-text-muted">
                                              Giả lập:
                                            </span>
                                            <div className="flex items-center gap-1">
                                              <span className="font-black text-accent-primary tabular-nums">
                                                {currentVal.toFixed(0)}
                                              </span>
                                              <span className="text-[9px] font-black text-emerald-400">
                                                +
                                                {(
                                                  currentVal - originalVal
                                                ).toFixed(0)}
                                              </span>
                                            </div>
                                          </div>
                                        </>
                                      ) : (
                                        <div className="flex items-center justify-between gap-4">
                                          <span className="text-text-muted">
                                            Đạt điểm:
                                          </span>
                                          <span
                                            className="font-black tabular-nums"
                                            style={{
                                              color: scoreColor(currentVal),
                                            }}
                                          >
                                            {currentVal.toFixed(0)}/100
                                          </span>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />

                          {isSimulated && (
                            <Radar
                              name="Original"
                              dataKey="originalScore"
                              stroke="rgba(255,255,255,0.25)"
                              fill="rgba(255,255,255,0.05)"
                              fillOpacity={0.1}
                              strokeWidth={1.5}
                              strokeDasharray="4 4"
                              isAnimationActive={false}
                            />
                          )}
                          <Radar
                            name={isSimulated ? "Simulated" : "Score"}
                            dataKey="score"
                            stroke="rgb(var(--accent-primary))"
                            fill="rgb(var(--accent-primary))"
                            fillOpacity={0.2}
                            strokeWidth={2.5}
                            isAnimationActive={false}
                          />
                        </RadarChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div className="w-full h-[300px] flex items-center justify-center bg-white/[0.01] rounded-2xl border border-white/5 py-8 text-center text-xs text-text-secondary italic">
                      Chưa nhận được breakdown 8 chiều từ backend.
                    </div>
                  )}

                  <div className="space-y-4">
                    {/* Footer metadata */}
                    <div className="flex flex-wrap gap-2 items-center justify-between text-xs border-t border-white/5 pt-4">
                      <div className="text-text-secondary flex items-center gap-1.5">
                        Snapshot:{" "}
                        <span className="text-text-primary font-semibold">
                          {safeData.snapshot_date}
                        </span>
                      </div>
                      {safeData.cold_start && (
                        <Badge
                          variant="destructive"
                          className="!text-[9px] font-bold animate-pulse"
                        >
                          Cold start · cần ≥4 tuần dữ liệu
                        </Badge>
                      )}
                    </div>

                    {/* Top Missing/Ideal Skills to learn */}
                    {safeData.missing_ideal.length > 0 && (
                      <div className="p-4 rounded-xl bg-white/[0.01] border border-white/5 text-xs text-text-secondary space-y-3">
                        <span className="font-extrabold uppercase tracking-widest text-[10px] text-text-muted block">
                          Các kỹ năng thiếu hụt ưu tiên học:{" "}
                        </span>
                        <div className="flex flex-wrap gap-2">
                          {(showAllMissingSkills
                            ? safeData.missing_ideal
                            : safeData.missing_ideal.slice(0, 5)
                          ).map((skill) => (
                            <button
                              key={skill}
                              onClick={() =>
                                navigate(
                                  `/market-intel?skill=${encodeURIComponent(skill)}`,
                                )
                              }
                              className="px-2.5 py-1.5 rounded-lg bg-white/5 border border-white/8 hover:border-accent-primary/40 hover:bg-accent-primary/10 transition-all flex items-center gap-1.5 group cursor-pointer"
                              title="Xem chi tiết tuyển dụng & mức lương"
                            >
                              <span className="font-medium text-text-secondary group-hover:text-accent-primary transition-colors">
                                {skill}
                              </span>
                              <ExternalLink className="w-3 h-3 text-text-muted group-hover:text-accent-primary transition-colors" />
                            </button>
                          ))}
                          {safeData.missing_ideal.length > 5 && (
                            <button
                              type="button"
                              onClick={() => setShowAllMissingSkills((v) => !v)}
                              className="self-center text-accent-primary hover:text-indigo-400 text-[11px] font-bold pl-1 transition-colors cursor-pointer"
                            >
                              {showAllMissingSkills
                                ? "Thu gọn"
                                : `và ${safeData.missing_ideal.length - 5} kỹ năng khác`}
                            </button>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Right Column (Per-dimension breakdown details) */}
                <div className="space-y-2.5">
                  {hasMulti && safeData.dimensions!.map((d) => {
                    const orig = originalData?.dimensions?.find(
                      (od) => od.name === d.name,
                    );
                    const origVal = orig ? orig.score : d.score;
                    const diff = d.score - origVal;
                    const hasDiff = Math.abs(diff) > 0.05;

                    return (
                      <div
                        key={d.name}
                        className="flex flex-col gap-1.5 p-3 rounded-xl bg-white/[0.015] border border-white/[0.04] text-xs hover:bg-white/[0.03] transition-all relative group/item"
                      >
                        <div className="flex items-center justify-between">
                          <div className="font-bold text-text-primary flex items-center gap-1.5">
                            {DIM_LABELS[d.name] ?? d.name}
                            {d.detail?.formula && (
                              <button
                                type="button"
                                onClick={() => setDetailDimName(d.name)}
                                className="text-text-muted hover:text-accent-primary transition-colors p-0.5 rounded hover:bg-white/5 cursor-pointer"
                                title="Xem chi tiết cách chấm điểm"
                                aria-label={`Chi tiết ${DIM_LABELS[d.name] ?? d.name}`}
                              >
                                <Info className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>
                          <div className="flex items-center gap-3">
                            {hasDiff && (
                              <span className="text-[10px] font-bold text-emerald-400">
                                +{diff.toFixed(0)}đ
                              </span>
                            )}
                            <div
                              className="font-black tabular-nums"
                              style={{ color: scoreColor(d.score) }}
                            >
                              {d.score.toFixed(0)}{" "}
                              <span className="text-text-muted font-normal text-[10px]">
                                /100
                              </span>
                            </div>
                            <div className="text-text-muted font-medium font-mono text-[10px]">
                              ω={d.weight.toFixed(2)}
                            </div>
                          </div>
                        </div>

                        <div className="w-full h-1.5 rounded-full bg-white/5 overflow-hidden relative">
                          {/* Original score indicator in back */}
                          {isSimulated && (
                            <div
                              className="absolute top-0 left-0 h-full bg-white/20 transition-all duration-500 rounded-full"
                              style={{ width: `${Math.min(100, origVal)}%` }}
                            />
                          )}
                          {/* Simulated/Current score indicator */}
                          <div
                            className="h-full rounded-full transition-all duration-500 relative z-10"
                            style={{
                              width: `${Math.min(100, d.score)}%`,
                              background: scoreColor(d.score),
                            }}
                          />
                        </div>

                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Scoring Criteria Modal */}
      <Dialog open={showCriteriaModal} onOpenChange={setShowCriteriaModal}>
        <DialogContent className="max-w-4xl p-0">
          <button
            type="button"
            onClick={() => setShowCriteriaModal(false)}
            className="absolute right-6 top-6 text-text-muted hover:text-text-primary z-10 cursor-pointer bg-surface/80 backdrop-blur-sm rounded-full p-1.5 border border-white/5 shadow-sm"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="max-h-[85vh] overflow-y-auto no-scrollbar rounded-[2.5rem]">
            <DialogHeader className="pt-10 px-10 pb-6 border-b border-white/5">
              <DialogTitle>Tiêu chí chấm điểm 8 chiều</DialogTitle>
              <DialogDescription className="mr-10">
                Hệ thống sử dụng mô hình <strong>Weighted Sum Model</strong> để
                đánh giá CV dựa trên 8 chiều. Trọng số (ω) của mỗi chiều được linh
                hoạt điều chỉnh dựa vào cấp bậc (Fresher/Junior sẽ tập trung vào
                Project & Skill, Senior/Lead sẽ tập trung vào Experience).
              </DialogDescription>
            </DialogHeader>
            <div className="p-10 grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-8 text-sm text-text-secondary">
              <div className="space-y-1.5">
                <h4 className="font-bold text-accent-primary">
                  1. Skill (Kỹ năng cốt lõi)
                </h4>
                <p className="leading-relaxed">
                  Phân tích độ phủ và xu hướng (trend) của các kỹ năng trong CV so
                  với nhu cầu thực tế của thị trường tuyển dụng trong 4 tuần gần
                  nhất. Kỹ năng có Demand cao sẽ mang lại điểm cao.
                </p>
              </div>
              <div className="space-y-1.5">
                <h4 className="font-bold text-emerald-400">
                  2. Experience (Kinh nghiệm)
                </h4>
                <p className="leading-relaxed">
                  Đánh giá số năm kinh nghiệm so với yêu cầu tiêu chuẩn của cấp
                  bậc (VD: Mid cần 3 năm). Đặc biệt, hệ thống đánh giá độ liên
                  quan (relevance) rất cao nếu chức danh (Job Title) cũ khớp với
                  vị trí đang ứng tuyển.
                </p>
              </div>
              <div className="space-y-1.5">
                <h4 className="font-bold text-blue-400">
                  3. Project (Dự án thực tế)
                </h4>
                <p className="leading-relaxed">
                  Dựa trên số lượng dự án (Portfolio) và mật độ sử dụng kỹ năng
                  (Skill Density) trong từng dự án. Chuẩn đánh giá là tối thiểu 3
                  dự án cá nhân chất lượng.
                </p>
              </div>
              <div className="space-y-1.5">
                <h4 className="font-bold text-orange-400">
                  4. Education (Học vấn)
                </h4>
                <p className="leading-relaxed">
                  Tính điểm nền tảng dựa trên bằng cấp (Cử nhân, Thạc sĩ...) và tự
                  động cộng thêm điểm thưởng (+10) nếu chuyên ngành thuộc nhóm
                  ngành Công nghệ Thông tin / Toán / Dữ liệu.
                </p>
              </div>
              <div className="space-y-1.5">
                <h4 className="font-bold text-purple-400">
                  5. Achievement (Thành tích & Chứng chỉ)
                </h4>
                <p className="leading-relaxed">
                  Tìm kiếm và tính điểm các thành tích nổi bật: Giải thưởng
                  (Olympic, Hackathon), Học bổng, Chứng chỉ quốc tế (AWS, Azure),
                  Báo cáo khoa học, và đóng góp Mã nguồn mở (Open Source).
                </p>
              </div>
              <div className="space-y-1.5">
                <h4 className="font-bold text-pink-400">
                  6. Language (Ngoại ngữ)
                </h4>
                <p className="leading-relaxed">
                  Quy đổi điểm IELTS, TOEIC hoặc các từ khóa mô tả trình độ ngôn
                  ngữ sang điểm số chuẩn mực hóa từ Basic (40) đến Native (100).
                </p>
              </div>
              <div className="space-y-1.5">
                <h4 className="font-bold text-amber-400">
                  7. Completeness (Độ hoàn thiện CV)
                </h4>
                <p className="leading-relaxed">
                  Kiểm tra tính đầy đủ của các thành phần bắt buộc trong một CV
                  chuẩn: Thông tin liên hệ, Tóm tắt (Summary), Học vấn, Kinh
                  nghiệm, Kỹ năng, và Dự án.
                </p>
              </div>
              <div className="space-y-1.5">
                <h4 className="font-bold text-cyan-400">
                  8. Market Align (Độ khớp thị trường)
                </h4>
                <p className="leading-relaxed">
                  Đo lường độ khớp rập khuôn bằng cách đối chiếu CV của bạn với
                  Top 10 kỹ năng đang được săn đón nhiều nhất của vị trí ứng tuyển
                  trên thị trường.
                </p>
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Per-dimension Detail Modal */}
      <Dialog
        open={!!detailDim}
        onOpenChange={(open) => { if (!open) setDetailDimName(null); }}
      >
        <DialogContent className="max-w-2xl p-0 border-white/10 bg-surface">
          {detailDim && (() => {
            const accent = scoreColor(detailDim.score);
            const dimLabel = DIM_LABELS[detailDim.name] ?? detailDim.name;
            return (
              <>
                <button
                  type="button"
                  onClick={() => setDetailDimName(null)}
                  className="absolute right-5 top-5 z-20 rounded-full p-1.5 bg-black/30 backdrop-blur-md border border-white/10 text-text-muted hover:text-text-primary hover:bg-black/50 transition-all cursor-pointer"
                  aria-label="Đóng"
                >
                  <X className="w-4 h-4" />
                </button>

                <div className="max-h-[85vh] overflow-y-auto no-scrollbar rounded-[1.5rem]">
                  {/* HERO HEADER — gradient nhuốm màu theo score */}
                  <div
                    className="relative border-b border-white/5 overflow-hidden"
                    style={{
                      background: `radial-gradient(circle at 20% 0%, ${accent}28 0%, transparent 55%), linear-gradient(135deg, rgba(255,255,255,0.02), transparent)`,
                    }}
                  >
                  <DialogHeader className="relative pt-8 pb-7 px-7 overflow-hidden">
                    {/* Glow dot */}
                    <div
                      className="absolute -top-10 -right-10 w-40 h-40 rounded-full opacity-20 blur-3xl pointer-events-none"
                      style={{ background: accent }}
                    />

                    <div className="relative flex items-start gap-5">
                      {/* Score ring */}
                      <div className="shrink-0 relative w-20 h-20">
                        <svg className="w-full h-full -rotate-90" viewBox="0 0 80 80">
                          <circle cx="40" cy="40" r="34" fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="6" />
                          <circle
                            cx="40" cy="40" r="34" fill="none"
                            stroke={accent} strokeWidth="6" strokeLinecap="round"
                            strokeDasharray={2 * Math.PI * 34}
                            strokeDashoffset={2 * Math.PI * 34 * (1 - Math.min(100, detailDim.score) / 100)}
                            style={{ transition: 'stroke-dashoffset 0.6s ease' }}
                          />
                        </svg>
                        <div className="absolute inset-0 flex flex-col items-center justify-center">
                          <div className="font-black text-xl tabular-nums leading-none" style={{ color: accent }}>
                            {detailDim.score.toFixed(0)}
                          </div>
                          <div className="text-[9px] text-text-muted font-bold uppercase tracking-wider mt-0.5">/100</div>
                        </div>
                      </div>

                      <div className="min-w-0 flex-1 pt-1">
                        <div className="flex items-center gap-2 flex-wrap">
                          <DialogTitle className="text-2xl font-extrabold font-outfit tracking-tight text-text-primary">
                            {dimLabel}
                          </DialogTitle>
                          <span
                            className="px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider"
                            style={{ background: `${accent}22`, color: accent, border: `1px solid ${accent}44` }}
                          >
                            {scoreLabel(detailDim.score)}
                          </span>
                        </div>
                        <DialogDescription className="text-text-secondary mt-1.5 leading-relaxed pr-8">
                          {detailDim.detail?.summary || ""}
                        </DialogDescription>
                        <div className="mt-3 flex items-center gap-3 text-[11px] font-mono">
                          <span className="text-text-muted">
                            <span className="text-text-muted/60">trọng số</span>
                            <span className="text-text-primary font-bold ml-1.5">ω = {detailDim.weight.toFixed(2)}</span>
                          </span>
                          <span className="w-px h-3 bg-white/10" />
                          <span className="text-text-muted">
                            <span className="text-text-muted/60">đóng góp</span>
                            <span className="text-emerald-400 font-bold ml-1.5">
                              {(detailDim.weight * detailDim.score).toFixed(1)} đ
                            </span>
                          </span>
                        </div>
                      </div>
                    </div>
                  </DialogHeader>
                  </div>

                  {/* BODY */}
                  <div className="px-7 py-6 space-y-6">

                    {/* CÔNG THỨC */}
                    {detailDim.detail?.formula && (
                      <section>
                        <div className="flex items-center gap-2 mb-2.5">
                          <div className="w-7 h-7 rounded-lg bg-accent-primary/15 border border-accent-primary/25 flex items-center justify-center">
                            <Sigma className="w-3.5 h-3.5 text-accent-primary" />
                          </div>
                          <h4 className="text-[11px] font-black uppercase tracking-[0.15em] text-text-primary">Công thức tính</h4>
                        </div>
                        <div className="relative rounded-xl bg-gradient-to-br from-black/60 to-black/30 border border-white/8 overflow-hidden">
                          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-accent-primary/60 to-transparent" />
                          <div className="px-5 py-5 katex-formula-block overflow-x-auto text-[15px]">
                            <BlockMath math={detailDim.detail.formula} errorColor="#f43f5e" />
                          </div>
                        </div>
                      </section>
                    )}

                    {/* INPUTS */}
                    {detailDim.detail?.inputs?.length > 0 && (
                      <section>
                        <div className="flex items-center gap-2 mb-2.5">
                          <div className="w-7 h-7 rounded-lg bg-indigo-500/15 border border-indigo-500/25 flex items-center justify-center">
                            <Database className="w-3.5 h-3.5 text-indigo-400" />
                          </div>
                          <h4 className="text-[11px] font-black uppercase tracking-[0.15em] text-text-primary">Dữ liệu đầu vào</h4>
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                          {detailDim.detail.inputs.map((inp, i) => (
                            <div
                              key={i}
                              className="group/inp rounded-xl bg-white/[0.02] border border-white/[0.06] px-3.5 py-2.5 hover:bg-white/[0.04] hover:border-white/10 transition-all"
                            >
                              <div className="text-[9.5px] font-bold uppercase tracking-[0.12em] text-text-muted/70">
                                {inp.label}
                              </div>
                              <div className="text-text-primary font-semibold text-[13.5px] break-words leading-snug mt-1">
                                {inp.value}
                              </div>
                              {inp.hint && (
                                <div className="text-[10.5px] text-text-muted/60 mt-1 italic leading-relaxed">
                                  {inp.hint}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </section>
                    )}

                    {/* BREAKDOWN */}
                    {detailDim.detail?.breakdown?.length > 0 && (
                      <section>
                        <div className="flex items-center gap-2 mb-2.5">
                          <div className="w-7 h-7 rounded-lg bg-amber-500/15 border border-amber-500/25 flex items-center justify-center">
                            <Compass className="w-3.5 h-3.5 text-amber-400" />
                          </div>
                          <h4 className="text-[11px] font-black uppercase tracking-[0.15em] text-text-primary">Vì sao điểm như vậy</h4>
                        </div>
                        <ul className="space-y-2">
                          {detailDim.detail.breakdown.map((b, i) => {
                            const { kind, body } = parseInsight(b);
                            const s = INSIGHT_STYLE[kind];
                            const Icon = s.icon;
                            return (
                              <li
                                key={i}
                                className={`flex gap-3 rounded-xl ${s.bg} border ${s.border} px-3.5 py-2.5 transition-colors`}
                              >
                                <Icon className={`w-4 h-4 ${s.color} shrink-0 mt-0.5`} strokeWidth={2.4} />
                                <span className="text-[13px] text-text-secondary leading-relaxed">{body}</span>
                              </li>
                            );
                          })}
                        </ul>
                      </section>
                    )}

                    {/* TIPS */}
                    {detailDim.detail?.tips?.length > 0 && (
                      <section>
                        <div className="flex items-center gap-2 mb-2.5">
                          <div className="w-7 h-7 rounded-lg bg-emerald-500/15 border border-emerald-500/25 flex items-center justify-center">
                            <Lightbulb className="w-3.5 h-3.5 text-emerald-400" />
                          </div>
                          <h4 className="text-[11px] font-black uppercase tracking-[0.15em] text-text-primary">Gợi ý cải thiện</h4>
                        </div>
                        <ul className="space-y-2">
                          {detailDim.detail.tips.map((t, i) => (
                            <li
                              key={i}
                              className="group/tip relative flex gap-3 rounded-xl bg-gradient-to-r from-emerald-500/[0.08] to-emerald-500/[0.03] border border-emerald-500/20 px-3.5 py-2.5 hover:from-emerald-500/[0.12] hover:to-emerald-500/[0.05] hover:border-emerald-500/30 transition-all"
                            >
                              <div className="absolute left-0 top-2 bottom-2 w-[2px] rounded-full bg-emerald-400/60" />
                              <Lightbulb className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                              <div className="text-[13px] text-emerald-100/95 leading-relaxed tip-markdown">
                                <ReactMarkdown
                                  components={{
                                    a: ({ href, children }) => (
                                      <a
                                        href={href}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-emerald-300 underline decoration-emerald-400/40 underline-offset-2 hover:text-emerald-200 hover:decoration-emerald-300 transition-colors font-medium"
                                      >
                                        {children}
                                      </a>
                                    ),
                                    p: ({ children }) => <span>{children}</span>,
                                  }}
                                >
                                  {t}
                                </ReactMarkdown>
                              </div>
                            </li>
                          ))}
                        </ul>
                      </section>
                    )}
                  </div>
                </div>
              </>
            );
          })()}
        </DialogContent>
      </Dialog>
    </Fragment>
  );
}

export default memo(FreshnessGaugeInner);
