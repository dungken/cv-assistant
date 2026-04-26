import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8081/api';
const AUTH_BASE = `${BASE_URL}/auth`;
const CHAT_BASE = `${BASE_URL}/chats`;

// All services routed through API Gateway for unified auth & CORS
const CHATBOT_BASE = `${BASE_URL}/chatbot`;
const SKILL_BASE = `${BASE_URL}/skills`;
const CAREER_BASE = `${BASE_URL}/career`;
const NER_BASE = `${BASE_URL}/ner`;

const api: AxiosInstance = axios.create({
    timeout: 30000,
});

// Request interceptor: attach token
api.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem('token');
        if (token && config.headers) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor: auto refresh token on 401
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;
            const refreshToken = localStorage.getItem('refreshToken');
            if (refreshToken) {
                try {
                    const res = await axios.post<AuthResponse>(`${AUTH_BASE}/refresh`, { refreshToken });
                    localStorage.setItem('token', res.data.token);
                    localStorage.setItem('refreshToken', res.data.refreshToken);
                    originalRequest.headers.Authorization = `Bearer ${res.data.token}`;
                    return api(originalRequest);
                } catch {
                    localStorage.removeItem('token');
                    localStorage.removeItem('refreshToken');
                    localStorage.removeItem('userName');
                    window.location.reload();
                }
            }
        }
        return Promise.reject(error);
    }
);

export interface Source {
    title: string;
    type: string;
    relevance: number;
}

export interface ChatResponse {
    response: string;
    sources: Source[];
    session_id: string;
    timestamp: string;
}

export interface TitleResponse {
    title: string;
}

export interface CVData {
    personal_info: {
        full_name: string;
        email: string;
        phone: string;
        location: string;
        title: string;
    };
    summary?: string;
    education: any[];
    experience: any[];
    skills: string[];
    projects: any[];
    certifications: any[];
    section_order?: string[];
}

export interface CollectorResponse {
    response: string;
    current_step: number;
    cv_data: CVData;
    session_id: string;
    timestamp: string;
}

export interface CVRewriteResponse {
    rewritten_points: string[];
}

export interface CVOptimizeResponse {
    optimized_cv: CVData;
    ats_result: {
        score: number;
        missing_keywords: string[];
        suggestions: string[];
    } | null;
}

export interface CollectorProgress {
    id: number;
    sessionId: number;
    currentStep: number;
    dataJson: string;
    isComplete: boolean;
    updatedAt: string;
}

export interface MessageHistory {
    id: number;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
}

export interface HealthResponse {
    status: string;
    ollama?: string;
    chroma?: string;
}

export interface AuthResponse {
    token: string;
    refreshToken: string;
    email: string;
    name: string;
    role: string;
}

export interface Session {
    id: number;
    title: string;
    updatedAt: string;
}

// Optimization Suggestions (US-17)
export interface OptimizationSuggestion {
    id: string;
    category: string;
    priority: 'critical' | 'important' | 'nice_to_have';
    title: string;
    description: string;
    why: string;
    how: string;
    evidence: string;
    confidence: number;
    preview?: string;
}

export interface OptimizationResponse {
    suggestions: OptimizationSuggestion[];
    ats_score: number;
    breakdown: Record<string, number>;
}

// Market Intelligence (US-19)
export interface SkillTrend {
    name: string;
    count: number;
    percentage: number;
    growth: number;
}

export interface SkillCorrelation {
    skill_a: string;
    skill_b: string;
    weight: number;
}

export interface SalaryStats {
    category: string;
    min_salary: number;
    max_salary: number;
    median_salary: number;
}

export interface MarketOverviewResponse {
    top_skills: SkillTrend[];
    industry_distribution: Record<string, number>;
    location_distribution: Record<string, number>;
    salary_overview: SalaryStats[];
    correlations: SkillCorrelation[];
}

// --- Auth API ---

