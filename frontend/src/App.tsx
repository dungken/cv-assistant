import { useState, useEffect, useRef } from 'react'
import {
  Sparkles,
  ChevronDown,
  Settings as SettingsIcon,
  PanelLeftOpen,
  Cpu
} from 'lucide-react';
import { chatbotApi, chatCrudApi, Source, Session } from './services/api';
import Login from './components/auth/Login';
import Register from './components/auth/Register';
import SettingsModal from './components/common/SettingsModal';
import Sidebar from './components/layout/Sidebar';
import MessageItem from './components/chat/MessageItem';
import PromptBar from './components/chat/PromptBar';
import CVUpload from './components/features/CVUpload';
import SkillMatch from './components/features/SkillMatch';
import CareerPath from './components/features/CareerPath';
import { cn } from './lib/utils';

export default function App() {
  const [messages, setMessages] = useState<{ role: 'user' | 'assistant', content: string, sources?: Source[] }[]>([]);
  const [input, setInput] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null);
  const [sessionList, setSessionList] = useState<Session[]>([]);
  const [isConnected, setIsConnected] = useState<boolean>(false);

  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!localStorage.getItem('token'));
  const [authView, setAuthView] = useState<'login' | 'register'>('login');
  const [userName, setUserName] = useState<string>(localStorage.getItem('userName') || '');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [theme, setTheme] = useState<'dark' | 'light'>((localStorage.getItem('theme') as 'dark' | 'light') || 'dark');
  const [activeTab, setActiveTab] = useState<'chat' | 'upload' | 'match' | 'career'>('chat');

  const [editingSessionId, setEditingSessionId] = useState<number | null>(null);
  const [tempTitle, setTempTitle] = useState('');
  const [loadingMessages, setLoadingMessages] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement | null>(null);

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

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
  };

  const selectSession = async (id: number) => {
    setCurrentSessionId(id);
    setLoadingMessages(true);
    try {
      const res = await chatCrudApi.getMessages(id);
      setMessages(res.data.map(m => ({ role: m.role as any, content: m.content, sources: [] })));
    } catch (error) {
      console.error('Failed to load messages');
    }
    setLoadingMessages(false);
  };

  const deleteChat = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    if (!window.confirm('Delete this neural session permanently?')) return;
    try {
      await chatCrudApi.deleteSession(id);
      setSessionList(prev => prev.filter(s => s.id !== id));
      if (currentSessionId === id) createNewChat();
    } catch (error) {
      console.error('Failed to delete');
    }
  };

  const startEditing = (e: React.MouseEvent, s: Session) => {
    e.stopPropagation();
    setEditingSessionId(s.id);
    setTempTitle(s.title);
  };

  const saveTitle = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation();
    try {
      await chatCrudApi.updateTitle(id, tempTitle);
      setSessionList(prev => prev.map(s => s.id === id ? { ...s, title: tempTitle } : s));
      setEditingSessionId(null);
    } catch (error) {
      setEditingSessionId(null);
    }
  };

  const handleAuthSuccess = (token: string, name: string) => {
    localStorage.setItem('token', token);
    localStorage.setItem('userName', name);
    setIsAuthenticated(true);
    setUserName(name);
  };

  const handleLogout = () => {
    // We remove native confirm to ensure it works for the user.
    // A custom modal can be added later if needed.
    localStorage.removeItem('token');
    localStorage.removeItem('userName');
    setIsAuthenticated(false);
    setMessages([]);
    setCurrentSessionId(null);
  };

  const sendMessage = async (overrideInput?: string) => {
    const textToSend = overrideInput || input;
    if (!textToSend.trim() || isLoading) return;

    let sessionId = currentSessionId;
    if (!sessionId) {
      const res = await chatCrudApi.createSession(textToSend.slice(0, 24));
      sessionId = res.data.id;
      setCurrentSessionId(sessionId);
      setSessionList(prev => [res.data, ...prev]);
    }

    setMessages(prev => [...prev, { role: 'user', content: textToSend, sources: [] }]);
    setInput('');
    setIsLoading(true);

    try {
      await chatCrudApi.saveMessage(sessionId!, 'user', textToSend);
      const res = await chatbotApi.chat(textToSend, sessionId.toString());
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response, sources: res.data.sources || [] }]);
      await chatCrudApi.saveMessage(sessionId!, 'assistant', res.data.response);
    } catch (error) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Connection Error. Please check AI backend.', sources: [] }]);
    }
    setIsLoading(false);
  };

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-canvas font-sans text-text-primary transition-all duration-500 overflow-y-auto">
        <div className="w-full flex justify-center py-10">
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-1000">
            {authView === 'login' ? (
              <Login onLoginSuccess={handleAuthSuccess} onSwitchToRegister={() => setAuthView('register')} />
            ) : (
              <Register onRegisterSuccess={handleAuthSuccess} onSwitchToLogin={() => setAuthView('login')} />
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-screen bg-canvas text-text-primary overflow-hidden font-sans transition-colors duration-500">
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
        onLogout={handleLogout}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      <main className="flex-1 flex flex-col relative overflow-hidden bg-canvas">
        <header className="h-20 flex items-center justify-between px-8 z-20 transition-all border-b border-border-main/5 bg-secondary/20 backdrop-blur-sm">
          <div className="flex items-center gap-6">
            {!isSidebarOpen && (
              <button onClick={() => setIsSidebarOpen(true)} className="p-2.5 glass-panel rounded-xl hover:scale-105 active:scale-95 shadow-md">
                <PanelLeftOpen className="w-5 h-5 text-text-muted transition-colors hover:text-accent-primary" />
              </button>
            )}
            <div className="flex items-center gap-2 font-black text-2xl tracking-tighter cursor-default group">
              CV Assistant
              <ChevronDown className="w-5 h-5 opacity-10 group-hover:opacity-100 transition-opacity" />
            </div>
          </div>

          <div className="hidden md:flex items-center bg-surface/80 rounded-full p-1 border border-border-main/20">
            {['chat', 'upload', 'match', 'career'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab as any)}
                className={cn(
                  "px-6 py-2 rounded-full text-sm font-bold transition-all",
                  activeTab === tab ? "bg-accent-primary text-white shadow-md relative group" : "text-text-secondary hover:text-text-primary hover:bg-overlay"
                )}
              >
                {tab === 'chat' ? 'Neural Chat' : tab === 'upload' ? 'Data Ingestion' : tab === 'match' ? 'Skill Matrix' : 'Career Paths'}
                {activeTab === tab && <div className="absolute inset-x-0 -bottom-1 h-0.5 bg-accent-primary mx-4 rounded-full" />}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-5">
            <div className="hidden sm:flex items-center gap-3 px-5 py-2 rounded-full border border-border-main bg-surface shadow-sm hover:border-accent-primary/20 transition-all">
              <div className={cn("w-2 h-2 rounded-full", isConnected ? "bg-emerald-500 shadow-[0_0_10px_rgba(16,185,129,0.5)]" : "bg-rose-500 animate-pulse shadow-[0_0_10px_rgba(244,63,94,0.5)]")} />
              <span className="text-[10px] font-black tracking-[0.3em] opacity-40 uppercase">
                {isConnected ? 'Neural Active' : 'Neural Loss'}
              </span>
            </div>
            <div onClick={() => setIsSettingsOpen(true)} className="p-2.5 hover:bg-overlay rounded-full cursor-pointer transition-all hover:scale-110 active:scale-90">
              <SettingsIcon className="w-5 h-5 text-text-secondary" />
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto no-scrollbar scroll-smooth">
          {activeTab === 'upload' && <CVUpload />}
          {activeTab === 'match' && <SkillMatch />}
          {activeTab === 'career' && <CareerPath />}

          {activeTab === 'chat' && (
            <>
              {(messages.length === 0 && !loadingMessages) ? (
                <div className="h-full flex flex-col items-center justify-center px-10 animate-in fade-in zoom-in-95 duration-1000 max-w-5xl mx-auto">
                  <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-accent-primary/5 rounded-full blur-[120px] pointer-events-none" />
                  <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-accent-secondary/5 rounded-full blur-[120px] pointer-events-none" />
                  
                  <h1 className="text-6xl font-black text-center mb-16 tracking-tight leading-tight z-10">
                    Welcome back, {userName.split(' ')[0]}. <br />
                    <span className="text-text-secondary/30 font-serif italic font-light">Optimize your career trajectory.</span>
                  </h1>

                  <PromptBar
                    input={input}
                    setInput={setInput}
                    isLoading={isLoading}
                    onSend={sendMessage}
                    onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                    showChips={true}
                  />
                </div>
              ) : (
                <div className="chat-stream-width px-6 py-12 space-y-20">
                  {loadingMessages && (
                    <div className="flex flex-col items-center justify-center py-40 opacity-15 gap-8">
                      <Cpu className="w-20 h-20 text-accent-primary animate-pulse" />
                      <p className="text-sm font-black uppercase tracking-[0.5em]">Syncing Expert Neural Context</p>
                    </div>
                  )}
                  {!loadingMessages && messages.map((m, i) => (
                    <MessageItem key={i} role={m.role} content={m.content} sources={m.sources} />
                  ))}
                  {isLoading && (
                    <div className="flex gap-10 animate-pulse opacity-30">
                      <div className="w-8 h-8 rounded-full bg-overlay"></div>
                      <div className="flex-1 space-y-5 pt-2">
                        <div className="h-2 bg-overlay rounded-full w-[95%]"></div>
                        <div className="h-2 bg-overlay rounded-full w-[80%]"></div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} className="h-48" />
                </div>
              )}
            </>
          )}
        </div>

        {activeTab === 'chat' && (messages.length > 0 || loadingMessages) && (
          <div className="px-6 py-8">
            <PromptBar
              input={input}
              setInput={setInput}
              isLoading={isLoading}
              onSend={sendMessage}
              onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
              showChips={false}
            />
          </div>
        )}
      </main>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        theme={theme}
        onThemeToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        userName={userName}
      />
    </div>
  );
}

