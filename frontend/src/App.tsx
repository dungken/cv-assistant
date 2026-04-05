import { useState, useEffect, useRef, useMemo } from 'react'
import {
  Sparkles,
  ChevronDown,
  Settings as SettingsIcon,
  PanelLeftOpen,
  Cpu,
  Layout as LayoutIcon
} from 'lucide-react';
import { Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { chatbotApi, chatCrudApi, collectorApi, memoryApi, userApi, Source, Session, CVData } from './services/api';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import ForgotPassword from './components/auth/ForgotPassword';
import SettingsModal from './components/common/SettingsModal';
import Sidebar from './components/layout/Sidebar';
import MessageItem from './components/chat/MessageItem';
import PromptBar from './components/chat/PromptBar';
import ChatTOC from './components/chat/ChatTOC';
import SearchView from './components/chat/SearchView';
import ArtifactPanel from './components/layout/ArtifactPanel';
import ProfilePage from './components/features/ProfilePage';
import CVListPage from './components/features/CVListPage';
import FeedbackModal from './components/features/FeedbackModal';
import UserMemoryPanel from './components/features/UserMemoryPanel';
import AdminPortal from './components/features/AdminPortal';
import { Button } from './components/ui/Button';
import { Badge } from './components/ui/Badge';
import { cn } from './lib/utils';
import { useTranslation } from 'react-i18next';
import { LanguageSwitcher } from './components/layout/LanguageSwitcher';

export default function App() {
  const { t, i18n } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant', content: string, sources?: Source[] }[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [sessionList, setSessionList] = useState<Session[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);

  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!localStorage.getItem('token'));
  const [authView, setAuthView] = useState<'login' | 'register' | 'forgot-password'>('login');
  const [userName, setUserName] = useState<string>(localStorage.getItem('userName') || '');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isSearchMode, setIsSearchMode] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [isCvListOpen, setIsCvListOpen] = useState(false);
  const [isFeedbackModalOpen, setIsFeedbackModalOpen] = useState(false);
  const [feedbackItemId, setFeedbackItemId] = useState<string | undefined>(undefined);
  const [userRole, setUserRole] = useState<string>(localStorage.getItem('userRole') || 'User');
  // US-27: Memory panel
  const [isMemoryPanelOpen, setIsMemoryPanelOpen] = useState(false);
  const [userEmail, setUserEmail] = useState<string>(localStorage.getItem('userEmail') || '');
  const [hasPersonalizedMemory, setHasPersonalizedMemory] = useState(false);
  const [guidanceSnoozeUntil, setGuidanceSnoozeUntil] = useState<number>(() => Number(localStorage.getItem('guidanceSnoozeUntil') || '0'));
  const [theme, setTheme] = useState<'dark' | 'light'>((localStorage.getItem('theme') as 'dark' | 'light') || 'dark');
  
  // Artifact/Unified Mode State
  const [isArtifactOpen, setIsArtifactOpen] = useState(false);
  const [artifactType, setArtifactType] = useState<'builder' | 'upload' | 'match' | 'career' | 'ats' | 'jd' | 'graph' | 'market' | 'admin' | null>(null);


  // Shared CV Builder State
  const [currentStep, setCurrentStep] = useState(1);
  const [cvData, setCvData] = useState<CVData>({
    personal_info: { full_name: '', email: '', phone: '', location: '', title: '' },
    education: [],
    experience: [],
    skills: [],
    projects: [],
    certifications: []
  });

  const [editingSessionId, setEditingSessionId] = useState<number | null>(null);
  const [tempTitle, setTempTitle] = useState('');
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [userHasScrolledUp, setUserHasScrolledUp] = useState(false);
  const [cursorPos, setCursorPos] = useState({ x: -9999, y: -9999 });
  const [showAllMessages, setShowAllMessages] = useState(false);
  const mainRef = useRef<HTMLDivElement>(null);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      setCursorPos({ x: e.clientX, y: e.clientY });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle('light', theme === 'light');
    localStorage.setItem('theme', theme);
  }, [theme]);

  useEffect(() => {
    if (isAuthenticated) {
      checkHealth();
      loadSessions();
    }
  }, [isAuthenticated]);

  // Ensure user identity fields exist for legacy sessions (token existed before we stored email/name).
  useEffect(() => {
    const hydrateIdentity = async () => {
      if (!isAuthenticated) return;
      if (userEmail && userName) return;
      try {
        const res = await userApi.getProfile();
        if (!userEmail && res.data.email) {
          setUserEmail(res.data.email);
          localStorage.setItem('userEmail', res.data.email);
        }
        if (!userName && res.data.name) {
          setUserName(res.data.name);
          localStorage.setItem('userName', res.data.name);
        }
      } catch {
        // Ignore; chat still works without personalization
      }
    };
    hydrateIdentity();
  }, [isAuthenticated, userEmail, userName]);

  // Bootstrap sync for older accounts:
  // if memory is empty, hydrate it from profile once on app load.
  useEffect(() => {
    const bootstrapProfileToMemory = async () => {
      if (!isAuthenticated || !userEmail) return;
      try {
        const [memoryRes, profileRes] = await Promise.all([
          memoryApi.get(userEmail),
          userApi.getProfile()
        ]);

        const memory = memoryRes.data;
        const profile = profileRes.data;
        const hasMemoryData = Boolean(
          memory.display_name ||
          memory.career_profile?.current_role ||
          (memory.career_profile?.current_skills || []).length > 0 ||
          memory.career_profile?.target_role ||
          (memory.skill_gaps || []).length > 0
        );
        if (hasMemoryData) return;

        await memoryApi.update(userEmail, {
          display_name: profile.name || null,
          language: profile.preferences?.language || 'vi',
          career_profile: {
            current_role: profile.preferences?.careerLevel || undefined
          }
        });
      } catch {
        // Non-blocking bootstrap path
      }
    };
    bootstrapProfileToMemory();
  }, [isAuthenticated, userEmail]);

  useEffect(() => {
    const loadMemoryBadge = async () => {
      if (!isAuthenticated || !userEmail) {
        setHasPersonalizedMemory(false);
        return;
      }
      try {
        const res = await memoryApi.get(userEmail);
        const m = res.data;
        const hasData = Boolean(
          m.display_name ||
          m.career_profile?.current_role ||
          (m.career_profile?.current_skills || []).length > 0 ||
          m.career_profile?.target_role ||
          (m.skill_gaps || []).length > 0
        );
        setHasPersonalizedMemory(hasData);
      } catch {
        setHasPersonalizedMemory(false);
      }
    };
    loadMemoryBadge();
  }, [isAuthenticated, userEmail]);

  useEffect(() => {
    if (!loadingMessages && !userHasScrolledUp) {
      messagesEndRef.current?.scrollIntoView({ 
        behavior: isStreaming ? 'auto' : 'smooth',
        block: 'end'
      });
    }
  }, [messages, loadingMessages, isStreaming, userHasScrolledUp]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    // If user is more than 150px away from bottom, consider they are looking up
    const isAtBottom = scrollHeight - scrollTop <= clientHeight + 150;
    setUserHasScrolledUp(!isAtBottom);
  };

  useEffect(() => {
    if (!isAuthenticated || !isArtifactOpen || !artifactType || Date.now() < guidanceSnoozeUntil) return;

    let timer: number | undefined;
    const ping = () => {
      if (timer) window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        setMessages(prev => {
          if (prev.length > 0) {
            const last = prev[prev.length - 1];
            if (last.role === 'assistant' && last.content.includes('[TOOL_QUICK_ACTION:snooze')) {
              return prev;
            }
          }
          return [
            ...prev,
            {
              role: 'assistant',
              content:
                `Bạn đang dừng khá lâu ở tool hiện tại.\n` +
                `[TOOL_QUICK_ACTION:help|Có, gợi ý giúp]\n` +
                `[TOOL_QUICK_ACTION:snooze|Để sau 10 phút]`,
              sources: []
            }
          ];
        });
      }, 120000);
    };

    const onActivity = () => ping();
    window.addEventListener('mousemove', onActivity);
    window.addEventListener('keydown', onActivity);
    ping();

    return () => {
      window.removeEventListener('mousemove', onActivity);
      window.removeEventListener('keydown', onActivity);
      if (timer) window.clearTimeout(timer);
    };
  }, [isAuthenticated, isArtifactOpen, artifactType, guidanceSnoozeUntil]);

  const checkHealth = async () => {
    try {
      const res = await chatbotApi.health();
      setIsConnected(res.data.ollama === 'connected');
    } catch (error) {
      setIsConnected(false);
    }
  };

  const loadSessions = async () => {
    try {
      const res = await chatCrudApi.getSessions();
      setSessionList(res.data);
    } catch (error) {
      console.error('Failed to load sessions');
    }
  };

  const createNewChat = () => {
    setCurrentSessionId(null);
    setMessages([]);
    setIsArtifactOpen(false);
    setArtifactType(null);
    setShowAllMessages(false);
    setIsSearchMode(false);
    resetBuilderState();
    if (location.pathname !== '/') {
        navigate('/');
    }
  };

  const resetBuilderState = () => {
    setCurrentStep(1);
    setCvData({
      personal_info: { full_name: '', email: '', phone: '', location: '', title: '' },
      education: [],
      experience: [],
      skills: [],
      projects: [],
      certifications: []
    });
  };

  const selectSession = async (id: number) => {
    setCurrentSessionId(id);
    setLoadingMessages(true);
    setIsArtifactOpen(false);
    setArtifactType(null);
    setShowAllMessages(false);
    setIsSearchMode(false);
    try {
      const res = await chatCrudApi.getMessages(id);
      setMessages(res.data.map(m => ({ role: m.role as any, content: m.content, sources: [] })));
      
      try {
          const progRes = await collectorApi.getProgress(id);
          if (progRes.data) {
              setCurrentStep(progRes.data.currentStep);
              setCvData(JSON.parse(progRes.data.dataJson));
              setArtifactType('builder');
              setIsArtifactOpen(true);
          }
      } catch (e) {}
    } catch (error) {
      console.error('Failed to load messages');
    }
    setLoadingMessages(false);
  };

  const deleteChat = async (e: React.MouseEvent | null, id: number) => {
    e?.stopPropagation();
    try {
      await chatCrudApi.deleteSession(id);
      setSessionList(prev => prev.filter(s => s.id !== id));
      if (currentSessionId === id) createNewChat();
    } catch (error) {
      console.error('Failed to delete');
    }
  };

  const startEditing = (e: React.MouseEvent | null, s: Session) => {
    e?.stopPropagation();
    setEditingSessionId(s.id);
    setTempTitle(s.title);
  };

  const saveTitle = async (e: React.MouseEvent | null, id: number, customTitle?: string) => {
    e?.stopPropagation();
    const finalTitle = customTitle || tempTitle;
    try {
      await chatCrudApi.updateTitle(id, finalTitle);
      setSessionList(prev => prev.map(s => s.id === id ? { ...s, title: finalTitle } : s));
      setEditingSessionId(null);
    } catch (error) {
      setEditingSessionId(null);
    }
  };

  const handleAuthSuccess = (token: string, name: string, role: string, email: string) => {
    localStorage.setItem('token', token);
    localStorage.setItem('userName', name);
    localStorage.setItem('userRole', role);
    localStorage.setItem('userEmail', email);
    setIsAuthenticated(true);
    setUserName(name);
    setUserRole(role);
    setUserEmail(email);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('userName');
    localStorage.removeItem('userRole');
    localStorage.removeItem('userEmail');
    setIsAuthenticated(false);
    setMessages([]);
    setCurrentSessionId(null);
    setIsArtifactOpen(false);
    setUserRole('User');
    setUserEmail('');
    setIsMemoryPanelOpen(false);
  };

  const inferSessionTitle = (userText: string, assistantText: string): string => {
    const stripStructured = (s: string) =>
      s
        .replace(/\[TOOL_CTA:[^\]]+\]\n?/g, ' ')
        .replace(/\[TOOL_CHECKLIST:[^\]]+\]\n?/g, ' ')
        .replace(/\[TOOL_QUICK_ACTION:[^\]]+\]\n?/g, ' ')
        .replace(/<[^>]+>/g, ' ')
        .replace(/[`*_#>\-\[\]\(\)]/g, ' ')
        .replace(/\s+/g, ' ')
        .trim();

    const toTitleCase = (s: string) =>
      s
        .split(' ')
        .filter(Boolean)
        .map(w => (w.length <= 2 ? w.toLowerCase() : w.charAt(0).toUpperCase() + w.slice(1)))
        .join(' ');

    const trimTitle = (s: string, max = 52) => {
      const t = s.replace(/\s+/g, ' ').trim();
      return t.length > max ? `${t.slice(0, max).trim()}…` : t;
    };

    const normalizeQuestionTitle = (text: string): string | null => {
      const q = stripStructured(text).replace(/[?!.]+$/g, '').trim();
      if (!q) return null;

      const lower = q.toLowerCase();
      const laGi = lower.match(/^(.{2,80})\s+là gì$/i);
      if (laGi?.[1]) return trimTitle(`${toTitleCase(laGi[1].trim())} là gì`);

      if (/^so sánh\b/i.test(lower)) return trimTitle(toTitleCase(q));
      if (/\blộ trình\b/i.test(lower)) return trimTitle(toTitleCase(q));
      if (/\bats\b/i.test(lower)) return trimTitle(toTitleCase(q));
      if (/\bcv\b/i.test(lower) && /\btối ưu|sửa|viết|tạo\b/i.test(lower)) return trimTitle(toTitleCase(q));

      // Generic short questions are usually the best title seed
      if (q.length <= 60) return trimTitle(toTitleCase(q));
      return null;
    };

    const pickAssistantSentence = (text: string): string | null => {
      const genericStarts = [
        'chào', 'xin chào', 'hi', 'hello', 'okay', 'ok', 'đây là', 'bạn có thể', 'chúng ta', 'chúng thường'
      ];
      const sentences = stripStructured(text)
        .split(/[.!?\n]/)
        .map(s => s.trim())
        .filter(Boolean);
      const picked = sentences.find(s =>
        s.length >= 14 &&
        s.length <= 70 &&
        !genericStarts.some(g => s.toLowerCase().startsWith(g))
      );
      return picked ? trimTitle(toTitleCase(picked)) : null;
    };

    const cleanedUser = stripStructured(userText);
    const fromUser = normalizeQuestionTitle(cleanedUser);
    if (fromUser) return fromUser;

    const fromAssistant = pickAssistantSentence(assistantText);
    if (fromAssistant) return fromAssistant;

    if (cleanedUser) return trimTitle(toTitleCase(cleanedUser));
    return 'New Conversation';
  };

  const sendMessage = async (messageContent: string) => {
    if (!messageContent.trim() || isLoading) return;
    const loweredMessage = messageContent.toLowerCase();
    if (loweredMessage.includes('bỏ qua') || loweredMessage.includes('để sau')) {
      const until = Date.now() + 10 * 60 * 1000;
      setGuidanceSnoozeUntil(until);
      localStorage.setItem('guidanceSnoozeUntil', String(until));
    }

    let sessionId = currentSessionId;
    let createdNewSession = false;
    if (!sessionId) {
      const res = await chatCrudApi.createSession('New Conversation');
      sessionId = res.data.id;
      createdNewSession = true;
      setCurrentSessionId(sessionId);
      setSessionList(prev => [res.data, ...prev]);
    }

    setMessages(prev => [...prev, { role: 'user', content: messageContent, sources: [] }]);
    setIsLoading(true);
    setUserHasScrolledUp(false); // Reset scroll to bottom when user sends new message

    let isFirstChunk = true;
    try {
      await chatCrudApi.saveMessage(sessionId!, 'user', messageContent);
      
      const buildToolContext = () => {
        if (!artifactType) return undefined;
        const skills = (cvData.skills || []).slice(0, 20);
        const expTitles = (cvData.experience || []).map(e => e.title).filter(Boolean).slice(0, 5);
        const projNames = (cvData.projects || []).map(p => p.name).filter(Boolean).slice(0, 5);
        const summary = [
          `tool=${artifactType}`,
          cvData.personal_info?.full_name ? `name=${cvData.personal_info.full_name}` : '',
          cvData.personal_info?.title ? `current_title=${cvData.personal_info.title}` : '',
          skills.length ? `skills=${skills.join(', ')}` : '',
          expTitles.length ? `experience_titles=${expTitles.join(' | ')}` : '',
          projNames.length ? `projects=${projNames.join(' | ')}` : '',
        ].filter(Boolean).join('\n');
        return summary || undefined;
      };

      const response = artifactType === 'builder'
        ? await chatbotApi.streamCollector(messageContent, sessionId.toString(), currentStep, cvData, userEmail)
        : await chatbotApi.streamChat(
            messageContent,
            sessionId.toString(),
            artifactType,
            userEmail,
            buildToolContext()
          );

      if (!response.body) throw new Error("No response body");
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = "";
      let pendingText = "";
      let flushTimer: number | null = null;
      let streamParseBuffer = "";
      const metadataMarker = "[METADATA]";
      const FLUSH_INTERVAL_MS = 34; // ~29fps for smoother/steadier markdown rendering

      const updateAssistantMessage = (content: string) => {
        setMessages(prev => {
          const newMsgs = [...prev];
          if (newMsgs.length > 0) newMsgs[newMsgs.length - 1].content = content;
          return newMsgs;
        });
      };

      const flushQueue = () => {
        if (pendingText.length === 0) {
          flushTimer = null;
          return;
        }

        // Adaptive chars/tick: keeps cadence steady while catching up on bursty chunks.
        const queueLen = pendingText.length;
        const take =
          queueLen > 3000 ? 280 :
          queueLen > 1500 ? 180 :
          queueLen > 700 ? 110 :
          queueLen > 250 ? 70 : 42;

        const slice = pendingText.slice(0, take);
        pendingText = pendingText.slice(take);
        fullContent += slice;
        updateAssistantMessage(fullContent);
        flushTimer = window.setTimeout(flushQueue, FLUSH_INTERVAL_MS);
      };

      const enqueueText = (text: string) => {
        if (!text) return;
        pendingText += text;
        if (flushTimer === null) {
          flushTimer = window.setTimeout(flushQueue, FLUSH_INTERVAL_MS);
        }
      };

      const tryExtractSafeText = (buf: string): { safe: string; rest: string } => {
        const idx = buf.indexOf(metadataMarker);
        if (idx >= 0) {
          return { safe: buf.slice(0, idx), rest: buf.slice(idx) };
        }

        // Keep possible partial suffix of metadata marker
        let keep = 0;
        const maxPrefix = Math.min(buf.length, metadataMarker.length - 1);
        for (let k = maxPrefix; k > 0; k--) {
          if (metadataMarker.startsWith(buf.slice(-k))) {
            keep = k;
            break;
          }
        }
        return keep > 0
          ? { safe: buf.slice(0, -keep), rest: buf.slice(-keep) }
          : { safe: buf, rest: "" };
      };

      while (true) {
        const { done, value } = await reader.read();
        
        if (done) {
          // Flush remaining parse buffer as text (if any)
          if (streamParseBuffer) {
            enqueueText(streamParseBuffer);
            streamParseBuffer = "";
          }

          // Wait until queue is fully rendered for smooth finish.
          await new Promise<void>((resolve) => {
            const wait = () => {
              if (pendingText.length === 0 && flushTimer === null) resolve();
              else setTimeout(wait, 12);
            };
            wait();
          });

          updateAssistantMessage(fullContent);
          break;
        }

        if (isFirstChunk) {
            setIsLoading(false);
            setIsStreaming(true);
            setMessages(prev => [...prev, { role: 'assistant', content: '', sources: [] }]);
            isFirstChunk = false;
        }

        const chunk = decoder.decode(value, { stream: true });
        streamParseBuffer += chunk;

        // Extract metadata robustly even when marker/json is split across chunks.
        const markerIdx = streamParseBuffer.indexOf(metadataMarker);
        if (markerIdx >= 0) {
          const textPart = streamParseBuffer.slice(0, markerIdx);
          if (textPart) enqueueText(textPart);

          const metadataPart = streamParseBuffer.slice(markerIdx + metadataMarker.length);
          try {
            const metadata = JSON.parse(metadataPart);
            if (metadata.step) setCurrentStep(metadata.step);
            if (metadata.cv_data) setCvData(metadata.cv_data);
            streamParseBuffer = "";
          } catch {
            // Incomplete metadata JSON, keep buffer until next chunk.
          }
        } else {
          const { safe, rest } = tryExtractSafeText(streamParseBuffer);
          if (safe) enqueueText(safe);
          streamParseBuffer = rest;
        }
      }

      if (flushTimer !== null) {
        window.clearTimeout(flushTimer);
        flushTimer = null;
      }

      setIsStreaming(false);
      await chatCrudApi.saveMessage(sessionId!, 'assistant', fullContent);

      // Auto title from first exchange context (not just first user sentence)
      if (createdNewSession) {
        const fallbackTitle = inferSessionTitle(messageContent, fullContent);
        let smartTitle = fallbackTitle;
        try {
          const titleRes = await chatbotApi.generateTitle({
            user_message: messageContent,
            assistant_message: fullContent,
            active_tool: artifactType,
            user_id: userEmail || undefined,
            tool_context: buildToolContext() || undefined
          });
          smartTitle = (titleRes.data?.title || '').trim() || fallbackTitle;
        } catch {
          smartTitle = fallbackTitle;
        }
        try {
          await chatCrudApi.updateTitle(sessionId!, smartTitle);
          setSessionList(prev => prev.map(s => s.id === sessionId ? { ...s, title: smartTitle } : s));
        } catch {
          // Non-blocking; fallback title remains.
        }
      }

      // US-28: Next-step suggestion after tool results
      if (artifactType === 'match') {
        const lc = fullContent.toLowerCase();
        if (lc.includes('thiếu') || lc.includes('missing') || lc.includes('gap')) {
          setMessages(prev => [
            ...prev,
            {
              role: 'assistant',
              content:
                'Bạn đã có kết quả Skill Match. Bước tiếp theo phù hợp:\n' +
                '[TOOL_CTA:career|🗺️ Dự đoán Career Path]\n' +
                '[TOOL_CTA:market|📈 Xem nhu cầu thị trường]\n' +
                '[TOOL_CHECKLIST:career|Xác nhận vai trò hiện tại ; Chọn vai trò mục tiêu ; Xem roadmap và mốc thời gian]',
              sources: []
            }
          ]);
        }
      }
      if (artifactType === 'upload') {
        const lc = fullContent.toLowerCase();
        if (lc.includes('upload') || lc.includes('trích xuất') || lc.includes('parsed')) {
          setMessages(prev => [
            ...prev,
            {
              role: 'assistant',
              content:
                'Upload xong rồi. Bước tiếp theo bạn có thể:\n' +
                '[TOOL_CTA:ats|📊 Chấm điểm ATS]\n' +
                '[TOOL_CTA:match|🎯 So sánh Skill Gap]\n' +
                '[TOOL_CHECKLIST:ats|Dán JD phù hợp ; Chạy chấm điểm ; Ưu tiên sửa mục điểm thấp]',
              sources: []
            }
          ]);
        }
      }
      if (artifactType === 'jd') {
        const lc = fullContent.toLowerCase();
        if (lc.includes('jd') || lc.includes('yêu cầu') || lc.includes('requirement')) {
          setMessages(prev => [
            ...prev,
            {
              role: 'assistant',
              content:
                'Đã phân tích JD. Bạn muốn đi bước nào tiếp theo?\n' +
                '[TOOL_CTA:match|🎯 Mở Skill Match]\n' +
                '[TOOL_CTA:ats|📊 Mở ATS Score]\n' +
                '[TOOL_CHECKLIST:match|Xác nhận CV hiện tại ; Chọn vị trí mục tiêu ; Chạy phân tích thiếu kỹ năng]',
              sources: []
            }
          ]);
        }
      }

      // Auto-open builder only for clear CV-builder intents
      if (artifactType !== 'builder') {
        const content = fullContent.toLowerCase();
        const shouldOpenBuilder =
          (content.includes('cv builder') || content.includes('ai builder') || content.includes('tạo cv')) &&
          !content.includes('lộ trình') &&
          !content.includes('career path') &&
          !content.includes('skill match');

        if (shouldOpenBuilder) {
            setArtifactType('builder');
            setIsArtifactOpen(true);
        }
      }

    } catch (error) {
      console.error("Chat error:", error);
      setIsStreaming(false);

      const errorMessage = 'Đã có lỗi xảy ra hoặc chatbot đang ngoại tuyến. Vui lòng thử lại sau.';
      
      if (isFirstChunk) {
        // We haven't even started writing the assistant message yet
        setMessages(prev => [...prev, { role: 'assistant', content: errorMessage, sources: [] }]);
      } else {
        // We were in the middle of streaming, update the existing message
        setMessages(prev => {
          const newMsgs = [...prev];
          newMsgs[newMsgs.length - 1].content += `\n\n[Error: ${errorMessage}]`;
          return newMsgs;
        });
      }
    }
    setIsLoading(false);
  };

  const handleEditMessage = async (index: number, newContent: string) => {
    // Keep messages up to (not including) the edited user message, then re-send
    setMessages(prev => prev.slice(0, index));
    await sendMessage(newContent);
  };

  const openArtifact = (type: string) => {
    setArtifactType(type as any);
    setIsArtifactOpen(true);
    if (type === 'builder' && messages.length === 0) {
        sendMessage("Bắt đầu tạo CV");
    }
  };

  const MAX_RENDERED_MESSAGES = 80;
  const visibleMessages = useMemo(() => {
    if (showAllMessages || isStreaming || messages.length <= MAX_RENDERED_MESSAGES) return messages;
    return messages.slice(-MAX_RENDERED_MESSAGES);
  }, [messages, showAllMessages, isStreaming]);
  const visibleOffset = messages.length - visibleMessages.length;
  const hiddenMessageCount = Math.max(0, visibleOffset);

  const handleMessageOpenTool = (tool: string) => {
    const mapped = tool === 'skill_match' ? 'match' : tool;
    openArtifact(mapped);
  };

  const handleQuickAction = (action: string) => {
    if (action === 'help') {
      const current = artifactType || 'tool hiện tại';
      sendMessage(`Mình đang bị kẹt khi dùng ${current}, bạn hướng dẫn từng bước giúp mình nhé.`);
      return;
    }
    if (action === 'snooze') {
      const until = Date.now() + 10 * 60 * 1000;
      setGuidanceSnoozeUntil(until);
      localStorage.setItem('guidanceSnoozeUntil', String(until));
      setMessages(prev => [...prev, { role: 'assistant', content: 'Ok, mình sẽ không nhắc lại trong 10 phút.', sources: [] }]);
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-canvas font-sans text-text-primary transition-all duration-500 overflow-y-auto">
        <div className="w-full flex justify-center py-10">
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-1000">
            {authView === 'login' ? (
              <Login onLoginSuccess={handleAuthSuccess} onSwitchToRegister={() => setAuthView('register')} onSwitchToForgotPassword={() => setAuthView('forgot-password')} />
            ) : authView === 'register' ? (
              <Register onRegisterSuccess={handleAuthSuccess} onSwitchToLogin={() => setAuthView('login')} />
            ) : (
              <ForgotPassword onBackToLogin={() => setAuthView('login')} />
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-canvas text-text-primary overflow-hidden font-sans transition-colors duration-500">
      {/* Fixed cursor spotlight - follows mouse globally */}
      <div
        className="fixed pointer-events-none z-[1]"
        style={{
          width: 700,
          height: 700,
          borderRadius: '50%',
          background: `radial-gradient(circle, rgba(var(--accent-primary), 0.12) 0%, transparent 65%)`,
          transform: 'translate(-50%, -50%)',
          left: cursorPos.x,
          top: cursorPos.y,
          transition: 'left 0.12s ease-out, top 0.12s ease-out',
        }}
      />
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onNewChat={createNewChat}
        sessions={sessionList}
        currentSessionId={currentSessionId}
        onSelectSession={selectSession}
        onDeleteSession={deleteChat}
        onStartEditing={startEditing}
        onSaveTitle={saveTitle}
        editingSessionId={editingSessionId}
        tempTitle={tempTitle}
        setTempTitle={setTempTitle}
        theme={theme}
        onThemeToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        userName={userName}
        userRole={userRole}
        onLogout={handleLogout}
        onOpenSettings={() => setIsSettingsOpen(true)}
        onSearchToggle={() => setIsSearchMode(!isSearchMode)}
        onOpenProfile={() => {
          setIsMemoryPanelOpen(false);
          setIsProfileOpen(true);
        }}
        onOpenCvList={() => {
          setIsMemoryPanelOpen(false);
          setIsCvListOpen(true);
        }}
        onOpenMemory={() => {
          setIsProfileOpen(false);
          setIsCvListOpen(false);
          setIsMemoryPanelOpen(true);
        }}
        onOpenMarket={() => openArtifact('market')}
        onOpenAdmin={() => {
            navigate('/admin');
        }}
      />


      <main
        ref={mainRef}
        className="flex-1 min-w-0 flex flex-col relative overflow-hidden bg-canvas transition-all duration-300"
      >
        <Routes>
          <Route 
            path="/admin" 
            element={userRole === 'Admin' ? <AdminPortal userName={userName} /> : <Navigate to="/" replace />} 
          />
          <Route path="/" element={
            <div className="flex-1 flex flex-col overflow-hidden relative">
              {/* Full-screen ambient blobs */}
              <div className="absolute top-0 right-0 w-[700px] h-[700px] bg-accent-primary/15 rounded-full blur-[160px] pointer-events-none z-0" />
              <div className="absolute bottom-0 left-0 w-[700px] h-[700px] bg-accent-secondary/15 rounded-full blur-[160px] pointer-events-none z-0" />
              <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_50%,rgba(var(--accent-primary),0.09)_0%,transparent_100%)] pointer-events-none z-0" />
              {/* Cursor spotlight */}
              <div
                className="absolute pointer-events-none z-0 transition-opacity duration-300"
                style={{
                  width: 600,
                  height: 600,
                  borderRadius: '50%',
                  background: `radial-gradient(circle, rgba(var(--accent-primary), 0.1) 0%, transparent 70%)`,
                  transform: 'translate(-50%, -50%)',
                  left: cursorPos.x,
                  top: cursorPos.y,
                  opacity: cursorPos.x < 0 ? 0 : 1,
                }}
              />

              <header className="h-16 flex items-center justify-between px-8 z-20 transition-all bg-canvas/80 backdrop-blur-md sticky top-0">
                <div className="w-32 flex items-center gap-3">
                    <span className="font-bold text-xl tracking-tight font-outfit truncate">{t('sidebar.assistant')}</span>
                </div>

                <div className="flex-1 flex items-center justify-center px-4 min-w-0">
                    {messages.length > 0 && currentSessionId && (
                        <p className="text-[14px] font-medium text-text-secondary truncate max-w-sm animate-in fade-in duration-300">
                            {sessionList.find(s => s.id === currentSessionId)?.title || ''}
                        </p>
                    )}
                </div>

                <div className="flex items-center justify-end gap-3 min-w-[200px]">
                    <LanguageSwitcher />
                    {isArtifactOpen && (
                        <button
                            onClick={() => setIsArtifactOpen(false)}
                            className="group flex items-center gap-2 px-4 h-9 rounded-xl bg-accent-primary/10 border border-accent-primary/20 text-accent-primary hover:bg-accent-primary hover:text-white transition-all shadow-sm hover:shadow-lg hover:shadow-accent-primary/30 active:scale-95"
                        >
                            <LayoutIcon className="w-3.5 h-3.5 transition-transform group-hover:rotate-12" />
                            <span className="text-[10px] font-black uppercase tracking-widest">{t('common.full_chat')}</span>
                        </button>
                    )}
                </div>
              </header>

              <div 
                className="flex-1 overflow-y-auto chat-scroll scroll-smooth relative z-10"
                onScroll={handleScroll}
              >
                {isSearchMode ? (
                    <SearchView
                        sessions={sessionList}
                        onSelectSession={selectSession}
                        onClose={() => setIsSearchMode(false)}
                    />
                ) : (messages.length === 0 && !loadingMessages) ? (
                    <div className="h-full flex flex-col items-center justify-center px-10 animate-in fade-in zoom-in-95 duration-1000 max-w-5xl mx-auto w-full">
                        <h1 className="text-5xl font-bold text-center mb-3 tracking-tight font-outfit">
                            Hi <span className="text-accent-primary">{userName.split(' ')[0]}</span>.
                        </h1>
                        <p className="text-4xl font-medium text-center text-text-secondary/50 font-outfit">
                            Where should we start?
                        </p>
                    </div>
                ) : (
                    <div className="chat-stream-width px-6 pt-8 pb-4 space-y-2">
                        {loadingMessages && (
                            <div className="flex flex-col items-center justify-center py-40 opacity-15 gap-8">
                            <Cpu className="w-20 h-20 text-accent-primary animate-pulse" />
                            <p className="text-sm font-black uppercase tracking-[0.5em]">Syncing Expert Neural Context</p>
                            </div>
                        )}
                        {!loadingMessages && (() => {
                            const lastUserIdx = messages.reduce((acc, m, i) => m.role === 'user' ? i : acc, -1);
                            return (
                              <>
                                {hiddenMessageCount > 0 && (
                                  <div className="mb-3">
                                    <button
                                      onClick={() => setShowAllMessages(true)}
                                      className="px-3 py-1.5 rounded-lg bg-surface/60 hover:bg-surface-hover text-xs text-text-secondary border border-white/10"
                                    >
                                      Hiển thị {hiddenMessageCount} tin nhắn cũ hơn
                                    </button>
                                  </div>
                                )}
                                {showAllMessages && messages.length > MAX_RENDERED_MESSAGES && (
                                  <div className="mb-3">
                                    <button
                                      onClick={() => setShowAllMessages(false)}
                                      className="px-3 py-1.5 rounded-lg bg-surface/60 hover:bg-surface-hover text-xs text-text-secondary border border-white/10"
                                    >
                                      Thu gọn lịch sử
                                    </button>
                                  </div>
                                )}
                                {visibleMessages.map((m, localIdx) => {
                                  const i = visibleOffset + localIdx;
                                  return (
                                <div id={`message-${i}`} key={i}>
                                    <MessageItem
                                        role={m.role}
                                        content={m.content}
                                        sources={m.sources}
                                        isPersonalized={m.role === 'assistant' ? hasPersonalizedMemory : undefined}
                                        onEdit={m.role === 'user' && i === lastUserIdx ? (newContent) => handleEditMessage(i, newContent) : undefined}
                                        onOpenTool={handleMessageOpenTool}
                                        onQuickAction={handleQuickAction}
                                        onShowFeedback={() => {
                                            setFeedbackItemId(currentSessionId?.toString());
                                            setIsFeedbackModalOpen(true);
                                        }}
                                        onSentiment={(s) => {
                                            console.log(`User feedback: ${s} for message ${i}`);
                                        }}
                                        isStreaming={isStreaming && i === messages.length - 1}
                                    />
                                </div>
                                  );
                                })}
                              </>
                            );
                        })()}
                        {isLoading && (
                            <div className="flex gap-4 sm:gap-6 pt-4 animate-in fade-in duration-500">
                                <div className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/25 animate-ai-thinking">
                                    <Sparkles className="w-4 h-4 fill-current" />
                                </div>
                                <div className="flex-1 space-y-3 pt-3 opacity-20">
                                    <div className="h-2 bg-text-primary rounded-full w-[90%]"></div>
                                    <div className="h-2 bg-text-primary rounded-full w-[70%]"></div>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                )}
              </div>

              {!isSearchMode && !isStreaming && visibleMessages.length >= 5 && (
                  <ChatTOC messages={visibleMessages} />
              )}

              {!isSearchMode && (
                  <div className="relative z-20 px-6 pb-8 pt-2">
                      <PromptBar
                          isLoading={isLoading}
                          onSend={sendMessage}
                          showChips={(messages.length === 0 && !loadingMessages)}
                          onModeSelect={openArtifact}
                          activeTool={isArtifactOpen ? artifactType : null}
                      />
                  </div>
              )}
            </div>
          } />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <ArtifactPanel 
        isOpen={isArtifactOpen}
        onClose={() => setIsArtifactOpen(false)}
        type={artifactType}
        sessionId={currentSessionId}
        cvData={cvData}
        currentStep={currentStep}
        onUpdateCvData={setCvData}
        onUpdateStep={setCurrentStep}
      />

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        theme={theme}
        onThemeToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        userName={userName}
        defaultTab="general"
      />

      {isProfileOpen && (
        <ProfilePage
          onClose={() => setIsProfileOpen(false)}
          onLogout={handleLogout}
          onProfileUpdated={({ name, language, email }) => {
            if (name) {
              setUserName(name);
              localStorage.setItem('userName', name);
            }
            if (email) {
              setUserEmail(email);
              localStorage.setItem('userEmail', email);
            }
            if (language) {
              i18n.changeLanguage(language);
            }
          }}
        />
      )}

      {isMemoryPanelOpen && userEmail && (
        <UserMemoryPanel
          userId={userEmail}
          userName={userName}
          onProfileSynced={({ name, language, email }) => {
            if (name) {
              setUserName(name);
              localStorage.setItem('userName', name);
            }
            if (email) {
              setUserEmail(email);
              localStorage.setItem('userEmail', email);
            }
            if (language) {
              i18n.changeLanguage(language);
            }
          }}
          onClose={() => setIsMemoryPanelOpen(false)}
        />
      )}

      <FeedbackModal 
        isOpen={isFeedbackModalOpen}
        onClose={() => setIsFeedbackModalOpen(false)}
        itemId={feedbackItemId}
      />

      {isCvListOpen && (
        <CVListPage 
          onClose={() => setIsCvListOpen(false)} 
          onSelect={async (doc, dataJson) => {
            try {
              const data = JSON.parse(dataJson);
              
              // 1. Ensure we have a session ID
              let sessionId = currentSessionId;
              if (!sessionId) {
                const res = await chatCrudApi.createSession(`Edit: ${doc.name}`);
                sessionId = res.data.id;
                setCurrentSessionId(sessionId);
                setSessionList(prev => [res.data, ...prev]);
              }

              // 2. Helper to ensure description is always a string array (prevents .map() crashes)
              const parseDesc = (desc: any): string[] => {
                if (Array.isArray(desc)) return desc;
                if (typeof desc === 'string') {
                  return desc.split('\n')
                    .map(l => l.trim().replace(/^[-•*◦]\s*/, ''))
                    .filter(Boolean);
                }
                return [];
              };

              // 3. Robust Mapping from ParseResult structure to CVData structure
              const mappedData: CVData = {
                personal_info: {
                  full_name: data.personal_info?.full_name || data.personal_info?.name || '',
                  email: data.personal_info?.email || '',
                  phone: data.personal_info?.phone || '',
                  location: data.personal_info?.location || '',
                  title: data.personal_info?.title || ''
                },
                education: (data.education || []).map((e: any) => ({
                  school: e.school || e.anchor || 'University',
                  degree: e.degree || (e.entities?.find((ent: any) => ent.type === 'DEGREE')?.text) || '',
                  major: e.major || (e.entities?.find((ent: any) => ent.type === 'MAJOR')?.text) || '',
                  start_date: e.start_date || (e.entities?.find((ent: any) => ent.type === 'DATE')?.text) || '',
                  end_date: e.end_date || '',
                  description: parseDesc(e.description)
                })),
                experience: (data.experience || []).map((e: any) => ({
                  company: e.company || e.anchor || 'Company',
                  position: e.position || (e.entities?.find((ent: any) => ent.type === 'JOB_TITLE')?.text) || '',
                  start_date: e.start_date || (e.entities?.find((ent: any) => ent.type === 'DATE')?.text) || '',
                  end_date: e.end_date || '',
                  description: parseDesc(e.description)
                })),
                skills: Array.isArray(data.skills) 
                  ? data.skills 
                  : Object.values(data.skills || {}).flat() as string[],
                projects: (data.projects || []).map((p: any) => ({
                  name: p.name || p.anchor || 'Project',
                  description: parseDesc(p.description),
                  technologies: p.technologies || (p.entities?.filter((ent: any) => ent.type === 'SKILL').map((ent: any) => ent.text)) || []
                })),
                certifications: (data.certifications || []).map((c: any) => ({
                  name: c.name || c.anchor || 'Certification',
                  organization: c.organization || (c.entities?.find((ent: any) => ent.type === 'ORG')?.text) || '',
                  issue_date: c.issue_date || (c.entities?.find((ent: any) => ent.type === 'DATE')?.text) || ''
                }))
              };
              
              // 4. Initialize State
              setCvData(mappedData);
              setCurrentStep(7); // Jump to Preview/Editor mode
              setArtifactType('builder');
              setIsArtifactOpen(true);
              setIsCvListOpen(false);

              // 5. Sync Progress
              await collectorApi.updateProgress(sessionId, 7, JSON.stringify(mappedData), true);
              
            } catch (e) {
              console.error("Failed to open CV document", e);
            }
          }}
        />
      )}
    </div>
  );
}