export const authApi = {
    login: (credentials: { email: string; password: string }) =>
        axios.post<AuthResponse>(`${AUTH_BASE}/login`, credentials),
    register: (userData: { name: string; email: string; password: string }) =>
        axios.post<AuthResponse>(`${AUTH_BASE}/register`, userData),
    refreshToken: (refreshToken: string) =>
        axios.post<AuthResponse>(`${AUTH_BASE}/refresh`, { refreshToken }),
    verifyEmail: (token: string) =>
        axios.post(`${AUTH_BASE}/verify-email`, { token }),
    forgotPassword: (email: string) =>
        axios.post(`${AUTH_BASE}/forgot-password`, { email }),
    resetPassword: (email: string, otp: string, newPassword: string) =>
        axios.post(`${AUTH_BASE}/reset-password`, { email, otp, newPassword }),
};

// --- User/Profile API ---

export interface UserPreferences {
    language?: string;
    industry?: string;
    careerLevel?: string;
}

export interface UserStats {
    cvsCreated: number;
    analysesDone: number;
    coursesBookmarked: number;
}

export interface UserProfile {
    id: number;
    email: string;
    name: string;
    bio: string;
    phone?: string;
    avatarUrl?: string;
    isEmailVerified: boolean;
    preferences?: UserPreferences;
    stats?: UserStats;
    createdAt: string;
}

export const userApi = {
    getProfile: () => api.get<UserProfile>(`${BASE_URL}/user/profile`),
    updateProfile: (data: { name?: string; bio?: string; phone?: string; preferences?: UserPreferences }) =>
        api.put<UserProfile>(`${BASE_URL}/user/profile`, data),
    uploadAvatar: (file: File) => {
        const form = new FormData();
        form.append('file', file);
        return api.post<UserProfile>(`${BASE_URL}/user/avatar`, form);
    },
    changePassword: (oldPassword: string, newPassword: string) =>
        api.put(`${BASE_URL}/user/change-password`, { oldPassword, newPassword }),
    deleteAccount: (password: string) =>
        api.delete(`${BASE_URL}/user/account`, { data: { password } }),
};

// --- CV Document API ---

export interface CvVersionInfo {
    id: number;
    versionNumber: number;
    note?: string;
    tag?: string;
    isStarred: boolean;
    createdAt: string;
}

export interface CvVersionDetail extends CvVersionInfo {
    dataJson: string;
}

export interface CvDocument {
    id: number;
    name: string;
    template?: string;
    targetJd?: string;
    atsScore?: number;
    currentVersion: number;
    createdAt: string;
    updatedAt: string;
    versions: CvVersionInfo[];
}

export interface CvDiff {
    oldVersion: CvVersionDetail;
    newVersion: CvVersionDetail;
}

export const cvDocumentApi = {
    list: (params?: { query?: string; template?: string; sortBy?: string; page?: number }, config?: import('axios').AxiosRequestConfig) =>
        api.get<CvDocument[]>(`${BASE_URL}/cv-documents`, { params, ...config }),
    getById: (id: number) =>
        api.get<CvDocument>(`${BASE_URL}/cv-documents/${id}`),
    create: (data: { name: string; template?: string; targetJd?: string; dataJson: string; note?: string }) =>
        api.post<CvDocument>(`${BASE_URL}/cv-documents`, data),
    update: (id: number, data: { name?: string; template?: string; targetJd?: string; atsScore?: number }) =>
        api.put<CvDocument>(`${BASE_URL}/cv-documents/${id}`, data),
    delete: (id: number) =>
        api.delete(`${BASE_URL}/cv-documents/${id}`),
    restore: (id: number) =>
        api.post<CvDocument>(`${BASE_URL}/cv-documents/${id}/restore`),

    // Versions
    createVersion: (docId: number, data: { dataJson: string; note?: string }) =>
        api.post<CvVersionDetail>(`${BASE_URL}/cv-documents/${docId}/versions`, data),
    getVersion: (docId: number, versionId: number) =>
        api.get<CvVersionDetail>(`${BASE_URL}/cv-documents/${docId}/versions/${versionId}`),
    updateVersion: (versionId: number, data: { note?: string; tag?: string; isStarred?: boolean }) =>
        api.put(`${BASE_URL}/cv-documents/versions/${versionId}`, data),
    diff: (docId: number, versionA: number, versionB: number) =>
        api.get<CvDiff>(`${BASE_URL}/cv-documents/${docId}/diff`, { params: { versionA, versionB } }),
    restoreVersion: (docId: number, versionNumber: number) =>
        api.post<CvDocument>(`${BASE_URL}/cv-documents/${docId}/versions/${versionNumber}/restore`),
};

