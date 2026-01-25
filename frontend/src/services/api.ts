import axios, { AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const BASE_URL = 'http://localhost:8081/api';
const AUTH_BASE = `${BASE_URL}/auth`;
const CHAT_BASE = `${BASE_URL}/chats`;

const CHATBOT_BASE = 'http://localhost:5004';
const SKILL_BASE = 'http://localhost:5002';
const CAREER_BASE = 'http://localhost:5003';

const api: AxiosInstance = axios.create({
    timeout: 30000,
});

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

export interface HealthResponse {
    status: string;
    ollama?: string;
    chroma?: string;
}

export interface AuthResponse {
    token: string;
    email: string;
    name: string;
}

export interface Session {
    id: number;
    title: string;
    updatedAt: string;
}

export interface MessageHistory {
    id: number;
    role: 'user' | 'assistant';
    content: string;
    timestamp: string;
}

export const authApi = {
    login: (credentials: any) => axios.post<AuthResponse>(`${AUTH_BASE}/login`, credentials),
    register: (userData: any) => axios.post<AuthResponse>(`${AUTH_BASE}/register`, userData),
};

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
    health: () => api.get(`${CHATBOT_BASE}/health`),
};

export const skillApi = {
    match: (cvSkills: string[], jdText: string) =>
        api.post(`${SKILL_BASE}/match`, { cv_skills: cvSkills, jd_text: jdText }),
};

export const careerApi = {
    recommend: (currentRole: string, targetRole: string | null, skills: string[]) =>
        api.post(`${CAREER_BASE}/recommend`, {
            current_role: currentRole,
            target_role: targetRole,
            current_skills: skills
        }),
};

export default api;