// --- Chat CRUD API ---

export const chatCrudApi = {
    getSessions: () => api.get<Session[]>(CHAT_BASE),
    createSession: (title: string) => api.post<Session>(CHAT_BASE, { title }),
    updateTitle: (id: number, title: string) => api.put<Session>(`${CHAT_BASE}/${id}`, { title }),
    deleteSession: (id: number) => api.delete(`${CHAT_BASE}/${id}`),
    getMessages: (id: number) => api.get<MessageHistory[]>(`${CHAT_BASE}/${id}/messages`),
    saveMessage: (id: number, role: string, content: string) =>
        api.post(`${CHAT_BASE}/${id}/messages`, { role, content }),
};

export const chatbotApi = {
    chat: (message: string, sessionId: string) =>
        api.post<ChatResponse>(`${CHATBOT_BASE}/chat`, { message, session_id: sessionId }),
    chatCollector: (message: string, sessionId: string, currentStep?: number, cvData?: CVData) =>
        api.post<CollectorResponse>(`${CHATBOT_BASE}/chat/collector`, {
            message,
            session_id: sessionId,
            current_step: currentStep,
            cv_data: cvData
        }),
    rewriteSection: (title: string, context: string, rawPoints: string[]) =>
        api.post<CVRewriteResponse>(`${CHATBOT_BASE}/cv/rewrite`, {
            title,
            context,
            raw_points: rawPoints
        }),
    optimizeCv: (cvData: CVData, jdText?: string) =>
        api.post<CVOptimizeResponse>(`${CHATBOT_BASE}/cv/generate`, {
            cv_data: cvData,
            jd_text: jdText
        }),
    // US-17
    getOptimizationSuggestions: (cvData: CVData, jdText?: string) =>
        api.post<OptimizationResponse>(`${CHATBOT_BASE}/cv/optimize-suggestions`, {
            cv_data: cvData,
            jd_text: jdText
        }),
    health: () => api.get(`${CHATBOT_BASE}/health`),
    generateTitle: (payload: {
        user_message: string;
        assistant_message: string;
        active_tool?: string | null;
        user_id?: string | null;
        tool_context?: string | null;
    }) => api.post<TitleResponse>(`${CHATBOT_BASE}/chat/title`, payload),

    // Streaming Fetch Helpers
    streamChat: async (
        message: string,
        sessionId: string,
        activeTool?: string | null,
        userId?: string | null,
        toolContext?: string | null
    ) => {
        const token = localStorage.getItem('token');
        return fetch(`${CHATBOT_BASE}/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                message,
                session_id: sessionId,
                active_tool: activeTool || undefined,
                user_id: userId || undefined,
                tool_context: toolContext || undefined
            })
        });
    },
    streamCollector: async (message: string, sessionId: string, currentStep?: number, cvData?: CVData, userId?: string | null) => {
        const token = localStorage.getItem('token');
        return fetch(`${CHATBOT_BASE}/chat/collector/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                message,
                session_id: sessionId,
                current_step: currentStep,
                cv_data: cvData,
                user_id: userId || undefined
            })
        });
    }
};

// ─── US-27: User Memory API ─────────────────────────────────────────────────

export interface CareerProfileMemory {
    current_role?: string;
    current_skills: string[];
    target_role?: string;
    timeline_months?: number;
}

export interface SuggestionRecord {
    type: string;
    content: string;
    given_at: string;
}

export interface UserMemory {
    user_id: string;
    display_name: string | null;
    tone_preference: string;
    language: string;
    career_profile: CareerProfileMemory;
    skill_gaps: string[];
    suggestion_history: SuggestionRecord[];
    field_timestamps: Record<string, string>;
    created_at: string;
    updated_at: string;
}

export interface MemoryUpdatePayload {
    display_name?: string | null;
    tone_preference?: string;
    language?: string;
    career_profile?: Partial<CareerProfileMemory>;
    skill_gaps?: string[];
}

export const memoryApi = {
    get: (userId: string) =>
        api.get<UserMemory>(`${CHATBOT_BASE}/memory/${encodeURIComponent(userId)}`),
    update: (userId: string, data: MemoryUpdatePayload) =>
        api.put<UserMemory>(`${CHATBOT_BASE}/memory/${encodeURIComponent(userId)}`, data),
    deleteField: (userId: string, field: string) =>
        api.delete(`${CHATBOT_BASE}/memory/${encodeURIComponent(userId)}/${field}`),
    deleteAll: (userId: string) =>
        api.delete(`${CHATBOT_BASE}/memory/${encodeURIComponent(userId)}`),
};

export const collectorApi = {
    getProgress: (sessionId: number) => api.get<CollectorProgress>(`${BASE_URL}/collector/${sessionId}`),
    updateProgress: (sessionId: number, currentStep: number, dataJson: string, isComplete: boolean) =>
        api.post<CollectorProgress>(`${BASE_URL}/collector/${sessionId}`, { currentStep, dataJson, isComplete }),
};

// --- Skill Service Interfaces ---

export interface GraphNode {
    id: string;
    label: string;
    category: string;
    demand: number;
    trending: boolean;
    distance: number;
}

export interface GraphEdge {
    source: string;
    target: string;
    type: string;
}

export interface GraphData {
    nodes: GraphNode[];
    edges: GraphEdge[];
}

export interface SkillNode {
    skill_id: string;
    name: string;
    category: string | null;
    subcategory: string | null;
    level_range: string[];
    description: string;
    demand_score: number;
    trending: boolean;
    relationships: Record<string, string[]>;
    required_by: string[];
    leads_from: string[];
}

export interface SkillSearchResult {
    name: string;
    category: string;
    subcategory: string;
    demand: number;
    trending: boolean;
    score: number;
}

export interface OntologyStats {
    total_nodes: number;
    total_edges: number;
    edge_counts: Record<string, number>;
    category_counts: Record<string, number>;
    connectivity: number;
    categories: number;
}

export interface SemanticMatch {
    cv_skill: string;
    jd_skill: string;
    similarity: number;
}

export interface OntologyMatch {
    cv_skill: string;
    jd_skill: string;
    distance: number;
    relationship: string;
    category: string;
}

export interface SkillGapExplanation {
    summary: string;
    score_interpretation: string;
    gap_by_category: Record<string, any>;
    priority_skills: any[];
    learning_plan: any[];
    transferable_strengths: any[];
    total_estimated_weeks: number;
}

export interface ExperienceMatch {
    current: number;
    required_min: number;
    required_max?: number;
    status: 'match' | 'partial' | 'gap' | 'overqualified';
    score: number;
}

export interface EducationMatch {
    current: string | null;
    required: string | null;
    status: 'match' | 'partial' | 'gap';
    score: number;
}

export interface MatchedSkill {
    skill: string;
    match_type: 'exact' | 'ontology' | 'semantic';
    cv_mention: string;
    jd_requirement: 'required' | 'preferred';
}

export interface MissingSkill {
    skill: string;
    jd_requirement: 'required' | 'preferred';
    priority: 'high' | 'medium' | 'low';
    suggestion: string;
}

export interface ExtraSkill {
    skill: string;
    relevance: 'high' | 'medium' | 'low';
    suggestion: string;
}

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

export interface LearningPhase {
    phase: string;
    weeks: string;
    skills: string[];
    courses: Course[];
    estimated_hours: number;
}

export interface LearningRoadmap {
    total_weeks: number;
    phases: LearningPhase[];
    current_progress?: number;
}

export interface SkillMatchResponse {
    analysis_id: string;
    jd_title: string;
    jd_company: string;
    overall_score: number;
    breakdown: {
        skills: number;
        experience: number;
        education: number;
    };
    skills: {
        matched: MatchedSkill[];
        missing: MissingSkill[];
        extra: ExtraSkill[];
    };
    experience: ExperienceMatch;
    education: EducationMatch;
    recommendations: string[];
    course_recommendations: Course[];
    learning_roadmap: LearningRoadmap | null;
    skill_gap_explanation?: SkillGapExplanation;
    // Legacy support
    jd_skills_extracted: string[];
    exact_matches: string[];
    ontology_matches: OntologyMatch[];
    semantic_matches: SemanticMatch[];
    missing_skills: string[];
    cv_profile: Record<string, string[]>;
}

export interface MultiSkillMatchResponse {
    results: SkillMatchResponse[];
}

export const skillApi = {
    match: (cvSkills: string[], jdText: string, cvDetails?: any) =>
        api.post<SkillMatchResponse>(`${SKILL_BASE}/match`, {
            cv_skills: cvSkills,
            jd_text: jdText,
            cv_details: cvDetails
        }),

    matchMulti: (cvDetails: any, jdTexts: string[]) =>
        api.post<MultiSkillMatchResponse>(`${SKILL_BASE}/match/multi`, {
            cv_details: cvDetails,
            jd_texts: jdTexts
        }),
    
    // US-19
    getMarketOverview: (industry?: string) =>
        api.get<MarketOverviewResponse>(`${SKILL_BASE}/market/overview`, { params: { industry } }),

    // ── Knowledge Graph / Ontology ──
    getSkillNode: (name: string) =>
        api.get<SkillNode>(`${SKILL_BASE}/ontology/skill/${encodeURIComponent(name)}`),

    getGraphData: (center?: string, depth: number = 1, maxNodes: number = 80) => {
        const params = new URLSearchParams({ depth: String(depth), max_nodes: String(maxNodes) });
        if (center) params.set('center', center);
        return api.get<GraphData>(`${SKILL_BASE}/ontology/graph?${params.toString()}`);
    },

    searchSkills: (query: string, limit: number = 20) =>
        api.get<{ results: SkillSearchResult[]; total: number }>(
            `${SKILL_BASE}/ontology/search?q=${encodeURIComponent(query)}&limit=${limit}`
        ),

    getStats: () =>
        api.get<OntologyStats>(`${SKILL_BASE}/ontology/stats`),

    getCategories: () =>
        api.get<{ categories: string[] }>(`${SKILL_BASE}/ontology/categories`),
};

export const courseApi = {
    bookmark: (courseId: string, userId?: string) =>
        api.post<{ status: string; is_bookmarked: boolean }>(`${SKILL_BASE}/courses/bookmark`, {
            course_id: courseId,
            user_id: userId
        }),
    updateProgress: (course_id: string, progress: number, user_id?: string) =>
        api.patch<{ status: string }>(`${SKILL_BASE}/courses/progress`, {
            course_id,
            progress,
            user_id
        }),
    getRecommendations: (skills: string[]) =>
        api.get<Course[]>(`${SKILL_BASE}/courses/recommend?skills=${encodeURIComponent(skills.join(','))}`),
};

export const careerApi = {
    recommend: (currentRole: string, targetRole: string | null, skills: string[]) =>
        api.post(`${CAREER_BASE}/recommend`, {
            current_role: currentRole,
            target_role: targetRole,
            current_skills: skills
        }),
};

export interface Entity {
    text: string;
    type: string;
    start: number;
    end: number;
    confidence: number;
}

export interface ExperienceItem {
    anchor: string;
    entities: Entity[];
    description: string;
}

export interface ParseResult {
    filename: string;
    summary: string;
    experience: ExperienceItem[];
    projects: ExperienceItem[];
    education: ExperienceItem[];
    certifications: ExperienceItem[];
    skills: Record<string, string[]>;
    languages: string[];
    raw_text: string;
    status: string;
    metadata: {
        language: string;
        pages: number;
        parse_method: string;
        parse_time_ms: number;
    };
    grouped_entities?: Record<string, string[]>;
    char_count?: number;
    entity_count?: number;
    raw_text_preview?: string;
}

export const nerApi = {
    parseCv: (file: File) => {
        const form = new FormData();
        form.append('file', file);
        return api.post<ParseResult>(`${NER_BASE}/parse-cv`, form);
    },
    generatePdf: (cvData: any) =>
        api.post(`${NER_BASE}/generate-pdf`, cvData, { responseType: 'blob' }),
};

// --- JD (Job Description) API ---

const JD_BASE = `${BASE_URL}/jd`;

export interface JDExtractedSkills {
    required: string[];
    preferred: string[];
}

export interface JDSections {
    requirements: string[];
    responsibilities: string[];
    benefits: string[];
    about: string[];
    preferred: string[];
}

export interface JDMetadata {
    language: string;
    parse_time_ms: number;
    input_method: string;
    source_url?: string;
}

export interface JDParseResult {
    jd_id: string;
    title: string;
    company: string;
    location: string;
    level: string;
    experience_years: string;
    sections: JDSections;
    extracted_skills: JDExtractedSkills;
    raw_text: string;
    metadata: JDMetadata;
    status: string;
    filename?: string;
}

export interface JDHistoryItem {
    id: number;
    title: string;
    company: string;
    inputMethod: string;
    createdAt: string;
}

export const jdApi = {
    parseFile: (file: File) => {
        const form = new FormData();
        form.append('file', file);
        return api.post<JDParseResult>(`${JD_BASE}/parse-file`, form, { timeout: 60000 });
    },
    parseText: (text: string, title?: string, company?: string) =>
        api.post<JDParseResult>(JD_BASE + '/parse-text', { text, title, company }),
    parseUrl: (url: string) =>
        api.post<JDParseResult>(JD_BASE + '/parse-url', { url }, { timeout: 30000 }),
    getHistory: () =>
        api.get<JDHistoryItem[]>(JD_BASE + '/history'),
    deleteHistory: (id: number) =>
        api.delete(JD_BASE + '/history/' + id),
};

// ─── US-29: CV Builder Optimization ─────────────────────────────────────────

export interface BulletSuggestion {
    id: number;
    bullet: string;
    star_format: { situation: string; task: string; action: string; result: string };
    confidence: number;
}

export interface CVSuggestResponse {
    job_title: string;
    company: string | null;
    duration: string | null;
    raw_input: string;
    suggestions: BulletSuggestion[];
}

export interface CVValidateResponse {
    field: string;
    is_valid: boolean;
    error: string | null;
    warning: string | null;
}

export interface CVDraftData {
    user_id: string;
    current_step: number;
    completed_steps: string[];
    progress_percent: number;
    data: CVData;
}

export const cvBuilderApi = {
    suggest: (payload: {
        job_title: string;
        company?: string;
        duration?: string;
        raw_input: string;
        section?: string;
    }) => api.post<CVSuggestResponse>(`${CHATBOT_BASE}/cv-builder/suggest`, payload),

    validate: (field: string, value: string, field_type: string) =>
        api.post<CVValidateResponse>(`${CHATBOT_BASE}/cv-builder/validate`, { field, value, field_type }),

    getDraft: (userId: string) =>
        api.get<CVDraftData>(`${CHATBOT_BASE}/cv-builder/draft/${encodeURIComponent(userId)}`),

    saveDraft: (userId: string, draft: CVDraftData) =>
        api.put<CVDraftData>(`${CHATBOT_BASE}/cv-builder/draft/${encodeURIComponent(userId)}`, draft),

    deleteDraft: (userId: string) =>
        api.delete(`${CHATBOT_BASE}/cv-builder/draft/${encodeURIComponent(userId)}`),
};

export const feedbackApi = {
    create: (data: { itemId?: string; type: string; rating?: number; comment?: string; correctionJson?: string }) =>
        api.post(`${BASE_URL}/feedback`, data),
    getAll: () => api.get<any[]>(`${BASE_URL}/feedback/all`),
    getByType: (type: string) => api.get<any[]>(`${BASE_URL}/feedback/type/${type}`),
};

export const templateApi = {
    getAll: (includeUnpublished: boolean = false) =>
        api.get<any[]>(`${BASE_URL}/templates`, { params: { includeUnpublished } }),
    getById: (id: number) => api.get<any>(`${BASE_URL}/templates/${id}`),
    create: (data: any) => api.post(`${BASE_URL}/templates`, data),
    update: (id: number, data: any) => api.put(`${BASE_URL}/templates/${id}`, data),
    delete: (id: number) => api.delete(`${BASE_URL}/templates/${id}`),
};

export const monitoringApi = {
    getStats: () => api.get<any>(`${BASE_URL}/admin/monitoring/stats`),
    getLogs: (tail: number = 100) => api.get<any>(`${BASE_URL}/admin/monitoring/logs`, { params: { tail } }),
};

export const adminApi = {
    getUsers: () => api.get<any[]>(`${BASE_URL}/admin/users`),
    updateUserRole: (id: number, role: string) => api.put(`${BASE_URL}/admin/users/${id}/role`, { role }),
};

export default api;
