'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  LayoutDashboard, BookOpen, FileText, Code2, Video, MessageSquare,
  Settings, Bell, Award, Flame, LogOut, ChevronRight, CheckCircle,
  Upload, Play, Cpu, VideoOff, Mic, Send, Lock, Mail, User, Plus,
  Sparkles, Clock, ExternalLink, AlertCircle, RefreshCw, ShieldAlert, Loader2,
  Download, Copy, X, Briefcase, GraduationCap, Globe, Check, Phone, Linkedin, Github,
  Search, HelpCircle, CheckCircle2, Terminal, SlidersHorizontal, History, Save, RotateCcw,
  Maximize2, ChevronDown, ChevronUp, Bug, Lightbulb, TrendingUp, Target, Activity, Zap, Compass, ArrowUpRight,
  Volume2, VolumeX, MicOff, PhoneOff, Subtitles, Sun, Moon, Youtube, PlayCircle, Pause, SkipForward, SkipBack, Wand2
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import MonacoCodeEditor from './MonacoCodeEditor';
import GapXLogo from './GapXLogo';
import ConceptPlayer from './ConceptPlayer';
import { startFaceAnalysis, FaceMetrics } from './faceAnalysis';
import {
  ResponsiveContainer, BarChart, Bar, Cell,
  PieChart, Pie, AreaChart, Area, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';

const BACKEND_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000') + '/api/v1';
const INITIAL_PROBLEMS: any[] = [];

const INTERVIEW_TRACKS = [
  { id: 'frontend', label: 'Frontend Engineer', icon: '🎨', sub: 'HTML/CSS, JS, React, performance' },
  { id: 'backend', label: 'Backend Engineer', icon: '🛠️', sub: 'APIs, databases, caching, scale' },
  { id: 'fullstack', label: 'Full Stack Engineer', icon: '🌐', sub: 'Web end to end, CORS, deploy' },
  { id: 'sde', label: 'Software Engineer (SDE)', icon: '🧩', sub: 'DSA, OOP, OS, DBMS' },
  { id: 'data_science', label: 'Data Scientist', icon: '📊', sub: 'Stats, ML, experiments' },
  { id: 'ml', label: 'AI / ML Engineer', icon: '🤖', sub: 'Deep learning, LLMs, RAG' },
  { id: 'devops', label: 'DevOps / Cloud', icon: '☁️', sub: 'CI/CD, Docker, Kubernetes' },
  { id: 'mobile', label: 'Mobile Developer', icon: '📱', sub: 'Android, iOS, Flutter' },
  { id: 'data_analyst', label: 'Data Analyst', icon: '📈', sub: 'SQL, BI, metrics' },
  { id: 'security', label: 'Cybersecurity', icon: '🛡️', sub: 'OWASP, crypto, IR' },
];

type AppState = 'splash' | 'auth' | 'onboarding' | 'dashboard';
type AuthMode = 'login' | 'register';
type SidebarTab = 'overview' | 'roadmap' | 'resume' | 'coding' | 'interview' | 'mentor' | 'admin' | 'profile';

interface Message { role: string; text: string; }
interface UserProfile {
  id: number; email: string; full_name: string; role: string;
  education: string; semester: string; skills: string[];
  languages_known: string[]; experience_level: string;
  preferred_learning_hours: number; expected_placement_date: string;
  target_roles: string[]; xp: number; level: number; streak: number;
  badges: string[]; created_at: string;
}
function safeArray(val: any): any[] {
  if (!val) return [];
  if (Array.isArray(val)) return val;
  if (typeof val === 'string') {
    const trimmed = val.trim();
    if (!trimmed) return [];
    if (trimmed.includes('\n')) return trimmed.split('\n').map(s => s.trim()).filter(Boolean);
    if (trimmed.includes(';')) return trimmed.split(';').map(s => s.trim()).filter(Boolean);
    return [trimmed];
  }
  if (typeof val === 'object') return [val];
  return [];
}

function renderInlineMarkdown(text: string) {
  const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);
  return parts.map((chunk, i) => {
    if (chunk.startsWith('**') && chunk.endsWith('**')) {
      return <strong key={i} className="font-semibold text-white">{chunk.slice(2, -2)}</strong>;
    }
    if (chunk.startsWith('`') && chunk.endsWith('`')) {
      return <code key={i} className="bg-zinc-800 text-indigo-300 px-1.5 py-0.5 rounded font-mono text-[11px]">{chunk.slice(1, -1)}</code>;
    }
    return chunk;
  });
}

function MarkdownChatBubble({ text }: { text: string }) {
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  const copyCode = (code: string, idx: number) => {
    navigator.clipboard.writeText(code);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  const parts = text.split(/(```[\s\S]*?```)/g);

  return (
    <div className="space-y-2 text-xs leading-relaxed">
      {parts.map((part, idx) => {
        if (part.startsWith('```') && part.endsWith('```')) {
          const match = part.match(/^```([a-zA-Z0-9_-]*)\n([\s\S]*?)```$/);
          const lang = match ? match[1] || 'code' : 'code';
          const code = match ? match[2] : part.slice(3, -3);

          return (
            <div key={idx} className="my-2 rounded-xl overflow-hidden border border-zinc-700/80 bg-zinc-950/90 shadow-md">
              <div className="flex items-center justify-between px-3 py-1.5 bg-zinc-800/80 border-b border-zinc-700/70 text-[10px] text-zinc-300 font-mono">
                <span className="uppercase font-bold text-indigo-400">{lang}</span>
                <button
                  type="button"
                  onClick={() => copyCode(code.trim(), idx)}
                  className="flex items-center gap-1 hover:text-white px-2 py-0.5 rounded bg-zinc-700/50 hover:bg-zinc-700 transition-colors cursor-pointer"
                >
                  {copiedIdx === idx ? (
                    <>
                      <Check className="w-3 h-3 text-green-400" />
                      <span className="text-green-400">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3 h-3" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
              <pre className="p-3 text-[11px] font-mono text-zinc-200 overflow-x-auto whitespace-pre leading-relaxed">
                <code>{code.trim()}</code>
              </pre>
            </div>
          );
        }

        const lines = part.split('\n');
        return (
          <div key={idx} className="space-y-1">
            {lines.map((line, lIdx) => {
              const trimmed = line.trim();
              if (!trimmed) return <div key={lIdx} className="h-0.5" />;

              if (trimmed.startsWith('### ')) {
                return <h3 key={lIdx} className="text-sm font-bold text-white mt-2 mb-1">{renderInlineMarkdown(trimmed.slice(4))}</h3>;
              }
              if (trimmed.startsWith('#### ')) {
                return <h4 key={lIdx} className="text-xs font-bold text-indigo-300 mt-1.5 mb-0.5">{renderInlineMarkdown(trimmed.slice(5))}</h4>;
              }
              if (trimmed.startsWith('- ') || trimmed.startsWith('* ') || trimmed.startsWith('• ')) {
                return (
                  <div key={lIdx} className="flex items-start gap-1.5 text-zinc-300 pl-1">
                    <span className="text-indigo-400 font-bold">•</span>
                    <span>{renderInlineMarkdown(trimmed.replace(/^[-*•]\s+/, ''))}</span>
                  </div>
                );
              }
              if (/^\d+\.\s+/.test(trimmed)) {
                const num = trimmed.match(/^(\d+\.)\s+/)?.[1] || '1.';
                const content = trimmed.replace(/^\d+\.\s+/, '');
                return (
                  <div key={lIdx} className="flex items-start gap-1.5 text-zinc-300 pl-1">
                    <span className="text-indigo-400 font-bold">{num}</span>
                    <span>{renderInlineMarkdown(content)}</span>
                  </div>
                );
              }
              return <p key={lIdx} className="text-zinc-200">{renderInlineMarkdown(trimmed)}</p>;
            })}
          </div>
        );
      })}
    </div>
  );
}

export default function GapXApp() {
  const [appState, setAppState] = useState<AppState>('splash');
  const [authMode, setAuthMode] = useState<AuthMode>('login');
  const [sidebarTab, setSidebarTab] = useState<SidebarTab>('overview');
  const [themeMode, setThemeMode] = useState<'dark' | 'light'>('dark');
  const themeLoadedRef = useRef(false);

  // Auth
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [token, setToken] = useState<string | null>(null);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [errorMessage, setErrorMessage] = useState('');
  const [loading, setLoading] = useState(false);

  // Onboarding
  const [onboardStep, setOnboardStep] = useState(1);
  const [customSkill, setCustomSkill] = useState('');
  const [onboardData, setOnboardData] = useState({
    role: 'Student', // 'Student' | 'Working Professional' | 'Career Switcher'

    // Student fields
    degreeBranch: 'B.Tech / B.E. - Computer Science & Engineering (CSE)',
    collegeName: '',
    studentSemester: '6th Semester (3rd Year)',
    cgpa: '8.2',
    gradYear: '2026',

    // Working Professional fields
    currentCompany: '',
    currentDesignation: 'Associate Software Engineer',
    yearsOfExperience: '1 - 2 Years (Mid-Level)',
    highestDegree: 'B.Tech in Computer Science',
    noticePeriod: '1 Month (30 Days)',

    // Career Switcher fields
    currentDomain: 'Mechanical / Civil / Core Engineering',
    currentRoleCompany: '',
    yearsInDomain: '2 - 3 Years',
    switchGoal: 'Full Stack Web Development (React / Node / Next.js)',
    transitionTimeline: '3 - 6 Months (Standard Transition)',

    // Common baseline fields
    education: '',
    semester: '',
    skills: ['Python', 'JavaScript', 'React', 'Git'] as string[],
    languages: ['Python', 'JavaScript', 'SQL'] as string[],
    experienceLevel: 'Beginner',
    learningHours: 3,
    expectedPlacement: 'June 2026',
    targetRoles: ['Software Engineer'] as string[]
  });

  // Data
  const [roadmap, setRoadmap] = useState<any>(null);
  const [roadmapLoading, setRoadmapLoading] = useState(false);
  const [resumeAnalysis, setResumeAnalysis] = useState<any>(null);
  const [readinessData, setReadinessData] = useState<any>(null);
  const [notesLoading, setNotesLoading] = useState<string | null>(null);
  const [selectedNotesTopic, setSelectedNotesTopic] = useState<any | null>(null);
  const [activeNotes, setActiveNotes] = useState<any | null>(null);
  const [activeNotesLoading, setActiveNotesLoading] = useState(false);
  const [copiedCode, setCopiedCode] = useState(false);
  const [codingProblems, setCodingProblems] = useState<any[]>(INITIAL_PROBLEMS);
  const [activeProblem, setActiveProblem] = useState<any>(INITIAL_PROBLEMS[0] || null);
  const [editorLang, setEditorLang] = useState('python');
  const [editorCode, setEditorCode] = useState(INITIAL_PROBLEMS[0]?.starter_code_python || '# Write solution here\n');
  const [codeOutput, setCodeOutput] = useState<any>(null);
  const [submittingCode, setSubmittingCode] = useState(false);
  const [codingHint, setCodingHint] = useState('');
  const [codingFilterCategory, setCodingFilterCategory] = useState<string>('All');
  const [codingFilterDifficulty, setCodingFilterDifficulty] = useState<string>('All');
  const [codingSearchQuery, setCodingSearchQuery] = useState<string>('');
  const [autoSaveStatus, setAutoSaveStatus] = useState<string>('Saved');
  const [autoSaveTime, setAutoSaveTime] = useState<string>('');
  const [showAiHintModal, setShowAiHintModal] = useState<boolean>(false);
  const [aiHintLevel, setAiHintLevel] = useState<number>(1);
  const [aiHintData, setAiHintData] = useState<any>(null);
  const [aiHintLoading, setAiHintLoading] = useState<boolean>(false);
  const [activeCodeTab, setActiveCodeTab] = useState<'description' | 'solution' | 'submissions'>('description');
  const [activeOutputTab, setActiveOutputTab] = useState<'testcases' | 'diagnostics'>('testcases');
  const [activeTestCaseIdx, setActiveTestCaseIdx] = useState<number>(0);
  const [syntaxErrorsCount, setSyntaxErrorsCount] = useState<number>(0);
  const lastSavedCodeRef = useRef<string>('');

  // Resume State & Builder (clean state with NO prefixed/dummy data)
  const [resumeMode, setResumeMode] = useState<'upload' | 'builder' | 'preview'>('upload');
  const [resumePdfLoading, setResumePdfLoading] = useState(false);
  const [uploadingPdf, setUploadingPdf] = useState(false);
  const [uploadedFileDetails, setUploadedFileDetails] = useState<{ name: string; size: string; timestamp: string } | null>(null);
  const [resumeForm, setResumeForm] = useState({
    name: '',
    headline: '',
    email: '',
    phone: '',
    location: '',
    linkedin: '',
    github: '',
    portfolio: '',
    summary: '',
    education: '',
    college: '',
    cgpa: '',
    gradYear: '',
    skills: '',
    languages: '',
    frameworks: '',
    tools: '',
    experienceCompany: '',
    experienceRole: '',
    experienceDuration: '',
    experienceLocation: '',
    experienceBullets: '',
    project1Title: '',
    project1Stack: '',
    project1Link: '',
    project1Bullets: '',
    certifications: '',
    achievements: '',
    interests: '',
    project2Title: '',
    project2Stack: '',
    project2Link: '',
    project2Bullets: ''
  });
  const [summaryLoading, setSummaryLoading] = useState(false);

  // Automatically sync profile and onboarding data directly into resume builder
  const syncResumeWithProfile = useCallback((prof?: UserProfile | null, onboard?: typeof onboardData) => {
    setResumeForm(prev => {
      const skillsArr = (prof?.skills && prof.skills.length > 0) ? prof.skills : (onboard?.skills || []);
      const langsArr = (prof?.languages_known && prof.languages_known.length > 0) ? prof.languages_known : (onboard?.languages || []);
      const targetRole = (prof?.target_roles && prof.target_roles.length > 0) ? prof.target_roles[0] : (onboard?.targetRoles?.[0] || '');
      const eduVal = prof?.education || onboard?.degreeBranch || '';

      return {
        ...prev,
        name: prev.name || prof?.full_name || fullName || '',
        email: prev.email || prof?.email || email || '',
        headline: prev.headline || targetRole || '',
        skills: prev.skills || (skillsArr.length > 0 ? skillsArr.join(', ') : ''),
        languages: prev.languages || (langsArr.length > 0 ? langsArr.join(', ') : ''),
        education: prev.education || eduVal || '',
        college: prev.college || onboard?.collegeName || '',
        cgpa: prev.cgpa || (onboard?.cgpa ? String(onboard.cgpa) : ''),
        gradYear: prev.gradYear || onboard?.gradYear || '',
        experienceCompany: prev.experienceCompany || onboard?.currentCompany || '',
        experienceRole: prev.experienceRole || onboard?.currentDesignation || '',
      };
    });
  }, [fullName, email]);

  // Interview
  const [interviewType, setInterviewType] = useState('Mixed');
  const [targetInterviewRole, setTargetInterviewRole] = useState('');
  const [jobDescription, setJobDescription] = useState('');
  const [interviewId, setInterviewId] = useState<number | null>(null);
  const [interviewStarted, setInterviewStarted] = useState(false);
  const [interviewMessages, setInterviewMessages] = useState<any[]>([]);
  const [candidateResponse, setCandidateResponse] = useState('');
  const [interviewFeedback, setInterviewFeedback] = useState<any>(null);
  const [currentTurnCorrection, setCurrentTurnCorrection] = useState<any>(null);
  const [liveInterviewScore, setLiveInterviewScore] = useState(82);
  const [liveConfidenceMetric, setLiveConfidenceMetric] = useState(85);
  const [speechWpm, setSpeechWpm] = useState(135);
  const [fillerWordsCount, setFillerWordsCount] = useState(0);
  const [webcamEnabled, setWebcamEnabled] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isAiSpeaking, setIsAiSpeaking] = useState(false);
  const [silenceCountdown, setSilenceCountdown] = useState<number | null>(null);
  const [audioLevel, setAudioLevel] = useState<number>(0);
  const [telemetry, setTelemetry] = useState({ attention: 0, smile: 0, stress: 0, eye: 0 });
  const [faceStatus, setFaceStatus] = useState<'off' | 'loading' | 'active' | 'no-face' | 'unavailable'>('off');
  const faceSamplesRef = useRef<FaceMetrics[]>([]);
  const [interviewLength, setInterviewLength] = useState(8);
  const [interviewPhase, setInterviewPhase] = useState('Introduction');
  const [questionNumber, setQuestionNumber] = useState(1);
  const [totalQuestions, setTotalQuestions] = useState(8);
  const [questionKind, setQuestionKind] = useState('intro');
  const [interviewTrackLabel, setInterviewTrackLabel] = useState('');
  const [questionElapsed, setQuestionElapsed] = useState(0);
  const questionStartRef = useRef<number>(Date.now());
  const speakingStartTimeRef = useRef<number | null>(null);
  const [meetingDrawerOpen, setMeetingDrawerOpen] = useState(false);
  const [subtitlesEnabled, setSubtitlesEnabled] = useState(true);
  const [callDuration, setCallDuration] = useState(0);

  useEffect(() => {
    let interval: any = null;
    if (interviewStarted) {
      setCallDuration(0);
      interval = setInterval(() => {
        setCallDuration(prev => prev + 1);
      }, 1000);
    } else {
      setCallDuration(0);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [interviewStarted]);

  const formatDuration = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  // Mentor
  const [mentorQuery, setMentorQuery] = useState('');
  const [mentorLoading, setMentorLoading] = useState(false);
  const mentorMessagesEndRef = useRef<HTMLDivElement>(null);
  const [mentorMessages, setMentorMessages] = useState<Message[]>([
    { role: 'assistant', text: '👋 Hello! I am your GapX AI Career Coach. Ask me anything about placement preparation, coding algorithms (e.g. *Solve Two Sum*), system design concepts, resume optimization, or interview questions!' }
  ]);
  const [mentorSuggestions, setMentorSuggestions] = useState([
    'Solve Two Sum in Python', 'How to prepare for FAANG?', 'Explain OOP concepts with code'
  ]);

  // Admin
  const [newProblem, setNewProblem] = useState({
    title: '', difficulty: 'Easy', category: 'Arrays', problem_statement: '',
    example_input: '', example_output: '', starter_code_python: ''
  });

  const [notifications, setNotifications] = useState<any[]>([]);
  const webcamRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const webcamStreamRef = useRef<MediaStream | null>(null);
  const [experienceLevel, setExperienceLevel] = useState<string>('Fresher');
  const [topicDomain, setTopicDomain] = useState<string>('');  // interview field/track id; '' = detect from role
  const [currentDifficulty, setCurrentDifficulty] = useState<'Easy' | 'Medium' | 'Hard'>('Easy');
  const [difficultyChange, setDifficultyChange] = useState<'decreased' | 'same' | 'increased'>('same');

  const [isOfflineMode, setIsOfflineMode] = useState(false);

  const silenceTimerRef = useRef<any>(null);
  const recognitionRef = useRef<any>(null);
  const [audioOutputEnabled, setAudioOutputEnabled] = useState(true);

  // --- SPLASH + RESTORE SESSION (token is verified with the server) ---
  useEffect(() => {
    const t = setTimeout(async () => {
      let saved: any = null;
      try { saved = JSON.parse(localStorage.getItem('gapx_session') || 'null'); } catch (_) {}
      try { localStorage.removeItem('gapx_users'); } catch (_) {}  // old offline accounts stored plain-text passwords
      const tok: string | undefined = saved?.token;
      if (tok && !tok.startsWith('local_')) {
        try {
          const r = await fetch(`${BACKEND_URL}/users/me`, { headers: { Authorization: `Bearer ${tok}` } });
          if (r.ok) {
            const prof = await r.json();
            setToken(tok);
            setUserProfile(prof);
            saveSession(tok, prof);
            if (prof.email) setEmail(prof.email);
            if (prof.full_name) setFullName(prof.full_name);
            syncResumeWithProfile(prof);
            setAppState(prof.education && prof.target_roles?.length ? 'dashboard' : 'onboarding');
            fetchRoadmap(tok); fetchProblems(tok); fetchNotifications(tok); fetchResume(tok); fetchReadiness(tok); fetchInterview(tok);
            return;
          }
          if (r.status === 401) setErrorMessage('Your session has expired. Please sign in again.');
        } catch (_) {
          setErrorMessage(`Can't reach the GapX server at ${BACKEND_URL.replace('/api/v1', '')}. Start the backend (run_app.bat) and refresh.`);
        }
      }
      localStorage.removeItem('gapx_session');
      setAppState('auth');
      setAuthMode('login');
      setPassword('');
    }, 1900);
    return () => clearTimeout(t);
  }, []);

  // --- SIGN-IN OPTIONS (Google / demo) ---
  const [authConfig, setAuthConfig] = useState<{ google_client_id: string | null; demo_login_enabled: boolean }>({ google_client_id: null, demo_login_enabled: false });
  const googleBtnRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    fetch(`${BACKEND_URL}/auth/config`).then(r => r.ok ? r.json() : null).then(d => d && setAuthConfig(d)).catch(() => {});
  }, []);

  // --- SESSION EXPIRY: any 401 from the API signs the user out cleanly ---
  const sessionExpiredRef = useRef<() => void>(() => {});
  useEffect(() => {
    const original = window.fetch;
    window.fetch = async (...args: Parameters<typeof fetch>) => {
      const res = await original(...args);
      const target = args[0] as any;
      const url = typeof target === 'string' ? target : (target?.url || String(target));
      if (res.status === 401 && url.startsWith(BACKEND_URL) && !url.includes('/auth/')) {
        sessionExpiredRef.current();
      }
      return res;
    };
    return () => { window.fetch = original; };
  }, []);

  // --- CODE AUTO-SAVE ENGINE (EVERY 15 SECONDS) ---
  const saveCodeDraft = useCallback(async (codeToSave: string, probId: number, lang: string) => {
    if (!probId || !codeToSave) return;
    try {
      setAutoSaveStatus('Saving...');
      const userKey = userProfile?.email || 'guest';
      localStorage.setItem(`gapx_draft_${userKey}_${probId}_${lang}`, codeToSave);

      if (token && !token.startsWith('local_')) {
        await fetch(`${BACKEND_URL}/coding/problems/${probId}/draft`, {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
          body: JSON.stringify({ code: codeToSave, language: lang })
        });
      }
      const now = new Date();
      const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      setAutoSaveStatus('Saved');
      setAutoSaveTime(timeStr);
      lastSavedCodeRef.current = codeToSave;
    } catch (_) {
      setAutoSaveStatus('Saved');
    }
  }, [token, userProfile]);

  useEffect(() => {
    if (!activeProblem || !editorCode) return;
    const interval = setInterval(() => {
      if (editorCode && editorCode !== lastSavedCodeRef.current) {
        saveCodeDraft(editorCode, activeProblem.id, editorLang);
      }
    }, 15000); // Auto-save every 15-20 seconds
    return () => clearInterval(interval);
  }, [activeProblem, editorCode, editorLang, saveCodeDraft]);

  // --- AUDIO OUTPUT (TEXT-TO-SPEECH WITH AI AVATAR PULSE) ---
  const speakInterviewerText = (text: string) => {
    if (!audioOutputEnabled) return;
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.02;
        utterance.pitch = 1.0;
        
        const voices = window.speechSynthesis.getVoices();
        const prefVoice = voices.find(v => v.lang.includes('en') && (
          v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Neural') || v.name.includes('Jenny') || v.name.includes('Guy') || v.name.includes('Samantha') || v.name.includes('Zira')
        )) || voices.find(v => v.lang.includes('en'));
        
        if (prefVoice) utterance.voice = prefVoice;
        
        utterance.onstart = () => { setIsAiSpeaking(true); };
        utterance.onend = () => { setIsAiSpeaking(false); };
        utterance.onerror = () => { setIsAiSpeaking(false); };
        
        window.speechSynthesis.speak(utterance);
      } catch (_) {
        setIsAiSpeaking(false);
      }
    }
  };

  // --- THEME ---
  useEffect(() => {
    if (!themeLoadedRef.current) {
      themeLoadedRef.current = true;
      try {
        const stored = localStorage.getItem('gapx_theme');
        if (stored === 'light' && themeMode !== 'light') { setThemeMode('light'); return; }
      } catch (_) {}
    }
    document.documentElement.classList.toggle('dark', themeMode === 'dark');
    document.documentElement.classList.toggle('light', themeMode === 'light');
    try { localStorage.setItem('gapx_theme', themeMode); } catch (_) {}
  }, [themeMode]);

  // --- FACE ANALYSIS (MediaPipe in the browser; video never leaves the device) ---
  useEffect(() => {
    if (!webcamEnabled) { setFaceStatus('off'); return; }
    let stop: (() => void) | null = null;
    let cancelled = false;
    const begin = async () => {
      const video = webcamRef.current;
      if (!video) return;
      setFaceStatus('loading');
      try {
        stop = await startFaceAnalysis(video, m => {
          if (!m.facePresent) { setFaceStatus('no-face'); return; }
          setFaceStatus('active');
          faceSamplesRef.current.push(m);
          if (faceSamplesRef.current.length > 600) faceSamplesRef.current.shift();
          setTelemetry({ attention: m.attention * 100, smile: m.smile * 100, stress: m.stress * 100, eye: m.eyeContact * 100 });
        });
        if (cancelled && stop) stop();
      } catch (_) {
        if (!cancelled) setFaceStatus('unavailable');
      }
    };
    const t = setTimeout(begin, 400);  // let the <video> attach the stream first
    return () => { cancelled = true; clearTimeout(t); if (stop) stop(); };
  }, [webcamEnabled]);

  // Time spent on the current question
  useEffect(() => {
    if (!interviewStarted) return;
    const iv = setInterval(() => setQuestionElapsed(Math.floor((Date.now() - questionStartRef.current) / 1000)), 1000);
    return () => clearInterval(iv);
  }, [interviewStarted]);

  // Averages the face metrics collected while the candidate answered the current question
  const collectFaceMetrics = () => {
    const samples = faceSamplesRef.current.filter(m => m.facePresent);
    faceSamplesRef.current = [];
    if (!webcamEnabled || samples.length < 3) return {};
    const avg = (k: keyof FaceMetrics) => samples.reduce((a, m) => a + (m[k] as number), 0) / samples.length;
    return { attention_metric: avg('attention'), smile_metric: avg('smile'), stress_metric: avg('stress'), eye_contact_metric: avg('eyeContact') };
  };

  // Ensure video element plays webcam stream smoothly whenever webcam is active
  useEffect(() => {
    if (webcamEnabled && webcamStreamRef.current && webcamRef.current) {
      if (webcamRef.current.srcObject !== webcamStreamRef.current) {
        webcamRef.current.srcObject = webcamStreamRef.current;
      }
      webcamRef.current.play().catch(() => {});
    }
  }, [webcamEnabled, interviewStarted]);

  // High-Tech Biometric HUD Canvas Overlay (Non-obstructive: Keeps candidate face 100% clear)
  useEffect(() => {
    if (!webcamEnabled || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    let raf: number;
    let frameCount = 0;

    const draw = () => {
      frameCount++;
      if (canvas.width !== canvas.clientWidth || canvas.height !== canvas.clientHeight) {
        if (canvas.clientWidth > 0 && canvas.clientHeight > 0) {
          canvas.width = canvas.clientWidth;
          canvas.height = canvas.clientHeight;
        }
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const w = canvas.width;
      const h = canvas.height;
      if (w <= 0 || h <= 0) {
        raf = requestAnimationFrame(draw);
        return;
      }

      // Outer Viewfinder Corner Brackets (Keeps face in center 100% visible)
      const m = 18;
      const cLen = 22;
      ctx.strokeStyle = 'rgba(99, 102, 241, 0.45)';
      ctx.lineWidth = 2;

      // Top-Left Bracket
      ctx.beginPath(); ctx.moveTo(m, m + cLen); ctx.lineTo(m, m); ctx.lineTo(m + cLen, m); ctx.stroke();
      // Top-Right Bracket
      ctx.beginPath(); ctx.moveTo(w - m - cLen, m); ctx.lineTo(w - m, m); ctx.lineTo(w - m, m + cLen); ctx.stroke();
      // Bottom-Left Bracket
      ctx.beginPath(); ctx.moveTo(m, h - m - cLen); ctx.lineTo(m, h - m); ctx.lineTo(m + cLen, h - m); ctx.stroke();
      // Bottom-Right Bracket
      ctx.beginPath(); ctx.moveTo(w - m - cLen, h - m); ctx.lineTo(w - m, h - m); ctx.lineTo(w - m, h - m - cLen); ctx.stroke();

      // Subtle Biometric Scanner Ticks on left & right borders
      const midY = h / 2;
      ctx.strokeStyle = 'rgba(16, 185, 129, 0.4)';
      ctx.lineWidth = 1.5;
      ctx.beginPath(); ctx.moveTo(m - 4, midY - 12); ctx.lineTo(m + 4, midY - 12); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(m - 4, midY + 12); ctx.lineTo(m + 4, midY + 12); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(w - m - 4, midY - 12); ctx.lineTo(w - m + 4, midY - 12); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(w - m - 4, midY + 12); ctx.lineTo(w - m + 4, midY + 12); ctx.stroke();

      // Biometric HUD Text in Corner Overlay (Frosted backdrop)
      ctx.fillStyle = 'rgba(9, 9, 11, 0.65)';
      ctx.fillRect(m + 4, m + 4, 180, 44);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
      ctx.strokeRect(m + 4, m + 4, 180, 44);

      ctx.fillStyle = '#10b981';
      ctx.font = 'bold 9px monospace';
      ctx.fillText(faceStatus === 'active' ? '● FACE ANALYSIS: ON' : faceStatus === 'loading' ? '○ LOADING FACE MODEL…' : faceStatus === 'no-face' ? '○ FACE NOT VISIBLE' : '○ FACE ANALYSIS OFF', m + 12, m + 18);

      ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
      ctx.font = '8px monospace';
      ctx.fillText(faceStatus === 'active' ? `EYE CONTACT: ${Math.round(telemetry.eye)}% · COMPOSURE: ${Math.round(100 - telemetry.stress)}%` : 'METRICS: —', m + 12, m + 30);
      ctx.fillStyle = isRecording ? '#f87171' : 'rgba(161, 161, 170, 0.8)';
      ctx.fillText(isRecording ? '🎙️ VOICE DETECTED (SPEAKING)' : '● AWAITING SPEECH RESPONSE', m + 12, m + 40);

      raf = requestAnimationFrame(draw);
    };

    draw();
    return () => cancelAnimationFrame(raf);
  }, [webcamEnabled, telemetry, isRecording, faceStatus]);

  // --- API HELPERS ---
  const authHeaders = () => ({ 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' });

  const fetchProfile = async (tok: string) => {
    const r = await fetch(`${BACKEND_URL}/users/me`, { headers: { Authorization: `Bearer ${tok}` } });
    if (r.ok) { const d = await r.json(); setUserProfile(d); return d; }
  };

  const fetchRoadmap = async (tok: string) => {
    const targetRole = userProfile?.target_roles?.[0] || 'Software Engineer';
    try {
      const headers = tok ? { Authorization: `Bearer ${tok}` } : {};
      const r = await fetch(`${BACKEND_URL}/roadmaps/current`, { headers });
      if (r.ok) {
        const d = await r.json();
        if (d && Array.isArray(d.stages_data) && d.stages_data.length > 0) {
          setRoadmap(d);
          return;
        }
      }
      const genR = await fetch(`${BACKEND_URL}/roadmaps/generate`, { method: 'POST', headers });
      if (genR.ok) {
        const d = await genR.json();
        if (d && Array.isArray(d.stages_data) && d.stages_data.length > 0) {
          setRoadmap(d);
          return;
        }
      }
    } catch (_) {}
  };

  const fetchProblems = async (tok: string) => {
    try {
      const headers = tok ? { Authorization: `Bearer ${tok}` } : {};
      const r = await fetch(`${BACKEND_URL}/coding/problems`, { headers });
      if (r.ok) {
        const listData = await r.json();
        if (Array.isArray(listData) && listData.length > 0) {
          const merged = listData.map((bp: any) => {
            const fullP = INITIAL_PROBLEMS.find((ip: any) => ip.id === bp.id || ip.title.toLowerCase() === bp.title.toLowerCase());
            return fullP ? { ...fullP, ...bp } : bp;
          });
          setCodingProblems(merged);
          return;
        }
      }
    } catch (_) {}
    // Robust local fallback with complete 30-problem LeetCode bank
    setCodingProblems(INITIAL_PROBLEMS);
  };

  const fetchNotifications = async (tok: string) => {
    try {
      const r = await fetch(`${BACKEND_URL}/users/notifications`, { headers: { Authorization: `Bearer ${tok}` } });
      if (r.ok) setNotifications(await r.json());
    } catch (_) {}
  };

  const fetchResume = async (tok: string) => {
    try {
      const r = await fetch(`${BACKEND_URL}/resumes/latest`, { headers: { Authorization: `Bearer ${tok}` } });
      if (r.ok) {
        const d = await r.json();
        setResumeAnalysis(d);
        if (d.resume_data) {
          const rd = d.resume_data;
          setResumeForm(prev => ({
            ...prev,
            name: rd.name || rd.parsed_name || prev.name,
            email: rd.email || rd.parsed_email || prev.email,
            headline: rd.headline || rd.target_role || prev.headline,
            phone: rd.phone || rd.parsed_phone || prev.phone,
            location: rd.location || prev.location,
            linkedin: rd.linkedin || rd.parsed_links?.linkedin || prev.linkedin,
            github: rd.github || rd.parsed_links?.github || prev.github,
            portfolio: rd.portfolio || rd.parsed_links?.portfolio || prev.portfolio,
            summary: rd.summary || prev.summary,
            education: rd.education || (rd.parsed_education?.[0]?.degree) || prev.education,
            college: rd.college || (rd.parsed_education?.[0]?.institution) || prev.college,
            cgpa: rd.cgpa || (rd.parsed_education?.[0]?.cgpa) || prev.cgpa,
            gradYear: rd.gradYear || prev.gradYear,
            skills: typeof rd.skills === 'string' ? rd.skills : (Array.isArray(rd.skills) ? rd.skills.join(', ') : prev.skills),
            languages: typeof rd.languages === 'string' ? rd.languages : (Array.isArray(rd.languages) ? rd.languages.join(', ') : prev.languages),
            frameworks: rd.frameworks || prev.frameworks,
            tools: rd.tools || prev.tools,
            experienceCompany: rd.experienceCompany || (rd.parsed_experience?.[0]?.company) || prev.experienceCompany,
            experienceRole: rd.experienceRole || (rd.parsed_experience?.[0]?.role) || prev.experienceRole,
            experienceDuration: rd.experienceDuration || (rd.parsed_experience?.[0]?.duration) || prev.experienceDuration,
            experienceLocation: rd.experienceLocation || prev.experienceLocation,
            experienceBullets: rd.experienceBullets || (rd.parsed_experience?.[0]?.description) || prev.experienceBullets,
            project1Title: rd.project1Title || (rd.parsed_projects?.[0]?.title) || prev.project1Title,
            project1Stack: rd.project1Stack || (rd.parsed_projects?.[0]?.stack) || prev.project1Stack,
            project1Link: rd.project1Link || prev.project1Link,
            project1Bullets: rd.project1Bullets || (rd.parsed_projects?.[0]?.description) || prev.project1Bullets,
            certifications: Array.isArray(rd.certifications) ? rd.certifications.join(', ') : (rd.certifications || prev.certifications),
            achievements: Array.isArray(rd.achievements) ? rd.achievements.join(', ') : (rd.achievements || prev.achievements),
            interests: Array.isArray(rd.interests) ? rd.interests.join(', ') : (rd.interests || prev.interests),
            project2Title: rd.projects?.[1]?.name || prev.project2Title,
            project2Stack: rd.projects?.[1]?.stack || prev.project2Stack,
            project2Link: rd.projects?.[1]?.link || prev.project2Link,
            project2Bullets: Array.isArray(rd.projects?.[1]?.bullets) ? rd.projects[1].bullets.join('\n') : prev.project2Bullets
          }));
        }
      }
    } catch (_) {}
  };

  const fetchReadiness = async (tok: string) => {
    try {
      const r = await fetch(`${BACKEND_URL}/users/readiness`, { headers: { Authorization: `Bearer ${tok}` } });
      if (r.ok) setReadinessData(await r.json());
    } catch (_) {}
  };

  const fetchInterview = async (tok: string) => {
    try {
      if (tok.startsWith('local_')) return;
      const r = await fetch(`${BACKEND_URL}/interviews/latest`, { headers: { Authorization: `Bearer ${tok}` } });
      if (r.ok) {
        const d = await r.json();
        setInterviewFeedback(d);
      }
    } catch (_) {}
  };

  // --- MOCK DATA (High quality 8-stage roadmap fallback) ---
  const createMockProfile = (emailVal: string, nameVal: string): UserProfile => ({
    id: Date.now(), email: emailVal, full_name: nameVal || emailVal.split('@')[0],
    role: 'Student', education: '', semester: '', skills: [], languages_known: [],
    experience_level: 'Beginner', preferred_learning_hours: 3,
    expected_placement_date: 'June 2027', target_roles: [], xp: 0, level: 1,
    streak: 0, badges: [], created_at: new Date().toISOString()
  });

  const saveSession = (tok: string, prof: UserProfile) => {
    localStorage.setItem('gapx_session', JSON.stringify({ token: tok, profile: prof }));
  };

  const enterDashboard = async (tok: string, prof: any) => {
    setToken(tok);
    setUserProfile(prof);
    saveSession(tok, prof);
    syncResumeWithProfile(prof);
    setAppState(prof.education && prof.target_roles?.length ? 'dashboard' : 'onboarding');
    fetchProblems(tok);
    if (prof.education) {
      fetchRoadmap(tok); fetchNotifications(tok); fetchResume(tok); fetchReadiness(tok); fetchInterview(tok);
    }
  };

  // --- AUTH ---
  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true); setErrorMessage('');
    try {
      const endpoint = authMode === 'login' ? 'login' : 'register';
      const body = authMode === 'login' ? { email, password } : { email, password, full_name: fullName };
      if (authMode === 'register' && password.length < 6) throw new Error('Use a password with at least 6 characters.');
      let r: Response;
      try {
        r = await fetch(`${BACKEND_URL}/auth/${endpoint}`, {
          method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
        });
      } catch (_) {
        throw new Error("Can't reach the GapX server. Make sure the backend is running (run_app.bat), then try again.");
      }
      const d = await r.json();
      if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : 'Authentication failed');
      setIsOfflineMode(false);
      const prof = await fetchProfile(d.access_token);
      if (!prof) throw new Error('Signed in, but your profile could not be loaded. Please try again.');
      await enterDashboard(d.access_token, prof);
    } catch (err: any) {
      setErrorMessage(err.message || 'Something went wrong. Please try again.');
    } finally { setLoading(false); }
  };

  const completeTokenLogin = async (accessToken: string) => {
    const prof = await fetchProfile(accessToken);
    if (!prof) throw new Error('Could not load your profile.');
    await enterDashboard(accessToken, prof);
  };

  // Google Identity Services: the official button appears when GOOGLE_CLIENT_ID is set on the backend
  useEffect(() => {
    const clientId = authConfig.google_client_id;
    if (!clientId || appState !== 'auth') return;
    const init = () => {
      const g = (window as any).google;
      if (!g?.accounts?.id || !googleBtnRef.current) return;
      g.accounts.id.initialize({
        client_id: clientId,
        callback: async (resp: any) => {
          setLoading(true); setErrorMessage('');
          try {
            const r = await fetch(`${BACKEND_URL}/auth/google`, {
              method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ credential: resp.credential })
            });
            const d = await r.json();
            if (!r.ok) throw new Error(d.detail || 'Google sign-in failed');
            await completeTokenLogin(d.access_token);
          } catch (err: any) { setErrorMessage(err.message); } finally { setLoading(false); }
        },
      });
      googleBtnRef.current.innerHTML = '';
      g.accounts.id.renderButton(googleBtnRef.current, { theme: themeMode === 'dark' ? 'filled_black' : 'outline', size: 'large', width: 360, text: 'continue_with', shape: 'pill' });
    };
    if ((window as any).google?.accounts?.id) { init(); return; }
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.onload = init;
    document.head.appendChild(script);
  }, [authConfig.google_client_id, appState, themeMode]);

  const handleDemoLogin = async () => {
    setLoading(true); setErrorMessage('');
    try {
      let r: Response;
      try { r = await fetch(`${BACKEND_URL}/auth/demo`, { method: 'POST' }); }
      catch (_) { throw new Error("Can't reach the GapX server."); }
      const d = await r.json();
      if (!r.ok) throw new Error(d.detail || 'Demo login is unavailable');
      await completeTokenLogin(d.access_token);
    } catch (err: any) {
      setErrorMessage(err.message || 'Something went wrong.');
    } finally { setLoading(false); }
  };

  const handleOnboard = async () => {
    if (!token) return;
    setLoading(true); setErrorMessage('');
    try {
      let formattedEdu = '';
      let formattedSem = '';

      if (onboardData.role === 'Student') {
        const deg = onboardData.degreeBranch || 'B.Tech CS';
        const col = onboardData.collegeName ? ` (${onboardData.collegeName})` : '';
        const grad = onboardData.gradYear ? ` - Class of ${onboardData.gradYear}` : '';
        formattedEdu = `${deg}${col}${grad}`;

        const sem = onboardData.studentSemester || 'Undergraduate';
        const cg = onboardData.cgpa ? ` | CGPA: ${onboardData.cgpa}` : '';
        formattedSem = `${sem}${cg}`;
      } else if (onboardData.role === 'Working Professional') {
        const desig = onboardData.currentDesignation || 'Software Professional';
        const comp = onboardData.currentCompany ? ` at ${onboardData.currentCompany}` : '';
        const exp = onboardData.yearsOfExperience ? ` (${onboardData.yearsOfExperience})` : '';
        formattedEdu = `${desig}${comp}${exp}`;

        const not = onboardData.noticePeriod ? `Notice: ${onboardData.noticePeriod}` : 'Active Prep';
        const deg = onboardData.highestDegree ? ` | Degree: ${onboardData.highestDegree}` : '';
        formattedSem = `${not}${deg}`;
      } else if (onboardData.role === 'Career Switcher') {
        const dom = onboardData.currentDomain || 'Non-Tech Field';
        const comp = onboardData.currentRoleCompany ? ` (${onboardData.currentRoleCompany})` : '';
        const exp = onboardData.yearsInDomain ? ` | ${onboardData.yearsInDomain} in ${dom}` : ` | Background: ${dom}`;
        formattedEdu = `Transitioning from ${dom}${comp}${exp}`;

        const goal = onboardData.switchGoal ? `Goal: ${onboardData.switchGoal}` : 'Tech Transition';
        const time = onboardData.transitionTimeline ? ` | Timeline: ${onboardData.transitionTimeline}` : '';
        formattedSem = `${goal}${time}`;
      }

      const r = await fetch(`${BACKEND_URL}/users/onboard`, {
        method: 'PUT', headers: authHeaders(),
        body: JSON.stringify({
          role: onboardData.role,
          education: formattedEdu,
          semester: formattedSem,
          skills: onboardData.skills,
          languages_known: onboardData.languages,
          experience_level: onboardData.experienceLevel,
          preferred_learning_hours: onboardData.learningHours,
          expected_placement_date: onboardData.expectedPlacement,
          target_roles: onboardData.targetRoles,

          // Role specific detailed metadata
          college_name: onboardData.collegeName,
          degree_branch: onboardData.degreeBranch,
          cgpa: Number(onboardData.cgpa) || null,
          graduation_year: onboardData.gradYear,
          current_company: onboardData.currentCompany,
          current_designation: onboardData.currentDesignation,
          years_of_experience: onboardData.yearsOfExperience,
          notice_period: onboardData.noticePeriod,
          highest_degree: onboardData.highestDegree,
          current_domain: onboardData.currentDomain,
          transition_timeline: onboardData.transitionTimeline,
          switch_goal: onboardData.switchGoal
        })
      });
      if (!r.ok) {
        const d = await r.json().catch(() => ({ detail: 'Onboarding failed' }));
        throw new Error(d.detail || 'Onboarding failed');
      }
      const updated = await r.json();
      setUserProfile(updated);
      saveSession(token, updated);
      syncResumeWithProfile(updated, onboardData);
      const rmr = await fetch(`${BACKEND_URL}/roadmaps/generate`, { method: 'POST', headers: authHeaders() });
      if (rmr.ok) {
        const rd = await rmr.json();
        if (rd && Array.isArray(rd.stages_data)) setRoadmap(rd);
      }
      setAppState('dashboard');
      fetchProblems(token!); fetchNotifications(token!);
    } catch (err: any) { setErrorMessage(err.message || 'Onboarding failed. Please try again.'); }
    finally { setLoading(false); }
  };

  // --- ROADMAP ---
  const handleGenerateRoadmap = async () => {
    if (!token) return;
    setRoadmapLoading(true);
    const targetRole = userProfile?.target_roles?.[0] || 'Software Engineer';
    try {
      const r = await fetch(`${BACKEND_URL}/roadmaps/generate`, {
        method: 'POST',
        headers: authHeaders()
      });
      if (r.ok) {
        const data = await r.json();
        if (data && Array.isArray(data.stages_data) && data.stages_data.length > 0) {
          setRoadmap(data);
          fetchProfile(token);
          fetchNotifications(token);
          return;
        }
      }
    } catch (_) {}
    finally {
      setRoadmapLoading(false);
    }
    alert("Couldn't generate the roadmap. Check that the backend is running and try again.");
  };

  const toggleTopic = async (stageId: any, topicId: any, currentCompleted: boolean) => {
    if (!token) return;

    const nextState = !currentCompleted;

    // Optimistic UI state update for immediate checkbox feedback
    if (roadmap && roadmap.stages_data) {
      const updatedStages = roadmap.stages_data.map((stg: any) => {
        const stageMatch = String(stg.id).trim() === String(stageId).trim();
        return {
          ...stg,
          topics: stg.topics?.map((top: any) => {
            const topicMatch = String(top.id).trim() === String(topicId).trim();
            if (stageMatch || topicMatch) {
              if (topicMatch) {
                return { ...top, is_completed: nextState };
              }
            }
            return top;
          })
        };
      });

      const totalTopics = updatedStages.reduce((acc: number, s: any) => acc + (s.topics?.length || 0), 0);
      const completedCount = updatedStages.reduce((acc: number, s: any) => acc + (s.topics?.filter((t: any) => t.is_completed)?.length || 0), 0);
      const newPct = totalTopics ? Math.round((completedCount / totalTopics) * 100) : 0;

      setRoadmap({ ...roadmap, stages_data: updatedStages, progress_percentage: newPct });

      // Optimistic XP update
      if (userProfile) {
        const updatedXp = nextState ? userProfile.xp + 50 : Math.max(0, userProfile.xp - 50);
        const updatedLevel = Math.max(1, Math.floor(updatedXp / 500) + 1);
        setUserProfile({ ...userProfile, xp: updatedXp, level: updatedLevel });
      }
    }

    if (token.startsWith('local_')) return;

    try {
      const r = await fetch(`${BACKEND_URL}/roadmaps/toggle-topic`, {
        method: 'POST',
        headers: authHeaders(),
        body: JSON.stringify({ stage_id: stageId, topic_id: topicId, is_completed: nextState })
      });
      if (r.ok) {
        const data = await r.json();
        setRoadmap(data);
        fetchProfile(token);
        fetchReadiness(token);
        fetchNotifications(token);
      }
    } catch (_) {}
  };

  const openTopicNotes = async (stageId: any, topic: any, stageTitle: string, withExplainer: boolean = false) => {
    setExplainerOpen(withExplainer);
    setSelectedNotesTopic({ ...topic, stageId, stageTitle });
    setActiveNotesLoading(true);
    setActiveNotes(null);
    try {
      const res = await fetch(`${BACKEND_URL}/roadmaps/notes/${stageId}/${topic.id}`, {
        headers: authHeaders()
      });
      if (res.ok) {
        const data = await res.json();
        setActiveNotes(data);
      } else {
        throw new Error('Failed to fetch detailed notes');
      }
    } catch (err: any) {
      setActiveNotes(null);
    } finally {
      setActiveNotesLoading(false);
    }
  };

  const [cheatsheetLoading, setCheatsheetLoading] = useState(false);
  const [explainerOpen, setExplainerOpen] = useState(false);
  const downloadCheatsheet = async () => {
    setCheatsheetLoading(true);
    try {
      const res = await fetch(`${BACKEND_URL}/roadmaps/cheatsheet-pdf`, { headers: authHeaders() });
      if (!res.ok) {
        const d = await res.json().catch(() => ({}));
        throw new Error(typeof d.detail === 'string' ? d.detail : 'Could not create the notes PDF.');
      }
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `GapX_${(roadmap?.target_role || 'Roadmap').replace(/[^a-zA-Z0-9]/g, '_')}_Last_Minute_Notes.pdf`;
      document.body.appendChild(a); a.click(); a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.message || 'Could not download the notes.');
    } finally {
      setCheatsheetLoading(false);
    }
  };

  const downloadNotesPdf = async (stageId: any, topicId: any, topicTitle: string) => {
    const key = `${stageId}-${topicId}`;
    setNotesLoading(key);
    try {
      const url = `${BACKEND_URL}/roadmaps/notes-pdf/${stageId}/${topicId}`;
      const res = await fetch(url, {
        headers: authHeaders()
      });
      if (!res.ok) throw new Error('Failed to generate PDF notes');
      const blob = await res.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = blobUrl;
      const cleanTitle = (topicTitle || `Stage_${stageId}_Topic_${topicId}`).replace(/[^a-zA-Z0-9]/g, '_');
      a.download = `GapX_AI_Notes_${cleanTitle}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(blobUrl);
    } catch (err: any) {
      alert(err.message || 'Failed to download notes PDF.');
    } finally { setNotesLoading(null); }
  };

  // --- RESUME ---
  const isValidLinkedIn = (url: string) => {
    if (!url || !url.trim()) return true;
    return /^(https?:\/\/)?(www\.)?linkedin\.com\/in\/[a-zA-Z0-9_\-\.]+\/?$/i.test(url.trim());
  };

  const isValidGitHub = (url: string) => {
    if (!url || !url.trim()) return true;
    return /^(https?:\/\/)?(www\.)?github\.com\/[a-zA-Z0-9_\-\.]+\/?$/i.test(url.trim());
  };

  // Builds the API payload from the resume form (shared by scoring, summary and PDF download)
  const buildResumePayload = () => {
    const list = (v: string) => v.split(',').map(x => x.trim()).filter(Boolean);
    const lines = (v: string) => v.split('\n').map(x => x.replace(/^[•\-*]\s*/, '').trim()).filter(Boolean);
    const projects = [
      { name: resumeForm.project1Title, stack: resumeForm.project1Stack, link: resumeForm.project1Link, bullets: lines(resumeForm.project1Bullets) },
      { name: resumeForm.project2Title, stack: resumeForm.project2Stack, link: resumeForm.project2Link, bullets: lines(resumeForm.project2Bullets) },
    ].filter(pr => pr.name.trim());
    return {
      name: resumeForm.name || userProfile?.full_name || 'Candidate',
      headline: resumeForm.headline || userProfile?.target_roles?.[0] || '',
      email: resumeForm.email || userProfile?.email,
      phone: resumeForm.phone,
      location: resumeForm.location,
      linkedin: resumeForm.linkedin,
      github: resumeForm.github,
      portfolio: resumeForm.portfolio,
      summary: resumeForm.summary,
      education: resumeForm.education,
      college: resumeForm.college,
      semester: resumeForm.gradYear,
      cgpa: resumeForm.cgpa || null,
      skills: list(resumeForm.skills),
      languages: list(resumeForm.languages),
      frameworks: list(resumeForm.frameworks),
      tools: list(resumeForm.tools),
      experience: resumeForm.experienceCompany ? [{
        company: resumeForm.experienceCompany,
        role: resumeForm.experienceRole,
        dates: resumeForm.experienceDuration,
        location: resumeForm.experienceLocation,
        bullets: lines(resumeForm.experienceBullets)
      }] : [],
      projects,
      certifications: list(resumeForm.certifications),
      achievements: list(resumeForm.achievements),
      interests: list(resumeForm.interests),
      is_fresher: userProfile?.role === 'Student' || !resumeForm.experienceCompany,
    };
  };

  const validateResumeLinks = () => {
    if (resumeForm.linkedin && !isValidLinkedIn(resumeForm.linkedin)) {
      alert('Please enter a valid LinkedIn profile URL (e.g. https://linkedin.com/in/username).');
      return false;
    }
    if (resumeForm.github && !isValidGitHub(resumeForm.github)) {
      alert('Please enter a valid GitHub profile URL (e.g. https://github.com/username).');
      return false;
    }
    return true;
  };

  const generateResumeSummary = async () => {
    if (!token) return;
    setSummaryLoading(true);
    try {
      const r = await fetch(`${BACKEND_URL}/resumes/generate-summary`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify(buildResumePayload())
      });
      const d = await r.json();
      if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : 'Could not write a summary.');
      setResumeForm(prev => ({ ...prev, summary: d.summary }));
    } catch (err: any) {
      alert(err.message || "Couldn't generate the summary. Check that the backend is running.");
    } finally {
      setSummaryLoading(false);
    }
  };

  const handleResumeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token || !validateResumeLinks()) return;
    setLoading(true);
    try {
      const r = await fetch(`${BACKEND_URL}/resumes/manual`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify(buildResumePayload())
      });
      const data = await r.json();
      if (!r.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'Could not score your resume.');
      setResumeAnalysis({ ...data, resume_data: buildResumePayload() });
      setResumeMode('preview');
      fetchProfile(token);
      fetchReadiness(token);
      fetchNotifications(token);
    } catch (err: any) {
      alert(err.message?.includes('fetch') ? "Can't reach the GapX server. Start the backend and try again." : (err.message || 'Error processing resume.'));
    } finally {
      setLoading(false);
    }
  };

  const downloadResumePdf = async () => {
    if (!token || !validateResumeLinks()) return;
    setResumePdfLoading(true);
    try {
      const response = await fetch(`${BACKEND_URL}/resumes/download-pdf`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify(buildResumePayload())
      });
      if (!response.ok) {
        const d = await response.json().catch(() => ({}));
        throw new Error(typeof d.detail === 'string' ? d.detail : 'Could not generate the PDF.');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const downloadName = (resumeForm.name || userProfile?.full_name || 'Candidate').replace(/\s+/g, '_');
      a.download = `${downloadName}_Resume.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      alert(err.message?.includes('fetch') ? "Can't reach the GapX server. Start the backend and try again." : (err.message || 'Error downloading resume PDF.'));
    } finally {
      setResumePdfLoading(false);
    }
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!token || !e.target.files?.[0]) return;
    const file = e.target.files[0];
    setUploadingPdf(true);
    setUploadedFileDetails({
      name: file.name,
      size: (file.size / 1024).toFixed(1) + ' KB',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    });

    const formData = new FormData();
    formData.append('file', file);
    try {
      const r = await fetch(`${BACKEND_URL}/resumes/upload`, {
        method: 'POST', headers: { Authorization: `Bearer ${token}` }, body: formData
      });
      if (r.ok) {
        const data = await r.json();
        setResumeAnalysis(data);
        setResumeMode('upload');
        fetchProfile(token); fetchReadiness(token); fetchNotifications(token);
      } else {
        const d = await r.json(); alert(d.detail || 'Upload failed');
      }
    } catch (err: any) { alert(err.message || 'Upload failed'); }
    finally { setUploadingPdf(false); }
  };

  // --- CODING MODULE HANDLERS ---
  const selectProblem = async (id: number) => {
    setCodeOutput(null); setCodingHint(''); setAiHintData(null);
    try {
      let p: any = null;
      if (token && !token.startsWith('local_')) {
        try {
          const r = await fetch(`${BACKEND_URL}/coding/problems/${id}`, { headers: { Authorization: `Bearer ${token}` } });
          if (r.ok) p = await r.json();
        } catch (_) {}
      }
      if (!p) {
        p = codingProblems.find(x => x.id === id) || INITIAL_PROBLEMS.find(x => x.id === id);
      }
      
      if (p) {
        setActiveProblem(p);
        setActiveCodeTab('description');
        setActiveOutputTab('testcases');
        setActiveTestCaseIdx(0);
        
        // Load draft for this user and language
        const userKey = userProfile?.email || 'guest';
        const localDraft = localStorage.getItem(`gapx_draft_${userKey}_${id}_${editorLang}`);
        if (localDraft) {
          setEditorCode(localDraft);
          lastSavedCodeRef.current = localDraft;
        } else if (!token.startsWith('local_')) {
          try {
            const draftR = await fetch(`${BACKEND_URL}/coding/problems/${id}/draft?language=${editorLang}`, { headers: authHeaders() });
            if (draftR.ok) {
              const draftData = await draftR.json();
              const starterMap: any = { python: p.starter_code_python, c: p.starter_code_c, cpp: p.starter_code_cpp, java: p.starter_code_java, javascript: p.starter_code_js };
              const chosenCode = draftData.code || starterMap[editorLang] || p.starter_code_python || '# Write solution here\n';
              setEditorCode(chosenCode);
              lastSavedCodeRef.current = chosenCode;
            } else {
              setEditorCode(p.starter_code_python || '# Write solution here\n');
            }
          } catch (_) {
            setEditorCode(p.starter_code_python || '# Write solution here\n');
          }
        } else {
          const starterMap: any = { python: p.starter_code_python, c: p.starter_code_c, cpp: p.starter_code_cpp, java: p.starter_code_java, javascript: p.starter_code_js };
          const defaultCode = starterMap[editorLang] || p.starter_code_python || '# Write solution here\n';
          setEditorCode(defaultCode);
          lastSavedCodeRef.current = defaultCode;
        }
      }
    } catch (_) {} finally { setLoading(false); }
  };

  const changeLang = async (lang: string) => {
    if (!activeProblem) return;
    // Save current language draft before switching
    if (editorCode && activeProblem) {
      saveCodeDraft(editorCode, activeProblem.id, editorLang);
    }
    
    setEditorLang(lang);
    const userKey = userProfile?.email || 'guest';
    const localDraft = localStorage.getItem(`gapx_draft_${userKey}_${activeProblem.id}_${lang}`);
    
    if (localDraft) {
      setEditorCode(localDraft);
      lastSavedCodeRef.current = localDraft;
    } else if (token && !token.startsWith('local_')) {
      try {
        const draftR = await fetch(`${BACKEND_URL}/coding/problems/${activeProblem.id}/draft?language=${lang}`, { headers: authHeaders() });
        if (draftR.ok) {
          const draftData = await draftR.json();
          const starterMap: any = { python: activeProblem.starter_code_python, c: activeProblem.starter_code_c, cpp: activeProblem.starter_code_cpp, java: activeProblem.starter_code_java, javascript: activeProblem.starter_code_js };
          const chosen = draftData.code || starterMap[lang] || '// Write solution here\n';
          setEditorCode(chosen);
          lastSavedCodeRef.current = chosen;
          return;
        }
      } catch (_) {}
      const starterMap: any = { python: activeProblem.starter_code_python, c: activeProblem.starter_code_c, cpp: activeProblem.starter_code_cpp, java: activeProblem.starter_code_java, javascript: activeProblem.starter_code_js };
      setEditorCode(starterMap[lang] || '// Write solution here\n');
    } else {
      const starterMap: any = { python: activeProblem.starter_code_python, c: activeProblem.starter_code_c, cpp: activeProblem.starter_code_cpp, java: activeProblem.starter_code_java, javascript: activeProblem.starter_code_js };
      setEditorCode(starterMap[lang] || '// Write solution here\n');
    }
  };

  const resetStarterCode = () => {
    if (!activeProblem) return;
    if (confirm('Reset editor to original starter template? Current changes for this language will be overwritten.')) {
      const starterMap: any = { python: activeProblem.starter_code_python, c: activeProblem.starter_code_c, cpp: activeProblem.starter_code_cpp, java: activeProblem.starter_code_java, javascript: activeProblem.starter_code_js };
      const templ = starterMap[editorLang] || '# Write solution here\n';
      setEditorCode(templ);
      saveCodeDraft(templ, activeProblem.id, editorLang);
    }
  };

  const runCode = async () => {
    if (!activeProblem) return;
    setSubmittingCode(true); setCodeOutput(null);
    try {
      const r = await fetch(`${BACKEND_URL}/coding/problems/${activeProblem.id}/run`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify({ code: editorCode, language: editorLang })
      });
      if (r.ok) {
        const d = await r.json();
        setCodeOutput(d);
        if (d.status !== 'Accepted' && d.error_details) {
          setActiveOutputTab('diagnostics');
        } else {
          setActiveOutputTab('testcases');
        }
      } else {
        const d = await r.json().catch(() => ({}));
        setCodeOutput({ status: 'Error', execution_time: 0, memory_usage: 0, message: typeof d.detail === 'string' ? d.detail : 'The run request failed.', test_results: [], error_details: null });
      }
    } catch (_) {
      setCodeOutput({
        status: 'Connection Error',
        execution_time: 0,
        memory_usage: 0,
        message: "Couldn't reach the GapX server, so your code wasn't run. Make sure the backend is running and try again.",
        test_results: [],
        ai_feedback: null,
        error_details: { error_type: 'Connection Error', explanation: "The code runner is part of the backend. Start it with run_app.bat (or uvicorn) and try again.", raw_trace: '' }
      });
      setActiveOutputTab('diagnostics');
    } finally { setSubmittingCode(false); }
  };

  const submitCode = async () => {
    if (!activeProblem) return;
    setSubmittingCode(true); setCodeOutput(null);
    try {
      const r = await fetch(`${BACKEND_URL}/coding/problems/${activeProblem.id}/submit`, {
        method: 'POST', headers: authHeaders(), body: JSON.stringify({ code: editorCode, language: editorLang })
      });
      if (r.ok) {
        const d = await r.json(); setCodeOutput(d);
        if (d.status !== 'Accepted' && d.error_details) {
          setActiveOutputTab('diagnostics');
        } else {
          setActiveOutputTab('testcases');
        }
        if (token) {
          fetchProblems(token); fetchProfile(token); fetchReadiness(token); fetchNotifications(token);
        }
      } else {
        const d = await r.json().catch(() => ({}));
        setCodeOutput({ status: 'Error', execution_time: 0, memory_usage: 0, message: typeof d.detail === 'string' ? d.detail : 'The submit request failed.', test_results: [], error_details: null });
      }
    } catch (_) {
      setCodeOutput({
        status: 'Connection Error',
        execution_time: 0,
        memory_usage: 0,
        message: "Couldn't reach the GapX server, so your code wasn't run. Make sure the backend is running and try again.",
        test_results: [],
        ai_feedback: null,
        error_details: { error_type: 'Connection Error', explanation: "The code runner is part of the backend. Start it with run_app.bat (or uvicorn) and try again.", raw_trace: '' }
      });
      setActiveOutputTab('diagnostics');
    } finally { setSubmittingCode(false); }
  };

  const requestSmartAiHint = async (level: number = 1) => {
    if (!activeProblem) return;
    setAiHintLoading(true);
    setAiHintLevel(level);
    setShowAiHintModal(true);
    try {
      if (token && !token.startsWith('local_')) {
        const r = await fetch(`${BACKEND_URL}/coding/problems/${activeProblem.id}/ai-hint`, {
          method: 'POST',
          headers: authHeaders(),
          body: JSON.stringify({
            code: editorCode,
            language: editorLang,
            hint_level: level
          })
        });
        if (r.ok) {
          const d = await r.json();
          setAiHintData(d);
          setCodingHint(d.current_hint);
          return;
        }
      }

      // Local fallback smart progressive hints
      const allHints = activeProblem.hints || [
        "Think about the optimal data structure (e.g. HashMap or Two Pointers).",
        "Keep track of previously processed elements to answer queries in O(1) time.",
        "Consider boundary cases like single elements, duplicate numbers, and negative inputs."
      ];
      const curHint = allHints[Math.min(level - 1, allHints.length - 1)];
      setAiHintData({
        title: activeProblem.title,
        hints: allHints,
        current_hint: curHint,
        approach: activeProblem.editorial || `Master this problem by applying ${activeProblem.category} techniques in ${activeProblem.expected_time_complexity || 'O(N)'} time.`,
        code_analysis: editorCode.length > 50 ? "Your current implementation structure is on the right path. Ensure your loop bounds, base cases, and return variables are correctly initialized." : null,
        edge_cases: ["Empty collection or 1-element input", "Duplicate values", "Extreme numerical limits"]
      });
      setCodingHint(curHint);
    } catch (_) {} finally {
      setAiHintLoading(false);
    }
  };

  // Tab change reactions: ensure problems, roadmap stages, and resume sync are always up to date
  useEffect(() => {
    if (sidebarTab === 'coding') {
      if (codingProblems.length === 0) {
        fetchProblems(token || '');
      }
      if (!activeProblem && codingProblems.length > 0) {
        selectProblem(codingProblems[0].id);
      }
    } else if (sidebarTab === 'roadmap') {
      if (!roadmap || !roadmap.stages_data) {
        fetchRoadmap(token || '');
      }
    } else if (sidebarTab === 'resume') {
      if (!resumeForm.name || !resumeForm.skills) {
        syncResumeWithProfile(userProfile, onboardData);
      }
      if (token) fetchResume(token);
    }
  }, [sidebarTab, codingProblems.length, activeProblem, roadmap, resumeForm.name, resumeForm.skills, syncResumeWithProfile, token, userProfile]);

  // --- INTERVIEW AUDIO INPUT (REAL-TIME SPEECH-TO-TEXT + WPM + FILLER WORDS + EQUALIZER) ---
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const animFrameRef = useRef<number | null>(null);

  const startVoiceRecording = async () => {
    if (typeof window === 'undefined') return;
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Chrome, Edge, or Brave.');
      return;
    }

    try {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (_) {}
      }

      // Initialize microphone stream analyzer for equalizer animation
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        audioStreamRef.current = stream;
        const AudioCtx = window.AudioContext || (window as any).webkitAudioContext;
        const audioCtx = new AudioCtx();
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 64;
        const source = audioCtx.createMediaStreamSource(stream);
        source.connect(analyser);

        audioContextRef.current = audioCtx;
        analyserRef.current = analyser;

        const dataArray = new Uint8Array(analyser.frequencyBinCount);
        const updateAudioMeter = () => {
          if (!analyserRef.current) return;
          analyserRef.current.getByteFrequencyData(dataArray);
          let sum = 0;
          for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
          const avg = sum / dataArray.length;
          setAudioLevel(Math.min(100, Math.round((avg / 128) * 100)));
          animFrameRef.current = requestAnimationFrame(updateAudioMeter);
        };
        updateAudioMeter();
      } catch (_) {}

      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      const startTime = Date.now();
      speakingStartTimeRef.current = startTime;

      recognition.onstart = () => {
        setIsRecording(true);
        setSilenceCountdown(null);
      };

      recognition.onresult = (event: any) => {
        let transcript = '';
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript;
        }

        if (transcript.trim()) {
          setCandidateResponse(transcript);

          // Calculate Speaking Pace (Words Per Minute)
          const words = transcript.trim().split(/\s+/);
          const elapsedMins = Math.max(0.1, (Date.now() - startTime) / 60000);
          const calculatedWpm = Math.min(220, Math.max(70, Math.round(words.length / elapsedMins)));
          setSpeechWpm(calculatedWpm);

          // Detect common filler words
          const lower = transcript.toLowerCase();
          const fillerMatches = lower.match(/\b(um|uh|like|basically|actually|sort of|you know|i mean)\b/g);
          setFillerWordsCount(fillerMatches ? fillerMatches.length : 0);

          // Auto-submit countdown after 4 seconds of speech silence
          if (silenceTimerRef.current) clearTimeout(silenceTimerRef.current);
          setSilenceCountdown(4);
          
          silenceTimerRef.current = setTimeout(() => {
            stopVoiceRecording();
            submitAnswerWithText(transcript);
          }, 4500);
        }
      };

      recognition.onerror = () => { stopVoiceRecording(); };
      recognition.onend = () => { setIsRecording(false); };

      recognition.start();
      recognitionRef.current = recognition;
    } catch (_) {
      setIsRecording(false);
    }
  };

  const stopVoiceRecording = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
    setSilenceCountdown(null);

    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (_) {}
      recognitionRef.current = null;
    }

    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach(t => t.stop());
      audioStreamRef.current = null;
    }
    if (audioContextRef.current) {
      try { audioContextRef.current.close(); } catch (_) {}
      audioContextRef.current = null;
    }

    setAudioLevel(0);
    setIsRecording(false);
  };

  // --- INTERVIEW ROOM EXECUTION ---
  const applyInterviewTurn = (d: any) => {
    if (d.phase) setInterviewPhase(d.phase);
    if (d.question_number) setQuestionNumber(d.question_number);
    if (d.total_questions) setTotalQuestions(d.total_questions);
    if (d.question_kind) setQuestionKind(d.question_kind);
    if (d.difficulty) setCurrentDifficulty(d.difficulty);
    if (d.difficulty_change) setDifficultyChange(d.difficulty_change);
    if (typeof d.current_live_score === 'number') setLiveInterviewScore(d.current_live_score);
    if (typeof d.confidence_metric === 'number') setLiveConfidenceMetric(d.confidence_metric);
    questionStartRef.current = Date.now();
    setQuestionElapsed(0);
  };

  const startInterview = async () => {
    if (!token) return;
    setLoading(true);
    setErrorMessage('');
    setInterviewFeedback(null);
    setInterviewMessages([]);
    setCurrentTurnCorrection(null);
    setDifficultyChange('same');
    setLiveInterviewScore(0);
    setLiveConfidenceMetric(0);
    faceSamplesRef.current = [];

    const track = INTERVIEW_TRACKS.find(t => t.id === topicDomain);
    const role = targetInterviewRole || track?.label || userProfile?.target_roles?.[0] || 'Software Engineer';
    if (!webcamEnabled) toggleWebcam();

    try {
      const r = await fetch(`${BACKEND_URL}/interviews/start`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({
          target_role: role,
          experience_level: experienceLevel || 'Fresher',
          interview_type: interviewType,
          job_description: jobDescription.trim() || undefined,
          track: topicDomain || undefined,
          num_questions: interviewLength,
        }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : 'Could not start the interview.');
      setInterviewId(d.interview_id);
      setInterviewTrackLabel(d.track_label || role);
      if (d.track && !topicDomain) setTopicDomain(d.track);
      applyInterviewTurn({ ...d, question_number: 1, question_kind: 'intro' });
      setInterviewMessages([{ role: 'interviewer', text: d.first_question, is_first: true }]);
      setInterviewStarted(true);
      speakInterviewerText(d.first_question);
    } catch (err: any) {
      const msg = err.message?.includes('fetch') ? "Can't reach the GapX server. Start the backend and try again." : err.message;
      setErrorMessage(msg);
      alert(msg);
    } finally {
      setLoading(false);
    }
  };

  const submitAnswerWithText = async (ansText?: string) => {
    const ans = (ansText || candidateResponse).trim();
    if (!ans || !interviewId) return;
    stopVoiceRecording();
    setLoading(true);
    const updatedMsgs = [...interviewMessages, { role: 'candidate', text: ans }];
    setInterviewMessages(updatedMsgs);
    setCandidateResponse('');

    try {
      const r = await fetch(`${BACKEND_URL}/interviews/${interviewId}/answer`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({
          answer: ans,
          audio_response: isRecording,
          wpm_metric: speechWpm,
          filler_words_count: fillerWordsCount,
          ...collectFaceMetrics(),
        }),
      });
      const d = await r.json();
      if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : 'The interviewer could not process that answer.');

      applyInterviewTurn(d);
      const correction = d.is_repeat ? null : {
        is_correct: d.is_correct,
        ai_correction: d.ai_correction,
        ideal_answer: d.ideal_answer,
        ai_immediate_feedback: d.ai_immediate_feedback,
        turn_score: d.turn_score,
      };
      if (correction) setCurrentTurnCorrection(correction);

      if (d.is_finished) {
        setInterviewMessages([...updatedMsgs, { role: 'interviewer', text: d.speech_text_to_speak, ...(correction || {}) }]);
        speakInterviewerText(d.speech_text_to_speak);
        const fbRes = await fetch(`${BACKEND_URL}/interviews/${interviewId}/feedback`, { headers: authHeaders() });
        if (fbRes.ok) setInterviewFeedback(await fbRes.json());
        setInterviewStarted(false);
        if (token) { fetchProfile(token); fetchReadiness(token); fetchNotifications(token); }
      } else {
        setInterviewMessages([
          ...updatedMsgs,
          { role: 'interviewer', text: d.next_question, spoken: d.speech_text_to_speak, kind: d.question_kind, ...(correction || {}) },
        ]);
        speakInterviewerText(d.speech_text_to_speak || d.next_question);
      }
    } catch (err: any) {
      setInterviewMessages(interviewMessages);
      setCandidateResponse(ans);
      alert(err.message?.includes('fetch') ? "Lost connection to the GapX server. Your answer is still in the box; try again." : err.message);
    } finally {
      setLoading(false);
      setIsRecording(false);
    }
  };

  const submitAnswer = () => submitAnswerWithText();

  const toggleWebcam = async () => {
    if (!webcamEnabled) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' }
        });
        webcamStreamRef.current = stream;
        setWebcamEnabled(true);
        if (webcamRef.current) {
          webcamRef.current.srcObject = stream;
          webcamRef.current.play().catch(() => {});
        }
      } catch (err) {
        console.error('Camera access error:', err);
      }
    } else {
      if (webcamStreamRef.current) {
        webcamStreamRef.current.getTracks().forEach(t => t.stop());
        webcamStreamRef.current = null;
      }
      if (webcamRef.current) {
        webcamRef.current.srcObject = null;
      }
      setWebcamEnabled(false);
    }
  };

  // --- LOCAL AI COACH KNOWLEDGE & RESPONSE GENERATOR ---
  function generateLocalMentorResponse(rawQuery: string, history: Message[]): { response: string; suggestions: string[] } {
    const q = rawQuery.trim();
    const qLower = q.toLowerCase();

    // Strict Topic Guardrail Check: Allows all DSA, engineering subjects, technical topics & career questions
    const outOfScopePatterns = [
      /\b(recipe|recipes|how to cook|how to bake|ingredient|ingredients|pasta recipe|pizza recipe|cake recipe|biryani recipe|bake a cake)\b/i,
      /\b(cook|bake|fry|boil)\s+(chicken|rice|paneer|curry|meat|fish|soup|pasta|egg|vegetable|mutton|food|meal|dinner|lunch|breakfast)\b/i,
      /\b(movie review|movie recommendation|latest movies|box office|who acted in|hollywood gossip|bollywood gossip|song lyrics|download song|bollywood|hollywood)\b/i,
      /\b(cricket|football|soccer|ipl|fifa|badminton|tennis|nba|olympics)\b/i,
      /\b(weather|forecast today|rain today|temperature outside|weather today|tomorrow weather)\b/i,
      /\b(paracetamol|medicine for|tablet for headache|cure disease|medical prescription|doctor prescription)\b/i,
      /\b(horoscope today|zodiac sign compatibility|astrology prediction)\b/i,
      /\b(how to get a girlfriend|how to get a boyfriend|dating tips|tinder profile tips|girlfriend|boyfriend|dating advice)\b/i,
    ];

    const hasTechOrEngineeringContext = /\b(engineering|science|math|physics|chemistry|mechanic|mechanical|electric|electrical|electronic|electronics|circuit|thermodynamic|thermodynamics|signal|control|computer|software|hardware|code|coding|algorithm|dsa|hash|map|hashmap|hashtable|hashing|system|design|app|api|program|project|database|developer|interview|placement|study|exam|course|college|career|work|job|skills)\b/i.test(qLower);

    const isExplicitlyOutOfScope = outOfScopePatterns.some(pat => pat.test(qLower)) && !hasTechOrEngineeringContext;

    if (isExplicitlyOutOfScope) {
      return {
        response: "I am designed only to answer questions related to interview, technical or communication skills only, so sorry I will not be able to answer this question.\n\nPlease feel free to ask me anything about:\n- 💻 **Technical & Coding**: Algorithms, data structures, system design, debugging, or code implementations.\n- 🎯 **Interview Preparation**: Behavioral questions, HR rounds, mock interview answers, and STAR frameworks.\n- 🗣️ **Communication Skills**: English fluency for interviews, articulation, body language, and placement communication.",
        suggestions: [
          "How to prepare for technical interviews?",
          "Solve Two Sum in Python",
          "Tips to improve communication skills for interviews"
        ]
      };
    }

    // Detect requested programming language
    let lang = 'python';
    if (/\b(c\+\+|cpp|in c\+\+)\b/.test(qLower)) lang = 'cpp';
    else if (/\b(c language|in c\b|c code)\b/.test(qLower) && !/c\+\+|cpp/.test(qLower)) lang = 'c';
    else if (/\b(java\b|in java)\b/.test(qLower) && !/javascript/.test(qLower)) lang = 'java';
    else if (/\b(javascript|js|in js|in javascript)\b/.test(qLower)) lang = 'javascript';

    // Hash Map / Hash Table / Hashing Deep Dive
    if (/hashmap|hash\s*map|hashtable|hash\s*table|hashing|separate\s*chaining|open\s*addressing/i.test(qLower)) {
      return {
        response: `### ⚡ Hash Map (Hash Table) Deep Dive & Architecture

A **Hash Map** (or Hash Table) is an associative data structure that maps keys to values, achieving **$\\mathcal{O}(1)$ average time complexity** for insertions, lookups, and deletions.

---

#### 🧩 1. Internal Working Mechanism
1. **Hash Function $h(\\text{key})$**: Computes an integer hash code from the key. A good hash function is deterministic and distributes keys uniformly.
2. **Index Compression**: The array index is calculated using modulo:
   $$\\text{index} = h(\\text{key}) \\pmod{\\text{capacity}}$$
   *(In Java / Python power-of-two arrays, this is optimized to bitwise AND: \`hash & (capacity - 1)\`)*.
3. **Bucket Array**: An internal array of contiguous memory slots. Each slot points to an entry, a linked list, or a balanced tree.
4. **Load Factor ($\\alpha$) & Dynamic Resizing (Rehashing)**:
   $$\\alpha = \\frac{\\text{Number of Stored Entries } (N)}{\\text{Total Capacity } (K)}$$
   - Standard threshold is **0.75** (e.g. Java's \`java.util.HashMap\`).
   - When $\\alpha > 0.75$, the table **doubles its capacity** and **rehashes** all existing keys into the new array. This amortizes insertions to $\\mathcal{O}(1)$.

---

#### ⚔️ 2. Collision Resolution Techniques

When two distinct keys produce the same bucket index ($h(k_1) \\equiv h(k_2)$), a collision occurs:

##### A. Separate Chaining (Open Hashing)
- Each bucket stores a linked list of entries that collided.
- **Java 8+ Optimization**: When a bucket's linked list length reaches **8 (TREEIFY_THRESHOLD)** and the table capacity is $\\ge 64$, the linked list converts into a **Red-Black Tree** (Self-Balancing BST). This changes worst-case lookup from $\\mathcal{O}(N)$ down to $\\mathcal{O}(\\log N)$!

##### B. Open Addressing (Closed Hashing)
All elements reside directly within the array itself. When a collision occurs, the algorithm probes alternative slots:
- **Linear Probing**: $h(k, i) = (h'(k) + i) \\pmod m$. Fast cache locality, but vulnerable to **primary clustering** (long contiguous blocks of occupied cells).
- **Quadratic Probing**: $h(k, i) = (h'(k) + c_1 i + c_2 i^2) \\pmod m$. Alleviates primary clustering.
- **Double Hashing**: $h(k, i) = (h_1(k) + i \\cdot h_2(k)) \\pmod m$. Uses a secondary hash function for probe step size; provides the best uniform spread.

---

#### ⏱️ 3. Time & Space Complexity

| Operation | Average Case | Worst Case (All Collide) | Java 8+ Treeified Worst Case |
| :--- | :--- | :--- | :--- |
| **Search / Get** | $\\mathcal{O}(1)$ | $\\mathcal{O}(N)$ | $\\mathcal{O}(\\log N)$ |
| **Insert / Put** | $\\mathcal{O}(1)$ amortized | $\\mathcal{O}(N)$ | $\\mathcal{O}(\\log N)$ |
| **Delete / Remove** | $\\mathcal{O}(1)$ | $\\mathcal{O}(N)$ | $\\mathcal{O}(\\log N)$ |
| **Space Complexity** | $\\mathcal{O}(N)$ | $\\mathcal{O}(N)$ | $\\mathcal{O}(N)$ |

---

#### 💻 4. Code Implementation (${lang.toUpperCase()}):
\`\`\`${lang}
${lang === 'java' ? `import java.util.HashMap;
import java.util.Map;

public class HashMapDemo {
    public static void main(String[] args) {
        Map<String, Integer> map = new HashMap<>();
        // O(1) Insertion
        map.put("Apple", 5);
        map.put("Banana", 3);
        
        // O(1) Lookup
        System.out.println("Apple: " + map.getOrDefault("Apple", 0));
        
        // Iterating entries
        for (Map.Entry<String, Integer> entry : map.entrySet()) {
            System.out.println(entry.getKey() + " -> " + entry.getValue());
        }
    }
}` : lang === 'cpp' ? `#include <iostream>
#include <unordered_map>
#include <string>

int main() {
    std::unordered_map<std::string, int> map;
    // O(1) Insertion
    map["Apple"] = 5;
    map["Banana"] = 3;

    // O(1) Lookup
    if (map.find("Apple") != map.end()) {
        std::cout << "Apple: " << map["Apple"] << "\\n";
    }
    return 0;
}` : lang === 'c' ? `#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define TABLE_SIZE 10

typedef struct Node {
    char key[50];
    int val;
    struct Node* next;
} Node;

Node* table[TABLE_SIZE];

unsigned int hash(const char* key) {
    unsigned int h = 0;
    while (*key) h = (h << 5) + *key++;
    return h % TABLE_SIZE;
}

void put(const char* key, int val) {
    unsigned int idx = hash(key);
    Node* cur = table[idx];
    while (cur) {
        if (strcmp(cur->key, key) == 0) { cur->val = val; return; }
        cur = cur->next;
    }
    Node* n = (Node*)malloc(sizeof(Node));
    strcpy(n->key, key); n->val = val;
    n->next = table[idx]; table[idx] = n;
}` : `# Python Dict (Built-in Optimized Hash Map)
freq_map = {}
nums = [1, 2, 2, 3, 3, 3]
for num in nums:
    freq_map[num] = freq_map.get(num, 0) + 1

# O(1) Lookup
print(f"Frequency of 3: {freq_map.get(3, 0)}")  # Output: 3

# Custom Hash Map with Separate Chaining:
class SimpleHashMap:
    def __init__(self, capacity=16):
        self.capacity = capacity
        self.buckets = [[] for _ in range(capacity)]

    def put(self, key, value):
        idx = hash(key) % self.capacity
        for i, (k, v) in enumerate(self.buckets[idx]):
            if k == key:
                self.buckets[idx][i] = (key, value)
                return
        self.buckets[idx].append((key, value))

    def get(self, key, default=None):
        idx = hash(key) % self.capacity
        for k, v in self.buckets[idx]:
            if k == key: return v
        return default`}
\`\`\`

---

#### 🏆 5. Top LeetCode & Interview Patterns
1. **Two Sum**: Complements lookup in single pass $\\mathcal{O}(N)$.
2. **Group Anagrams**: Use sorted word or char frequency tuple as the map key.
3. **Longest Consecutive Sequence**: Use \`HashSet\` for $\\mathcal{O}(1)$ neighbor lookups.
4. **Subarray Sum Equals K**: Cumulative prefix sum frequency hash map.
5. **LRU Cache**: Doubly Linked List + HashMap for $\\mathcal{O}(1)$ get and evict.`,
        suggestions: [
          'How does Java 8 HashMap Red-Black tree conversion work?',
          'Difference between HashMap and HashTable / ConcurrentHashMap',
          'Solve Group Anagrams using HashMap in Python'
        ]
      };
    }

    // 1. Specific Coding Algorithms
    // Two Sum
    if (qLower.includes('two sum') || qLower.includes('2 sum') || (qLower.includes('pair') && qLower.includes('target sum'))) {
      const code = lang === 'c' ? 
`#include <stdio.h>
#include <stdlib.h>

int* twoSum(int* nums, int numsSize, int target, int* returnSize) {
    *returnSize = 2;
    int* res = (int*)malloc(2 * sizeof(int));
    for (int i = 0; i < numsSize; i++) {
        for (int j = i + 1; j < numsSize; j++) {
            if (nums[i] + nums[j] == target) {
                res[0] = i; res[1] = j;
                return res;
            }
        }
    }
    return res;
}` : lang === 'java' ?
`import java.util.HashMap;
import java.util.Map;

public class Solution {
    public int[] twoSum(int[] nums, int target) {
        Map<Integer, Integer> map = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int complement = target - nums[i];
            if (map.containsKey(complement)) {
                return new int[] { map.get(complement), i };
            }
            map.put(nums[i], i);
        }
        return new int[]{};
    }
}` : lang === 'cpp' ?
`#include <vector>
#include <unordered_map>
using namespace std;

class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        unordered_map<int, int> map;
        for (int i = 0; i < nums.size(); i++) {
            int comp = target - nums[i];
            if (map.count(comp)) return {map[comp], i};
            map[nums[i]] = i;
        }
        return {};
    }
};` :
`def two_sum(nums: list[int], target: int) -> list[int]:
    """
    Finds two indices such that nums[i] + nums[j] == target.
    Time Complexity: O(N) | Space Complexity: O(N)
    """
    seen = {}
    for i, num in enumerate(nums):
        complement = target - num
        if complement in seen:
            return [seen[complement], i]
        seen[num] = i
    return []`;

      return {
        response: `### 💡 Two Sum Problem Solution & Guide\n\n#### 🎯 Optimal Approach (Hash Map / Hash Table):\nInstead of a quadratic $\\mathcal{O}(N^2)$ brute-force check, use a Hash Map to store each number's value and index as you iterate. For each element, look up \`target - nums[i]\` in $\\mathcal{O}(1)$ time.\n\n#### 💻 Code Implementation (${lang.toUpperCase()}):\n\`\`\`${lang}\n${code}\n\`\`\`\n\n#### ⏱️ Complexity Analysis:\n- **Time Complexity**: $\\mathcal{O}(N)$ — Single pass through the array.\n- **Space Complexity**: $\\mathcal{O}(N)$ — Hash map stores up to $N$ elements.\n\n#### ⚡ Interview Pro-Tips:\n- Clarify if the array is already sorted: if yes, you can use **Two Pointers** in $\\mathcal{O}(1)$ space!\n- Mention duplicate handling: storing the current element *after* checking ensures distinct index pairs.`,
        suggestions: ['Solve Two Sum II (Sorted Array)', 'Explain Three Sum approach', 'How to write unit tests for Two Sum']
      };
    }

    // Valid Parentheses
    if (qLower.includes('valid parentheses') || (qLower.includes('parentheses') && qLower.includes('stack')) || qLower.includes('balanced brackets')) {
      return {
        response: `### 💡 Valid Parentheses (LIFO Stack Pattern)\n\n#### 🎯 Core Mechanism:\nUse a **Stack** (Last-In, First-Out). Push opening brackets \`(\`, \`{\`, \`[\`. When encountering a closing bracket, check whether the stack top contains its matching opening bracket. If mismatched or stack is empty, return \`false\`.\n\n#### 💻 Python Implementation:\n\`\`\`python\ndef is_valid(s: str) -> bool:\n    stack = []\n    mapping = {')': '(', '}': '{', ']': '['}\n    for char in s:\n        if char in mapping:\n            top = stack.pop() if stack else '#'\n            if mapping[char] != top:\n                return False\n        else:\n            stack.append(char)\n    return len(stack) == 0\n\`\`\`\n\n#### ⏱️ Complexity Analysis:\n- **Time Complexity**: $\\mathcal{O}(N)$ — single pass through the string.\n- **Space Complexity**: $\\mathcal{O}(N)$ — stack stores opening characters.\n\n#### ⚡ Edge Cases:\n- String with odd length (instant \`false\`).\n- String starting with closing bracket (e.g. \`"]"\`).\n- Leftover opening brackets (e.g. \`"(("\`).`,
        suggestions: ['Trapping Rain Water with Stack', 'Min Stack Implementation', 'Next Greater Element Algorithm']
      };
    }

    // Reverse Linked List
    if (qLower.includes('reverse linked list') || (qLower.includes('reverse') && qLower.includes('list'))) {
      return {
        response: `### 💡 Reverse a Singly Linked List\n\n#### 🎯 Approach (Three Pointers: \`prev\`, \`curr\`, \`next_node\`):\nMaintain three pointers. At each node, save the next node, redirect \`curr.next\` to \`prev\`, and advance \`prev\` and \`curr\`.\n\n#### 💻 Implementation:\n\`\`\`python\nclass ListNode:\n    def __init__(self, val=0, next=None):\n        self.val = val\n        self.next = next\n\ndef reverse_list(head: ListNode) -> ListNode:\n    prev = None\n    curr = head\n    while curr:\n        next_node = curr.next\n        curr.next = prev\n        prev = curr\n        curr = next_node\n    return prev\n\`\`\`\n\n#### ⏱️ Complexity:\n- **Time**: $\\mathcal{O}(N)$ | **Space**: $\\mathcal{O}(1)$ auxiliary memory.\n- **Recursive Variant**: Can also be implemented recursively in $\\mathcal{O}(N)$ time with $\\mathcal{O}(N)$ call stack space.`,
        suggestions: ['Reverse Linked List II (between m and n)', 'Detect cycle in Linked List (Floyd Cycle Finding)', 'Merge Two Sorted Lists']
      };
    }

    // Binary Search
    if (qLower.includes('binary search') || qLower.includes('bsearch')) {
      return {
        response: `### 💡 Binary Search Algorithm\n\n#### 🎯 Mechanics:\nFor a sorted collection, repeatedly divide the search interval in half. Calculate \`mid = left + (right - left) // 2\` to prevent integer overflow.\n\n#### 💻 Implementation:\n\`\`\`python\ndef binary_search(nums: list[int], target: int) -> int:\n    left, right = 0, len(nums) - 1\n    while left <= right:\n        mid = left + (right - left) // 2\n        if nums[mid] == target:\n            return mid\n        elif nums[mid] < target:\n            left = mid + 1\n        else:\n            right = mid - 1\n    return -1\n\`\`\`\n\n#### ⏱️ Complexity:\n- **Time**: $\\mathcal{O}(\\log N)$ logarithmic runtime.\n- **Space**: $\\mathcal{O}(1)$ iterative space.`,
        suggestions: ['Search in Rotated Sorted Array', 'Find First and Last Position in Sorted Array', 'Binary Search on Answer Space']
      };
    }

    // 2. Core CS Concepts: OOP
    if (qLower.includes('oop') || qLower.includes('object oriented') || qLower.includes('polymorphism') || qLower.includes('encapsulation') || qLower.includes('inheritance')) {
      return {
        response: `### 🏛️ The 4 Core Pillars of Object-Oriented Programming (OOP)\n\n#### 1. Encapsulation:\nBundling data and methods into a single unit (class) while restricting direct access to internal state using private fields and getters/setters.\n\n#### 2. Abstraction:\nHiding internal implementation details and exposing only the essential high-level interfaces (e.g. abstract classes, interfaces).\n\n#### 3. Inheritance:\nAllowing a child class to inherit fields and behaviors from a parent class to promote reusability.\n\n#### 4. Polymorphism:\nThe ability for different classes to be treated as instances of the same superclass. Two types:\n- **Compile-Time (Overloading)**: Same method name with different parameters.\n- **Run-Time (Overriding)**: Child class implements a specific version of a method already defined in its parent.\n\n\`\`\`python\nclass Animal:\n    def speak(self): pass  # Abstraction\n\nclass Dog(Animal):\n    def speak(self): return "Woof!"  # Polymorphism (Overriding)\n\nclass Cat(Animal):\n    def speak(self): return "Meow!"\n\ndef animal_sound(animal: Animal):\n    print(animal.speak())\n\`\`\`\n\n#### ⚡ SOLID Principles Quick Reference:\n- **S**: Single Responsibility Principle\n- **O**: Open/Closed Principle\n- **L**: Liskov Substitution Principle\n- **I**: Interface Segregation Principle\n- **D**: Dependency Inversion Principle`,
        suggestions: ['Explain SOLID principles with code', 'Composition vs Inheritance', 'Design Patterns: Factory vs Singleton']
      };
    }

    // 3. Interview & Career: Tell me about yourself / FAANG / Resume / ATS
    if (qLower.includes('tell me about yourself') || qLower.includes('introduce yourself')) {
      return {
        response: `### 🎯 Mastering "Tell Me About Yourself" (The Winning Formula)\n\nUse the **Present - Past - Future** framework (90 seconds):\n\n1. **Present (30s)**: Where you are right now, your primary technical expertise, and recent high-impact project.\n2. **Past (30s)**: Relevant academic background, internships, and key accomplishments with quantifiable metrics.\n3. **Future (30s)**: Why this exact company and role aligns with your engineering aspirations.\n\n#### 📝 Model Script:\n> *"I am a Software Engineer specializing in scalable full-stack applications with Python, React, and relational databases. Recently, I architected a high-throughput platform that processes live queries with sub-100ms response times. Prior to this, I completed my degree in Computer Science where I led competitive coding initiatives and built open-source tools. What excites me most about this role is your team's work on distributed systems, and I'm eager to bring my problem-solving skills to scale your infrastructure."*`,
        suggestions: ['Answering "What is your biggest weakness?"', 'STAR method for behavioral questions', 'Salary negotiation tactics']
      };
    }

    if (qLower.includes('faang') || qLower.includes('tier 1') || qLower.includes('placement preparation') || qLower.includes('how to prepare')) {
      return {
        response: `### 🚀 Tier-1 Tech & FAANG Placement Preparation Blueprint\n\n#### 🗓️ Phase 1: Core DSA Mastery (4-6 Weeks):\n- Master **Patterns**, not memorized solutions: Two Pointers, Sliding Window, Fast/Slow Pointers, BFS/DFS, Top-K Heap, and Dynamic Programming.\n- Solve the **Blind 75** or **NeetCode 150** list with timed practice.\n\n#### 🏗️ Phase 2: System Design & CS Fundamentals (2-3 Weeks):\n- **CS Fundamentals**: OS (Processes/Threads/Deadlocks), DBMS (Indexing/ACID/Normalization), Networks (TCP/UDP, HTTP/HTTPS).\n- **High-Level Design**: Client-Server, Load Balancers, Caching (Redis), SQL vs NoSQL, and Message Queues (Kafka).\n\n#### 💼 Phase 3: Resume & Mock Interviews (2 Weeks):\n- Optimize resume for **ATS formatting** with strong action verbs and Google XYZ formula (*Accomplished [X], as measured by [Y], by doing [Z]*).\n- Conduct at least 5 live behavioral and technical mock interviews.`,
        suggestions: ['Top 20 System Design interview questions', 'How to get referrals on LinkedIn', 'Resume review checklist']
      };
    }

    if (qLower.includes('ats') || qLower.includes('resume') || qLower.includes('cv')) {
      return {
        response: `### 📄 High-Impact Resume & ATS Optimization Guide\n\n#### 🎯 Key ATS Formatting Rules:\n1. **Clean Single-Column Layout**: Avoid tables, graphics, multi-column templates, or text boxes that confuse parser bots.\n2. **Google XYZ Formula**: Structure every bullet point as: *"Accomplished [X], as measured by [Y], by doing [Z]"*.\n3. **Keyword Density**: Include exact technical skills matching job descriptions (e.g. *REST APIs, Docker, PostgreSQL, CI/CD*).\n4. **Standard Headings**: Use standard headings: *Education, Technical Skills, Projects, Experience, Certifications*.\n\n#### 📝 Bullet Point Before vs After:\n- ❌ *Built an e-commerce website using React and Node.*\n- ✅ *Architected full-stack e-commerce platform using React, Node.js, and PostgreSQL, reducing query latency by 38% and supporting 5,000+ simulated concurrent checkouts.*`,
        suggestions: ['Review my resume bullets', 'Top projects for software engineer resume', 'LinkedIn outreach template']
      };
    }

    // 4. System Design / Architecture / Microservices
    if (qLower.includes('system design') || qLower.includes('microservice') || qLower.includes('cache') || qLower.includes('redis') || qLower.includes('rest vs graphql')) {
      return {
        response: `### 🏗️ System Design & Distributed Architecture Blueprint\n\n#### 🎯 Key Architectural Pillars:\n1. **Horizontal Scaling & Load Balancing**: Distribute traffic across stateless application instances via Nginx / AWS ALB.\n2. **In-Memory Caching (Redis/Memcached)**: Cache frequent reads to drop database response times from 50ms to <2ms.\n3. **Database Scaling**: Read replicas for read-heavy workloads, connection pooling (PgBouncer), and sharding for massive datasets.\n4. **Asynchronous Processing**: Decouple intensive background tasks using message brokers like RabbitMQ or Apache Kafka.\n\n#### 💡 Common System Design Interview Framework:\n- **Step 1**: Clarify Requirements & Scope (DAU, Read/Write ratio, storage estimates).\n- **Step 2**: Define High-Level API contracts.\n- **Step 3**: Sketch Core Architecture Diagram.\n- **Step 4**: Deep dive into Bottlenecks & Single Points of Failure (SPOFs).`,
        suggestions: ['Design a URL Shortener (Bitly)', 'Cache Invalidation Strategies (Write-through vs Write-back)', 'CAP Theorem Explained']
      };
    }

    // 5. Universal Dynamic Response for Any Query
    const topicTitle = q.replace(/[?.,!]+$/, '').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
    const isCode = /\b(code|function|program|implement|algorithm|syntax|method|class|array|loop|string|tree|graph)\b/i.test(q);
    const isCareer = /\b(interview|job|company|hiring|salary|offer|project|fresher|intern|experience)\b/i.test(q);
    const isEngineering = /\b(engineering|thermodynamic|fluid|mechanic|mechanical|civil|electrical|electronic|circuit|transistor|semiconductor|diode|gate|fourier|laplace|calculus|matrix|derivative|integral|physics|chemistry|signal|control system|nyquist|microprocessor|sensor|actuator|power system|electromagnetic|maxwell|entropy|heat transfer|stress|strain|beam|finite element|aerodynamics|cad|cam)\b/i.test(q);

    let responseBody = '';
    if (isCode) {
      responseBody = `### 💻 Technical Guide: ${topicTitle}\n\n#### 🎯 Strategic Analysis & Approach:\nTo solve and implement **${q}** effectively:\n1. **Understand Constraints & Edge Cases**: Identify minimum/maximum input sizes, empty collections, duplicate values, and negative inputs.\n2. **Select Optimal Data Structures**: Choose structures that optimize running time (e.g. Hash Map for $\\mathcal{O}(1)$ lookups, Monotonic Stack for boundary scans, or Heaps for ranking).\n3. **Algorithm Blueprint**:\n   - Check edge conditions and return base cases early.\n   - Execute main processing loop with clear pointer or accumulator tracking.\n   - Verify time complexity adheres to industry standards (typically $\\mathcal{O}(N)$ or $\\mathcal{O}(N \\log N)$).\n\n#### 💡 Clean Code Implementation:\n\`\`\`${lang}\n# Production-grade template for: ${q}\ndef solve(*args, **kwargs):\n    # 1. Edge case guard\n    if not args:\n        return None\n        \n    # 2. Algorithm implementation\n    result = []\n    # Iterate and compute optimal solution\n    return result\n\`\`\`\n\n#### ⏱️ Performance & Trade-offs:\n- Analyze worst-case Big-O time and auxiliary space consumption.\n- Benchmark with large datasets to ensure memory overhead is minimized.`;
    } else if (isCareer) {
      responseBody = `### 🧭 Career & Placement Advisory: ${topicTitle}\n\n#### 🎯 Strategic Placement Analysis:\nRegarding **${q}**:\n\n1. **Core Industry Expectation**:\n   - Interviewers look for structured problem-solving, architectural awareness, and clear technical communication.\n   - Frame every response with measurable outcomes and specific engineering decisions.\n\n2. **Actionable Step-by-Step Plan**:\n   - **Step 1**: Solidify core fundamentals and build 2-3 end-to-end production-grade portfolio projects with live deployment links.\n   - **Step 2**: Benchmark your skills against standard Tier-1 job descriptions.\n   - **Step 3**: Practice timed coding sprints (25-35 minutes per Medium problem).\n\n3. **Interview Delivery Tip**:\n   - Think out loud. State your brute force idea first, explain why it is suboptimal, and then optimize to your final solution.`;
    } else if (isEngineering) {
      responseBody = `### ⚙️ Engineering Principles & Fundamentals: ${topicTitle}\n\n#### 🎯 Core Concept & Theoretical Foundations:\nWhen analyzing **${q}** across engineering disciplines:\n1. **Governing Physical Laws & Principles**:\n   - Understand the fundamental governing equations and boundary conditions dictating system behavior.\n   - Examine the operational trade-offs, transfer functions, and conservation laws (energy, momentum, mass, or charge).\n2. **Mathematical Formulation & Analytical Modeling**:\n   - Formulate the system state equations or characteristic differential relationships.\n   - Analyze stability margins, frequency responses, or thermodynamic efficiencies depending on the discipline.\n\n#### 🛠️ Practical Engineering Applications & Industrial Practices:\n- **Design & Synthesis**: Sizing components with appropriate safety margins, load factors, and tolerances.\n- **Noise, Losses & Thermal Dissipation**: Mitigating non-idealities, parasitics, mechanical vibration, or thermal bottlenecks.\n- **Quality & Standards**: Adhering to standard industrial specifications (e.g. IEEE, ASME, ISO, IEC).\n\n#### 🎓 Placement & Technical Assessment Focus:\n- In technical interviews and exams, examiners look for first-principles derivations, qualitative intuition behind the math, and how you evaluate real-world trade-offs under practical physical constraints.`;
    } else {
      responseBody = `### 💡 GapX AI Coach Insights: ${topicTitle}\n\n#### 🎯 Comprehensive Breakdown:\nHere is a structured, in-depth overview addressing **${q}**:\n\n1. **Fundamental Concept**:\n   - Gain a solid grasp of the core theoretical principles before applying specialized tooling.\n   - Break complex problems down into modular, independently testable sub-components.\n\n2. **Practical Application & Best Practices**:\n   - Write clean, self-documenting code with clear variable naming and robust error handling.\n   - Follow industry-standard design patterns to keep components maintainable and scalable.\n\n3. **Placement & Interview Relevance**:\n   - In technical interviews, demonstrate both depth of knowledge and practical engineering trade-offs.\n   - Be ready to discuss alternative approaches and why you selected your specific solution.`;
    }

    return {
      response: responseBody,
      suggestions: [
        `Deep dive into ${topicTitle} best practices`,
        `How is ${topicTitle} asked in tech interviews?`,
        `Related LeetCode coding patterns`
      ]
    };
  }

  // --- MENTOR ---
  const sendMentor = async (queryText?: string) => {
    const q = (queryText || mentorQuery).trim();
    if (!q || mentorLoading) return;
    const updated = [...mentorMessages, { role: 'user', text: q }];
    setMentorMessages(updated);
    setMentorQuery('');
    setMentorLoading(true);
    try {
      const headers: Record<string, string> = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = `Bearer ${token}`;

      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 6000);

      const r = await fetch(`${BACKEND_URL}/mentor/chat`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ message: q, history: mentorMessages.map(m => ({ role: m.role, text: m.text })) }),
        signal: controller.signal
      });
      clearTimeout(timeoutId);

      if (r.ok) {
        const d = await r.json();
        if (d && d.response) {
          setMentorMessages([...updated, { role: 'assistant', text: d.response }]);
          if (Array.isArray(d.suggestions) && d.suggestions.length > 0) {
            setMentorSuggestions(d.suggestions);
          }
          return;
        }
      }
      // If response not ok or response empty, fall back to rich local engine
      const fallback = generateLocalMentorResponse(q, mentorMessages);
      setMentorMessages([...updated, { role: 'assistant', text: fallback.response }]);
      setMentorSuggestions(fallback.suggestions);
    } catch (_) {
      // Local comprehensive AI Coach fallback engine — NEVER fails to answer
      const fallback = generateLocalMentorResponse(q, mentorMessages);
      setMentorMessages([...updated, { role: 'assistant', text: fallback.response }]);
      setMentorSuggestions(fallback.suggestions);
    } finally {
      setMentorLoading(false);
      setTimeout(() => {
        mentorMessagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  };

  // --- ADMIN ---
  const createProblem = async (e: React.FormEvent) => {
    e.preventDefault(); if (!token) return;
    setLoading(true);
    try {
      const r = await fetch(`${BACKEND_URL}/admin/problems`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({
          ...newProblem,
          expected_time_complexity: 'O(N)', expected_space_complexity: 'O(1)',
          test_cases: [{ input: newProblem.example_input, output: newProblem.example_output, is_hidden: false }]
        })
      });
      if (r.ok) { alert('Problem added!'); fetchProblems(token); }
      else { const d = await r.json(); alert(d.detail); }
    } catch (_) {} finally { setLoading(false); }
  };

  const readiness = () => {
    if (readinessData?.placement_readiness_score) return readinessData.placement_readiness_score;
    let s = 40;
    if (userProfile) s += Math.min(Math.floor((userProfile.xp || 0) / 100) * 3, 20);
    if (roadmap) s += Math.floor((roadmap.progress_percentage || 0) * 0.25);
    if (resumeAnalysis) s += Math.floor((resumeAnalysis.ats_score || 0) * 0.2);
    if (codingProblems.length > 0) {
      const solved = codingProblems.filter(p => p.is_solved).length;
      s += Math.floor((solved / codingProblems.length) * 15);
    }
    if (interviewFeedback) s += Math.floor((interviewFeedback.overall_score || 0) * 0.15);
    return Math.min(s, 100);
  };

  sessionExpiredRef.current = () => {
    if (!localStorage.getItem('gapx_session')) return;
    logout();
    setErrorMessage('Your session has expired. Please sign in again.');
  };

  const logout = () => {
    localStorage.removeItem('gapx_session');
    setAppState('auth');
    setAuthMode('login');
    setToken(null);
    setUserProfile(null);
    setEmail('');
    setPassword('');
    setFullName('');
    setErrorMessage('');
    setRoadmap(null);
    setResumeAnalysis(null);
    setCodingProblems([]);
    setActiveProblem(null);
    setCodeOutput(null);
    setCodingHint('');
    setAiHintData(null);
    setShowAiHintModal(false);
    setInterviewStarted(false);
    setInterviewFeedback(null);
    setNotifications([]);
    setReadinessData(null);
  };

  // ──────────────────────────────────────────────────────────────────────────
  // RENDER
  // ──────────────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex flex-col bg-zinc-950 text-white font-sans">

      {/* ── SPLASH ── */}
      <AnimatePresence>
        {appState === 'splash' && (
          <motion.div
            key="splash"
            className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-zinc-950"
            exit={{ opacity: 0 }} transition={{ duration: 0.6 }}
          >
            <motion.div
              className="mb-4 rounded-3xl shadow-2xl shadow-indigo-500/40"
              initial={{ scale: 0.6, opacity: 0, rotate: -12 }} animate={{ scale: 1, opacity: 1, rotate: 0 }}
              transition={{ type: 'spring', stiffness: 160, damping: 14 }}
            >
              <GapXLogo size={84} animated />
            </motion.div>
            <motion.h1
              className="text-4xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-violet-400"
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}
            >
              GapX AI
            </motion.h1>
            <p className="text-zinc-500 text-xs mt-2 tracking-widest uppercase">Skill Gap Intelligence Platform</p>
            <div className="mt-8 w-40 h-1 rounded-full bg-zinc-800 overflow-hidden">
              <motion.div className="h-full bg-gradient-to-r from-indigo-500 via-violet-500 to-fuchsia-500"
                initial={{ width: '0%' }} animate={{ width: '100%' }} transition={{ duration: 1.8, ease: 'easeInOut' }} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <AnimatePresence mode="wait">
      {appState !== 'splash' && (
      <motion.div
        key={appState}
        className="flex-1 flex flex-col"
        initial={{ opacity: 0, y: 28, scale: 0.985 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -28, scale: 0.985 }}
        transition={{ duration: 0.45, ease: [0.22, 1, 0.36, 1] }}
      >
      {/* ── AUTH ── */}
      {appState === 'auth' && (
        <div className="flex-1 flex items-center justify-center p-6 bg-zinc-950 min-h-screen">
          <motion.div
            className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-2xl p-8 shadow-2xl"
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
          >
            <div className="text-center mb-6">
              <GapXLogo size={56} className="mx-auto mb-3 drop-shadow-lg" />
              <h2 className="text-2xl font-bold">Welcome to GapX AI</h2>
              <p className="text-zinc-400 text-sm mt-1">Your AI-Powered Placement Coach</p>
            </div>

            {errorMessage && (
              <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 text-red-400 rounded-xl text-xs flex items-start gap-2">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            <form onSubmit={handleAuth} className="space-y-4">
              {authMode === 'register' && (
                <div className="relative">
                  <User className="absolute left-3 top-3 w-4 h-4 text-zinc-500" />
                  <input type="text" placeholder="Full Name" required value={fullName} onChange={e => setFullName(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-white" />
                </div>
              )}
              <div className="relative">
                <Mail className="absolute left-3 top-3 w-4 h-4 text-zinc-500" />
                <input type="text" placeholder="Email Address" required value={email} onChange={e => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-white" />
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-3 w-4 h-4 text-zinc-500" />
                <input type="password" placeholder="Password" required value={password} onChange={e => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 bg-zinc-800 border border-zinc-700 rounded-xl text-sm focus:outline-none focus:border-indigo-500 text-white" />
              </div>
              <button type="submit" disabled={loading}
                className="w-full py-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-semibold rounded-xl transition-all shadow-lg shadow-indigo-500/20 text-sm">
                {loading ? 'Please wait...' : (authMode === 'login' ? 'Sign In' : 'Create Account')}
              </button>
            </form>

            {(authConfig.google_client_id || authConfig.demo_login_enabled) && (
              <div className="relative my-5">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-zinc-800" /></div>
                <div className="relative flex justify-center"><span className="bg-zinc-900 px-3 text-xs text-zinc-500">or</span></div>
              </div>
            )}

            {/* Official Google button (rendered by Google Identity Services when configured) */}
            {authConfig.google_client_id && <div ref={googleBtnRef} className="flex justify-center min-h-[44px]" />}

            {authConfig.demo_login_enabled && (
              <button onClick={handleDemoLogin} disabled={loading} type="button"
                className="w-full mt-3 py-2.5 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-sm font-medium rounded-xl flex items-center justify-center gap-2 transition-colors">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Try the demo account
              </button>
            )}

            <p className="text-center text-xs text-zinc-500 mt-5">
              {authMode === 'login' ? "Don't have an account? " : 'Already registered? '}
              <button onClick={() => { setAuthMode(authMode === 'login' ? 'register' : 'login'); setErrorMessage(''); }}
                className="text-indigo-400 hover:underline font-semibold">
                {authMode === 'login' ? 'Create one' : 'Sign in'}
              </button>
            </p>
          </motion.div>
        </div>
      )}

      {/* ── ONBOARDING ── */}
      {appState === 'onboarding' && (
        <div className="flex-1 flex items-center justify-center p-6 min-h-screen bg-zinc-950">
          <div className="w-full max-w-2xl bg-zinc-900 border border-zinc-800 rounded-2xl p-8">
            {/* Steps bar */}
            <div className="flex items-center mb-8">
              {[1, 2, 3].map((s, i) => (
                <React.Fragment key={s}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0 transition-all ${onboardStep >= s ? 'bg-indigo-600 text-white' : 'bg-zinc-800 text-zinc-500'}`}>{s}</div>
                  {i < 2 && <div className={`flex-1 h-1 mx-2 rounded-full transition-colors ${onboardStep > s ? 'bg-indigo-600' : 'bg-zinc-800'}`} />}
                </React.Fragment>
              ))}
            </div>

            {/* ── STEP 1: DYNAMIC ROLE-BASED PROFILE ── */}
            {onboardStep === 1 && (
              <div>
                <h3 className="text-xl font-bold mb-1 text-white">Tell us about yourself</h3>
                <p className="text-zinc-400 text-xs mb-5">Select your background so we can personalize your placement roadmap and prep strategy.</p>
                
                <div className="space-y-5">
                  {/* Role Selector Tabs */}
                  <div>
                    <label className="text-xs text-zinc-400 uppercase font-semibold mb-2 block">I am currently a:</label>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      {[
                        { id: 'Student', label: '🎓 College Student', desc: 'Undergrad / Master student preparing for campus drives & internships' },
                        { id: 'Working Professional', label: '💼 Working Professional', desc: 'Employed engineer preparing for product company switches' },
                        { id: 'Career Switcher', label: '🔄 Career Switcher', desc: 'Transitioning from non-tech or different industry into tech' }
                      ].map(item => (
                        <button
                          key={item.id}
                          type="button"
                          onClick={() => setOnboardData({ ...onboardData, role: item.id })}
                          className={`p-3.5 rounded-xl border text-left transition-all cursor-pointer ${onboardData.role === item.id ? 'border-indigo-500 bg-indigo-500/10 shadow-sm shadow-indigo-500/20' : 'border-zinc-800 bg-zinc-800/40 hover:border-zinc-700'}`}
                        >
                          <div className={`text-xs font-bold ${onboardData.role === item.id ? 'text-indigo-300' : 'text-white'}`}>{item.label}</div>
                          <div className="text-[10px] text-zinc-400 mt-1 leading-snug">{item.desc}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* 1A. STUDENT SPECIFIC FORM */}
                  {onboardData.role === 'Student' && (
                    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-3.5 pt-2 border-t border-zinc-800">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">Degree &amp; Major</label>
                          <select
                            value={onboardData.degreeBranch}
                            onChange={e => setOnboardData({ ...onboardData, degreeBranch: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
                          >
                            <option value="B.Tech / B.E. - Computer Science & Engineering (CSE)">B.Tech / B.E. - Computer Science (CSE)</option>
                            <option value="B.Tech / B.E. - Information Technology (IT)">B.Tech / B.E. - Information Tech (IT)</option>
                            <option value="B.Tech / B.E. - AI & Machine Learning / Data Science">B.Tech / B.E. - AI &amp; Data Science</option>
                            <option value="BCA / MCA (Computer Applications)">BCA / MCA (Computer Applications)</option>
                            <option value="B.Tech / B.E. - Electronics & Communication (ECE)">B.Tech / B.E. - Electronics (ECE)</option>
                            <option value="B.Sc / M.Sc - Computer Science / IT">B.Sc / M.Sc - Computer Science</option>
                            <option value="Other Engineering / Technical Degree">Other Technical Degree</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">College / University Name</label>
                          <input
                            type="text"
                            placeholder="e.g. National Institute of Tech / State University"
                            value={onboardData.collegeName}
                            onChange={e => setOnboardData({ ...onboardData, collegeName: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-3.5">
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">Current Semester</label>
                          <select
                            value={onboardData.studentSemester}
                            onChange={e => setOnboardData({ ...onboardData, studentSemester: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
                          >
                            <option value="1st / 2nd Semester (1st Year)">1st Year (Sem 1-2)</option>
                            <option value="3rd / 4th Semester (2nd Year)">2nd Year (Sem 3-4)</option>
                            <option value="5th / 6th Semester (3rd Year)">3rd Year (Sem 5-6)</option>
                            <option value="7th / 8th Semester (Final Year)">Final Year (Sem 7-8)</option>
                            <option value="Recent Graduate / Fresher">Recent Graduate (Fresher)</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">Current CGPA / %</label>
                          <input
                            type="text"
                            placeholder="e.g. 8.4"
                            value={onboardData.cgpa}
                            onChange={e => setOnboardData({ ...onboardData, cgpa: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">Graduation Year</label>
                          <select
                            value={onboardData.gradYear}
                            onChange={e => setOnboardData({ ...onboardData, gradYear: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
                          >
                            <option value="2025">2025</option>
                            <option value="2026">2026</option>
                            <option value="2027">2027</option>
                            <option value="2028">2028</option>
                            <option value="2029">2029</option>
                          </select>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* 1B. WORKING PROFESSIONAL SPECIFIC FORM */}
                  {onboardData.role === 'Working Professional' && (
                    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-3.5 pt-2 border-t border-zinc-800">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">Current Company / Employer</label>
                          <input
                            type="text"
                            placeholder="e.g. Infosys, TCS, Accenture, Product Startup"
                            value={onboardData.currentCompany}
                            onChange={e => setOnboardData({ ...onboardData, currentCompany: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">Current Job Title / Designation</label>
                          <input
                            type="text"
                            placeholder="e.g. Associate Software Engineer / QA Tester"
                            value={onboardData.currentDesignation}
                            onChange={e => setOnboardData({ ...onboardData, currentDesignation: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-3.5">
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">Total Experience</label>
                          <select
                            value={onboardData.yearsOfExperience}
                            onChange={e => setOnboardData({ ...onboardData, yearsOfExperience: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
                          >
                            <option value="< 1 Year (Junior / Fresher)">&lt; 1 Year (Junior)</option>
                            <option value="1 - 2 Years (Associate / Mid)">1 - 2 Years</option>
                            <option value="2 - 4 Years (Experienced)">2 - 4 Years</option>
                            <option value="4 - 7 Years (Senior Engineer)">4 - 7 Years</option>
                            <option value="7+ Years (Lead / Staff)">7+ Years</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">Highest Degree</label>
                          <input
                            type="text"
                            placeholder="e.g. B.Tech CS / MCA"
                            value={onboardData.highestDegree}
                            onChange={e => setOnboardData({ ...onboardData, highestDegree: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">Notice Period</label>
                          <select
                            value={onboardData.noticePeriod}
                            onChange={e => setOnboardData({ ...onboardData, noticePeriod: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
                          >
                            <option value="Immediate (< 15 Days)">Immediate (&lt; 15 Days)</option>
                            <option value="1 Month (30 Days)">1 Month (30 Days)</option>
                            <option value="2 Months (60 Days)">2 Months (60 Days)</option>
                            <option value="3 Months (90 Days)">3 Months (90 Days)</option>
                            <option value="Serving Notice Currently">Serving Notice</option>
                            <option value="Casually Upskilling">Casually Upskilling</option>
                          </select>
                        </div>
                      </div>
                    </motion.div>
                  )}

                  {/* 1C. CAREER SWITCHER SPECIFIC FORM */}
                  {onboardData.role === 'Career Switcher' && (
                    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-3.5 pt-2 border-t border-zinc-800">
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">Current Domain / Background</label>
                          <select
                            value={onboardData.currentDomain}
                            onChange={e => setOnboardData({ ...onboardData, currentDomain: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
                          >
                            <option value="Mechanical / Civil / Core Engineering">Mechanical / Civil / Core Engineering</option>
                            <option value="Electrical / Instrumentation / Electronics">Electrical / Instrumentation</option>
                            <option value="Sales / Marketing / Business Operations">Sales / Marketing / Operations</option>
                            <option value="Banking / Finance / Accounting">Banking / Finance / Accounting</option>
                            <option value="Customer Support / BPO / Non-Tech Services">Support / BPO / Services</option>
                            <option value="Healthcare / Biotech / Pharma">Healthcare / Pharma / Biotech</option>
                            <option value="Other Non-IT Background">Other Non-IT Background</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">Current Role &amp; Organization</label>
                          <input
                            type="text"
                            placeholder="e.g. Quality Analyst at Manufacturing Plant"
                            value={onboardData.currentRoleCompany}
                            onChange={e => setOnboardData({ ...onboardData, currentRoleCompany: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-3 gap-3.5">
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">Years in Current Field</label>
                          <select
                            value={onboardData.yearsInDomain}
                            onChange={e => setOnboardData({ ...onboardData, yearsInDomain: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
                          >
                            <option value="< 1 Year (Fresh Transition)">&lt; 1 Year</option>
                            <option value="1 - 3 Years">1 - 3 Years</option>
                            <option value="3 - 5 Years">3 - 5 Years</option>
                            <option value="5+ Years">5+ Years</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">Target Tech Track</label>
                          <select
                            value={onboardData.switchGoal}
                            onChange={e => setOnboardData({ ...onboardData, switchGoal: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
                          >
                            <option value="Full Stack Web Development (React / Node / Next.js)">Full Stack Web Dev</option>
                            <option value="Backend & Cloud Engineering (Python / Java / Go)">Backend &amp; Cloud</option>
                            <option value="Data Analytics & Data Science">Data Analytics &amp; Science</option>
                            <option value="Artificial Intelligence & Machine Learning">AI &amp; Machine Learning</option>
                            <option value="DevOps & Cloud Infrastructure">DevOps &amp; Cloud</option>
                          </select>
                        </div>
                        <div>
                          <label className="text-xs text-zinc-400 mb-1 block font-medium">Switch Target Timeline</label>
                          <select
                            value={onboardData.transitionTimeline}
                            onChange={e => setOnboardData({ ...onboardData, transitionTimeline: e.target.value })}
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2.5 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
                          >
                            <option value="1 - 3 Months (Aggressive / Bootcamp)">1 - 3 Months</option>
                            <option value="3 - 6 Months (Standard Transition)">3 - 6 Months</option>
                            <option value="6 - 12 Months (Comprehensive Part-Time)">6 - 12 Months</option>
                          </select>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </div>
              </div>
            )}

            {/* ── STEP 2: SKILLS & LANGUAGES ── */}
            {onboardStep === 2 && (
              <div>
                <h3 className="text-xl font-bold mb-1 text-white">Skills &amp; Languages Baseline</h3>
                <p className="text-zinc-400 text-xs mb-5">Select what you already know so the AI avoids teaching you redundant concepts.</p>
                <div className="space-y-4">
                  <div>
                    <label className="text-xs text-zinc-400 uppercase font-semibold mb-2 block">Programming Languages Known</label>
                    <div className="flex flex-wrap gap-2">
                      {['Python', 'Java', 'C++', 'JavaScript', 'TypeScript', 'SQL', 'Go', 'Rust', 'Kotlin', 'C#'].map(l => (
                        <button
                          key={l}
                          type="button"
                          onClick={() => setOnboardData({ ...onboardData, languages: onboardData.languages.includes(l) ? onboardData.languages.filter(x => x !== l) : [...onboardData.languages, l] })}
                          className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${onboardData.languages.includes(l) ? 'border-indigo-500 bg-indigo-500/10 text-indigo-300 shadow-sm' : 'border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-white'}`}
                        >
                          {l}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div>
                    <label className="text-xs text-zinc-400 uppercase font-semibold mb-2 block">Frameworks &amp; Technical Tools</label>
                    <div className="flex flex-wrap gap-2">
                      {['React', 'Next.js', 'FastAPI', 'Node.js', 'PostgreSQL', 'MongoDB', 'Docker', 'Kubernetes', 'Git & GitHub', 'Machine Learning', 'Data Structures & Algorithms', 'System Design', 'Redis', 'AWS'].map(s => (
                        <button
                          key={s}
                          type="button"
                          onClick={() => setOnboardData({ ...onboardData, skills: onboardData.skills.includes(s) ? onboardData.skills.filter(x => x !== s) : [...onboardData.skills, s] })}
                          className={`px-3 py-1.5 rounded-lg border text-xs font-semibold transition-all cursor-pointer ${onboardData.skills.includes(s) ? 'border-violet-500 bg-violet-500/10 text-violet-300 shadow-sm' : 'border-zinc-700 text-zinc-400 hover:border-zinc-500 hover:text-white'}`}
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Add Custom Skill */}
                  <div className="pt-2">
                    <label className="text-xs text-zinc-400 mb-1 block font-medium">Add Other Custom Skills</label>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="e.g. GraphQL, Tailwind, PyTorch, Flutter, Spring Boot"
                        value={customSkill}
                        onChange={e => setCustomSkill(e.target.value)}
                        onKeyDown={e => {
                          if (e.key === 'Enter' && customSkill.trim()) {
                            e.preventDefault();
                            if (!onboardData.skills.includes(customSkill.trim())) {
                              setOnboardData({ ...onboardData, skills: [...onboardData.skills, customSkill.trim()] });
                            }
                            setCustomSkill('');
                          }
                        }}
                        className="flex-1 bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          if (customSkill.trim() && !onboardData.skills.includes(customSkill.trim())) {
                            setOnboardData({ ...onboardData, skills: [...onboardData.skills, customSkill.trim()] });
                            setCustomSkill('');
                          }
                        }}
                        className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-indigo-400 border border-zinc-700 rounded-xl text-xs font-bold transition-all cursor-pointer"
                      >
                        + Add
                      </button>
                    </div>
                  </div>

                  {/* Self Experience Rating */}
                  <div className="pt-2">
                    <label className="text-xs text-zinc-400 uppercase font-semibold mb-2 block">Current Technical Comfort Level</label>
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { id: 'Beginner', title: 'Beginner', sub: 'Syntax & basic scripts' },
                        { id: 'Intermediate', title: 'Intermediate', sub: 'Built full stack projects' },
                        { id: 'Advanced', title: 'Advanced', sub: 'Production & System Design' }
                      ].map(exp => (
                        <button
                          key={exp.id}
                          type="button"
                          onClick={() => setOnboardData({ ...onboardData, experienceLevel: exp.id })}
                          className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer ${onboardData.experienceLevel === exp.id ? 'border-indigo-500 bg-indigo-500/10 text-indigo-300' : 'border-zinc-800 bg-zinc-800/40 text-zinc-400 hover:border-zinc-700'}`}
                        >
                          <div className="text-xs font-bold text-white">{exp.title}</div>
                          <div className="text-[10px] text-zinc-400 mt-0.5">{exp.sub}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* ── STEP 3: TARGET ROLE & GOALS ── */}
            {onboardStep === 3 && (
              <div>
                <h3 className="text-xl font-bold mb-1 text-white">Target Role &amp; Learning Commitment</h3>
                <p className="text-zinc-400 text-xs mb-5">Select your primary placement goal so we customize coding problems, roadmaps, and mock interviews.</p>
                <div className="space-y-4">
                  <div>
                    <label className="text-xs text-zinc-400 uppercase font-semibold mb-2 block">Choose Your Target Job Track</label>
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 max-h-56 overflow-y-auto pr-1">
                      {[
                        { id: 'Software Engineer', title: 'Software Engineer', sub: 'DSA, Core CS & System Design' },
                        { id: 'Frontend Developer', title: 'Frontend Developer', sub: 'React, Next.js & Web Vitals' },
                        { id: 'Backend Developer', title: 'Backend Developer', sub: 'APIs, DBs, Microservices' },
                        { id: 'Full Stack Developer', title: 'Full Stack Developer', sub: 'End-to-end architectures' },
                        { id: 'AI / ML Engineer', title: 'AI / ML Engineer', sub: 'LLMs, PyTorch & MLOps' },
                        { id: 'DevOps & Cloud Engineer', title: 'DevOps & Cloud Engineer', sub: 'Docker, K8s & CI/CD' },
                        { id: 'Data Scientist', title: 'Data Scientist', sub: 'Analytics, ML & SQL' },
                        { id: 'Android Developer', title: 'Android Developer', sub: 'Kotlin, Compose & Android SDK' },
                        { id: 'Cloud Architect', title: 'Cloud Architect', sub: 'AWS, GCP & High Availability' }
                      ].map(r => (
                        <button
                          key={r.id}
                          type="button"
                          onClick={() => setOnboardData({ ...onboardData, targetRoles: [r.id] })}
                          className={`p-3 rounded-xl border text-left transition-all cursor-pointer ${onboardData.targetRoles.includes(r.id) ? 'border-indigo-500 bg-indigo-500/10 shadow-sm' : 'border-zinc-800 bg-zinc-800/40 hover:border-zinc-700'}`}
                        >
                          <div className={`text-xs font-bold ${onboardData.targetRoles.includes(r.id) ? 'text-indigo-300' : 'text-white'}`}>{r.title}</div>
                          <div className="text-[10px] text-zinc-400 mt-0.5">{r.sub}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                    <div>
                      <label className="text-xs text-zinc-400 mb-1 block font-medium">Expected Placement / Switch Date</label>
                      <input
                        type="text"
                        placeholder="e.g. June 2026 / Within 3 Months"
                        value={onboardData.expectedPlacement}
                        onChange={e => setOnboardData({ ...onboardData, expectedPlacement: e.target.value })}
                        className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                      />
                    </div>
                    <div>
                      <label className="text-xs text-zinc-400 mb-1 block font-medium">Daily Dedicated Study Commitment</label>
                      <div className="grid grid-cols-3 gap-2">
                        {[
                          { hours: 2, label: '1-2 hrs' },
                          { hours: 3, label: '3-4 hrs' },
                          { hours: 5, label: '5+ hrs' }
                        ].map(h => (
                          <button
                            key={h.hours}
                            type="button"
                            onClick={() => setOnboardData({ ...onboardData, learningHours: h.hours })}
                            className={`py-2 rounded-xl border text-xs font-bold transition-all cursor-pointer ${onboardData.learningHours === h.hours ? 'border-indigo-500 bg-indigo-500/20 text-indigo-300' : 'border-zinc-800 bg-zinc-800/40 text-zinc-400 hover:border-zinc-700'}`}
                          >
                            {h.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {errorMessage && <p className="text-red-400 text-xs mt-3">{errorMessage}</p>}

            <div className="flex justify-between mt-8 pt-5 border-t border-zinc-800">
              <button disabled={onboardStep === 1} onClick={() => setOnboardStep(p => p - 1)}
                className="px-4 py-2 border border-zinc-700 hover:bg-zinc-800 rounded-xl text-xs font-semibold disabled:opacity-30 cursor-pointer">
                Back
              </button>
              {onboardStep < 3
                ? <button onClick={() => setOnboardStep(p => p + 1)} className="px-5 py-2 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-xl text-xs font-semibold flex items-center gap-1 cursor-pointer">
                    Continue <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                : <button onClick={handleOnboard} disabled={loading} className="px-5 py-2 bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-xl text-xs font-semibold cursor-pointer">
                    {loading ? 'Generating Roadmap...' : 'Launch Dashboard'}
                  </button>
              }
            </div>
          </div>
        </div>
      )}

      {/* ── DASHBOARD ── */}
      {appState === 'dashboard' && (
        <div className="flex h-screen overflow-hidden">

          {/* Sidebar: stays fixed; scrolls on its own only if its content is taller than the screen */}
          <aside className="w-60 h-screen sticky top-0 bg-zinc-950 border-r border-zinc-800 flex flex-col flex-shrink-0 overflow-y-auto">
            <div className="p-5">
              <div className="flex items-center gap-2.5 mb-7">
                <GapXLogo size={32} className="flex-shrink-0" />
                <div>
                  <div className="text-sm font-bold">GapX AI</div>
                  <div className="text-[10px] text-zinc-500 uppercase tracking-widest">Premium</div>
                </div>
              </div>
              <nav className="space-y-1">
                {([
                  ['overview', 'Dashboard', LayoutDashboard],
                  ['roadmap', 'AI Roadmap', BookOpen],
                  ['resume', 'Resume Score', FileText],
                  ['coding', 'Coding Practice', Code2],
                  ['interview', 'Mock Interview', Video],
                  ['mentor', 'AI Coach', MessageSquare],
                  ['admin', 'Admin Panel', ShieldAlert],
                  ['profile', 'Settings', Settings],
                ] as [SidebarTab, string, any][]).map(([id, label, Icon]) => (
                  <button key={id} onClick={() => setSidebarTab(id)}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${sidebarTab === id ? 'bg-indigo-600/15 text-indigo-400 border-l-2 border-indigo-500' : 'text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900'}`}>
                    <Icon className={`w-4 h-4 flex-shrink-0 ${sidebarTab === id ? 'text-indigo-400' : 'text-zinc-500'}`} />
                    {label}
                  </button>
                ))}
              </nav>
            </div>
            <div className="mt-auto p-4 border-t border-zinc-800 flex items-center justify-between">
              <div className="flex items-center gap-2 overflow-hidden">
                <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-indigo-600 to-violet-600 flex items-center justify-center text-xs font-bold flex-shrink-0">
                  {userProfile?.full_name?.charAt(0)?.toUpperCase() || 'U'}
                </div>
                <div className="overflow-hidden">
                  <div className="text-xs font-bold text-white truncate">{userProfile?.full_name || 'User'}</div>
                  <div className="text-[10px] text-zinc-500 truncate">{userProfile?.email}</div>
                </div>
              </div>
              <button onClick={logout} className="text-zinc-500 hover:text-red-400 p-1.5 rounded-lg transition-colors flex-shrink-0">
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </aside>

          {/* Main area */}
          <main className="flex-1 flex flex-col overflow-hidden h-screen">
            {/* Topbar */}
            <header className="h-14 border-b border-zinc-800 px-6 flex items-center justify-between bg-zinc-950/80 backdrop-blur-sm sticky top-0 z-10 flex-shrink-0">
              <div className="flex items-center gap-3">
                <span className="text-sm font-semibold text-zinc-300 capitalize">{sidebarTab === 'overview' ? 'Dashboard' : sidebarTab}</span>
                {(userProfile?.streak || 0) > 0 && (
                  <div className="flex items-center gap-1 px-2 py-1 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-full text-[10px] font-bold">
                    <Flame className="w-3 h-3" /> {userProfile?.streak} Day Streak
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => setThemeMode(t => t === 'dark' ? 'light' : 'dark')}
                  title={themeMode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
                  aria-label="Toggle light and dark mode"
                  className="p-2 border border-zinc-800 rounded-lg hover:bg-zinc-800 text-zinc-400 transition-colors">
                  <motion.span key={themeMode} initial={{ rotate: -90, opacity: 0 }} animate={{ rotate: 0, opacity: 1 }} className="block">
                    {themeMode === 'dark' ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5 text-indigo-400" />}
                  </motion.span>
                </button>
                <button className="p-2 border border-zinc-800 rounded-lg hover:bg-zinc-800 text-zinc-400 transition-colors relative">
                  <Bell className="w-3.5 h-3.5" />
                  {notifications.filter(n => !n.is_read).length > 0 && (
                    <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
                  )}
                </button>
                {userProfile && (
                  <div className="px-2.5 py-1 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-lg text-[11px] font-bold">
                    LVL {userProfile.level} • {userProfile.xp} XP
                  </div>
                )}
              </div>
            </header>

            {/* Page content */}
            <div className="flex-1 overflow-y-auto p-6">
              <AnimatePresence mode="wait">
              <motion.div
                key={sidebarTab}
                initial={{ opacity: 0, x: 24 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -24 }}
                transition={{ duration: 0.28, ease: 'easeOut' }}
              >

              {/* ── OVERVIEW / REAL-TIME ANALYTICS DASHBOARD ── */}
              {sidebarTab === 'overview' && (() => {
                // 1. Real-Time Coding Practice Metrics
                const totalProblems = codingProblems.length || 30;
                const solvedProblems = codingProblems.filter(p => p.is_solved).length;
                const solvedEasy = codingProblems.filter(p => p.is_solved && p.difficulty === 'Easy').length;
                const totalEasy = Math.max(1, codingProblems.filter(p => p.difficulty === 'Easy').length || 10);
                const solvedMedium = codingProblems.filter(p => p.is_solved && p.difficulty === 'Medium').length;
                const totalMedium = Math.max(1, codingProblems.filter(p => p.difficulty === 'Medium').length || 15);
                const solvedHard = codingProblems.filter(p => p.is_solved && p.difficulty === 'Hard').length;
                const totalHard = Math.max(1, codingProblems.filter(p => p.difficulty === 'Hard').length || 5);
                const codingPct = Math.round((solvedProblems / totalProblems) * 100);

                // 2. Real-Time 8-Stage Roadmap Metrics
                const roadmapProgress = Number(roadmap?.progress_percentage || 0);
                const allRoadmapTopics = safeArray(roadmap?.stages_data).flatMap((s: any) => safeArray(s.topics));
                const completedRoadmapTopics = allRoadmapTopics.filter((t: any) => t.is_completed).length;
                const totalRoadmapTopics = Math.max(1, allRoadmapTopics.length || 16);
                const activeStage = safeArray(roadmap?.stages_data).find((s: any) => 
                  safeArray(s.topics).some((t: any) => !t.is_completed)
                ) || safeArray(roadmap?.stages_data)[0];

                // 3. Real-Time Resume ATS Metrics
                const atsScore = Number(resumeAnalysis?.ats_score || 0);

                // 4. Real-Time Mock Interview & Measured Confidence Metrics
                const interviewConfidence = interviewFeedback?.confidence_score ?? (interviewFeedback?.overall_score ? Math.round(interviewFeedback.overall_score * 0.95) : null);
                const interviewTech = interviewFeedback?.technical_score ?? null;
                const interviewComm = interviewFeedback?.communication_score ?? null;
                const interviewProblemSolving = interviewFeedback?.problem_solving_score ?? null;
                const interviewLeadership = interviewFeedback?.leadership_score ?? null;
                const interviewOverall = interviewFeedback?.overall_score ?? null;

                // 5. Dynamic Real-Time Placement Readiness Score
                const codingPts = Math.min(30, Math.round((solvedProblems / totalProblems) * 30));
                const roadmapPts = Math.min(30, Math.round((roadmapProgress / 100) * 30));
                const resumePts = Math.min(20, atsScore > 0 ? Math.round((atsScore / 100) * 20) : 5);
                const interviewPts = Math.min(20, interviewOverall ? Math.round((interviewOverall / 100) * 20) : (interviewConfidence ? Math.round((interviewConfidence / 100) * 18) : 5));
                const dynamicReadiness = Math.min(100, Math.max(15, codingPts + roadmapPts + resumePts + interviewPts));

                // 6. Domain Proficiency Benchmark Bar Chart Data (Replaces Spiderweb)
                const domainBenchmarkData = [
                  { name: 'Coding (DSA)', score: codingPct, target: 100, fill: '#6366f1', count: `${solvedProblems}/${totalProblems} Solved` },
                  { name: 'Roadmap (CS)', score: roadmapProgress, target: 100, fill: '#8b5cf6', count: `${completedRoadmapTopics}/${totalRoadmapTopics} Topics` },
                  { name: 'Resume (ATS)', score: atsScore, target: 100, fill: '#10b981', count: atsScore > 0 ? `${atsScore}% Fit` : 'Upload Resume' },
                  { name: 'Interview (Tech)', score: interviewTech || (interviewOverall ? Math.round(interviewOverall * 0.9) : 0), target: 100, fill: '#06b6d4', count: interviewTech ? `${interviewTech}% Rating` : 'Take Interview' },
                  { name: 'Confidence Score', score: interviewConfidence || 0, target: 100, fill: '#f59e0b', count: interviewConfidence ? `${interviewConfidence}% Assessed` : 'Pending Interview' }
                ];

                // 7. Pie / Donut Chart Data (Coding Practice Distribution)
                const codingPieData = [
                  { name: 'Easy Done', value: solvedEasy, fill: '#10b981' },
                  { name: 'Medium Done', value: solvedMedium, fill: '#f59e0b' },
                  { name: 'Hard Done', value: solvedHard, fill: '#ef4444' },
                  { name: 'Remaining', value: Math.max(0, totalProblems - solvedProblems), fill: '#27272a' }
                ].filter(d => d.value > 0);

                // 8. Dynamic Target Company Fit Data
                const companiesFit = [
                  { name: 'Google', role: 'Software Engineer', match: Math.min(99, Math.max(48, Math.round(dynamicReadiness * 0.95 + 4))), focus: 'DSA & System Design' },
                  { name: 'Microsoft', role: 'SDE-1', match: Math.min(99, Math.max(45, Math.round(dynamicReadiness * 0.92 + 7))), focus: 'Algorithms & OOP' },
                  { name: 'Amazon', role: 'SDE-1', match: Math.min(99, Math.max(46, Math.round(dynamicReadiness * 0.90 + 9))), focus: 'Leadership & Coding' },
                  { name: 'Atlassian', role: 'Graduate Dev', match: Math.min(99, Math.max(50, Math.round(dynamicReadiness * 0.88 + 11))), focus: 'Full Stack & APIs' },
                  { name: 'Apple', role: 'Core SWE', match: Math.min(99, Math.max(42, Math.round(dynamicReadiness * 0.93 + 5))), focus: 'Systems & Performance' }
                ];

                return (
                  <div className="space-y-6">
                    {/* Hero Header & Quick Action Launcher */}
                    <div className="bg-gradient-to-r from-zinc-900 via-zinc-900/90 to-zinc-900 border border-zinc-800 rounded-3xl p-6 relative overflow-hidden shadow-xl">
                      <div className="absolute top-0 right-0 w-96 h-96 bg-indigo-600/10 rounded-full blur-3xl pointer-events-none" />
                      <div className="absolute bottom-0 right-1/3 w-64 h-64 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none" />

                      <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                        <div>
                          <div className="flex items-center gap-2 mb-2 flex-wrap">
                            <span className="text-xs font-extrabold uppercase tracking-wider text-indigo-400 bg-indigo-500/10 px-2.5 py-1 rounded-lg border border-indigo-500/20 flex items-center gap-1.5">
                              <Sparkles className="w-3.5 h-3.5" /> Real-Time Placement Analytics
                            </span>
                            <span className="text-xs font-bold text-zinc-400 bg-zinc-800/80 px-2.5 py-1 rounded-lg border border-zinc-700/60 flex items-center gap-1.5">
                              <Target className="w-3.5 h-3.5 text-amber-400" /> Target: {roadmap?.target_role || userProfile?.target_roles?.[0] || 'Software Engineer'}
                            </span>
                          </div>
                          <h2 className="text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
                            Welcome back, <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-purple-300 to-emerald-400">{userProfile?.full_name || 'Engineer'}</span>
                          </h2>
                          <p className="text-xs text-zinc-400 mt-1 max-w-2xl leading-relaxed">
                            Your comprehensive career readiness is calibrated continuously from your active coding submissions, completed roadmap milestones, ATS resume scans, and mock interview performance.
                          </p>
                        </div>

                        {/* Fast Navigation Shortcut Pills */}
                        <div className="flex items-center gap-2 flex-wrap">
                          <button
                            onClick={() => setSidebarTab('coding')}
                            className="px-3.5 py-2 bg-indigo-600/20 hover:bg-indigo-600 border border-indigo-500/30 hover:border-indigo-500 text-indigo-300 hover:text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-sm group"
                          >
                            <Code2 className="w-3.5 h-3.5 group-hover:scale-110 transition-transform text-indigo-400 group-hover:text-white" /> Practice Coding
                          </button>
                          <button
                            onClick={() => setSidebarTab('roadmap')}
                            className="px-3.5 py-2 bg-purple-600/20 hover:bg-purple-600 border border-purple-500/30 hover:border-purple-500 text-purple-300 hover:text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-sm group"
                          >
                            <BookOpen className="w-3.5 h-3.5 group-hover:scale-110 transition-transform text-purple-400 group-hover:text-white" /> View Roadmap
                          </button>
                          <button
                            onClick={() => setSidebarTab('interview')}
                            className="px-3.5 py-2 bg-amber-600/20 hover:bg-amber-600 border border-amber-500/30 hover:border-amber-500 text-amber-300 hover:text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-sm group"
                          >
                            <Mic className="w-3.5 h-3.5 group-hover:scale-110 transition-transform text-amber-400 group-hover:text-white" /> Mock Interview
                          </button>
                          <button
                            onClick={() => setSidebarTab('resume')}
                            className="px-3.5 py-2 bg-emerald-600/20 hover:bg-emerald-600 border border-emerald-500/30 hover:border-emerald-500 text-emerald-300 hover:text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-sm group"
                          >
                            <FileText className="w-3.5 h-3.5 group-hover:scale-110 transition-transform text-emerald-400 group-hover:text-white" /> Resume Score
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* 4 Real-Time KPI Cards */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                      {/* Card 1: Placement Readiness */}
                      <div className="bg-zinc-900/90 border border-zinc-800/90 hover:border-indigo-500/40 rounded-2xl p-5 relative overflow-hidden transition-all shadow-sm group">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-[10px] font-extrabold uppercase tracking-wider text-zinc-400">Placement Readiness</span>
                          <div className="w-8 h-8 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400 group-hover:scale-110 transition-transform">
                            <Award className="w-4 h-4" />
                          </div>
                        </div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-3xl font-black text-white">{dynamicReadiness}%</span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${dynamicReadiness >= 75 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : dynamicReadiness >= 50 ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}`}>
                            {dynamicReadiness >= 75 ? 'Placement Ready' : dynamicReadiness >= 50 ? 'Accelerating' : 'Building Up'}
                          </span>
                        </div>
                        {/* Breakdown progress bar */}
                        <div className="mt-3 space-y-1.5">
                          <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden flex">
                            <div style={{ width: `${codingPts * 3.33}%` }} className="bg-indigo-500 h-full" title="Coding Contribution" />
                            <div style={{ width: `${roadmapPts * 3.33}%` }} className="bg-purple-500 h-full" title="Roadmap Contribution" />
                            <div style={{ width: `${resumePts * 5}%` }} className="bg-emerald-500 h-full" title="Resume Contribution" />
                            <div style={{ width: `${interviewPts * 5}%` }} className="bg-amber-500 h-full" title="Interview Contribution" />
                          </div>
                          <div className="flex justify-between text-[9px] text-zinc-500 font-medium">
                            <span className="text-indigo-400">Code {codingPts}p</span>
                            <span className="text-purple-400">Roadmap {roadmapPts}p</span>
                            <span className="text-emerald-400">Resume {resumePts}p</span>
                            <span className="text-amber-400">Interview {interviewPts}p</span>
                          </div>
                        </div>
                      </div>

                      {/* Card 2: Coding Practice Solved */}
                      <div className="bg-zinc-900/90 border border-zinc-800/90 hover:border-emerald-500/40 rounded-2xl p-5 relative overflow-hidden transition-all shadow-sm group">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-[10px] font-extrabold uppercase tracking-wider text-zinc-400">Problems Solved</span>
                          <div className="w-8 h-8 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 group-hover:scale-110 transition-transform">
                            <Code2 className="w-4 h-4" />
                          </div>
                        </div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-3xl font-black text-white">{solvedProblems}</span>
                          <span className="text-xs font-semibold text-zinc-500">/ {totalProblems} ({codingPct}%)</span>
                        </div>
                        <div className="mt-3 flex items-center gap-1.5 text-[10px]">
                          <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-bold border border-emerald-500/20">E: {solvedEasy}/{totalEasy}</span>
                          <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-400 font-bold border border-amber-500/20">M: {solvedMedium}/{totalMedium}</span>
                          <span className="px-1.5 py-0.5 rounded bg-rose-500/10 text-rose-400 font-bold border border-rose-500/20">H: {solvedHard}/{totalHard}</span>
                        </div>
                      </div>

                      {/* Card 3: 8-Stage Roadmap Progress */}
                      <div className="bg-zinc-900/90 border border-zinc-800/90 hover:border-purple-500/40 rounded-2xl p-5 relative overflow-hidden transition-all shadow-sm group">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-[10px] font-extrabold uppercase tracking-wider text-zinc-400">Roadmap Milestone</span>
                          <div className="w-8 h-8 rounded-xl bg-purple-500/10 border border-purple-500/20 flex items-center justify-center text-purple-400 group-hover:scale-110 transition-transform">
                            <BookOpen className="w-4 h-4" />
                          </div>
                        </div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-3xl font-black text-white">{roadmapProgress}%</span>
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-purple-500/10 text-purple-300 border border-purple-500/20">
                            {completedRoadmapTopics}/{totalRoadmapTopics} Topics
                          </span>
                        </div>
                        <div className="text-[11px] text-zinc-400 mt-2.5 truncate flex items-center gap-1">
                          <Compass className="w-3.5 h-3.5 text-purple-400 flex-shrink-0" />
                          <span className="truncate">{activeStage?.title || 'Core Fundamentals'}</span>
                        </div>
                      </div>

                      {/* Card 4: Mock Interview Confidence */}
                      <div className="bg-zinc-900/90 border border-zinc-800/90 hover:border-amber-500/40 rounded-2xl p-5 relative overflow-hidden transition-all shadow-sm group">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-[10px] font-extrabold uppercase tracking-wider text-zinc-400">Interview Confidence</span>
                          <div className="w-8 h-8 rounded-xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center text-amber-400 group-hover:scale-110 transition-transform">
                            <Zap className="w-4 h-4" />
                          </div>
                        </div>
                        <div className="flex items-baseline gap-2">
                          <span className="text-3xl font-black text-white">{interviewConfidence ? `${interviewConfidence}%` : 'Pending'}</span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${interviewConfidence >= 80 ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : interviewConfidence ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-zinc-800 text-zinc-400 border border-zinc-700'}`}>
                            {interviewConfidence >= 80 ? 'High Confidence' : interviewConfidence ? 'Developing' : 'Not Evaluated'}
                          </span>
                        </div>
                        <div className="text-[10px] text-zinc-500 mt-2.5 flex items-center justify-between">
                          <span>Tech: <strong className="text-cyan-400">{interviewTech ? `${interviewTech}%` : '--'}</strong></span>
                          <span>Comm: <strong className="text-amber-400">{interviewComm ? `${interviewComm}%` : '--'}</strong></span>
                          <span>XP: <strong className="text-green-400">+{userProfile?.xp || 0}</strong></span>
                        </div>
                      </div>
                    </div>

                    {/* Central Analytics: Colorful Bar Chart + Coding Mastery Donut Chart */}
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                      
                      {/* Left: Domain Competency & Industry Benchmark (VIBRANT BAR CHART) */}
                      <div className="lg:col-span-2 bg-zinc-900/90 border border-zinc-800/90 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-4 pb-3 border-b border-zinc-800/80">
                          <div>
                            <div className="flex items-center gap-2">
                              <Activity className="w-4 h-4 text-indigo-400" />
                              <h3 className="text-sm font-bold text-white">Live Competency & Placement Benchmarks</h3>
                            </div>
                            <p className="text-[11px] text-zinc-400 mt-0.5">Real-time performance across core pillars compared against target benchmarks (100%)</p>
                          </div>
                          <div className="flex items-center gap-3 text-[10px]">
                            <div className="flex items-center gap-1.5 text-zinc-300">
                              <span className="w-2.5 h-2.5 rounded-sm bg-indigo-500 inline-block" /> Your Score
                            </div>
                            <div className="flex items-center gap-1.5 text-zinc-400">
                              <span className="w-2.5 h-2.5 rounded-sm bg-zinc-700 inline-block" /> Target (100)
                            </div>
                          </div>
                        </div>

                        {/* Bar Chart Container */}
                        <div className="h-64 w-full">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                              data={domainBenchmarkData}
                              margin={{ top: 10, right: 10, left: -20, bottom: 25 }}
                            >
                              <CartesianGrid strokeDasharray="3 3" stroke="#27272a" vertical={false} />
                              <XAxis
                                dataKey="name"
                                stroke="#71717a"
                                fontSize={11}
                                tickLine={false}
                                interval={0}
                                angle={-15}
                                textAnchor="end"
                              />
                              <YAxis
                                stroke="#71717a"
                                fontSize={11}
                                domain={[0, 100]}
                                tickLine={false}
                                tickFormatter={(v) => `${v}%`}
                              />
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: '#18181b',
                                  borderColor: '#3f3f46',
                                  borderRadius: '12px',
                                  fontSize: '11px',
                                  color: '#fff',
                                  boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)'
                                }}
                                formatter={(value: any, name: string, item: any) => [
                                  `${value}% (${item.payload.count})`,
                                  'Current Mastery'
                                ]}
                              />
                              <Bar dataKey="score" radius={[6, 6, 0, 0]} maxBarSize={48}>
                                {domainBenchmarkData.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={entry.fill} />
                                ))}
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </div>

                        {/* Domain Legend Cards */}
                        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mt-4 pt-3 border-t border-zinc-800/80">
                          {domainBenchmarkData.map((d) => (
                            <div key={d.name} className="bg-zinc-800/50 border border-zinc-800 rounded-xl p-2 text-center">
                              <div className="text-[10px] text-zinc-400 truncate">{d.name}</div>
                              <div className="text-sm font-black mt-0.5" style={{ color: d.fill }}>{d.score}%</div>
                              <div className="text-[9px] text-zinc-500 truncate">{d.count}</div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Right: Coding Practice Distribution (PIE / DONUT CHART) */}
                      <div className="bg-zinc-900/90 border border-zinc-800/90 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
                        <div className="flex items-center justify-between mb-2 pb-3 border-b border-zinc-800/80">
                          <div>
                            <div className="flex items-center gap-2">
                              <Code2 className="w-4 h-4 text-emerald-400" />
                              <h3 className="text-sm font-bold text-white">Coding Difficulty Mastery</h3>
                            </div>
                            <p className="text-[11px] text-zinc-400 mt-0.5">Distribution of 30 LeetCode problems</p>
                          </div>
                          <span className="text-xs font-extrabold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-lg border border-emerald-500/20">
                            {codingPct}% Done
                          </span>
                        </div>

                        {/* Donut Chart */}
                        <div className="h-44 w-full relative flex items-center justify-center">
                          <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                              <Pie
                                data={codingPieData}
                                cx="50%"
                                cy="50%"
                                innerRadius={48}
                                outerRadius={68}
                                paddingAngle={3}
                                dataKey="value"
                              >
                                {codingPieData.map((entry, index) => (
                                  <Cell key={`pie-cell-${index}`} fill={entry.fill} />
                                ))}
                              </Pie>
                              <Tooltip
                                contentStyle={{
                                  backgroundColor: '#18181b',
                                  borderColor: '#3f3f46',
                                  borderRadius: '10px',
                                  fontSize: '11px',
                                  color: '#fff'
                                }}
                              />
                            </PieChart>
                          </ResponsiveContainer>
                          {/* Inner center counter */}
                          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                            <span className="text-xl font-black text-white">{solvedProblems}</span>
                            <span className="text-[9px] uppercase font-bold text-zinc-500">Solved</span>
                          </div>
                        </div>

                        {/* Difficulty Breakdown Bars */}
                        <div className="space-y-2 mt-2 pt-2 border-t border-zinc-800/80">
                          {/* Easy */}
                          <div>
                            <div className="flex justify-between text-[11px] font-semibold mb-1">
                              <span className="text-emerald-400 flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-emerald-500" /> Easy
                              </span>
                              <span className="text-zinc-300">{solvedEasy} / {totalEasy}</span>
                            </div>
                            <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                              <div className="bg-emerald-500 h-full rounded-full transition-all" style={{ width: `${Math.round((solvedEasy / totalEasy) * 100)}%` }} />
                            </div>
                          </div>
                          {/* Medium */}
                          <div>
                            <div className="flex justify-between text-[11px] font-semibold mb-1">
                              <span className="text-amber-400 flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-amber-500" /> Medium
                              </span>
                              <span className="text-zinc-300">{solvedMedium} / {totalMedium}</span>
                            </div>
                            <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                              <div className="bg-amber-500 h-full rounded-full transition-all" style={{ width: `${Math.round((solvedMedium / totalMedium) * 100)}%` }} />
                            </div>
                          </div>
                          {/* Hard */}
                          <div>
                            <div className="flex justify-between text-[11px] font-semibold mb-1">
                              <span className="text-rose-400 flex items-center gap-1">
                                <span className="w-2 h-2 rounded-full bg-rose-500" /> Hard
                              </span>
                              <span className="text-zinc-300">{solvedHard} / {totalHard}</span>
                            </div>
                            <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                              <div className="bg-rose-500 h-full rounded-full transition-all" style={{ width: `${Math.round((solvedHard / totalHard) * 100)}%` }} />
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Bottom Row: Real Mock Interview Diagnostic Card + AI Target Company Match */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                      {/* Mock Interview Real-Time Diagnostic & Confidence */}
                      <div className="bg-zinc-900/90 border border-zinc-800/90 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
                        <div>
                          <div className="flex items-center justify-between pb-3 mb-4 border-b border-zinc-800/80">
                            <div>
                              <div className="flex items-center gap-2">
                                <Mic className="w-4 h-4 text-amber-400" />
                                <h3 className="text-sm font-bold text-white">Mock Interview & Confidence Telemetry</h3>
                              </div>
                              <p className="text-[11px] text-zinc-400 mt-0.5">Real-time evaluation from your latest mock interview session</p>
                            </div>
                            <button
                              onClick={() => setSidebarTab('interview')}
                              className="px-3 py-1 bg-amber-500/10 hover:bg-amber-500 text-amber-300 hover:text-black rounded-lg text-xs font-bold transition-all border border-amber-500/20 cursor-pointer flex items-center gap-1"
                            >
                              {interviewFeedback ? 'Practice Again' : 'Start Interview'} <ArrowUpRight className="w-3 h-3" />
                            </button>
                          </div>

                          {interviewFeedback ? (
                            <div className="space-y-4">
                              {/* Confidence Gauge Pill */}
                              <div className="bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent border border-amber-500/20 rounded-2xl p-4 flex items-center justify-between">
                                <div>
                                  <span className="text-[10px] font-extrabold uppercase tracking-wider text-amber-400">Calibrated Confidence Score</span>
                                  <div className="text-2xl font-black text-white mt-0.5">{interviewConfidence}%</div>
                                  <p className="text-[11px] text-zinc-400 mt-0.5">Measured across pacing, articulation clarity, and answer delivery</p>
                                </div>
                                <div className="text-right">
                                  <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-500/30">
                                    {interviewConfidence >= 80 ? '🔥 Placement Confident' : '⚡ Developing Fluency'}
                                  </span>
                                  <div className="text-[10px] text-zinc-500 mt-1.5">Role: {interviewFeedback.target_role || 'Software Engineer'}</div>
                                </div>
                              </div>

                              {/* 4 Score Badges */}
                              <div className="grid grid-cols-4 gap-2 text-center">
                                <div className="bg-zinc-800/60 border border-zinc-800 rounded-xl p-2.5">
                                  <div className="text-[10px] text-zinc-400 font-semibold">Technical</div>
                                  <div className="text-base font-extrabold text-cyan-400 mt-0.5">{interviewTech || 0}%</div>
                                </div>
                                <div className="bg-zinc-800/60 border border-zinc-800 rounded-xl p-2.5">
                                  <div className="text-[10px] text-zinc-400 font-semibold">Communication</div>
                                  <div className="text-base font-extrabold text-amber-400 mt-0.5">{interviewComm || 0}%</div>
                                </div>
                                <div className="bg-zinc-800/60 border border-zinc-800 rounded-xl p-2.5">
                                  <div className="text-[10px] text-zinc-400 font-semibold">Problem Solving</div>
                                  <div className="text-base font-extrabold text-indigo-400 mt-0.5">{interviewProblemSolving || 0}%</div>
                                </div>
                                <div className="bg-zinc-800/60 border border-zinc-800 rounded-xl p-2.5">
                                  <div className="text-[10px] text-zinc-400 font-semibold">Overall</div>
                                  <div className="text-base font-extrabold text-emerald-400 mt-0.5">{interviewOverall || 0}%</div>
                                </div>
                              </div>

                              {/* AI Immediate Key Feedback snippet */}
                              {interviewFeedback.feedback && typeof interviewFeedback.feedback === 'object' && (
                                <div className="bg-zinc-800/40 border border-zinc-800 rounded-xl p-3 text-xs text-zinc-300">
                                  <div className="text-[10px] uppercase font-bold text-indigo-400 mb-1 flex items-center gap-1">
                                    <Lightbulb className="w-3 h-3 text-indigo-400" /> AI Coach Recommendation
                                  </div>
                                  <p className="text-[11px] leading-relaxed text-zinc-300">
                                    {typeof interviewFeedback.feedback.summary === 'string'
                                      ? interviewFeedback.feedback.summary
                                      : 'Maintain structured STAR format for behavioral questions and verbalize time complexity before writing solution code.'}
                                  </p>
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="text-center py-8 bg-zinc-800/30 border border-zinc-800/60 rounded-2xl p-6">
                              <Mic className="w-10 h-10 mx-auto mb-2 text-amber-400/50" />
                              <h4 className="text-sm font-bold text-white">No Mock Interview Completed Yet</h4>
                              <p className="text-xs text-zinc-400 mt-1 max-w-sm mx-auto">
                                Take a 5-question AI mock interview with speech recognition to calibrate your live confidence score and verbal performance.
                              </p>
                              <button
                                onClick={() => setSidebarTab('interview')}
                                className="mt-4 px-4 py-2 bg-amber-500 hover:bg-amber-400 text-black rounded-xl text-xs font-bold transition-all inline-flex items-center gap-1.5 cursor-pointer shadow-md"
                              >
                                <Zap className="w-3.5 h-3.5" /> Start 1st Mock Interview (+300 XP)
                              </button>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* AI Matched Target Companies & Real Readiness Match */}
                      <div className="bg-zinc-900/90 border border-zinc-800/90 rounded-3xl p-6 shadow-sm flex flex-col justify-between">
                        <div>
                          <div className="flex items-center justify-between pb-3 mb-4 border-b border-zinc-800/80">
                            <div>
                              <div className="flex items-center gap-2">
                                <TrendingUp className="w-4 h-4 text-green-400" />
                                <h3 className="text-sm font-bold text-white">AI Target Company Hiring Match</h3>
                              </div>
                              <p className="text-[11px] text-zinc-400 mt-0.5">Calculated from your live coding mastery, roadmap completion, and ATS compatibility</p>
                            </div>
                            <span className="text-[10px] font-bold text-indigo-300 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                              Tier-1 Benchmark
                            </span>
                          </div>

                          <div className="space-y-2.5">
                            {companiesFit.map((comp) => (
                              <div
                                key={comp.name}
                                className="p-3 bg-zinc-800/50 hover:bg-zinc-800/80 border border-zinc-800 hover:border-zinc-700 rounded-2xl flex items-center justify-between gap-3 transition-all"
                              >
                                <div className="flex items-center gap-3">
                                  <div className="w-9 h-9 rounded-xl bg-zinc-700/60 border border-zinc-600/50 flex items-center justify-center font-black text-xs text-white">
                                    {comp.name[0]}
                                  </div>
                                  <div>
                                    <div className="text-xs font-bold text-white flex items-center gap-2">
                                      {comp.name}
                                      <span className="text-[10px] text-zinc-400 font-normal">({comp.role})</span>
                                    </div>
                                    <div className="text-[10px] text-zinc-500 mt-0.5">Key Focus: {comp.focus}</div>
                                  </div>
                                </div>
                                <div className="text-right flex-shrink-0">
                                  <span className={`text-xs font-extrabold px-2 py-0.5 rounded-lg ${comp.match >= 75 ? 'text-emerald-400 bg-emerald-500/10 border border-emerald-500/20' : comp.match >= 60 ? 'text-indigo-400 bg-indigo-500/10 border border-indigo-500/20' : 'text-amber-400 bg-amber-500/10 border border-amber-500/20'}`}>
                                    {comp.match}% Match
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Quick Strengths / Weaknesses footer */}
                        <div className="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-xs text-zinc-400">
                          <span className="flex items-center gap-1 text-[11px]">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" /> Resume ATS: <strong className="text-white">{atsScore > 0 ? `${atsScore}%` : 'Pending'}</strong>
                          </span>
                          <button
                            onClick={() => setSidebarTab('resume')}
                            className="text-[11px] text-indigo-400 hover:text-indigo-300 font-bold cursor-pointer"
                          >
                            Update Resume Analysis →
                          </button>
                        </div>
                      </div>

                    </div>

                  </div>
                );
              })()}

              {/* ── ROADMAP ── */}
              {sidebarTab === 'roadmap' && (
                <div className="space-y-4">
                  <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-white">{roadmap?.stages_data?.length || 8}-Stage Preparation Roadmap</h3>
                        <span className="text-[10px] font-extrabold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">Role-Specific</span>
                      </div>
                      <p className="text-xs text-zinc-400 mt-1">
                        Track: <span className="text-indigo-300 font-semibold">{roadmap?.target_role || userProfile?.target_roles?.[0] || 'Software Engineer'}</span> • Each topic has concepts, last-minute notes, a narrated explainer and video links • <span className="text-green-400 font-bold">+50 XP</span> per topic
                        {roadmap?.estimated_completion_date && <> • Target finish: <span className="text-zinc-300 font-semibold">{roadmap.estimated_completion_date}</span></>}
                      </p>
                    </div>
                    <div className="flex items-center gap-3 self-end sm:self-center flex-wrap justify-end">
                      {roadmap?.stages_data && (
                        <button
                          type="button"
                          disabled={cheatsheetLoading}
                          onClick={downloadCheatsheet}
                          className="px-3.5 py-2 bg-emerald-600/15 hover:bg-emerald-600 border border-emerald-500/30 text-emerald-300 hover:text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                        >
                          {cheatsheetLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                          {cheatsheetLoading ? 'Preparing...' : 'All Notes (PDF)'}
                        </button>
                      )}
                      <button
                        type="button"
                        disabled={roadmapLoading}
                        onClick={handleGenerateRoadmap}
                        className="px-3.5 py-2 bg-indigo-600/20 hover:bg-indigo-600 border border-indigo-500/30 text-indigo-300 hover:text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 disabled:opacity-50 cursor-pointer shadow-sm"
                      >
                        {roadmapLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                        {roadmapLoading ? 'Generating...' : (roadmap?.stages_data ? 'Refresh Roadmap' : 'Generate Roadmap')}
                      </button>
                      <div className="text-right pl-3 border-l border-zinc-800">
                        <div className="text-2xl font-extrabold text-white">{roadmap?.progress_percentage || 0}%</div>
                        <div className="text-[10px] text-zinc-400">Total Completion</div>
                      </div>
                    </div>
                  </div>

                  {roadmap?.stages_data ? (
                    <div className="space-y-4">
                      {roadmap.stages_data.map((stage: any) => {
                        const stageTopics = stage.topics || [];
                        const completedInStage = stageTopics.filter((t: any) => t.is_completed).length;
                        const isStageAllDone = stageTopics.length > 0 && completedInStage === stageTopics.length;

                        return (
                          <div key={stage.id} className={`bg-zinc-900/90 border rounded-2xl p-5 transition-all ${isStageAllDone ? 'border-green-500/30 bg-green-950/10' : 'border-zinc-800'}`}>
                            <div className="mb-4 pb-3 border-b border-zinc-800 flex items-start justify-between">
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="text-[10px] text-indigo-400 font-extrabold uppercase tracking-wider bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">Stage {stage.id}</span>
                                  {isStageAllDone && (
                                    <span className="text-[10px] text-green-400 font-bold bg-green-500/10 px-2 py-0.5 rounded border border-green-500/20 flex items-center gap-1">
                                      <CheckCircle className="w-3 h-3" /> Stage Completed
                                    </span>
                                  )}
                                </div>
                                <h4 className="text-base font-bold text-white mt-1.5">{stage.title}</h4>
                                <p className="text-xs text-zinc-400 mt-0.5 leading-relaxed">{stage.description}</p>
                              </div>
                              <div className="text-right text-xs font-semibold text-zinc-400 flex-shrink-0 ml-3">
                                <span className="text-indigo-400 font-bold">{completedInStage}</span> / {stageTopics.length} Done
                              </div>
                            </div>
                            <div className="space-y-2.5">
                              {stageTopics.map((topic: any) => (
                                <div
                                  key={topic.id}
                                  className={`p-3.5 rounded-xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-all ${topic.is_completed ? 'bg-indigo-950/20 border-indigo-500/30 shadow-sm' : 'bg-zinc-800/40 border-zinc-700/70 hover:border-zinc-600 hover:bg-zinc-800/70'}`}
                                >
                                  <div className="flex items-start gap-3 flex-1 min-w-0">
                                    <button
                                      type="button"
                                      aria-label={topic.is_completed ? "Mark topic incomplete" : "Mark topic complete"}
                                      onClick={() => toggleTopic(stage.id, topic.id, topic.is_completed)}
                                      className={`mt-0.5 w-6 h-6 rounded-lg border flex-shrink-0 flex items-center justify-center transition-all cursor-pointer ${topic.is_completed ? 'bg-green-500 border-green-500 text-white shadow-md shadow-green-500/30' : 'border-zinc-500 bg-zinc-800 hover:border-indigo-400 hover:bg-zinc-700'}`}
                                    >
                                      {topic.is_completed ? (
                                        <CheckCircle className="w-4 h-4 text-white" />
                                      ) : (
                                        <span className="w-2 h-2 rounded-sm bg-zinc-600" />
                                      )}
                                    </button>
                                    <div className="min-w-0 flex-1">
                                      <div className="flex items-center gap-2 flex-wrap">
                                        <span className={`text-xs font-bold ${topic.is_completed ? 'text-zinc-200 line-through decoration-zinc-500' : 'text-white'}`}>{topic.title}</span>
                                        <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold ${topic.difficulty === 'Hard' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : topic.difficulty === 'Medium' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-green-500/10 text-green-400 border border-green-500/20'}`}>{topic.difficulty}</span>
                                        <span className="text-[10px] text-zinc-400 flex items-center gap-0.5"><Clock className="w-3 h-3 text-zinc-500" />{topic.estimated_hours}h study</span>
                                        {topic.is_completed && <span className="text-[9px] font-bold text-green-400 bg-green-500/10 px-1.5 py-0.5 rounded border border-green-500/20">+50 XP Earned</span>}
                                      </div>
                                      <p className="text-[11px] text-zinc-400 mt-1 leading-relaxed">{topic.description}</p>
                                      {topic.already_familiar && !topic.is_completed && (
                                        <span className="inline-block mt-1 text-[9px] font-bold text-sky-300 bg-sky-500/10 border border-sky-500/20 px-1.5 py-0.5 rounded">You listed this skill: a quick revision may be enough</span>
                                      )}
                                      {Array.isArray(topic.concepts) && topic.concepts.length > 0 && (
                                        <div className="flex flex-wrap gap-1 mt-2">
                                          {topic.concepts.map((c: string) => (
                                            <span key={c} className="text-[10px] px-1.5 py-0.5 rounded-md bg-zinc-900 border border-zinc-700/70 text-zinc-300">{c}</span>
                                          ))}
                                        </div>
                                      )}
                                      {Array.isArray(topic.resources) && topic.resources.length > 0 && (
                                        <div className="flex flex-wrap gap-x-3 gap-y-1 mt-2">
                                          {topic.resources.map((r: any, idx: number) => (
                                            <a key={idx} href={r.url} target="_blank" rel="noreferrer"
                                              className={`text-[10.5px] font-semibold inline-flex items-center gap-1 hover:underline ${r.type === 'YouTube' ? 'text-red-400' : 'text-indigo-300'}`}>
                                              {r.type === 'YouTube' ? <Youtube className="w-3.5 h-3.5" /> : <ExternalLink className="w-3 h-3" />}
                                              {r.type === 'YouTube' ? r.title.replace(/^YouTube:\s*/, '') : r.title}
                                            </a>
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                  <div className="flex items-center gap-2 self-end sm:self-center flex-shrink-0">
                                    <button
                                      type="button"
                                      onClick={() => openTopicNotes(stage.id, topic, stage.title)}
                                      className="px-3 py-1.5 bg-indigo-600/20 border border-indigo-500/30 text-indigo-300 hover:bg-indigo-600 hover:text-white text-[11px] font-bold rounded-lg transition-all flex items-center gap-1.5 cursor-pointer shadow-sm"
                                    >
                                      <BookOpen className="w-3.5 h-3.5" /> Notes
                                    </button>
                                    <button
                                      type="button"
                                      onClick={() => openTopicNotes(stage.id, topic, stage.title, true)}
                                      className="px-3 py-1.5 bg-fuchsia-600/15 border border-fuchsia-500/30 text-fuchsia-300 hover:bg-fuchsia-600 hover:text-white text-[11px] font-bold rounded-lg transition-all flex items-center gap-1.5 cursor-pointer"
                                      title="Narrated, animated concept explainer"
                                    >
                                      <PlayCircle className="w-3.5 h-3.5" /> Explainer
                                    </button>
                                    <button
                                      type="button"
                                      disabled={notesLoading === `${stage.id}-${topic.id}`}
                                      onClick={() => downloadNotesPdf(stage.id, topic.id, topic.title)}
                                      className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 text-zinc-300 hover:bg-zinc-700 hover:text-white text-[11px] font-bold rounded-lg transition-all flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                                    >
                                      {notesLoading === `${stage.id}-${topic.id}` ? (
                                        <>
                                          <Loader2 className="w-3.5 h-3.5 animate-spin text-indigo-400" /> Exporting...
                                        </>
                                      ) : (
                                        <>
                                          <Download className="w-3.5 h-3.5 text-zinc-400" /> PDF
                                        </>
                                      )}
                                    </button>
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <div className="text-center py-16 text-zinc-500 bg-zinc-900/60 border border-zinc-800 rounded-2xl p-8">
                      <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-30 text-indigo-400" />
                      <p className="text-sm font-bold text-white">No roadmap generated yet</p>
                      <p className="text-xs text-zinc-400 mt-1 mb-5">Click below to generate your personalized 8-Stage preparation path tailored to your skills.</p>
                      <button
                        type="button"
                        disabled={roadmapLoading}
                        onClick={handleGenerateRoadmap}
                        className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all inline-flex items-center gap-2 disabled:opacity-50 cursor-pointer shadow-lg shadow-indigo-600/30"
                      >
                        {roadmapLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                        {roadmapLoading ? 'Generating AI Roadmap...' : 'Generate 8-Stage AI Roadmap'}
                      </button>
                    </div>
                  )}
                </div>
              )}

              {/* ── RESUME & ATS WORKSPACE ── */}
              {sidebarTab === 'resume' && (
                <div className="space-y-6">
                  {/* Top Bar Navigation */}
                  <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="text-base font-bold text-white">AI Resume &amp; ATS Intelligence</h3>
                        <span className="text-[10px] font-extrabold text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">Standard ATS Format</span>
                      </div>
                      <p className="text-xs text-zinc-400 mt-1">
                        Upload an existing resume to audit ATS compatibility, or build and export a standard ATS resume (<span className="text-green-400 font-bold">+150 XP</span>)
                      </p>
                    </div>

                    <div className="flex items-center gap-2.5 flex-wrap">
                      <div className="bg-zinc-800/80 p-1 rounded-xl border border-zinc-700/60 flex items-center gap-1">
                        <button
                          type="button"
                          onClick={() => setResumeMode('upload')}
                          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${resumeMode === 'upload' ? 'bg-indigo-600 text-white shadow-sm' : 'text-zinc-400 hover:text-white'}`}
                        >
                          📤 Upload &amp; Audit PDF
                        </button>
                        <button
                          type="button"
                          onClick={() => setResumeMode('builder')}
                          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${resumeMode === 'builder' ? 'bg-indigo-600 text-white shadow-sm' : 'text-zinc-400 hover:text-white'}`}
                        >
                          📝 Build Resume
                        </button>
                        <button
                          type="button"
                          onClick={() => setResumeMode('preview')}
                          className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer ${resumeMode === 'preview' ? 'bg-indigo-600 text-white shadow-sm' : 'text-zinc-400 hover:text-white'}`}
                        >
                          📄 Standard Preview
                        </button>
                      </div>

                      <button
                        type="button"
                        disabled={resumePdfLoading}
                        onClick={downloadResumePdf}
                        className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-md shadow-indigo-600/30 disabled:opacity-50"
                      >
                        {resumePdfLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                        {resumePdfLoading ? 'Exporting PDF...' : 'Download Resume PDF'}
                      </button>
                    </div>
                  </div>

                  {/* ── 1. UPLOAD & AUDIT EXISTING PDF ── */}
                  {resumeMode === 'upload' && (
                    <div className="space-y-6">
                      {/* Upload Box or Confirmed State Card */}
                      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6">
                        <div className="flex items-center justify-between mb-3">
                          <span className="text-xs font-bold uppercase tracking-wider text-white">Upload Existing PDF Resume</span>
                          <span className="text-[11px] text-zinc-500">PDF format, max 5MB</span>
                        </div>

                        {uploadingPdf ? (
                          <div className="border-2 border-dashed border-indigo-500/60 rounded-xl p-10 flex flex-col items-center justify-center bg-indigo-500/5">
                            <Loader2 className="w-8 h-8 text-indigo-400 animate-spin mb-3" />
                            <p className="text-xs font-bold text-white">Scanning document text &amp; running ATS analysis...</p>
                            <p className="text-[11px] text-zinc-400 mt-1">Extracting skills, projects, and keywords</p>
                          </div>
                        ) : uploadedFileDetails ? (
                          <div className="border border-emerald-500/30 bg-emerald-500/10 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                            <div className="flex items-center gap-3">
                              <div className="w-10 h-10 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center flex-shrink-0">
                                <CheckCircle className="w-5 h-5" />
                              </div>
                              <div>
                                <div className="text-xs font-bold text-white flex items-center gap-2">
                                  <span>{uploadedFileDetails.name}</span>
                                  <span className="text-[10px] text-emerald-400 font-extrabold bg-emerald-500/20 px-1.5 py-0.5 rounded">✓ Uploaded</span>
                                </div>
                                <div className="text-[11px] text-zinc-400 mt-0.5">
                                  Size: {uploadedFileDetails.size} • Scanned at {uploadedFileDetails.timestamp}
                                </div>
                              </div>
                            </div>
                            <label className="px-3.5 py-1.5 bg-zinc-800 hover:bg-zinc-700 text-white rounded-lg text-xs font-semibold cursor-pointer text-center transition-colors">
                              Upload Different File
                              <input type="file" accept=".pdf" onChange={handleResumeUpload} className="hidden" />
                            </label>
                          </div>
                        ) : (
                          <label className="border-2 border-dashed border-zinc-700 hover:border-indigo-500/50 rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer transition-all bg-zinc-950/40 relative">
                            <input type="file" accept=".pdf" onChange={handleResumeUpload} className="absolute inset-0 opacity-0 cursor-pointer" />
                            <Upload className="w-8 h-8 text-indigo-400 mb-2" />
                            <p className="text-xs font-bold text-white">Click or Drop PDF to Upload</p>
                            <p className="text-[11px] text-zinc-400 mt-1">Our engine extracts the text and runs an authentic ATS keyword audit</p>
                          </label>
                        )}
                      </div>

                      {/* Analysis Results for Uploaded File */}
                      {resumeAnalysis && (
                        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 space-y-6">
                          {/* Score Header */}
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-zinc-800 pb-5">
                            <div>
                              <h4 className="text-base font-bold text-white flex items-center gap-2">
                                <span>ATS Compatibility Audit &amp; Entity Scanner</span>
                                <span className="text-[10px] bg-green-500/10 border border-green-500/20 text-green-400 font-semibold px-2 py-0.5 rounded-full">
                                  ✓ Live Extracted
                                </span>
                              </h4>
                              <p className="text-xs text-zinc-400 mt-0.5">
                                Analyzed against hiring benchmarks for <span className="text-indigo-400 font-semibold">{userProfile?.target_roles?.[0] || 'Software Engineer'}</span>
                              </p>
                            </div>
                            <div className="flex items-center gap-3 flex-wrap sm:flex-nowrap">
                              <div className="bg-zinc-800/90 border border-zinc-700 rounded-xl px-4 py-2.5 text-center min-w-[100px]">
                                <div className="text-[10px] text-zinc-400 uppercase font-bold">ATS Score</div>
                                <div className="text-2xl font-extrabold text-indigo-400 mt-0.5">{resumeAnalysis.ats_score}%</div>
                              </div>
                              <div className="bg-zinc-800/90 border border-zinc-700 rounded-xl px-4 py-2.5 text-center min-w-[100px]">
                                <div className="text-[10px] text-zinc-400 uppercase font-bold">Quality</div>
                                <div className="text-2xl font-extrabold text-violet-400 mt-0.5">{resumeAnalysis.resume_score}%</div>
                              </div>
                              <div className="bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl px-4 py-2.5 text-center min-w-[120px]">
                                <div className="text-[10px] uppercase font-bold">Readiness</div>
                                <div className="text-xs font-extrabold mt-1">{resumeAnalysis.readiness_level}</div>
                              </div>
                            </div>
                          </div>

                          {/* Low match / Invalid Document Alert if score is low */}
                          {resumeAnalysis.ats_score < 30 && (
                            <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex items-start gap-3">
                              <AlertCircle className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
                              <div className="text-xs text-amber-200">
                                <div className="font-bold mb-0.5">Low ATS Match Detected</div>
                                This document lacks standard resume sections (Education, Technical Skills, Experience, Projects) or contains unreadable scanned images. We recommend building your resume using our standard builder tab.
                              </div>
                            </div>
                          )}

                          {/* Extracted Candidate Profile & Verified Links */}
                          {(resumeAnalysis.parsed_name || resumeAnalysis.parsed_email || resumeAnalysis.parsed_phone || resumeAnalysis.parsed_links) && (
                            <div className="bg-zinc-950/60 border border-zinc-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
                              <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-indigo-500/20 text-indigo-400 font-bold flex items-center justify-center text-sm border border-indigo-500/30">
                                  {resumeAnalysis.parsed_name ? resumeAnalysis.parsed_name.charAt(0).toUpperCase() : <User className="w-5 h-5" />}
                                </div>
                                <div>
                                  <div className="text-sm font-bold text-white">
                                    {resumeAnalysis.parsed_name || 'Candidate Name Extracted'}
                                  </div>
                                  <div className="text-xs text-zinc-400 flex flex-wrap items-center gap-3 mt-0.5">
                                    {resumeAnalysis.parsed_email && (
                                      <span className="flex items-center gap-1">
                                        <Mail className="w-3 h-3 text-zinc-500" /> {resumeAnalysis.parsed_email}
                                      </span>
                                    )}
                                    {resumeAnalysis.parsed_phone && (
                                      <span className="flex items-center gap-1">
                                        <Phone className="w-3 h-3 text-zinc-500" /> {resumeAnalysis.parsed_phone}
                                      </span>
                                    )}
                                  </div>
                                </div>
                              </div>

                              {/* Detected Links */}
                              {resumeAnalysis.parsed_links && Object.keys(resumeAnalysis.parsed_links).length > 0 && (
                                <div className="flex items-center gap-2 flex-wrap">
                                  {resumeAnalysis.parsed_links.linkedin && (
                                    <a
                                      href={resumeAnalysis.parsed_links.linkedin.startsWith('http') ? resumeAnalysis.parsed_links.linkedin : `https://${resumeAnalysis.parsed_links.linkedin}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="px-2.5 py-1 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 rounded-lg text-[11px] font-semibold flex items-center gap-1.5 transition-colors"
                                    >
                                      <Linkedin className="w-3 h-3 text-blue-400" />
                                      <span>LinkedIn</span>
                                      <ExternalLink className="w-2.5 h-2.5 text-zinc-500" />
                                    </a>
                                  )}
                                  {resumeAnalysis.parsed_links.github && (
                                    <a
                                      href={resumeAnalysis.parsed_links.github.startsWith('http') ? resumeAnalysis.parsed_links.github : `https://${resumeAnalysis.parsed_links.github}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="px-2.5 py-1 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 rounded-lg text-[11px] font-semibold flex items-center gap-1.5 transition-colors"
                                    >
                                      <Github className="w-3 h-3 text-zinc-200" />
                                      <span>GitHub</span>
                                      <ExternalLink className="w-2.5 h-2.5 text-zinc-500" />
                                    </a>
                                  )}
                                  {resumeAnalysis.parsed_links.portfolio && (
                                    <a
                                      href={resumeAnalysis.parsed_links.portfolio.startsWith('http') ? resumeAnalysis.parsed_links.portfolio : `https://${resumeAnalysis.parsed_links.portfolio}`}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="px-2.5 py-1 bg-zinc-800 hover:bg-zinc-700 border border-zinc-700 text-zinc-300 rounded-lg text-[11px] font-semibold flex items-center gap-1.5 transition-colors"
                                    >
                                      <Globe className="w-3 h-3 text-indigo-400" />
                                      <span>Portfolio</span>
                                      <ExternalLink className="w-2.5 h-2.5 text-zinc-500" />
                                    </a>
                                  )}
                                </div>
                              )}
                            </div>
                          )}

                          {/* Multi-Dimensional ATS Score Breakdown */}
                          {resumeAnalysis.score_breakdown && (
                            <div className="bg-zinc-950/60 border border-zinc-800 rounded-xl p-4">
                              <div className="text-xs font-bold uppercase tracking-wider text-zinc-400 mb-3 flex items-center gap-1.5">
                                <Award className="w-3.5 h-3.5 text-indigo-400" /> Multi-Dimensional Evaluation Breakdown
                              </div>
                              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                <div className="bg-zinc-900/80 border border-zinc-800 p-3 rounded-lg">
                                  <div className="text-[10px] font-bold text-zinc-400 uppercase">Keyword &amp; Skills</div>
                                  <div className="text-lg font-extrabold text-indigo-400 mt-0.5">
                                    {resumeAnalysis.score_breakdown.keyword_match}%
                                  </div>
                                  <div className="w-full bg-zinc-800 h-1.5 rounded-full mt-2 overflow-hidden">
                                    <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${resumeAnalysis.score_breakdown.keyword_match}%` }}></div>
                                  </div>
                                </div>
                                <div className="bg-zinc-900/80 border border-zinc-800 p-3 rounded-lg">
                                  <div className="text-[10px] font-bold text-zinc-400 uppercase">Projects &amp; Depth</div>
                                  <div className="text-lg font-extrabold text-violet-400 mt-0.5">
                                    {resumeAnalysis.score_breakdown.experience_projects}%
                                  </div>
                                  <div className="w-full bg-zinc-800 h-1.5 rounded-full mt-2 overflow-hidden">
                                    <div className="bg-violet-500 h-full rounded-full" style={{ width: `${resumeAnalysis.score_breakdown.experience_projects}%` }}></div>
                                  </div>
                                </div>
                                <div className="bg-zinc-900/80 border border-zinc-800 p-3 rounded-lg">
                                  <div className="text-[10px] font-bold text-zinc-400 uppercase">ATS Formatting</div>
                                  <div className="text-lg font-extrabold text-emerald-400 mt-0.5">
                                    {resumeAnalysis.score_breakdown.formatting_structure}%
                                  </div>
                                  <div className="w-full bg-zinc-800 h-1.5 rounded-full mt-2 overflow-hidden">
                                    <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${resumeAnalysis.score_breakdown.formatting_structure}%` }}></div>
                                  </div>
                                </div>
                                <div className="bg-zinc-900/80 border border-zinc-800 p-3 rounded-lg">
                                  <div className="text-[10px] font-bold text-zinc-400 uppercase">Measurable Impact</div>
                                  <div className="text-lg font-extrabold text-amber-400 mt-0.5">
                                    {resumeAnalysis.score_breakdown.measurable_impact}%
                                  </div>
                                  <div className="w-full bg-zinc-800 h-1.5 rounded-full mt-2 overflow-hidden">
                                    <div className="bg-amber-500 h-full rounded-full" style={{ width: `${resumeAnalysis.score_breakdown.measurable_impact}%` }}></div>
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Extracted Skills Taxonomy by Category */}
                          {resumeAnalysis.parsed_skills && typeof resumeAnalysis.parsed_skills === 'object' && (
                            <div className="bg-zinc-950/60 border border-zinc-800 rounded-xl p-4 space-y-3">
                              <div className="text-xs font-bold uppercase tracking-wider text-zinc-300 flex items-center justify-between">
                                <span className="flex items-center gap-1.5">
                                  <Code2 className="w-3.5 h-3.5 text-indigo-400" /> Extracted Technical Competencies (Categorized)
                                </span>
                              </div>
                              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                                {safeArray(resumeAnalysis.parsed_skills.programming_languages).length > 0 && (
                                  <div className="bg-zinc-900/70 border border-zinc-800 p-3 rounded-lg space-y-1.5">
                                    <div className="text-[10px] font-bold uppercase text-indigo-400">Programming Languages</div>
                                    <div className="flex flex-wrap gap-1">
                                      {safeArray(resumeAnalysis.parsed_skills.programming_languages).map((s: any, idx: number) => (
                                        <span key={idx} className="bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded text-[10px] font-semibold">
                                          {typeof s === 'string' ? s : JSON.stringify(s)}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {safeArray(resumeAnalysis.parsed_skills.frameworks_libraries).length > 0 && (
                                  <div className="bg-zinc-900/70 border border-zinc-800 p-3 rounded-lg space-y-1.5">
                                    <div className="text-[10px] font-bold uppercase text-violet-400">Frameworks &amp; Libraries</div>
                                    <div className="flex flex-wrap gap-1">
                                      {safeArray(resumeAnalysis.parsed_skills.frameworks_libraries).map((s: any, idx: number) => (
                                        <span key={idx} className="bg-violet-500/10 border border-violet-500/20 text-violet-300 px-2 py-0.5 rounded text-[10px] font-semibold">
                                          {typeof s === 'string' ? s : JSON.stringify(s)}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {safeArray(resumeAnalysis.parsed_skills.databases).length > 0 && (
                                  <div className="bg-zinc-900/70 border border-zinc-800 p-3 rounded-lg space-y-1.5">
                                    <div className="text-[10px] font-bold uppercase text-emerald-400">Databases</div>
                                    <div className="flex flex-wrap gap-1">
                                      {safeArray(resumeAnalysis.parsed_skills.databases).map((s: any, idx: number) => (
                                        <span key={idx} className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 px-2 py-0.5 rounded text-[10px] font-semibold">
                                          {typeof s === 'string' ? s : JSON.stringify(s)}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {safeArray(resumeAnalysis.parsed_skills.cloud_devops).length > 0 && (
                                  <div className="bg-zinc-900/70 border border-zinc-800 p-3 rounded-lg space-y-1.5">
                                    <div className="text-[10px] font-bold uppercase text-amber-400">Cloud &amp; DevOps</div>
                                    <div className="flex flex-wrap gap-1">
                                      {safeArray(resumeAnalysis.parsed_skills.cloud_devops).map((s: any, idx: number) => (
                                        <span key={idx} className="bg-amber-500/10 border border-amber-500/20 text-amber-300 px-2 py-0.5 rounded text-[10px] font-semibold">
                                          {typeof s === 'string' ? s : JSON.stringify(s)}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {safeArray(resumeAnalysis.parsed_skills.core_cs).length > 0 && (
                                  <div className="bg-zinc-900/70 border border-zinc-800 p-3 rounded-lg space-y-1.5">
                                    <div className="text-[10px] font-bold uppercase text-cyan-400">Core Computer Science</div>
                                    <div className="flex flex-wrap gap-1">
                                      {safeArray(resumeAnalysis.parsed_skills.core_cs).map((s: any, idx: number) => (
                                        <span key={idx} className="bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 px-2 py-0.5 rounded text-[10px] font-semibold">
                                          {typeof s === 'string' ? s : JSON.stringify(s)}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                                {safeArray(resumeAnalysis.parsed_skills.ai_ml).length > 0 && (
                                  <div className="bg-zinc-900/70 border border-zinc-800 p-3 rounded-lg space-y-1.5">
                                    <div className="text-[10px] font-bold uppercase text-pink-400">AI / Machine Learning</div>
                                    <div className="flex flex-wrap gap-1">
                                      {safeArray(resumeAnalysis.parsed_skills.ai_ml).map((s: any, idx: number) => (
                                        <span key={idx} className="bg-pink-500/10 border border-pink-500/20 text-pink-300 px-2 py-0.5 rounded text-[10px] font-semibold">
                                          {typeof s === 'string' ? s : JSON.stringify(s)}
                                        </span>
                                      ))}
                                    </div>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Extracted Projects & Experience & Education Grid */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Detected Projects */}
                            {safeArray(resumeAnalysis.parsed_projects).length > 0 && (
                              <div className="bg-zinc-950/60 border border-zinc-800 rounded-xl p-4 space-y-2.5">
                                <div className="text-xs font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
                                  <Code2 className="w-3.5 h-3.5 text-indigo-400" /> Extracted Projects ({safeArray(resumeAnalysis.parsed_projects).length})
                                </div>
                                <div className="space-y-2">
                                  {safeArray(resumeAnalysis.parsed_projects).map((p: any, idx: number) => {
                                    const isObj = typeof p === 'object' && p !== null;
                                    const title = isObj ? (p.title || p.name || 'Technical Project') : String(p);
                                    const stack = isObj ? (p.stack || p.technologies || '') : '';
                                    const desc = isObj ? (p.description || (p.bullets ? p.bullets[0] : '')) : '';
                                    return (
                                      <div key={idx} className="bg-zinc-900/70 border border-zinc-800/80 p-2.5 rounded-lg">
                                        <div className="text-xs font-bold text-white">{title}</div>
                                        {stack && (
                                          <div className="text-[10px] text-indigo-400 font-mono mt-0.5">{stack}</div>
                                        )}
                                        {desc && (
                                          <div className="text-[11px] text-zinc-400 mt-1 line-clamp-2">{desc}</div>
                                        )}
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            )}

                            {/* Detected Experience & Education */}
                            <div className="space-y-4">
                              {safeArray(resumeAnalysis.parsed_experience).length > 0 && (
                                <div className="bg-zinc-950/60 border border-zinc-800 rounded-xl p-4 space-y-2.5">
                                  <div className="text-xs font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
                                    <Briefcase className="w-3.5 h-3.5 text-violet-400" /> Extracted Experience ({safeArray(resumeAnalysis.parsed_experience).length})
                                  </div>
                                  <div className="space-y-2">
                                    {safeArray(resumeAnalysis.parsed_experience).map((exp: any, idx: number) => {
                                      const isObj = typeof exp === 'object' && exp !== null;
                                      const role = isObj ? (exp.role || exp.title || 'Software Engineering Role') : String(exp);
                                      const company = isObj ? (exp.company || exp.organization || '') : '';
                                      const duration = isObj ? (exp.duration || exp.dates || '') : '';
                                      const desc = isObj ? (exp.description || (exp.bullets ? exp.bullets[0] : '')) : '';
                                      return (
                                        <div key={idx} className="bg-zinc-900/70 border border-zinc-800/80 p-2.5 rounded-lg">
                                          <div className="text-xs font-bold text-white">{role}</div>
                                          {(company || duration) && (
                                            <div className="text-[10px] text-violet-400 flex items-center justify-between mt-0.5">
                                              {company && <span>{company}</span>}
                                              {duration && <span>{duration}</span>}
                                            </div>
                                          )}
                                          {desc && (
                                            <div className="text-[11px] text-zinc-400 mt-1">{desc}</div>
                                          )}
                                        </div>
                                      );
                                    })}
                                  </div>
                                </div>
                              )}

                              {safeArray(resumeAnalysis.parsed_education).length > 0 && (
                                <div className="bg-zinc-950/60 border border-zinc-800 rounded-xl p-4 space-y-2">
                                  <div className="text-xs font-bold uppercase tracking-wider text-zinc-300 flex items-center gap-1.5">
                                    <GraduationCap className="w-3.5 h-3.5 text-emerald-400" /> Extracted Education
                                  </div>
                                  {safeArray(resumeAnalysis.parsed_education).map((edu: any, idx: number) => {
                                    const isObj = typeof edu === 'object' && edu !== null;
                                    const degree = isObj ? (edu.degree || edu.title || 'Degree / Major') : String(edu);
                                    const inst = isObj ? (edu.institution || edu.college || edu.university || '') : '';
                                    const cgpa = isObj ? edu.cgpa : '';
                                    const year = isObj ? (edu.year || edu.dates || '') : '';
                                    return (
                                      <div key={idx} className="text-xs text-zinc-300 bg-zinc-900/70 border border-zinc-800/80 p-2.5 rounded-lg">
                                        <div className="font-bold text-white">{degree}</div>
                                        {inst && <div className="text-[11px] text-zinc-400 mt-0.5">{inst}</div>}
                                        {(cgpa || year) && (
                                          <div className="text-[10px] text-emerald-400 flex items-center gap-2 mt-1">
                                            {cgpa && <span>CGPA: {cgpa}</span>}
                                            {year && <span>• {year}</span>}
                                          </div>
                                        )}
                                      </div>
                                    );
                                  })}
                                </div>
                              )}
                            </div>
                          </div>

                          {/* 4 Categorized Audit Cards */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Strengths */}
                            <div className="bg-zinc-950/60 border border-green-500/20 rounded-xl p-4">
                              <div className="text-xs font-bold uppercase tracking-wider text-green-400 mb-2.5 flex items-center gap-1.5">
                                <CheckCircle className="w-4 h-4" /> Detected Strengths
                              </div>
                              <div className="space-y-1.5 text-xs text-zinc-300">
                                {safeArray(resumeAnalysis.strengths).map((item: any, idx: number) => (
                                  <div key={idx} className="flex items-start gap-2">
                                    <span className="text-green-400 font-bold">•</span>
                                    <span>{typeof item === 'string' ? item : JSON.stringify(item)}</span>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Weaknesses */}
                            <div className="bg-zinc-950/60 border border-red-500/20 rounded-xl p-4">
                              <div className="text-xs font-bold uppercase tracking-wider text-red-400 mb-2.5 flex items-center gap-1.5">
                                <AlertCircle className="w-4 h-4" /> Content &amp; Formatting Gaps
                              </div>
                              <div className="space-y-1.5 text-xs text-zinc-300">
                                {safeArray(resumeAnalysis.weaknesses).map((item: any, idx: number) => (
                                  <div key={idx} className="flex items-start gap-2">
                                    <span className="text-red-400 font-bold">•</span>
                                    <span>{typeof item === 'string' ? item : JSON.stringify(item)}</span>
                                  </div>
                                ))}
                              </div>
                            </div>

                            {/* Missing Industry Keywords */}
                            <div className="bg-zinc-950/60 border border-amber-500/20 rounded-xl p-4">
                              <div className="text-xs font-bold uppercase tracking-wider text-amber-400 mb-2.5 flex items-center gap-1.5">
                                <Sparkles className="w-4 h-4" /> Missing Keywords for Target Role
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                {safeArray(resumeAnalysis.missing_keywords).map((k: any, idx: number) => (
                                  <span key={idx} className="bg-amber-500/10 border border-amber-500/20 text-amber-300 px-2 py-0.5 rounded text-[11px] font-bold">
                                    + {typeof k === 'string' ? k : JSON.stringify(k)}
                                  </span>
                                ))}
                              </div>
                            </div>

                            {/* AI Recommendations */}
                            <div className="bg-zinc-950/60 border border-indigo-500/20 rounded-xl p-4">
                              <div className="text-xs font-bold uppercase tracking-wider text-indigo-400 mb-2.5 flex items-center gap-1.5">
                                <BookOpen className="w-4 h-4" /> Recommendations to Improve Callback Rate
                              </div>
                              <div className="space-y-1.5 text-xs text-zinc-300">
                                {safeArray(resumeAnalysis.suggestions).map((item: any, idx: number) => (
                                  <div key={idx} className="flex items-start gap-2">
                                    <span className="text-indigo-400 font-bold">•</span>
                                    <span>{typeof item === 'string' ? item : JSON.stringify(item)}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          </div>

                          {/* Action to Build Standard ATS Resume */}
                          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-4 border-t border-zinc-800">
                            <span className="text-xs text-zinc-400">Want to download an optimized 100% ATS-compliant single-page resume?</span>
                            <div className="flex items-center gap-2">
                              <button
                                type="button"
                                onClick={downloadResumePdf}
                                disabled={resumePdfLoading}
                                className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl text-xs font-bold transition-all cursor-pointer flex items-center gap-1.5 shadow-md"
                              >
                                {resumePdfLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Download className="w-3.5 h-3.5" />}
                                <span>Download ATS Resume PDF</span>
                              </button>
                              <button
                                type="button"
                                onClick={() => setResumeMode('builder')}
                                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all cursor-pointer"
                              >
                                📝 Customize in Builder
                              </button>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* ── 2. BUILD STANDARD RESUME ── */}
                  {resumeMode === 'builder' && (
                    <form onSubmit={handleResumeSubmit} className="space-y-6">
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Section 1: Contact & Verified Profiles */}
                        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-4">
                          <div className="text-xs font-bold uppercase tracking-wider text-white border-b border-zinc-800 pb-2">
                            1. Contact &amp; Verified Profiles
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                              <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Full Name *</label>
                              <input
                                type="text"
                                value={resumeForm.name}
                                placeholder={userProfile?.full_name || "e.g. John Doe"}
                                onChange={e => setResumeForm({ ...resumeForm, name: e.target.value })}
                                required
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>
                            <div>
                              <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Target Role Headline *</label>
                              <input
                                type="text"
                                value={resumeForm.headline}
                                placeholder={userProfile?.target_roles?.[0] || "e.g. Software Engineer"}
                                onChange={e => setResumeForm({ ...resumeForm, headline: e.target.value })}
                                required
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                              <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Email Address</label>
                              <input
                                type="email"
                                value={resumeForm.email}
                                placeholder={userProfile?.email || "e.g. name@example.com"}
                                onChange={e => setResumeForm({ ...resumeForm, email: e.target.value })}
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>
                            <div>
                              <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Phone Number</label>
                              <input
                                type="text"
                                value={resumeForm.phone}
                                placeholder="e.g. +91 98765 43210"
                                onChange={e => setResumeForm({ ...resumeForm, phone: e.target.value })}
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>
                          </div>

                          <div>
                            <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Location</label>
                            <input
                              type="text"
                              value={resumeForm.location}
                              placeholder="e.g. Bengaluru, India"
                              onChange={e => setResumeForm({ ...resumeForm, location: e.target.value })}
                              className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                            />
                          </div>

                          {/* LinkedIn with Real-Time Verification */}
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <label className="text-[11px] text-zinc-400 font-medium">Verified LinkedIn URL</label>
                              {resumeForm.linkedin && (
                                isValidLinkedIn(resumeForm.linkedin) ? (
                                  <span className="text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20 flex items-center gap-1">
                                    <CheckCircle className="w-3 h-3" /> Verified Profile
                                  </span>
                                ) : (
                                  <span className="text-[10px] text-red-400 font-bold bg-red-500/10 px-1.5 py-0.5 rounded border border-red-500/20">
                                    ⚠️ Invalid URL
                                  </span>
                                )
                              )}
                            </div>
                            <input
                              type="url"
                              value={resumeForm.linkedin}
                              placeholder="https://linkedin.com/in/username"
                              onChange={e => setResumeForm({ ...resumeForm, linkedin: e.target.value })}
                              className={`w-full bg-zinc-800 border rounded-xl px-3 py-2 text-xs text-white focus:outline-none ${resumeForm.linkedin && !isValidLinkedIn(resumeForm.linkedin) ? 'border-red-500' : 'border-zinc-700 focus:border-indigo-500'}`}
                            />
                          </div>

                          {/* GitHub with Real-Time Verification */}
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <label className="text-[11px] text-zinc-400 font-medium">Verified GitHub URL</label>
                              {resumeForm.github && (
                                isValidGitHub(resumeForm.github) ? (
                                  <span className="text-[10px] text-emerald-400 font-bold bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20 flex items-center gap-1">
                                    <CheckCircle className="w-3 h-3" /> Verified Profile
                                  </span>
                                ) : (
                                  <span className="text-[10px] text-red-400 font-bold bg-red-500/10 px-1.5 py-0.5 rounded border border-red-500/20">
                                    ⚠️ Invalid URL
                                  </span>
                                )
                              )}
                            </div>
                            <input
                              type="url"
                              value={resumeForm.github}
                              placeholder="https://github.com/username"
                              onChange={e => setResumeForm({ ...resumeForm, github: e.target.value })}
                              className={`w-full bg-zinc-800 border rounded-xl px-3 py-2 text-xs text-white focus:outline-none ${resumeForm.github && !isValidGitHub(resumeForm.github) ? 'border-red-500' : 'border-zinc-700 focus:border-indigo-500'}`}
                            />
                          </div>

                          {/* Professional Summary */}
                          <div>
                            <div className="flex items-center justify-between mb-1">
                              <label className="text-[11px] text-zinc-400 font-medium">Professional Summary (introduction)</label>
                              <button
                                type="button"
                                onClick={generateResumeSummary}
                                disabled={summaryLoading}
                                className="text-[10px] font-bold text-indigo-300 bg-indigo-500/10 border border-indigo-500/30 hover:bg-indigo-600 hover:text-white px-2 py-0.5 rounded-lg flex items-center gap-1 transition-colors disabled:opacity-50 cursor-pointer"
                              >
                                {summaryLoading ? <Loader2 className="w-3 h-3 animate-spin" /> : <Wand2 className="w-3 h-3" />}
                                {summaryLoading ? 'Writing...' : 'Write it for me'}
                              </button>
                            </div>
                            <textarea
                              rows={3}
                              value={resumeForm.summary}
                              onChange={e => setResumeForm({ ...resumeForm, summary: e.target.value })}
                              placeholder="Concise overview highlighting your core strengths, algorithms knowledge, and career track."
                              className="w-full bg-zinc-800 border border-zinc-700 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500 resize-none leading-relaxed"
                            />
                          </div>
                        </div>

                        {/* Section 2: Education & Technical Skills */}
                        <div className="space-y-6">
                          {/* Education */}
                          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-4">
                            <div className="text-xs font-bold uppercase tracking-wider text-white border-b border-zinc-800 pb-2">
                              2. Academic Education
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                              <div>
                                <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Degree &amp; Major</label>
                                <input
                                  type="text"
                                  value={resumeForm.education}
                                  onChange={e => setResumeForm({ ...resumeForm, education: e.target.value })}
                                  placeholder={userProfile?.education || "e.g. B.Tech in Computer Science"}
                                  className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                                />
                              </div>
                              <div>
                                <label className="text-[11px] text-zinc-400 block mb-1 font-medium">College / University Name</label>
                                <input
                                  type="text"
                                  value={resumeForm.college}
                                  onChange={e => setResumeForm({ ...resumeForm, college: e.target.value })}
                                  placeholder="e.g. State Technical University"
                                  className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                                />
                              </div>
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                              <div>
                                <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Cumulative CGPA / %</label>
                                <input
                                  type="text"
                                  value={resumeForm.cgpa}
                                  onChange={e => setResumeForm({ ...resumeForm, cgpa: e.target.value })}
                                  placeholder="e.g. 8.6 or 85%"
                                  className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                                />
                              </div>
                              <div>
                                <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Graduation Timeline</label>
                                <input
                                  type="text"
                                  value={resumeForm.gradYear}
                                  onChange={e => setResumeForm({ ...resumeForm, gradYear: e.target.value })}
                                  placeholder="e.g. 2022 - 2026"
                                  className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                                />
                              </div>
                            </div>
                          </div>

                          {/* Technical Skills */}
                          <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-3.5">
                            <div className="text-xs font-bold uppercase tracking-wider text-white border-b border-zinc-800 pb-2">
                              3. Categorized Technical Skills
                            </div>

                            <div>
                              <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Core Technical Skills (auto-synced from sign-in) *</label>
                              <input
                                type="text"
                                value={resumeForm.skills}
                                onChange={e => setResumeForm({ ...resumeForm, skills: e.target.value })}
                                placeholder="e.g. Python, Java, SQL, React"
                                required
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>

                            <div>
                              <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Programming Languages (comma-separated)</label>
                              <input
                                type="text"
                                value={resumeForm.languages}
                                onChange={e => setResumeForm({ ...resumeForm, languages: e.target.value })}
                                placeholder="e.g. Python, Java, JavaScript, C++, SQL"
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>

                            <div>
                              <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Frameworks &amp; Web Technologies</label>
                              <input
                                type="text"
                                value={resumeForm.frameworks}
                                onChange={e => setResumeForm({ ...resumeForm, frameworks: e.target.value })}
                                placeholder="e.g. React, Next.js, FastAPI, Node.js, Express, Tailwind CSS"
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>

                            <div>
                              <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Developer Tools, Cloud &amp; Databases</label>
                              <input
                                type="text"
                                value={resumeForm.tools}
                                onChange={e => setResumeForm({ ...resumeForm, tools: e.target.value })}
                                placeholder="e.g. PostgreSQL, MongoDB, Docker, Git, Redis, AWS, Linux"
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>
                          </div>
                        </div>
                      </div>

                      {/* Section 3: Experience & Projects */}
                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Work Experience */}
                        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-3.5">
                          <div className="text-xs font-bold uppercase tracking-wider text-white border-b border-zinc-800 pb-2">
                            4. Work Experience &amp; Internships
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                              <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Organization / Company</label>
                              <input
                                type="text"
                                value={resumeForm.experienceCompany}
                                onChange={e => setResumeForm({ ...resumeForm, experienceCompany: e.target.value })}
                                placeholder="e.g. Acme Tech"
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>
                            <div>
                              <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Job Title / Role</label>
                              <input
                                type="text"
                                value={resumeForm.experienceRole}
                                onChange={e => setResumeForm({ ...resumeForm, experienceRole: e.target.value })}
                                placeholder="e.g. Software Engineering Intern"
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                              <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Duration / Dates</label>
                              <input
                                type="text"
                                value={resumeForm.experienceDuration}
                                onChange={e => setResumeForm({ ...resumeForm, experienceDuration: e.target.value })}
                                placeholder="e.g. June 2024 - Aug 2024"
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>
                            <div>
                              <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Location</label>
                              <input
                                type="text"
                                value={resumeForm.experienceLocation}
                                onChange={e => setResumeForm({ ...resumeForm, experienceLocation: e.target.value })}
                                placeholder="e.g. Bengaluru, India"
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>
                          </div>

                          <div>
                            <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Achievement Bullets (one per line)</label>
                            <textarea
                              rows={3}
                              value={resumeForm.experienceBullets}
                              onChange={e => setResumeForm({ ...resumeForm, experienceBullets: e.target.value })}
                              placeholder="• Developed high-performance REST APIs in FastAPI reducing response latency by 35%&#10;• Integrated Redis caching for faster database lookups"
                              className="w-full bg-zinc-800 border border-zinc-700 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500 resize-none leading-relaxed"
                            />
                          </div>
                        </div>

                        {/* Projects */}
                        <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-3.5">
                          <div className="text-xs font-bold uppercase tracking-wider text-white border-b border-zinc-800 pb-2">
                            5. Key Technical Projects
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            <div>
                              <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Project Title</label>
                              <input
                                type="text"
                                value={resumeForm.project1Title}
                                onChange={e => setResumeForm({ ...resumeForm, project1Title: e.target.value })}
                                placeholder="e.g. Distributed Task Queue Platform"
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>
                            <div>
                              <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Tech Stack Used</label>
                              <input
                                type="text"
                                value={resumeForm.project1Stack}
                                onChange={e => setResumeForm({ ...resumeForm, project1Stack: e.target.value })}
                                placeholder="e.g. Next.js 14, FastAPI, PostgreSQL"
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>
                          </div>

                          <div>
                            <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Project GitHub / Live Link</label>
                            <input
                              type="url"
                              value={resumeForm.project1Link}
                              onChange={e => setResumeForm({ ...resumeForm, project1Link: e.target.value })}
                              placeholder="https://github.com/username/project"
                              className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                            />
                          </div>

                          <div>
                            <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Project Bullets (one per line)</label>
                            <textarea
                              rows={3}
                              value={resumeForm.project1Bullets}
                              onChange={e => setResumeForm({ ...resumeForm, project1Bullets: e.target.value })}
                              placeholder="• Built automated ATS resume parsing engine&#10;• Engineered interactive code execution workspace"
                              className="w-full bg-zinc-800 border border-zinc-700 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500 resize-none leading-relaxed"
                            />
                          </div>

                          <div className="pt-3 border-t border-zinc-800 space-y-3">
                            <div className="text-[11px] font-bold text-zinc-300">Second project (optional)</div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                              <input
                                type="text"
                                value={resumeForm.project2Title}
                                onChange={e => setResumeForm({ ...resumeForm, project2Title: e.target.value })}
                                placeholder="Project title"
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                              <input
                                type="text"
                                value={resumeForm.project2Stack}
                                onChange={e => setResumeForm({ ...resumeForm, project2Stack: e.target.value })}
                                placeholder="Tech stack"
                                className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                              />
                            </div>
                            <input
                              type="url"
                              value={resumeForm.project2Link}
                              onChange={e => setResumeForm({ ...resumeForm, project2Link: e.target.value })}
                              placeholder="https://github.com/username/another-project"
                              className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                            />
                            <textarea
                              rows={2}
                              value={resumeForm.project2Bullets}
                              onChange={e => setResumeForm({ ...resumeForm, project2Bullets: e.target.value })}
                              placeholder="• What you built and the measurable result (one per line)"
                              className="w-full bg-zinc-800 border border-zinc-700 rounded-xl p-3 text-xs text-white focus:outline-none focus:border-indigo-500 resize-none leading-relaxed"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Section 4: Certifications & Honors */}
                      <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5 space-y-3.5">
                        <div className="text-xs font-bold uppercase tracking-wider text-white border-b border-zinc-800 pb-2">
                          6. Certifications, Honors &amp; Interests
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
                          <div>
                            <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Certifications (comma-separated)</label>
                            <input
                              type="text"
                              value={resumeForm.certifications}
                              onChange={e => setResumeForm({ ...resumeForm, certifications: e.target.value })}
                              placeholder="e.g. AWS Certified Cloud Practitioner, Meta Full Stack Developer"
                              className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                          <div>
                            <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Honors &amp; Hackathons (comma-separated)</label>
                            <input
                              type="text"
                              value={resumeForm.achievements}
                              onChange={e => setResumeForm({ ...resumeForm, achievements: e.target.value })}
                              placeholder="e.g. Smart India Hackathon Finalist, LeetCode Top 5% Global Ranking"
                              className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                          <div className="sm:col-span-2">
                            <label className="text-[11px] text-zinc-400 block mb-1 font-medium">Interests &amp; Hobbies (comma-separated)</label>
                            <input
                              type="text"
                              value={resumeForm.interests}
                              onChange={e => setResumeForm({ ...resumeForm, interests: e.target.value })}
                              placeholder="e.g. Open-source contribution, Chess, Technical blogging, Robotics club"
                              className="w-full bg-zinc-800 border border-zinc-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                            />
                          </div>
                        </div>
                      </div>

                      {/* Submit Actions */}
                      <div className="flex flex-col sm:flex-row items-center gap-3">
                        <button
                          type="submit"
                          disabled={loading}
                          className="flex-1 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-bold rounded-xl transition-all shadow-lg shadow-indigo-600/30 flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                        >
                          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                          {loading ? 'Compiling & Scoring...' : 'Generate Standard Resume & Run ATS Score (+150 XP)'}
                        </button>
                        <button
                          type="button"
                          disabled={resumePdfLoading}
                          onClick={downloadResumePdf}
                          className="px-6 py-3 bg-zinc-800 hover:bg-zinc-700 text-white text-xs font-bold rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer shadow-md disabled:opacity-50"
                        >
                          {resumePdfLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                          Download PDF
                        </button>
                      </div>
                    </form>
                  )}

                  {/* ── 3. STANDARD ATS RESUME DOCUMENT PREVIEW ── */}
                  {resumeMode === 'preview' && (
                    <div className="space-y-6">
                      {/* A4 Document Sheet (210 × 297 mm), same single-column ATS layout as the PDF */}
                      <div className="text-[11px] text-zinc-500 text-center -mb-3">A4 preview · single column · ATS friendly</div>
                      <div className="overflow-x-auto pb-2">
                      <div
                        className="resume-sheet bg-white text-slate-900 mx-auto shadow-2xl font-sans border border-slate-200"
                        style={{ width: '210mm', minHeight: '297mm', padding: '13mm 16mm' }}
                      >
                        {(() => {
                          const list = (v: string) => v.split(',').map(x => x.trim()).filter(Boolean);
                          const lines = (v: string) => v.split('\n').map(x => x.replace(/^[•\-*]\s*/, '').trim()).filter(Boolean);
                          const clean = (u: string) => u.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '');
                          const href = (u: string) => (u.startsWith('http') ? u : `https://${u}`);
                          const Section = ({ title, children }: { title: string; children: React.ReactNode }) => (
                            <div className="mt-3">
                              <h2 className="text-[12px] font-bold uppercase tracking-wide text-slate-900">{title}</h2>
                              <div className="border-t border-slate-900 mt-0.5 mb-1.5" />
                              {children}
                            </div>
                          );
                          const projects = [
                            { t: resumeForm.project1Title, st: resumeForm.project1Stack, l: resumeForm.project1Link, b: resumeForm.project1Bullets },
                            { t: resumeForm.project2Title, st: resumeForm.project2Stack, l: resumeForm.project2Link, b: resumeForm.project2Bullets },
                          ].filter(pr => pr.t.trim());
                          const contact = [resumeForm.phone, resumeForm.email || userProfile?.email, resumeForm.location].filter(Boolean) as string[];
                          const links = [resumeForm.linkedin, resumeForm.github, resumeForm.portfolio].filter(Boolean) as string[];
                          const skillRows: [string, string][] = ([
                            ['Languages', resumeForm.languages], ['Frameworks & Libraries', resumeForm.frameworks],
                            ['Tools & Platforms', resumeForm.tools], ['Core Skills', resumeForm.skills],
                          ] as [string, string][]).filter(([, v]) => v.trim());
                          return (
                            <>
                              <div className="text-center">
                                <h1 className="text-[22px] font-bold leading-tight">{resumeForm.name || userProfile?.full_name || 'Your Name'}</h1>
                                <div className="text-[12.5px] text-slate-600">{resumeForm.headline || userProfile?.target_roles?.[0] || 'Target Role'}</div>
                                <div className="text-[10.5px] text-slate-600 mt-1">
                                  {[...contact, ...links].map((c, i) => (
                                    <span key={i}>
                                      {i > 0 && <span className="mx-1.5">|</span>}
                                      {links.includes(c) ? <a href={href(c)} target="_blank" rel="noreferrer" className="text-blue-700">{clean(c)}</a> : c}
                                    </span>
                                  ))}
                                </div>
                              </div>

                              {resumeForm.summary && (
                                <Section title="Professional Summary">
                                  <p className="text-[11px] leading-relaxed">{resumeForm.summary}</p>
                                </Section>
                              )}

                              {(resumeForm.education || resumeForm.college) && (
                                <Section title="Education">
                                  <div className="flex justify-between text-[11.5px]"><span className="font-bold">{resumeForm.education || 'Degree'}</span><span className="text-slate-600">{resumeForm.gradYear}</span></div>
                                  <div className="text-[10.5px] italic text-slate-600">{[resumeForm.college, resumeForm.cgpa && `CGPA: ${resumeForm.cgpa}`].filter(Boolean).join(', ')}</div>
                                </Section>
                              )}

                              {skillRows.length > 0 && (
                                <Section title="Technical Skills">
                                  {skillRows.map(([k, v]) => (
                                    <div key={k} className="text-[11px] leading-relaxed"><span className="font-bold">{k}:</span> {list(v).join(', ')}</div>
                                  ))}
                                </Section>
                              )}

                              {projects.length > 0 && (
                                <Section title="Projects">
                                  {projects.map((pr, i) => (
                                    <div key={i} className="mb-2">
                                      <div className="text-[11.5px]"><span className="font-bold">{pr.t}</span>{pr.st && <span className="italic text-slate-600"> | {pr.st}</span>}</div>
                                      {pr.l && <a href={href(pr.l)} target="_blank" rel="noreferrer" className="text-[10.5px] text-blue-700 italic">{clean(pr.l)}</a>}
                                      <ul className="list-disc ml-4 text-[11px] leading-relaxed">{lines(pr.b).map((b, j) => <li key={j}>{b}</li>)}</ul>
                                    </div>
                                  ))}
                                </Section>
                              )}

                              {resumeForm.experienceCompany && (
                                <Section title="Experience">
                                  <div className="flex justify-between text-[11.5px]">
                                    <span><span className="font-bold">{resumeForm.experienceRole}</span> — {resumeForm.experienceCompany}</span>
                                    <span className="text-slate-600">{resumeForm.experienceDuration}</span>
                                  </div>
                                  {resumeForm.experienceLocation && <div className="text-[10.5px] italic text-slate-600">{resumeForm.experienceLocation}</div>}
                                  <ul className="list-disc ml-4 text-[11px] leading-relaxed">{lines(resumeForm.experienceBullets).map((b, j) => <li key={j}>{b}</li>)}</ul>
                                </Section>
                              )}

                              {resumeForm.certifications.trim() && (
                                <Section title="Certifications">
                                  <ul className="list-disc ml-4 text-[11px] leading-relaxed">{list(resumeForm.certifications).map((c, i) => <li key={i}>{c}</li>)}</ul>
                                </Section>
                              )}

                              {resumeForm.achievements.trim() && (
                                <Section title="Achievements">
                                  <ul className="list-disc ml-4 text-[11px] leading-relaxed">{list(resumeForm.achievements).map((c, i) => <li key={i}>{c}</li>)}</ul>
                                </Section>
                              )}

                              {resumeForm.interests.trim() && (
                                <Section title="Interests">
                                  <p className="text-[11px]">{list(resumeForm.interests).join(', ')}</p>
                                </Section>
                              )}
                            </>
                          );
                        })()}
                      </div>
                      </div>

                      {/* Action Bar */}
                      <div className="flex items-center justify-center gap-3 pt-2">
                        <button
                          type="button"
                          onClick={() => setResumeMode('builder')}
                          className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl text-xs font-bold transition-all cursor-pointer"
                        >
                          ✏️ Edit Resume Details
                        </button>
                        <button
                          type="button"
                          disabled={resumePdfLoading}
                          onClick={downloadResumePdf}
                          className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-2 cursor-pointer shadow-lg shadow-indigo-600/30 disabled:opacity-50"
                        >
                          {resumePdfLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                          {resumePdfLoading ? 'Exporting PDF...' : 'Download Standard Resume PDF'}
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* ── CODING ── */}
              {sidebarTab === 'coding' && (
                <div className="grid grid-cols-12 gap-5 h-[calc(100vh-8rem)]">
                  {/* Left: Problem Bank & Filters (Col 4) */}
                  <div className="col-span-4 bg-zinc-900/90 border border-zinc-800 rounded-2xl p-4 flex flex-col min-h-0">
                    <div className="flex items-center justify-between mb-3 flex-shrink-0">
                      <div className="flex items-center gap-2">
                        <Code2 className="w-4 h-4 text-indigo-400" />
                        <span className="text-xs font-bold uppercase tracking-wider text-white">Problem Bank</span>
                      </div>
                      <span className="text-[10px] text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded-full font-mono">
                        {codingProblems.filter(p => {
                          const matchesCat = codingFilterCategory === 'All' || p.category.toLowerCase().includes(codingFilterCategory.toLowerCase());
                          const matchesDiff = codingFilterDifficulty === 'All' || p.difficulty === codingFilterDifficulty;
                          const matchesSearch = !codingSearchQuery || p.title.toLowerCase().includes(codingSearchQuery.toLowerCase()) || p.category.toLowerCase().includes(codingSearchQuery.toLowerCase());
                          return matchesCat && matchesDiff && matchesSearch;
                        }).length} / {codingProblems.length}
                      </span>
                    </div>

                    {/* Search & Difficulty Filter */}
                    <div className="space-y-2 mb-3 flex-shrink-0">
                      <div className="relative">
                        <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
                        <input
                          type="text"
                          value={codingSearchQuery}
                          onChange={e => setCodingSearchQuery(e.target.value)}
                          placeholder="Search title, category, company..."
                          className="w-full pl-8 pr-3 py-1.5 bg-zinc-950 border border-zinc-800 rounded-xl text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500"
                        />
                      </div>
                      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 text-[11px]">
                        {['All', 'Easy', 'Medium', 'Hard'].map(diff => (
                          <button
                            key={diff}
                            onClick={() => setCodingFilterDifficulty(diff)}
                            className={`px-2.5 py-1 rounded-lg font-semibold transition-all cursor-pointer flex-shrink-0 ${
                              codingFilterDifficulty === diff
                                ? 'bg-indigo-600 text-white shadow-sm'
                                : 'bg-zinc-800/80 text-zinc-400 hover:text-white hover:bg-zinc-800'
                            }`}
                          >
                            {diff}
                          </button>
                        ))}
                      </div>
                    </div>

                    {/* Problem list */}
                    <div className="flex-1 overflow-y-auto space-y-2 pr-1 min-h-0">
                      {codingProblems.length === 0 ? (
                        <div className="text-center py-12 text-zinc-500">
                          <Code2 className="w-8 h-8 mx-auto mb-2 opacity-30 animate-pulse" />
                          <p className="text-xs font-semibold">Loading problem bank...</p>
                          <p className="text-[10px] text-zinc-600 mt-1">Connecting to coding intelligence sandbox</p>
                        </div>
                      ) : codingProblems
                          .filter(p => {
                            const matchesCat = codingFilterCategory === 'All' || p.category.toLowerCase().includes(codingFilterCategory.toLowerCase());
                            const matchesDiff = codingFilterDifficulty === 'All' || p.difficulty === codingFilterDifficulty;
                            const matchesSearch = !codingSearchQuery || p.title.toLowerCase().includes(codingSearchQuery.toLowerCase()) || p.category.toLowerCase().includes(codingSearchQuery.toLowerCase());
                            return matchesCat && matchesDiff && matchesSearch;
                          })
                          .map(p => (
                            <button
                              key={p.id}
                              onClick={() => selectProblem(p.id)}
                              className={`w-full text-left p-3 rounded-xl border transition-all text-xs cursor-pointer group ${
                                activeProblem?.id === p.id
                                  ? 'border-indigo-500 bg-indigo-500/10 shadow-lg shadow-indigo-500/10'
                                  : 'border-zinc-800/80 hover:border-zinc-700 bg-zinc-950/60 hover:bg-zinc-800/40'
                              }`}
                            >
                              <div className="flex items-center justify-between mb-1">
                                <span className="font-semibold text-white group-hover:text-indigo-300 transition-colors flex items-center gap-1.5 truncate">
                                  {p.is_solved && <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 flex-shrink-0" />}
                                  {p.title}
                                </span>
                                <span
                                  className={`text-[9px] px-2 py-0.5 rounded-full font-bold flex-shrink-0 ${
                                    p.difficulty === 'Hard'
                                      ? 'bg-red-500/15 text-red-400 border border-red-500/30'
                                      : p.difficulty === 'Medium'
                                      ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                                      : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                  }`}
                                >
                                  {p.difficulty}
                                </span>
                              </div>
                              <div className="flex items-center justify-between text-[10px] text-zinc-400">
                                <span>{p.category}</span>
                                {p.company_tags && p.company_tags.length > 0 && (
                                  <span className="text-zinc-500 truncate max-w-[120px]">{p.company_tags.slice(0, 2).join(', ')}</span>
                                )}
                              </div>
                            </button>
                          ))}
                    </div>
                  </div>

                  {/* Right: Problem Details & Monaco Editor (Col 8) */}
                  <div className="col-span-8 flex flex-col gap-4 min-h-0">
                    {activeProblem ? (
                      <>
                        {/* Problem Details Card */}
                        <div className="bg-zinc-900/90 border border-zinc-800 rounded-2xl p-4 overflow-y-auto max-h-[36vh] flex flex-col flex-shrink-0">
                          {/* Title & Metadata */}
                          <div className="flex items-start justify-between gap-4 pb-3 border-b border-zinc-800 mb-3 flex-shrink-0">
                            <div>
                              <div className="flex items-center gap-2">
                                <h2 className="font-bold text-base text-white">{activeProblem.title}</h2>
                                <span
                                  className={`text-[10px] px-2.5 py-0.5 rounded-full font-bold ${
                                    activeProblem.difficulty === 'Hard'
                                      ? 'bg-red-500/15 text-red-400 border border-red-500/30'
                                      : activeProblem.difficulty === 'Medium'
                                      ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                                      : 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                  }`}
                                >
                                  {activeProblem.difficulty}
                                </span>
                                <span className="text-[10px] bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded-full border border-zinc-700">
                                  {activeProblem.category}
                                </span>
                              </div>
                              {activeProblem.company_tags && activeProblem.company_tags.length > 0 && (
                                <div className="flex items-center gap-1.5 mt-2">
                                  <span className="text-[10px] text-zinc-500 font-semibold">Asked in:</span>
                                  {activeProblem.company_tags.map((tag: string) => (
                                    <span key={tag} className="text-[10px] bg-zinc-800/80 text-indigo-300 px-2 py-0.5 rounded border border-zinc-700/60">
                                      {tag}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>

                            {/* Complexity Targets */}
                            <div className="flex flex-col items-end text-[10px] text-zinc-400 font-mono flex-shrink-0">
                              <span>Time: <strong className="text-indigo-300">{activeProblem.expected_time_complexity || 'O(N)'}</strong></span>
                              <span>Space: <strong className="text-indigo-300">{activeProblem.expected_space_complexity || 'O(1)'}</strong></span>
                            </div>
                          </div>

                          {/* Problem Tab Bar */}
                          <div className="flex items-center gap-4 text-xs font-semibold border-b border-zinc-800/80 mb-3 pb-2 flex-shrink-0">
                            <button
                              onClick={() => setActiveCodeTab('description')}
                              className={`transition-colors cursor-pointer ${
                                activeCodeTab === 'description' ? 'text-indigo-400 border-b-2 border-indigo-500 pb-2 -mb-2' : 'text-zinc-400 hover:text-zinc-200'
                              }`}
                            >
                              Description
                            </button>
                            <button
                              onClick={() => setActiveCodeTab('solution')}
                              className={`transition-colors cursor-pointer ${
                                activeCodeTab === 'solution' ? 'text-indigo-400 border-b-2 border-indigo-500 pb-2 -mb-2' : 'text-zinc-400 hover:text-zinc-200'
                              }`}
                            >
                              Editorial & Blueprint
                            </button>
                          </div>

                          {/* Tab Content */}
                          {activeCodeTab === 'description' ? (
                            <div className="space-y-3 text-xs text-zinc-300 leading-relaxed overflow-y-auto pr-1">
                              <p className="whitespace-pre-wrap">{activeProblem.problem_statement}</p>

                              {/* Structured Examples */}
                              {activeProblem.example_input && (
                                <div className="p-3 bg-zinc-950/80 border border-zinc-800 rounded-xl space-y-1.5 font-mono text-[11px]">
                                  <div className="text-zinc-400 font-sans font-bold text-xs uppercase tracking-wide text-indigo-400">Example 1:</div>
                                  <div>
                                    <span className="text-zinc-500 font-semibold">Input: </span>
                                    <code className="text-indigo-300">{activeProblem.example_input}</code>
                                  </div>
                                  <div>
                                    <span className="text-zinc-500 font-semibold">Output: </span>
                                    <code className="text-emerald-400">{activeProblem.example_output}</code>
                                  </div>
                                  {activeProblem.explanation && (
                                    <div className="text-zinc-400 font-sans text-xs pt-1 border-t border-zinc-800/60 mt-1">
                                      <span className="text-zinc-500 font-semibold">Explanation: </span>
                                      {activeProblem.explanation}
                                    </div>
                                  )}
                                </div>
                              )}

                              {/* Constraints Section */}
                              {activeProblem.constraints && (
                                <div className="pt-2 border-t border-zinc-800/60">
                                  <div className="text-zinc-400 font-bold text-xs mb-1.5">Constraints:</div>
                                  <div className="bg-zinc-950/50 p-2.5 rounded-xl border border-zinc-800/60 space-y-1 text-[11px] font-mono text-zinc-300">
                                    {activeProblem.constraints.split('\n').map((c: string, i: number) => (
                                      <div key={i} className="flex items-start gap-1.5">
                                        <span className="text-indigo-400">•</span>
                                        <span>{c.replace(/^[•\-*]\s*/, '')}</span>
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          ) : (
                            <div className="text-xs text-zinc-300 space-y-3 overflow-y-auto pr-1">
                              <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 rounded-xl">
                                <h4 className="font-bold text-indigo-300 mb-1">Algorithmic Approach</h4>
                                <p className="leading-relaxed">{activeProblem.editorial || 'Analyze time & space trade-offs by identifying optimal data structures (e.g. HashMap or Two Pointers).'}</p>
                              </div>
                              <div className="space-y-1.5">
                                <h4 className="font-bold text-white text-xs">Progressive Hints:</h4>
                                {(activeProblem.hints || []).map((h: string, i: number) => (
                                  <div key={i} className="p-2.5 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 flex items-start gap-2">
                                    <span className="font-bold text-indigo-400 flex-shrink-0">#{i + 1}</span>
                                    <span>{h}</span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        {/* Monaco Editor Card */}
                        <div className="flex-1 bg-zinc-900/90 border border-zinc-800 rounded-2xl overflow-hidden flex flex-col min-h-0 shadow-2xl">
                          {/* Editor Top Bar */}
                          <div className="px-4 py-2.5 bg-zinc-950 border-b border-zinc-800 flex items-center justify-between flex-shrink-0">
                            <div className="flex items-center gap-3">
                              {/* Language Selector */}
                              <select
                                value={editorLang}
                                onChange={e => changeLang(e.target.value)}
                                className="bg-zinc-900 border border-zinc-700 text-zinc-200 rounded-lg px-2.5 py-1 text-xs font-semibold focus:outline-none focus:border-indigo-500 cursor-pointer"
                              >
                                <option value="python">Python 3</option>
                                <option value="cpp">C++ (GCC, C++17)</option>
                                <option value="java">Java (OpenJDK 17)</option>
                                <option value="javascript">JavaScript (Node.js)</option>
                              </select>

                              {/* Auto-save Status Indicator */}
                              <div className="flex items-center gap-1.5 text-[11px] text-zinc-400 font-mono">
                                <span className={`w-2 h-2 rounded-full ${autoSaveStatus.includes('Saving') ? 'bg-amber-400 animate-ping' : 'bg-emerald-400'}`} />
                                <span>{autoSaveStatus} {autoSaveTime ? `(${autoSaveTime})` : ''}</span>
                              </div>
                            </div>

                            {/* Actions: AI Hint & Reset */}
                            <div className="flex items-center gap-2">
                              <button
                                onClick={resetStarterCode}
                                title="Reset code to original template"
                                className="p-1.5 rounded-lg border border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors cursor-pointer text-[11px] flex items-center gap-1"
                              >
                                <RotateCcw className="w-3.5 h-3.5" />
                                <span className="hidden sm:inline">Reset</span>
                              </button>

                              <button
                                onClick={() => requestSmartAiHint(1)}
                                className="px-3 py-1 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-md transition-all cursor-pointer"
                              >
                                <Lightbulb className="w-3.5 h-3.5 text-amber-300" />
                                <span>AI Hint</span>
                              </button>
                            </div>
                          </div>

                          {/* Monaco Code Editor with Real-Time Syntax Validation */}
                          <div className="flex-1 w-full min-h-0">
                            <MonacoCodeEditor
                              theme={themeMode}
                              code={editorCode}
                              language={editorLang}
                              onChange={(val) => {
                                setEditorCode(val);
                                setAutoSaveStatus('Saving...');
                              }}
                              onSyntaxErrorChange={(errors) => setSyntaxErrorsCount(errors.length)}
                            />
                          </div>

                          {/* Output & Diagnostics Console */}
                          {codeOutput && (
                            <div className="border-t border-zinc-800 bg-zinc-950 flex flex-col max-h-48 overflow-y-auto text-xs flex-shrink-0">
                              {/* Output Header */}
                              <div className="px-4 py-2 border-b border-zinc-800/80 flex items-center justify-between bg-zinc-900/60 flex-shrink-0">
                                <div className="flex items-center gap-3">
                                  <button
                                    onClick={() => setActiveOutputTab('testcases')}
                                    className={`font-semibold transition-colors cursor-pointer text-xs ${
                                      activeOutputTab === 'testcases' ? 'text-indigo-400' : 'text-zinc-400 hover:text-white'
                                    }`}
                                  >
                                    Test Cases
                                  </button>
                                  {codeOutput.error_details && (
                                    <button
                                      onClick={() => setActiveOutputTab('diagnostics')}
                                      className={`font-semibold flex items-center gap-1 transition-colors cursor-pointer text-xs ${
                                        activeOutputTab === 'diagnostics' ? 'text-red-400' : 'text-zinc-400 hover:text-red-300'
                                      }`}
                                    >
                                      <Bug className="w-3.5 h-3.5" />
                                      Detailed Error Analysis
                                    </button>
                                  )}
                                </div>

                                {/* Status Badge */}
                                <div className="flex items-center gap-2">
                                  <span
                                    className={`font-bold px-2.5 py-0.5 rounded-full text-[10px] ${
                                      codeOutput.status === 'Accepted'
                                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                                        : 'bg-red-500/15 text-red-400 border border-red-500/30 animate-pulse'
                                    }`}
                                  >
                                    {codeOutput.status}
                                  </span>
                                  {codeOutput.execution_time > 0 && (
                                    <span className="text-[10px] text-zinc-500 font-mono">
                                      {codeOutput.execution_time} ms
                                    </span>
                                  )}
                                </div>
                              </div>

                              {/* Output Content */}
                              <div className="p-3 overflow-y-auto">
                                {activeOutputTab === 'diagnostics' && codeOutput.error_details ? (
                                  /* LeetCode-Grade Detailed Error Breakdown */
                                  <div className="space-y-2.5 font-mono text-[11px]">
                                    <div className="p-3 bg-red-950/40 border border-red-800/80 rounded-xl space-y-2">
                                      <div className="flex items-center gap-2 text-red-400 font-bold text-xs">
                                        <AlertCircle className="w-4 h-4 flex-shrink-0" />
                                        <span>{codeOutput.error_details.error_type || 'Execution Error'}: {codeOutput.error_details.error_message || codeOutput.status}</span>
                                      </div>

                                      {/* Explanation */}
                                      <div className="font-sans text-xs text-zinc-200 bg-red-900/20 p-2.5 rounded-lg border border-red-800/40 leading-relaxed">
                                        <strong className="text-red-300">Why this error happened: </strong>
                                        {codeOutput.error_details.explanation}
                                      </div>

                                      {/* Code Line Snippet */}
                                      {codeOutput.error_details.line_number && (
                                        <div className="bg-zinc-950 p-2.5 rounded-lg border border-zinc-800 text-zinc-300 space-y-1">
                                          <div className="text-zinc-500 text-[10px]">Location: Line {codeOutput.error_details.line_number}</div>
                                          {codeOutput.error_details.line_code && (
                                            <div className="text-red-300 font-semibold pl-2 border-l-2 border-red-500">
                                              {codeOutput.error_details.line_code}
                                            </div>
                                          )}
                                        </div>
                                      )}

                                      {/* Raw Traceback Expandable */}
                                      {codeOutput.error_details.raw_trace && (
                                        <details className="text-[10px] text-zinc-400 pt-1">
                                          <summary className="cursor-pointer hover:text-white font-sans">View Full Error Traceback</summary>
                                          <pre className="mt-1.5 p-2 bg-zinc-950 rounded text-red-400 overflow-x-auto whitespace-pre-wrap">
                                            {codeOutput.error_details.raw_trace}
                                          </pre>
                                        </details>
                                      )}
                                    </div>
                                  </div>
                                ) : (
                                  /* Test Cases View */
                                  <div className="space-y-2">
                                    {codeOutput.test_results && codeOutput.test_results.length > 0 ? (
                                      <div className="space-y-2">
                                        <div className="flex items-center gap-1.5 pb-1">
                                          {codeOutput.test_results.map((tc: any, i: number) => (
                                            <button
                                              key={i}
                                              onClick={() => setActiveTestCaseIdx(i)}
                                              className={`px-2.5 py-1 rounded-lg text-[10px] font-mono font-semibold transition-all cursor-pointer ${
                                                activeTestCaseIdx === i
                                                  ? 'bg-zinc-800 text-white border border-zinc-700'
                                                  : 'bg-zinc-950 text-zinc-400 hover:bg-zinc-900'
                                              } flex items-center gap-1.5`}
                                            >
                                              <span className={`w-1.5 h-1.5 rounded-full ${tc.passed ? 'bg-emerald-400' : 'bg-red-400'}`} />
                                              Case {i + 1}
                                            </button>
                                          ))}
                                        </div>

                                        {/* Active Test Case Details */}
                                        {codeOutput.test_results[activeTestCaseIdx] && (
                                          <div className="p-3 bg-zinc-900/60 rounded-xl border border-zinc-800 space-y-1.5 font-mono text-[11px]">
                                            <div>
                                              <span className="text-zinc-500">Input: </span>
                                              <code className="text-indigo-300">{codeOutput.test_results[activeTestCaseIdx].input || '(No input)'}</code>
                                            </div>
                                            <div>
                                              <span className="text-zinc-500">Output: </span>
                                              <code className={codeOutput.test_results[activeTestCaseIdx].passed ? 'text-emerald-400' : 'text-red-400'}>
                                                {codeOutput.test_results[activeTestCaseIdx].actual}
                                              </code>
                                            </div>
                                            <div>
                                              <span className="text-zinc-500">Expected: </span>
                                              <code className="text-zinc-300">{codeOutput.test_results[activeTestCaseIdx].expected}</code>
                                            </div>
                                            {codeOutput.test_results[activeTestCaseIdx].stdout && (
                                              <div>
                                                <span className="text-zinc-500">Your print output:</span>
                                                <pre className="mt-1 p-2 bg-zinc-950 border border-zinc-800 rounded-lg text-zinc-300 whitespace-pre-wrap max-h-28 overflow-auto">{codeOutput.test_results[activeTestCaseIdx].stdout}</pre>
                                              </div>
                                            )}
                                          </div>
                                        )}
                                      </div>
                                    ) : (
                                      <p className="text-zinc-300 font-sans text-xs">{codeOutput.message}</p>
                                    )}

                                    {codeOutput.ai_feedback && (
                                      <div className="mt-2 p-2.5 bg-indigo-500/10 border border-indigo-500/20 rounded-xl text-xs text-indigo-300">
                                        💡 {codeOutput.ai_feedback}
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Footer Controls */}
                          <div className="px-4 py-2.5 border-t border-zinc-800 bg-zinc-950 flex items-center justify-between flex-shrink-0">
                            <div className="flex items-center gap-2 text-[11px] text-zinc-500">
                              {syntaxErrorsCount > 0 ? (
                                <span className="text-red-400 flex items-center gap-1 font-semibold">
                                  <AlertCircle className="w-3.5 h-3.5 animate-pulse" /> {syntaxErrorsCount} Syntax Error{syntaxErrorsCount > 1 ? 's' : ''} on red squiggly lines
                                </span>
                              ) : (
                                <span className="text-emerald-400/90 flex items-center gap-1">
                                  <CheckCircle2 className="w-3.5 h-3.5" /> Syntax clean
                                </span>
                              )}
                            </div>

                            <div className="flex items-center gap-2.5">
                              <button
                                onClick={runCode}
                                disabled={submittingCode}
                                className="px-4 py-1.5 border border-zinc-700 hover:bg-zinc-800 text-xs font-semibold rounded-xl flex items-center gap-1.5 transition-colors cursor-pointer text-zinc-200"
                              >
                                <Play className="w-3.5 h-3.5 text-indigo-400" />
                                {submittingCode ? 'Running...' : 'Run Code'}
                              </button>
                              <button
                                onClick={submitCode}
                                disabled={submittingCode}
                                className="px-5 py-1.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white text-xs font-semibold rounded-xl transition-all shadow-md shadow-indigo-600/30 cursor-pointer"
                              >
                                {submittingCode ? 'Submitting...' : 'Submit'}
                              </button>
                            </div>
                          </div>
                        </div>
                      </>
                    ) : (
                      <div className="flex-1 bg-zinc-900/90 border border-zinc-800 rounded-2xl flex flex-col items-center justify-center text-center p-12">
                        <Code2 className="w-12 h-12 text-zinc-600 mb-3 animate-pulse" />
                        <h3 className="text-base font-bold text-zinc-300">Select a problem to start coding</h3>
                        <p className="text-xs text-zinc-500 mt-1 max-w-sm">
                          Choose from 30 curated LeetCode-style questions on the left to analyze time complexity, solve test cases, and earn XP.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ── AI SMART HINT MODAL ── */}
              <AnimatePresence>
                {showAiHintModal && (
                  <motion.div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                  >
                    <motion.div
                      className="bg-zinc-900 border border-zinc-800 w-full max-w-lg rounded-2xl p-6 shadow-2xl space-y-4"
                      initial={{ scale: 0.95, y: 10 }}
                      animate={{ scale: 1, y: 0 }}
                      exit={{ scale: 0.95, y: 10 }}
                    >
                      <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                        <div className="flex items-center gap-2">
                          <Lightbulb className="w-5 h-5 text-amber-400" />
                          <h3 className="font-bold text-white text-sm">AI Problem Tutor: {activeProblem?.title}</h3>
                        </div>
                        <button onClick={() => setShowAiHintModal(false)} className="text-zinc-500 hover:text-white p-1 rounded-lg">
                          <X className="w-4 h-4" />
                        </button>
                      </div>

                      {/* 3-Level Hint Selector */}
                      <div className="flex items-center gap-2 border-b border-zinc-800/60 pb-3 text-xs">
                        {[
                          { lvl: 1, label: '💡 1. Intuition' },
                          { lvl: 2, label: '🔍 2. Strategy' },
                          { lvl: 3, label: '⚡ 3. Edge Cases' }
                        ].map(item => (
                          <button
                            key={item.lvl}
                            onClick={() => requestSmartAiHint(item.lvl)}
                            className={`flex-1 py-1.5 rounded-xl font-semibold transition-all cursor-pointer ${
                              aiHintLevel === item.lvl
                                ? 'bg-indigo-600 text-white shadow-sm'
                                : 'bg-zinc-800 text-zinc-400 hover:bg-zinc-700 hover:text-white'
                            }`}
                          >
                            {item.label}
                          </button>
                        ))}
                      </div>

                      {/* Hint Content */}
                      {aiHintLoading ? (
                        <div className="py-8 text-center text-zinc-400 space-y-2">
                          <Loader2 className="w-6 h-6 mx-auto animate-spin text-indigo-400" />
                          <p className="text-xs">Analyzing problem blueprint & code structure...</p>
                        </div>
                      ) : aiHintData ? (
                        <div className="space-y-3 text-xs">
                          <div className="p-3.5 bg-indigo-500/10 border border-indigo-500/30 rounded-xl space-y-1.5">
                            <div className="text-[10px] uppercase font-bold text-indigo-400 tracking-wider">
                              Level {aiHintLevel} Clue:
                            </div>
                            <p className="text-zinc-200 leading-relaxed text-sm font-medium">
                              {aiHintData.current_hint}
                            </p>
                          </div>

                          {aiHintData.code_analysis && (
                            <div className="p-3 bg-zinc-950 rounded-xl border border-zinc-800 space-y-1">
                              <span className="text-[10px] text-amber-400 font-bold uppercase tracking-wider">
                                🤖 AI Code Doctor Feedback on your Typed Code:
                              </span>
                              <p className="text-zinc-300 leading-relaxed">{aiHintData.code_analysis}</p>
                            </div>
                          )}

                          <div className="p-3 bg-zinc-950/60 rounded-xl border border-zinc-800/80 space-y-1 text-zinc-400">
                            <span className="text-[10px] font-bold text-zinc-500 uppercase">Optimal Blueprint:</span>
                            <p className="text-zinc-300">{aiHintData.approach}</p>
                          </div>
                        </div>
                      ) : null}

                      <div className="flex justify-end gap-2 pt-2">
                        {aiHintLevel < 3 && (
                          <button
                            onClick={() => requestSmartAiHint(aiHintLevel + 1)}
                            className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 rounded-xl text-xs font-semibold cursor-pointer"
                          >
                            Next Clue →
                          </button>
                        )}
                        <button
                          onClick={() => setShowAiHintModal(false)}
                          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-semibold cursor-pointer"
                        >
                          Got It
                        </button>
                      </div>
                    </motion.div>
                  </motion.div>
                )}
              </AnimatePresence>

              {/* ── REAL-TIME AI MOCK INTERVIEW ROOM ── */}
              {sidebarTab === 'interview' && (
                <div className="space-y-6">
                  {/* PHASE 1: PRE-INTERVIEW SETUP & JOB DESCRIPTION */}
                  {!interviewStarted && !interviewFeedback && (
                    <motion.div
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="max-w-3xl mx-auto bg-zinc-900/90 border border-zinc-800 rounded-3xl p-7 shadow-2xl backdrop-blur-xl space-y-6"
                    >
                      {/* Header */}
                      <div className="text-center space-y-2">
                        <div className="inline-flex items-center gap-2 px-3 py-1 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-full text-xs font-bold uppercase tracking-wider">
                          <Sparkles className="w-3.5 h-3.5" /> Real-Time AI Interview Room
                        </div>
                        <h2 className="text-2xl font-black text-white tracking-tight">
                          Realistic Mock Interview for Your Field
                        </h2>
                        <p className="text-zinc-400 text-xs max-w-lg mx-auto leading-relaxed">
                          A live, spoken interview that flows like the real thing: introduction, a deep-dive into your project, field-specific technical questions, a scenario, behavioral questions and your questions at the end. Every follow-up is based on what you actually say.
                        </p>
                      </div>

                      {/* Config Grid */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <label className="text-xs text-zinc-300 font-bold block mb-1.5 flex items-center gap-1.5">
                            <Briefcase className="w-3.5 h-3.5 text-indigo-400" /> Target Job Role
                          </label>
                          <input
                            value={targetInterviewRole || userProfile?.target_roles?.[0] || 'Software Engineer'}
                            onChange={e => setTargetInterviewRole(e.target.value)}
                            placeholder="e.g. AI / ML Engineer, Full Stack Developer, SDE-1"
                            className="w-full bg-zinc-950 border border-zinc-800 focus:border-indigo-500 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none transition-colors"
                          />
                        </div>

                        <div>
                          <label className="text-xs text-zinc-300 font-bold block mb-1.5 flex items-center gap-1.5">
                            <SlidersHorizontal className="w-3.5 h-3.5 text-violet-400" /> Interview Format
                          </label>
                          <select
                            value={interviewType}
                            onChange={e => setInterviewType(e.target.value)}
                            className="w-full bg-zinc-950 border border-zinc-800 focus:border-indigo-500 rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none transition-colors"
                          >
                            <option value="Mixed">⚡ Full Placement Screening (Mixed)</option>
                            <option value="Technical">🛠️ Technical Deep-Dive & Architecture</option>
                            <option value="HR">🤝 HR & Behavioral (STAR Method)</option>
                          </select>
                        </div>
                      </div>

                      {/* Experience Level & Track Selection */}
                      <div>
                        <label className="text-xs text-zinc-300 font-bold block mb-1.5 flex items-center justify-between">
                          <span className="flex items-center gap-1.5">
                            <GraduationCap className="w-3.5 h-3.5 text-emerald-400" /> Candidate Experience Track
                          </span>
                          <span className="text-[10px] text-zinc-400 font-mono">Tailors question context</span>
                        </label>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                          <button
                            type="button"
                            onClick={() => {
                              setExperienceLevel('Fresher');
                              setCurrentDifficulty('Easy');
                            }}
                            className={`p-3 rounded-2xl border text-left transition-all cursor-pointer ${
                              experienceLevel === 'Fresher'
                                ? 'bg-emerald-500/10 border-emerald-500/40 ring-1 ring-emerald-500/30'
                                : 'bg-zinc-950 border-zinc-800 hover:border-zinc-700'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                                <span>🎓 Fresher / Student Track</span>
                              </span>
                              {experienceLevel === 'Fresher' && (
                                <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />
                              )}
                            </div>
                            <div className="text-[10px] text-zinc-400 mt-1 leading-relaxed">
                              Academic projects, core CS, basic AIML & fundamentals. <strong className="text-emerald-400/90 font-medium">No previous job questions</strong>.
                            </div>
                          </button>

                          <button
                            type="button"
                            onClick={() => {
                              setExperienceLevel('Experienced');
                              setCurrentDifficulty('Medium');
                            }}
                            className={`p-3 rounded-2xl border text-left transition-all cursor-pointer ${
                              experienceLevel === 'Experienced'
                                ? 'bg-indigo-500/10 border-indigo-500/40 ring-1 ring-indigo-500/30'
                                : 'bg-zinc-950 border-zinc-800 hover:border-zinc-700'
                            }`}
                          >
                            <div className="flex items-center justify-between">
                              <span className="text-xs font-bold text-white flex items-center gap-1.5">
                                <span>💼 Experienced Engineer Track</span>
                              </span>
                              {experienceLevel === 'Experienced' && (
                                <span className="w-2 h-2 rounded-full bg-indigo-400 shadow-[0_0_8px_rgba(129,140,248,0.8)]" />
                              )}
                            </div>
                            <div className="text-[10px] text-zinc-400 mt-1 leading-relaxed">
                              Past work history, system design, production outages, database scaling & leadership.
                            </div>
                          </button>
                        </div>
                      </div>

                      {/* Field / job family */}
                      <div>
                        <label className="text-xs text-zinc-300 font-bold block mb-1.5 flex items-center justify-between">
                          <span className="flex items-center gap-1.5">
                            <Sparkles className="w-3.5 h-3.5 text-amber-400" /> Field you're interviewing for
                          </span>
                          <span className="text-[10px] text-amber-400/90 font-semibold">
                            {topicDomain ? 'Questions tailored to this field' : 'Auto-detected from your target role'}
                          </span>
                        </label>
                        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                          {INTERVIEW_TRACKS.map(t => (
                            <button
                              key={t.id}
                              type="button"
                              onClick={() => { setTopicDomain(t.id); setTargetInterviewRole(t.label); }}
                              className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer ${
                                topicDomain === t.id
                                  ? 'bg-amber-500/10 border-amber-500/40 ring-1 ring-amber-500/30'
                                  : 'bg-zinc-950 border-zinc-800 hover:border-zinc-700'
                              }`}
                            >
                              <div className="text-xs font-bold text-white flex items-center justify-between gap-1">
                                <span className="truncate">{t.icon} {t.label}</span>
                                {topicDomain === t.id && <span className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0" />}
                              </div>
                              <div className="text-[9px] text-zinc-400 mt-1 truncate">{t.sub}</div>
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Interview length */}
                      <div className="flex items-center justify-between gap-3 flex-wrap">
                        <span className="text-xs text-zinc-300 font-bold flex items-center gap-1.5"><Clock className="w-3.5 h-3.5 text-indigo-400" /> Interview length</span>
                        <div className="flex gap-1.5">
                          {[{ n: 6, label: 'Quick · ~15 min' }, { n: 8, label: 'Standard · ~25 min' }, { n: 10, label: 'Full · ~35 min' }].map(o => (
                            <button key={o.n} type="button" onClick={() => setInterviewLength(o.n)}
                              className={`px-2.5 py-1 rounded-lg text-[10px] font-bold border transition-colors cursor-pointer ${interviewLength === o.n ? 'bg-indigo-600 border-indigo-600 text-white' : 'border-zinc-700 text-zinc-400 hover:bg-zinc-800'}`}>
                              {o.n} questions · {o.label.split(' · ')[1]}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Job Description (JD) Box */}
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <label className="text-xs text-zinc-300 font-bold flex items-center gap-1.5">
                            <FileText className="w-3.5 h-3.5 text-emerald-400" /> Custom Job Description (JD) / Requirements
                          </label>
                          <span className="text-[11px] text-zinc-500">Optional · AI adapts questions to this JD</span>
                        </div>
                        <textarea
                          rows={3}
                          value={jobDescription}
                          onChange={e => setJobDescription(e.target.value)}
                          placeholder="Paste target Job Description, required tech stack (e.g. PyTorch, Generative AI, React, Next.js, FastAPI, PostgreSQL, Redis, Docker), or syllabus..."
                          className="w-full bg-zinc-950 border border-zinc-800 focus:border-indigo-500 rounded-xl p-3 text-xs text-white placeholder-zinc-600 focus:outline-none transition-colors resize-none"
                        />
                        {/* Quick JD Presets */}
                        <div className="flex items-center gap-2 flex-wrap pt-1">
                          <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Quick Presets:</span>
                          {[
                            { label: '🎨 Frontend Fresher', role: 'Frontend Engineer', domain: 'frontend', level: 'Fresher', jd: 'Frontend Developer (fresher) with HTML, CSS, JavaScript, TypeScript, React and Next.js, focused on accessibility and web performance.' },
                            { label: '🤖 AI/ML Fresher', role: 'AI / ML Engineer', domain: 'ml', level: 'Fresher', jd: 'Junior ML Engineer with Python, PyTorch, scikit-learn, transformers, RAG and LLM application experience.' },
                            { label: '🧩 SDE Fresher (DSA)', role: 'Software Engineer', domain: 'sde', level: 'Fresher', jd: 'Entry-level Software Engineer with strong data structures, algorithms, OOP, operating systems and SQL fundamentals.' },
                            { label: '⚙️ Backend (Experienced)', role: 'Backend Engineer', domain: 'backend', level: 'Experienced', jd: 'Backend Engineer with Python/FastAPI or Node.js, PostgreSQL, Redis, Kafka, Docker and system design experience.' },
                          ].map(preset => (
                            <button
                              key={preset.label}
                              type="button"
                              onClick={() => {
                                setJobDescription(preset.jd);
                                setTopicDomain(preset.domain);
                                setExperienceLevel(preset.level);
                                setTargetInterviewRole(preset.role);
                              }}
                              className="px-2.5 py-1 bg-zinc-800/80 hover:bg-zinc-700 text-zinc-300 border border-zinc-700/60 rounded-lg text-[10px] font-semibold transition-colors cursor-pointer"
                            >
                              {preset.label}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Device & Behavior Checklist */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 p-4 bg-zinc-950/70 border border-zinc-800/80 rounded-2xl">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                              <Video className="w-4 h-4 text-indigo-400" />
                            </div>
                            <div>
                              <div className="text-xs font-bold text-white flex items-center gap-1.5">
                                <span>Camera & Facial Mirror</span>
                                {webcamEnabled && (
                                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                                )}
                              </div>
                              <div className="text-[10px] text-zinc-400">
                                {webcamEnabled ? 'Face mirror active · 1080p Stream' : 'Your face will be displayed mirrored during interview'}
                              </div>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={toggleWebcam}
                            className={`px-3 py-1 rounded-lg text-[10px] font-bold border transition-colors cursor-pointer ${webcamEnabled ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/20' : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:bg-zinc-700 hover:text-white'}`}
                          >
                            {webcamEnabled ? '● Camera ON' : 'Enable Camera'}
                          </button>
                        </div>

                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center">
                              <Mic className="w-4 h-4 text-violet-400" />
                            </div>
                            <div>
                              <div className="text-xs font-bold text-white">Voice & Speech Mode</div>
                              <div className="text-[10px] text-zinc-400">Audio Q&A + WPM tracker</div>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={() => setAudioOutputEnabled(!audioOutputEnabled)}
                            className={`px-3 py-1 rounded-lg text-[10px] font-bold border transition-colors cursor-pointer ${audioOutputEnabled ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400' : 'bg-zinc-800 border-zinc-700 text-zinc-400 hover:bg-zinc-700 hover:text-white'}`}
                          >
                            {audioOutputEnabled ? '🔊 Audio ON' : '🔇 Muted'}
                          </button>
                        </div>
                      </div>

                      {/* Start Interview Button */}
                      <button
                        type="button"
                        onClick={startInterview}
                        disabled={loading}
                        className="w-full py-3.5 bg-gradient-to-r from-indigo-600 via-indigo-500 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-bold rounded-2xl text-sm shadow-lg shadow-indigo-600/30 transition-all transform active:scale-[0.99] flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                      >
                        {loading ? (
                          <>
                            <Loader2 className="w-4 h-4 animate-spin" />
                            <span>Initializing Interview Session & Tailoring Questions...</span>
                          </>
                        ) : (
                          <>
                            <Play className="w-4 h-4 fill-white" />
                            <span>Enter Real-Time Interview Room</span>
                          </>
                        )}
                      </button>
                    </motion.div>
                  )}

                  {/* PHASE 2: LIVE REAL-TIME ONLINE VIDEO INTERVIEW ROOM */}
                  {interviewStarted && (() => {
                    const interviewerMessages = interviewMessages.filter(m => m.role === 'interviewer');
                    const candidateMessages = interviewMessages.filter(m => m.role === 'candidate');
                    const latestInterviewerMsg = interviewerMessages[interviewerMessages.length - 1];
                    const currentQuestion = latestInterviewerMsg?.text || 'Welcome to your interview.';
                    const currentRole = targetInterviewRole || interviewTrackLabel || userProfile?.target_roles?.[0] || 'Software Engineer';
                    const kindLabel: Record<string, string> = { intro: 'Introduction', deep_dive: 'Project deep-dive', tech: 'Technical', scenario: 'Scenario', behavioral: 'Behavioral', closing: 'Your questions', 'follow-up': 'Follow-up' };
                    const faceLabel = { off: 'Camera off', loading: 'Loading face analysis…', active: 'Face analysis on', 'no-face': 'Face not visible', unavailable: 'Face analysis unavailable' }[faceStatus];

                    return (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.99 }}
                        animate={{ opacity: 1, scale: 1 }}
                        className="space-y-4 relative"
                      >
                        {/* 1. TOP VIDEO CONFERENCE MEETING BAR (Google Meet / Zoom Style) */}
                        <div className="bg-zinc-900/90 backdrop-blur-md border border-zinc-800 rounded-2xl p-3 md:p-4 flex flex-wrap items-center justify-between gap-3 shadow-xl">
                          {/* Left: Meeting Status & Title */}
                          <div className="flex items-center gap-3">
                            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 text-[11px] font-bold">
                              <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                              </span>
                              <span>REC</span>
                            </div>

                            <div className="h-4 w-px bg-zinc-800" />

                            <div>
                              <div className="flex items-center gap-2 flex-wrap">
                                <h3 className="text-xs font-black text-white uppercase tracking-wider">
                                  {currentRole} · Mock Interview
                                </h3>
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-indigo-500/10 border border-indigo-500/20 text-indigo-300">
                                  {interviewType} Interview
                                </span>
                                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold border ${
                                  experienceLevel === 'Fresher'
                                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                                    : 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300'
                                }`}>
                                  {experienceLevel === 'Fresher' ? '🎓 Fresher Track · Academic Focus' : '💼 Experienced Track'}
                                </span>
                                <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 border border-amber-500/30 text-amber-300">
                                  {INTERVIEW_TRACKS.find(t => t.id === topicDomain)?.icon || '🎯'} {interviewTrackLabel || INTERVIEW_TRACKS.find(t => t.id === topicDomain)?.label || 'General'}
                                </span>
                              </div>
                              <div className="flex items-center gap-2 text-[10px] text-zinc-400 mt-1">
                                <span className="flex items-center gap-1">
                                  <Clock className="w-3 h-3 text-indigo-400" />
                                  <span className="font-mono">{formatDuration(callDuration)}</span>
                                </span>
                                <span>•</span>
                                <span className="text-zinc-300 font-medium">This question: <span className="font-mono">{formatDuration(questionElapsed)}</span></span>
                                <span>•</span>
                                <span className={faceStatus === 'active' ? 'text-emerald-400' : 'text-zinc-500'}>{faceLabel}</span>
                              </div>
                            </div>
                          </div>

                          {/* Center / Right: Turn Stage Indicator, Live Adaptive Difficulty & Scores */}
                          <div className="flex items-center gap-3 flex-wrap">
                            {/* Segmented Stage Indicator */}
                            <div className="hidden sm:flex flex-col gap-1 min-w-[190px]">
                              <div className="flex justify-between text-[10px]">
                                <span className="font-bold text-zinc-300">Question {questionNumber} of {totalQuestions}</span>
                                <span className="text-indigo-400 font-semibold truncate max-w-[130px]" title={interviewPhase}>
                                  {questionKind === 'follow-up' ? '↳ Follow-up' : (kindLabel[questionKind] || interviewPhase)}
                                </span>
                              </div>
                              <div className="flex gap-1 h-1.5 w-full">
                                {Array.from({ length: totalQuestions }, (_, i) => i + 1).map(step => (
                                  <div
                                    key={step}
                                    className={`flex-1 h-full rounded-full transition-all duration-500 ${
                                      step < questionNumber
                                        ? 'bg-emerald-500'
                                        : step === questionNumber
                                        ? 'bg-indigo-500 animate-pulse'
                                        : 'bg-zinc-800'
                                    }`}
                                  />
                                ))}
                              </div>
                              <div className="text-[10px] text-zinc-500 truncate" title={interviewPhase}>Topic: {interviewPhase}</div>
                            </div>

                            {/* Live Dynamic Adaptive Difficulty Pill */}
                            <div className="px-3 py-1 bg-zinc-950 border border-zinc-800 rounded-xl flex flex-col justify-center">
                              <div className="text-[9px] text-zinc-400 font-bold uppercase tracking-wider">AI Question Difficulty</div>
                              <div className="flex items-center gap-1.5 mt-0.5">
                                <span className={`w-2 h-2 rounded-full ${
                                  currentDifficulty === 'Easy' ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]' : currentDifficulty === 'Medium' ? 'bg-amber-400 shadow-[0_0_8px_rgba(251,191,36,0.8)]' : 'bg-red-400 shadow-[0_0_8px_rgba(248,113,113,0.8)]'
                                }`} />
                                <span className={`text-xs font-black ${
                                  currentDifficulty === 'Easy' ? 'text-emerald-400' : currentDifficulty === 'Medium' ? 'text-amber-400' : 'text-red-400'
                                }`}>
                                  {currentDifficulty === 'Easy' ? 'Foundational' : currentDifficulty === 'Medium' ? 'Intermediate' : 'Advanced'}
                                </span>
                                {difficultyChange === 'decreased' && (
                                  <span className="text-[9px] font-bold text-amber-400 animate-pulse bg-amber-500/15 px-1.5 py-0.5 rounded border border-amber-500/30">
                                    ↓ Adapted Down
                                  </span>
                                )}
                                {difficultyChange === 'increased' && (
                                  <span className="text-[9px] font-bold text-indigo-400 animate-pulse bg-indigo-500/15 px-1.5 py-0.5 rounded border border-indigo-500/30">
                                    ↑ Scaled Up
                                  </span>
                                )}
                              </div>
                            </div>

                            {/* Readiness & Confidence Telemetry Chips */}
                            <div className="flex items-center gap-2">
                              <div className="px-2.5 py-1 bg-zinc-950 border border-zinc-800 rounded-xl text-center">
                                <div className="text-[9px] text-zinc-400 font-bold uppercase tracking-wider">Live score</div>
                                <div className="text-xs font-black text-emerald-400 font-mono">{questionNumber > 1 && liveInterviewScore ? `${liveInterviewScore}%` : '—'}</div>
                              </div>
                              <div className="px-2.5 py-1 bg-zinc-950 border border-zinc-800 rounded-xl text-center">
                                <div className="text-[9px] text-zinc-400 font-bold uppercase tracking-wider">Confidence</div>
                                <div className="text-xs font-black text-indigo-400 font-mono">{liveConfidenceMetric ? `${liveConfidenceMetric}%` : '—'}</div>
                              </div>
                            </div>

                            {/* Leave Call Button */}
                            <button
                              type="button"
                              onClick={() => submitAnswerWithText('Thank you, I would like to conclude the interview.')}
                              className="px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-bold rounded-xl transition-all flex items-center gap-1.5 cursor-pointer"
                            >
                              <PhoneOff className="w-3.5 h-3.5" />
                              <span className="hidden md:inline">Leave Call</span>
                            </button>
                          </div>
                        </div>

                        {/* 2. DUAL-TILE VIDEO CONFERENCE STAGE */}
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                          {/* TILE 1: INTERVIEWER VIDEO FEED (Dr. Alex Vance) */}
                          <div
                            className={`relative rounded-3xl bg-gradient-to-b from-zinc-900 via-zinc-950 to-zinc-950 border overflow-hidden h-[360px] md:h-[420px] flex flex-col justify-between p-4 shadow-2xl transition-all ${
                              isAiSpeaking
                                ? 'border-emerald-500/70 ring-2 ring-emerald-500/40 shadow-[0_0_35px_rgba(16,185,129,0.2)]'
                                : 'border-zinc-800'
                            }`}
                          >
                            {/* Ambient Studio Lighting Backdrop */}
                            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_30%,_rgba(99,102,241,0.12),transparent_65%)] pointer-events-none" />

                            {/* Interviewer Tile Header */}
                            <div className="relative z-10 flex items-center justify-between">
                              <div className="flex items-center gap-2.5 bg-black/50 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/10">
                                <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                                <div>
                                  <div className="text-xs font-bold text-white flex items-center gap-1.5">
                                    <span>Alex</span>
                                    <span className="text-[10px] text-zinc-400 font-normal">· AI Interviewer</span>
                                  </div>
                                </div>
                              </div>

                              <div className="flex items-center gap-2">
                                {isAiSpeaking ? (
                                  <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/20 border border-emerald-500/30 text-emerald-300 text-[10px] font-bold animate-pulse">
                                    <span>Speaking</span>
                                  </div>
                                ) : (
                                  <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-zinc-800/80 border border-zinc-700/60 text-zinc-400 text-[10px] font-medium">
                                    <span>Listening</span>
                                  </div>
                                )}

                                <button
                                  type="button"
                                  onClick={() => speakInterviewerText(currentQuestion)}
                                  className="p-1.5 bg-zinc-800/80 hover:bg-zinc-700 text-indigo-400 hover:text-indigo-300 rounded-lg border border-zinc-700/60 transition-colors cursor-pointer"
                                  title="Replay Voice Question"
                                >
                                  <Volume2 className="w-3.5 h-3.5" />
                                </button>
                              </div>
                            </div>

                            {/* Interviewer Center Stage: Animated Persona Avatar with Speaking Waves */}
                            <div className="relative z-10 flex flex-col items-center justify-center my-auto">
                              <div className="relative flex items-center justify-center">
                                {/* Outer ripples when speaking */}
                                {isAiSpeaking && (
                                  <>
                                    <span className="absolute -inset-4 rounded-full bg-indigo-500/20 animate-ping opacity-60" />
                                    <span className="absolute -inset-8 rounded-full bg-violet-500/10 animate-pulse opacity-40" />
                                  </>
                                )}

                                {/* Main Avatar */}
                                <div
                                  className={`w-28 h-28 md:w-32 md:h-32 rounded-full bg-gradient-to-tr from-indigo-900 via-indigo-700 to-violet-600 border-2 flex items-center justify-center shadow-2xl transition-all duration-300 ${
                                    isAiSpeaking
                                      ? 'border-emerald-400 scale-105 shadow-indigo-500/40 ring-4 ring-emerald-500/30'
                                      : 'border-indigo-400/50'
                                  }`}
                                >
                                  <div className="text-center text-white space-y-1">
                                    <Sparkles className="w-9 h-9 mx-auto text-indigo-200 animate-pulse" />
                                    <span className="text-[10px] font-black uppercase tracking-wider text-indigo-100 block">AI INTERVIEWER</span>
                                  </div>
                                </div>
                              </div>

                              {/* Voice Wave Spectrum Equalizer */}
                              <div className="mt-4 flex items-center gap-1.5 h-6">
                                {[0.3, 0.9, 0.5, 1.0, 0.7, 0.95, 0.4, 0.8, 0.6].map((scale, idx) => (
                                  <motion.div
                                    key={idx}
                                    animate={
                                      isAiSpeaking
                                        ? { height: ['6px', `${22 * scale}px`, '6px'] }
                                        : { height: '6px' }
                                    }
                                    transition={{
                                      repeat: isAiSpeaking ? Infinity : 0,
                                      duration: 0.5 + idx * 0.08,
                                      ease: 'easeInOut'
                                    }}
                                    className={`w-1 rounded-full transition-colors ${
                                      isAiSpeaking ? 'bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.6)]' : 'bg-zinc-700'
                                    }`}
                                  />
                                ))}
                              </div>

                              <div className="mt-2 text-[11px] font-semibold text-zinc-400">
                                {isAiSpeaking ? 'Alex is speaking…' : loading ? 'Thinking about your answer…' : 'Listening. Take your time.'}
                              </div>
                            </div>

                            {/* Interviewer Tile Footer */}
                            <div className="relative z-10 flex items-center justify-between text-[11px] text-zinc-400 border-t border-zinc-800/80 pt-2.5">
                              <span className="flex items-center gap-1 text-[10px] text-zinc-400">
                                <Cpu className="w-3 h-3 text-indigo-400" />
                                Follow-ups adapt to your answers
                              </span>
                              <span className="text-[10px] font-mono text-zinc-500">
                                {currentDifficulty} level
                              </span>
                            </div>
                          </div>

                          {/* TILE 2: CANDIDATE VIDEO FEED (Your Camera + Mirrored Face + HUD Overlay) */}
                          <div
                            className={`relative rounded-3xl bg-zinc-950 border overflow-hidden h-[360px] md:h-[420px] flex flex-col justify-between p-4 shadow-2xl transition-all ${
                              isRecording
                                ? 'border-indigo-500/70 ring-2 ring-indigo-500/40 shadow-[0_0_35px_rgba(99,102,241,0.2)]'
                                : 'border-zinc-800'
                            }`}
                          >
                            {/* Webcam Video Stream & Canvas - Permanently mounted so ref and face stream are always active */}
                            <video
                              ref={webcamRef}
                              autoPlay
                              playsInline
                              muted
                              className={`absolute inset-0 w-full h-full object-cover scale-x-[-1] transition-opacity duration-300 ${
                                webcamEnabled ? 'opacity-100 z-0' : 'opacity-0 -z-10 pointer-events-none'
                              }`}
                            />
                            <canvas
                              ref={canvasRef}
                              className={`absolute inset-0 w-full h-full pointer-events-none transition-opacity duration-300 ${
                                webcamEnabled ? 'opacity-100 z-[1]' : 'opacity-0 -z-10'
                              }`}
                            />

                            {!webcamEnabled && (
                              <div className="absolute inset-0 z-0 flex flex-col items-center justify-center p-6 text-center bg-zinc-950 text-zinc-500">
                                <div className="w-16 h-16 rounded-2xl bg-zinc-900 border border-zinc-800 flex items-center justify-center mb-3">
                                  <VideoOff className="w-8 h-8 text-zinc-600" />
                                </div>
                                <div className="text-xs font-bold text-white mb-1">Camera Feed is Disabled</div>
                                <p className="text-[11px] text-zinc-400 max-w-xs mb-3">
                                  Enable camera to display your face with live eye-contact tracking, composure metrics, and biometric verification.
                                </p>
                                <button
                                  type="button"
                                  onClick={toggleWebcam}
                                  className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-xl transition-all shadow-md shadow-indigo-600/30 flex items-center gap-1.5 cursor-pointer"
                                >
                                  <Video className="w-3.5 h-3.5" />
                                  <span>Enable Camera</span>
                                </button>
                              </div>
                            )}

                            {/* Candidate Tile Top Header */}
                            <div className="relative z-10 flex items-center justify-between">
                              <div className="flex items-center gap-2 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/10">
                                <span className={`w-2 h-2 rounded-full ${webcamEnabled ? 'bg-emerald-400' : 'bg-amber-400'}`} />
                                <span className="text-xs font-bold text-white">
                                  {userProfile?.full_name || 'Candidate (You)'}
                                </span>
                              </div>

                              {/* Toggle Camera button right in tile */}
                              <div className="flex items-center gap-2">
                                <button
                                  type="button"
                                  onClick={toggleWebcam}
                                  className={`px-2.5 py-1 rounded-xl text-[10px] font-bold border transition-colors flex items-center gap-1 cursor-pointer bg-black/60 backdrop-blur-md ${
                                    webcamEnabled ? 'border-emerald-500/40 text-emerald-300 hover:bg-emerald-500/10' : 'border-zinc-700 text-zinc-400 hover:bg-zinc-800'
                                  }`}
                                  title={webcamEnabled ? 'Turn off camera' : 'Turn on camera'}
                                >
                                  {webcamEnabled ? <Video className="w-3 h-3 text-emerald-400" /> : <VideoOff className="w-3 h-3 text-zinc-400" />}
                                  <span>{webcamEnabled ? 'Camera ON' : 'Camera OFF'}</span>
                                </button>

                                {/* Candidate Biometric HUD Badges (Frosted glass overlay) */}
                                <div className="flex items-center gap-1.5 flex-wrap justify-end">
                                  <div className="bg-black/60 backdrop-blur-md border border-white/10 px-2.5 py-1 rounded-xl text-[10px] font-mono text-emerald-400 flex items-center gap-1">
                                    <span>👁️ Eye contact:</span>
                                    <span className="font-bold">{faceStatus === 'active' ? `${Math.round(telemetry.eye)}%` : '—'}</span>
                                  </div>
                                  <div className="bg-black/60 backdrop-blur-md border border-white/10 px-2.5 py-1 rounded-xl text-[10px] font-mono text-indigo-400 flex items-center gap-1">
                                    <span>🧠 Composure:</span>
                                    <span className="font-bold">{faceStatus === 'active' ? `${Math.round(100 - telemetry.stress)}%` : '—'}</span>
                                  </div>
                                  <div className="bg-black/60 backdrop-blur-md border border-white/10 px-2.5 py-1 rounded-xl text-[10px] font-mono text-amber-400 flex items-center gap-1">
                                    <span>⚡ {speechWpm} WPM</span>
                                  </div>
                                </div>
                              </div>
                            </div>

                            {/* Candidate Tile Footer */}
                            <div className="relative z-10 flex items-center justify-between border-t border-white/10 pt-2.5 bg-black/40 backdrop-blur-md -mx-4 -mb-4 p-4">
                              <div className="flex items-center gap-2">
                                <span
                                  className={`px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center gap-1 ${
                                    isRecording
                                      ? 'bg-red-500/20 text-red-300 border border-red-500/30 animate-pulse'
                                      : 'bg-zinc-800 text-zinc-400 border border-zinc-700'
                                  }`}
                                >
                                  {isRecording ? <Mic className="w-3 h-3 text-red-400" /> : <MicOff className="w-3 h-3 text-zinc-500" />}
                                  <span>{isRecording ? 'Mic Live (Speaking)' : 'Mic Muted'}</span>
                                </span>

                                {/* Live volume equalizer bars responding to audioLevel */}
                                {isRecording && (
                                  <div className="flex items-center gap-1 h-4">
                                    {[0.3, 0.8, 0.5, 1.0, 0.6, 0.9].map((scale, i) => (
                                      <div
                                        key={i}
                                        className="w-1 bg-red-400 rounded-full transition-all duration-75"
                                        style={{ height: `${Math.max(3, (audioLevel / 100) * 16 * scale)}px` }}
                                      />
                                    ))}
                                  </div>
                                )}
                              </div>

                              <span className="text-[10px] text-zinc-400 font-mono">
                                {faceLabel}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* 3. LIVE FLOATING CLOSED CAPTIONS (Subtitles Overlay - Google Meet / Zoom CC) */}
                        {subtitlesEnabled && (
                          <motion.div
                            initial={{ opacity: 0, y: 8 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="bg-zinc-950/90 backdrop-blur-md border border-zinc-700/60 p-3.5 md:p-4 rounded-2xl shadow-2xl max-w-4xl mx-auto"
                          >
                            <div className="flex items-start gap-3">
                              <div className="p-2 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 mt-0.5">
                                <Subtitles className="w-4 h-4" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between mb-1">
                                  <div className="text-[11px] font-bold tracking-wider flex items-center gap-1.5">
                                    {isRecording ? (
                                      <span className="text-red-400 flex items-center gap-1">
                                        <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                                        You (Speaking Real-Time):
                                      </span>
                                    ) : isAiSpeaking ? (
                                      <span className="text-emerald-400 flex items-center gap-1">
                                        <Sparkles className="w-3 h-3 text-emerald-400 animate-spin" />
                                        Alex (asking):
                                      </span>
                                    ) : (
                                      <span className="text-zinc-300">
                                        Alex (current question):
                                      </span>
                                    )}
                                  </div>
                                  <button
                                    type="button"
                                    onClick={() => setSubtitlesEnabled(false)}
                                    className="text-zinc-500 hover:text-zinc-300 text-[10px] cursor-pointer"
                                  >
                                    Hide CC
                                  </button>
                                </div>

                                <p className="text-xs md:text-sm text-zinc-100 font-normal leading-relaxed">
                                  {isRecording
                                    ? candidateResponse || 'Listening to your voice... Speak your answer now.'
                                    : currentQuestion}
                                </p>
                              </div>
                            </div>
                          </motion.div>
                        )}

                        {/* 4. IN-CALL CANDIDATE RESPONSE INPUT */}
                        <div className="bg-zinc-900/90 backdrop-blur-md border border-zinc-800 rounded-2xl p-4 shadow-xl space-y-3">
                          {/* Recording status banner if voice is active */}
                          {isRecording && (
                            <motion.div
                              initial={{ opacity: 0, height: 0 }}
                              animate={{ opacity: 1, height: 'auto' }}
                              className="p-3 bg-red-950/40 border border-red-500/40 rounded-xl flex items-center justify-between gap-3 text-xs"
                            >
                              <div className="flex items-center gap-2 text-red-300 font-bold">
                                <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
                                <span>Voice Input Live</span>
                                <span className="font-mono text-[10px] text-red-400">({speechWpm} WPM · Silence detector auto-submits in 4s)</span>
                              </div>
                              <button
                                type="button"
                                onClick={stopVoiceRecording}
                                className="px-2.5 py-1 bg-red-600 hover:bg-red-500 text-white rounded-lg text-[10px] font-bold cursor-pointer"
                              >
                                Stop Recording
                              </button>
                            </motion.div>
                          )}

                          {/* Interview etiquette helpers (handled by the interviewer like in a real interview) */}
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-[10px] text-zinc-500 font-bold uppercase tracking-wider">Quick replies:</span>
                            {[
                              { label: '🔁 Repeat the question', text: 'Could you repeat the question?' },
                              { label: '💡 Clarify / hint', text: 'Could you clarify what you mean? A hint would help.' },
                              { label: '⏭️ Skip this one', text: "I don't know this one." },
                            ].map(q => (
                              <button key={q.label} type="button" disabled={loading} onClick={() => submitAnswerWithText(q.text)}
                                className="px-2.5 py-1 rounded-lg text-[10px] font-semibold border border-zinc-700 text-zinc-300 hover:bg-zinc-800 disabled:opacity-40 cursor-pointer">
                                {q.label}
                              </button>
                            ))}
                            <span className="ml-auto text-[10px] text-zinc-500">Tip: think aloud and use examples from your projects.</span>
                          </div>

                          {/* Candidate Answer Bar */}
                          <div className="flex gap-2 items-center">
                            <div className="relative flex-1">
                              <input
                                value={candidateResponse}
                                onChange={e => setCandidateResponse(e.target.value)}
                                onKeyDown={e => e.key === 'Enter' && !e.shiftKey && submitAnswer()}
                                placeholder={isRecording ? 'Listening to speech... (or type your technical answer here)' : 'Speak your answer using the microphone, or type here... (Press Enter to submit)'}
                                className="w-full bg-zinc-950 border border-zinc-800 focus:border-indigo-500 rounded-xl pl-4 pr-10 py-3 text-xs text-white placeholder-zinc-500 focus:outline-none transition-colors"
                              />
                              {candidateResponse && (
                                <button
                                  type="button"
                                  onClick={() => setCandidateResponse('')}
                                  className="absolute right-3 top-1/2 -translate-y-1/2 text-zinc-500 hover:text-zinc-300 cursor-pointer"
                                >
                                  <X className="w-3.5 h-3.5" />
                                </button>
                              )}
                            </div>

                            {/* Mic Toggle Button */}
                            <button
                              type="button"
                              onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
                              className={`px-4 py-3 rounded-xl font-bold text-xs flex items-center gap-2 border transition-all cursor-pointer ${
                                isRecording
                                  ? 'bg-red-600 hover:bg-red-500 text-white border-red-500 shadow-lg shadow-red-600/30 animate-pulse'
                                  : 'bg-zinc-800 hover:bg-zinc-700 text-indigo-400 border-zinc-700'
                              }`}
                            >
                              <Mic className="w-4 h-4" />
                              <span className="hidden sm:inline">{isRecording ? 'Stop & Submit' : 'Speak (Voice In)'}</span>
                            </button>

                            {/* Submit Button */}
                            <button
                              type="button"
                              onClick={submitAnswer}
                              disabled={loading || !candidateResponse.trim()}
                              className="px-4 py-3 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl disabled:opacity-40 transition-all cursor-pointer flex items-center gap-1.5 text-xs font-bold shadow-lg shadow-indigo-600/30"
                            >
                              {loading ? (
                                <Loader2 className="w-4 h-4 animate-spin" />
                              ) : (
                                <>
                                  <Send className="w-4 h-4" />
                                  <span className="hidden sm:inline">Submit Answer</span>
                                </>
                              )}
                            </button>
                          </div>
                        </div>

                        {/* 5. FLOATING IN-CALL MEETING DOCK (Google Meet / Zoom Toolbar) */}
                        <div className="bg-zinc-950/90 backdrop-blur-md border border-zinc-800 rounded-2xl p-2.5 flex items-center justify-center gap-2 sm:gap-4 shadow-2xl max-w-2xl mx-auto">
                          {/* Mic Button */}
                          <button
                            type="button"
                            onClick={isRecording ? stopVoiceRecording : startVoiceRecording}
                            className={`p-3 rounded-xl border text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                              isRecording
                                ? 'bg-red-600 text-white border-red-500 shadow-lg shadow-red-600/30'
                                : 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-zinc-800'
                            }`}
                            title={isRecording ? 'Mute Microphone' : 'Unmute Microphone'}
                          >
                            {isRecording ? <Mic className="w-4 h-4" /> : <MicOff className="w-4 h-4 text-zinc-500" />}
                            <span className="hidden md:inline text-[11px]">{isRecording ? 'Mic Live' : 'Mute'}</span>
                          </button>

                          {/* Camera Button */}
                          <button
                            type="button"
                            onClick={toggleWebcam}
                            className={`p-3 rounded-xl border text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                              webcamEnabled
                                ? 'bg-zinc-900 border-zinc-800 text-emerald-400 hover:bg-zinc-800'
                                : 'bg-red-500/10 border-red-500/30 text-red-400'
                            }`}
                            title={webcamEnabled ? 'Turn Off Camera' : 'Turn On Camera'}
                          >
                            {webcamEnabled ? <Video className="w-4 h-4" /> : <VideoOff className="w-4 h-4" />}
                            <span className="hidden md:inline text-[11px]">{webcamEnabled ? 'Camera On' : 'Camera Off'}</span>
                          </button>

                          {/* Captions Toggle */}
                          <button
                            type="button"
                            onClick={() => setSubtitlesEnabled(!subtitlesEnabled)}
                            className={`p-3 rounded-xl border text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                              subtitlesEnabled
                                ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300'
                                : 'bg-zinc-900 border-zinc-800 text-zinc-500 hover:bg-zinc-800'
                            }`}
                            title="Toggle Subtitles"
                          >
                            <Subtitles className="w-4 h-4" />
                            <span className="hidden md:inline text-[11px]">CC</span>
                          </button>

                          {/* Speaker Audio Mode */}
                          <button
                            type="button"
                            onClick={() => setAudioOutputEnabled(!audioOutputEnabled)}
                            className={`p-3 rounded-xl border text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                              audioOutputEnabled
                                ? 'bg-indigo-500/10 border-indigo-500/30 text-indigo-300'
                                : 'bg-zinc-900 border-zinc-800 text-zinc-500 hover:bg-zinc-800'
                            }`}
                            title="Toggle AI Spoken Voice"
                          >
                            {audioOutputEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
                            <span className="hidden md:inline text-[11px]">{audioOutputEnabled ? 'Voice Mode' : 'Muted'}</span>
                          </button>

                          {/* Meeting Chat / Transcript Drawer Toggle */}
                          <button
                            type="button"
                            onClick={() => setMeetingDrawerOpen(!meetingDrawerOpen)}
                            className={`p-3 rounded-xl border text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                              meetingDrawerOpen
                                ? 'bg-indigo-600 text-white border-indigo-500 shadow-md shadow-indigo-600/30'
                                : 'bg-zinc-900 border-zinc-800 text-zinc-300 hover:bg-zinc-800'
                            }`}
                            title="View Meeting Notes & Transcript"
                          >
                            <MessageSquare className="w-4 h-4" />
                            <span className="hidden md:inline text-[11px]">Transcript & AI Notes</span>
                            {interviewMessages.length > 1 && (
                              <span className="px-1.5 py-0.2 rounded-full bg-indigo-500/30 text-indigo-300 text-[9px] font-mono">
                                {interviewMessages.length}
                              </span>
                            )}
                          </button>

                          {/* Leave Call */}
                          <button
                            type="button"
                            onClick={() => submitAnswerWithText('Thank you, I would like to conclude the interview.')}
                            className="p-3 bg-red-600 hover:bg-red-500 text-white rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all shadow-md shadow-red-600/30 cursor-pointer"
                            title="End Interview"
                          >
                            <PhoneOff className="w-4 h-4" />
                            <span className="hidden sm:inline text-[11px]">End Call</span>
                          </button>
                        </div>

                        {/* 6. SLIDE-OVER IN-CALL MEETING DRAWER (Transcript & Immediate AI Feedback) */}
                        <AnimatePresence>
                          {meetingDrawerOpen && (
                            <motion.div
                              initial={{ opacity: 0, x: 20 }}
                              animate={{ opacity: 1, x: 0 }}
                              exit={{ opacity: 0, x: 20 }}
                              className="bg-zinc-900/95 backdrop-blur-md border border-zinc-800 rounded-3xl p-5 shadow-2xl space-y-4 max-h-[500px] overflow-y-auto"
                            >
                              <div className="flex items-center justify-between border-b border-zinc-800 pb-3">
                                <div className="flex items-center gap-2">
                                  <MessageSquare className="w-4 h-4 text-indigo-400" />
                                  <h4 className="text-xs font-black text-white uppercase tracking-wider">
                                    Meeting Transcript & Real-Time AI Diagnostics
                                  </h4>
                                </div>
                                <button
                                  type="button"
                                  onClick={() => setMeetingDrawerOpen(false)}
                                  className="text-zinc-500 hover:text-zinc-300 cursor-pointer"
                                >
                                  <X className="w-4 h-4" />
                                </button>
                              </div>

                              {/* Turn-by-turn items */}
                              <div className="space-y-4">
                                {interviewMessages.map((m, idx) => (
                                  <div key={idx} className="space-y-2">
                                    <div
                                      className={`p-3.5 rounded-2xl text-xs leading-relaxed ${
                                        m.role === 'interviewer'
                                          ? 'bg-zinc-950 border border-zinc-800 text-zinc-200'
                                          : 'bg-indigo-950/40 border border-indigo-500/30 text-indigo-100'
                                      }`}
                                    >
                                      <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-wider mb-1.5 opacity-80 border-b border-white/5 pb-1">
                                        <span>{m.role === 'interviewer' ? '🤖 Alex (Interviewer)' : `👤 ${userProfile?.full_name || 'Candidate'}`}</span>
                                        {m.role === 'interviewer' && (
                                          <button
                                            type="button"
                                            onClick={() => speakInterviewerText(m.text)}
                                            className="text-indigo-400 hover:text-indigo-300 flex items-center gap-1 cursor-pointer normal-case"
                                          >
                                            <Volume2 className="w-3 h-3" /> Replay Voice
                                          </button>
                                        )}
                                      </div>
                                      <div>{m.text}</div>
                                    </div>

                                    {/* Turn Immediate Evaluation Card if present */}
                                    {m.role === 'interviewer' && !m.is_first && (m.ai_correction || m.ai_immediate_feedback) && (
                                      <div
                                        className={`p-3 rounded-xl border text-xs ${
                                          m.is_correct === false || m.ai_correction
                                            ? 'bg-amber-950/30 border-amber-500/30 text-amber-200'
                                            : 'bg-emerald-950/30 border-emerald-500/30 text-emerald-200'
                                        }`}
                                      >
                                        <div className="flex items-center gap-1.5 font-bold text-[11px] mb-1">
                                          {m.is_correct === false || m.ai_correction ? (
                                            <>
                                              <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
                                              <span>Identified Technical Gap & Feedback</span>
                                            </>
                                          ) : (
                                            <>
                                              <CheckCircle className="w-3.5 h-3.5 text-emerald-400" />
                                              <span>Answer Approved · Solid Technical Breakdown</span>
                                            </>
                                          )}
                                        </div>

                                        {m.ai_immediate_feedback && (
                                          <p className="text-zinc-300 mb-1">{m.ai_immediate_feedback}</p>
                                        )}

                                        {m.ai_correction && (
                                          <div className="p-2 bg-black/40 rounded-lg space-y-1 mt-1 text-[11px]">
                                            <div className="font-bold text-amber-300 uppercase tracking-wider text-[10px]">What was missing:</div>
                                            <div className="text-zinc-300">{m.ai_correction}</div>
                                            {m.ideal_answer && (
                                              <div className="pt-1 border-t border-zinc-800">
                                                <div className="font-bold text-emerald-300 uppercase tracking-wider text-[10px]">💡 Ideal Staff Engineer Answer:</div>
                                                <div className="text-zinc-300 italic">{m.ideal_answer}</div>
                                              </div>
                                            )}
                                          </div>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </motion.div>
                    );
                  })()}

                  {/* PHASE 3: COMPREHENSIVE POST-INTERVIEW SCORECARD */}
                  {interviewFeedback && (
                    <motion.div
                      initial={{ opacity: 0, y: 15 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="max-w-4xl mx-auto space-y-6"
                    >
                      {/* Top Overall Result Hero */}
                      <div className="bg-gradient-to-r from-zinc-900 via-zinc-900 to-indigo-950/40 border border-zinc-800 rounded-3xl p-7 shadow-2xl flex flex-wrap items-center justify-between gap-5">
                        <div className="space-y-1.5">
                          <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 rounded-full text-xs font-bold uppercase tracking-wider">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Interview Completed
                          </div>
                          <h2 className="text-2xl font-black text-white tracking-tight">
                            AI Placement Interview Scorecard
                          </h2>
                          <p className="text-zinc-400 text-xs">
                            Candidate Evaluation for <strong className="text-white">{interviewFeedback.target_role}</strong> · {interviewFeedback.interview_type}
                          </p>
                        </div>

                        {/* Big Score Gauge */}
                        <div className="flex items-center gap-4 bg-zinc-950 border border-zinc-800 p-4 rounded-2xl">
                          <div className="text-right">
                            <div className="text-[10px] font-bold uppercase tracking-wider text-zinc-400">Readiness Score</div>
                            <div className={`text-xs font-bold ${interviewFeedback.overall_score >= 75 ? 'text-emerald-400' : interviewFeedback.overall_score >= 55 ? 'text-amber-400' : 'text-red-400'}`}>
                              {interviewFeedback.overall_score >= 75 ? 'Interview ready' : interviewFeedback.overall_score >= 55 ? 'Getting there' : 'Needs more practice'}
                            </div>
                          </div>
                          <div className="text-4xl font-black text-indigo-400 font-mono">
                            {interviewFeedback.overall_score}<span className="text-zinc-600 text-lg">/100</span>
                          </div>
                        </div>
                      </div>

                      {/* 5 Core Competency Metric Cards */}
                      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                        {[
                          { label: 'Technical Depth', score: interviewFeedback.technical_score, color: 'text-indigo-400', icon: Code2 },
                          { label: 'Communication', score: interviewFeedback.communication_score, color: 'text-violet-400', icon: MessageSquare },
                          { label: 'Confidence & Poise', score: interviewFeedback.confidence_score, color: 'text-emerald-400', icon: Target },
                          { label: 'Problem Solving', score: interviewFeedback.problem_solving_score, color: 'text-cyan-400', icon: Cpu },
                          { label: 'Leadership & STAR', score: interviewFeedback.leadership_score, color: 'text-amber-400', icon: Award },
                        ].map(c => {
                          const IconComponent = c.icon;
                          return (
                            <div key={c.label} className="bg-zinc-900/80 border border-zinc-800 rounded-2xl p-4 text-center shadow-lg">
                              <IconComponent className={`w-5 h-5 mx-auto mb-1.5 ${c.color}`} />
                              <div className="text-[10px] text-zinc-400 font-bold uppercase truncate">{c.label}</div>
                              <div className="text-xl font-black text-white mt-1 font-mono">{c.score}/100</div>
                            </div>
                          );
                        })}
                      </div>

                      {/* Detailed Feedback Sections */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Strengths */}
                        <div className="bg-zinc-900/90 border border-zinc-800 rounded-3xl p-5 shadow-xl space-y-3">
                          <div className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center gap-2">
                            <CheckCircle className="w-4 h-4" /> Demonstrated Strengths
                          </div>
                          <div className="space-y-2">
                            {(interviewFeedback.feedback?.strengths || []).map((s: string, idx: number) => (
                              <div key={idx} className="text-xs text-zinc-300 bg-zinc-950/70 border border-zinc-800/80 p-2.5 rounded-xl flex items-start gap-2">
                                <span className="text-emerald-400 font-bold">•</span>
                                <span>{s}</span>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Critical Corrections & Mistakes */}
                        <div className="bg-zinc-900/90 border border-zinc-800 rounded-3xl p-5 shadow-xl space-y-3">
                          <div className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center gap-2">
                            <AlertCircle className="w-4 h-4" /> Areas for Technical Improvement
                          </div>
                          <div className="space-y-2">
                            {([...(interviewFeedback.feedback?.weaknesses || []), ...(interviewFeedback.feedback?.suggestions || [])]).map((m: string, idx: number) => (
                              <div key={idx} className="text-xs text-zinc-300 bg-zinc-950/70 border border-zinc-800/80 p-2.5 rounded-xl flex items-start gap-2">
                                <span className="text-amber-400 font-bold">⚠️</span>
                                <span>{m}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Actionable 7-Day Study Plan */}
                      <div className="bg-zinc-900/90 border border-zinc-800 rounded-3xl p-5 shadow-xl space-y-3">
                        <div className="text-xs font-bold uppercase tracking-wider text-indigo-400 flex items-center gap-2">
                          <Compass className="w-4 h-4" /> 7-Day Custom Action Plan
                        </div>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                          {(interviewFeedback.feedback?.practice_plan || []).map((plan: string, idx: number) => (
                            <div key={idx} className="p-3 bg-zinc-950 border border-zinc-800 rounded-2xl">
                              <div className="text-[10px] font-bold text-indigo-400 uppercase">Milestone {idx + 1}</div>
                              <div className="text-xs text-zinc-200 mt-1 font-medium">{plan}</div>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Question-by-question review */}
                      {Array.isArray(interviewFeedback.feedback?.turns) && interviewFeedback.feedback.turns.length > 0 && (
                        <div className="bg-zinc-900/90 border border-zinc-800 rounded-3xl p-5 shadow-xl space-y-3">
                          <div className="text-xs font-bold uppercase tracking-wider text-violet-400 flex items-center gap-2">
                            <MessageSquare className="w-4 h-4" /> Question-by-question review
                          </div>
                          {interviewFeedback.feedback.turns.map((t: any, idx: number) => {
                            const ideal = (interviewFeedback.feedback?.ideal_answers || []).find((i: any) => i.question === t.question);
                            return (
                              <details key={idx} className="group bg-zinc-950/70 border border-zinc-800 rounded-2xl p-3">
                                <summary className="flex items-center justify-between gap-3 cursor-pointer list-none">
                                  <span className="text-xs text-zinc-200 font-semibold min-w-0">
                                    <span className="text-zinc-500 mr-1">{t.is_followup ? '↳' : `${idx + 1}.`}</span>{t.topic}: <span className="font-normal text-zinc-400">{t.question.length > 90 ? t.question.slice(0, 90) + '…' : t.question}</span>
                                  </span>
                                  <span className={`text-xs font-black font-mono flex-shrink-0 ${t.score >= 72 ? 'text-emerald-400' : t.score >= 45 ? 'text-amber-400' : 'text-red-400'}`}>{t.score}</span>
                                </summary>
                                <div className="mt-2 space-y-2 text-[11px]">
                                  <div className="text-zinc-400"><span className="font-bold text-zinc-300">Your answer:</span> {t.answer}</div>
                                  {t.covered?.length > 0 && <div className="text-emerald-300">✓ Covered: {t.covered.join(', ')}</div>}
                                  {t.missing?.length > 0 && <div className="text-amber-300">✗ Missed: {t.missing.join(', ')}</div>}
                                  {ideal && <div className="text-zinc-300 bg-zinc-900 border border-zinc-800 rounded-xl p-2"><span className="font-bold text-indigo-300">Model answer:</span> {ideal.ideal_answer}</div>}
                                </div>
                              </details>
                            );
                          })}
                        </div>
                      )}

                      {/* Body language (only when face analysis ran) */}
                      {interviewFeedback.behavior_scores?.aggregate?.has_face_data && (
                        <div className="bg-zinc-900/90 border border-zinc-800 rounded-3xl p-5 shadow-xl space-y-3">
                          <div className="text-xs font-bold uppercase tracking-wider text-sky-400 flex items-center gap-2">
                            <Video className="w-4 h-4" /> Body language ({interviewFeedback.behavior_scores.aggregate.overall_behavior_rating})
                          </div>
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            {[['Eye contact', 'avg_eye_contact'], ['Attention', 'avg_attention'], ['Smile', 'avg_smile'], ['Composure', 'avg_stress']].map(([label, key]) => (
                              <div key={key} className="p-3 bg-zinc-950 border border-zinc-800 rounded-2xl text-center">
                                <div className="text-[10px] text-zinc-400 font-bold uppercase">{label}</div>
                                <div className="text-lg font-black text-white font-mono">{Math.round(key === 'avg_stress' ? 100 - interviewFeedback.behavior_scores.aggregate[key] : interviewFeedback.behavior_scores.aggregate[key])}%</div>
                              </div>
                            ))}
                          </div>
                          <p className="text-xs text-zinc-300">{interviewFeedback.behavior_scores.aggregate.body_language_feedback}</p>
                          <p className="text-[10px] text-zinc-500">{interviewFeedback.behavior_scores.aggregate.disclaimer}</p>
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex items-center gap-3">
                        <button
                          type="button"
                          onClick={() => {
                            setInterviewFeedback(null);
                            setInterviewId(null);
                            setInterviewMessages([]);
                            setCurrentTurnCorrection(null);
                          }}
                          className="flex-1 py-3 bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold rounded-2xl shadow-lg transition-colors cursor-pointer"
                        >
                          Start Another Mock Interview
                        </button>
                        <button
                          type="button"
                          onClick={() => setSidebarTab('overview')}
                          className="px-6 py-3 border border-zinc-700 hover:bg-zinc-800 text-xs font-bold text-zinc-300 rounded-2xl transition-colors cursor-pointer"
                        >
                          Return to Dashboard
                        </button>
                      </div>
                    </motion.div>
                  )}
                </div>
              )}

              {/* ── MENTOR ── */}
              {sidebarTab === 'mentor' && (
                <div className="max-w-3xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
                  <div className="flex-1 bg-zinc-900 border border-zinc-800 rounded-2xl flex flex-col overflow-hidden min-h-0">
                    <div className="px-5 py-4 border-b border-zinc-800 flex items-center justify-between flex-shrink-0">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-indigo-500/10 border border-indigo-500/20 rounded-xl flex items-center justify-center">
                          <MessageSquare className="w-4 h-4 text-indigo-400" />
                        </div>
                        <div>
                          <div className="text-sm font-bold flex items-center gap-2">
                            <span>GapX AI Career Coach</span>
                            <span className="text-[10px] bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 font-semibold px-2 py-0.5 rounded-full">
                              v2.0 Dynamic Engine
                            </span>
                          </div>
                          <div className="text-[10px] text-green-400 flex items-center gap-1.5 mt-0.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse"></span>
                            <span>Online · Ready for Coding, Concepts &amp; Career Guidance</span>
                          </div>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setMentorMessages([
                            { role: 'assistant', text: '👋 Hello! I am your GapX AI Career Coach. Ask me anything about placement preparation, coding algorithms (e.g. *Solve Two Sum*), system design concepts, resume optimization, or interview questions!' }
                          ]);
                          setMentorSuggestions(['Solve Two Sum in Python', 'How to prepare for FAANG?', 'Explain OOP concepts with code']);
                        }}
                        className="text-[11px] text-zinc-400 hover:text-white px-2.5 py-1 rounded-lg border border-zinc-800 hover:bg-zinc-800 transition-colors flex items-center gap-1.5 cursor-pointer"
                        title="Clear conversation"
                      >
                        <RefreshCw className="w-3 h-3" />
                        <span>Reset Chat</span>
                      </button>
                    </div>

                    {/* Messages Container */}
                    <div className="flex-1 overflow-y-auto p-5 space-y-4 min-h-0">
                      {mentorMessages.map((m, i) => (
                        <div key={i} className={`flex ${m.role === 'assistant' ? 'justify-start' : 'justify-end'}`}>
                          <div className={`p-4 rounded-2xl max-w-2xl text-xs leading-relaxed ${
                            m.role === 'assistant' 
                              ? 'bg-zinc-850 bg-zinc-900/90 border border-zinc-800 rounded-tl-none shadow-md' 
                              : 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white rounded-tr-none shadow-lg'
                          }`}>
                            <div className="text-[9px] font-bold uppercase tracking-wide opacity-70 mb-1.5 flex items-center gap-1.5">
                              {m.role === 'assistant' ? (
                                <>
                                  <Sparkles className="w-3 h-3 text-indigo-400" />
                                  <span>🤖 GapX AI Coach</span>
                                </>
                              ) : (
                                <>
                                  <User className="w-3 h-3" />
                                  <span>👤 You</span>
                                </>
                              )}
                            </div>
                            {m.role === 'assistant' ? (
                              <MarkdownChatBubble text={m.text} />
                            ) : (
                              <p className="whitespace-pre-wrap">{m.text}</p>
                            )}
                          </div>
                        </div>
                      ))}

                      {/* Loading state */}
                      {mentorLoading && (
                        <div className="flex justify-start">
                          <div className="p-4 rounded-2xl max-w-md bg-zinc-900 border border-zinc-800 rounded-tl-none flex items-center gap-2.5 text-xs text-zinc-400">
                            <Loader2 className="w-4 h-4 text-indigo-400 animate-spin flex-shrink-0" />
                            <span>AI Coach is analyzing and generating solution...</span>
                          </div>
                        </div>
                      )}
                      <div ref={mentorMessagesEndRef} />
                    </div>

                    {/* Suggestions & Input Box */}
                    <div className="p-4 border-t border-zinc-800 space-y-3 flex-shrink-0 bg-zinc-900/60">
                      <div className="flex flex-wrap gap-1.5">
                        {mentorSuggestions.map((s, i) => (
                          <button
                            key={i}
                            type="button"
                            onClick={() => sendMentor(s)}
                            disabled={mentorLoading}
                            className="bg-zinc-800/90 hover:bg-indigo-600/20 hover:border-indigo-500/40 border border-zinc-700/80 text-zinc-300 hover:text-indigo-200 px-3 py-1 rounded-full text-[10px] font-semibold transition-all cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
                          >
                            <Sparkles className="w-2.5 h-2.5 text-indigo-400" />
                            <span>{s}</span>
                          </button>
                        ))}
                      </div>
                      <div className="flex gap-3">
                        <input
                          value={mentorQuery}
                          onChange={e => setMentorQuery(e.target.value)}
                          onKeyDown={e => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                              e.preventDefault();
                              sendMentor();
                            }
                          }}
                          placeholder="Ask about coding problems, career roadmaps, interview answers..."
                          disabled={mentorLoading}
                          className="flex-1 bg-zinc-800 border border-zinc-700 rounded-xl px-4 py-2.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-indigo-500 transition-colors disabled:opacity-50"
                        />
                        <button
                          type="button"
                          onClick={() => sendMentor()}
                          disabled={!mentorQuery.trim() || mentorLoading}
                          className="p-2.5 bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white rounded-xl disabled:opacity-40 transition-all cursor-pointer flex items-center justify-center min-w-[42px]"
                        >
                          {mentorLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* ── ADMIN ── */}
              {sidebarTab === 'admin' && (
                <div className="space-y-5 max-w-2xl">
                  <div className="p-4 bg-amber-500/10 border border-amber-500/20 text-amber-400 rounded-xl text-xs font-semibold flex items-center gap-3">
                    <ShieldAlert className="w-5 h-5 flex-shrink-0" />
                    Admin Panel — Use email starting with "admin" to access this panel.
                  </div>
                  <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-5">
                    <div className="text-xs font-bold uppercase tracking-wider mb-4">Add New Coding Problem</div>
                    <form onSubmit={createProblem} className="space-y-3 text-xs">
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-zinc-400 block mb-1">Title</label>
                          <input value={newProblem.title} onChange={e => setNewProblem({ ...newProblem, title: e.target.value })} required
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg p-2 text-white focus:outline-none" />
                        </div>
                        <div>
                          <label className="text-zinc-400 block mb-1">Category</label>
                          <input value={newProblem.category} onChange={e => setNewProblem({ ...newProblem, category: e.target.value })} required
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg p-2 text-white focus:outline-none" />
                        </div>
                      </div>
                      <div>
                        <label className="text-zinc-400 block mb-1">Difficulty</label>
                        <select value={newProblem.difficulty} onChange={e => setNewProblem({ ...newProblem, difficulty: e.target.value })}
                          className="w-full bg-zinc-800 border border-zinc-700 rounded-lg p-2 text-white focus:outline-none">
                          <option>Easy</option><option>Medium</option><option>Hard</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-zinc-400 block mb-1">Problem Statement</label>
                        <textarea value={newProblem.problem_statement} onChange={e => setNewProblem({ ...newProblem, problem_statement: e.target.value })} required
                          className="w-full bg-zinc-800 border border-zinc-700 rounded-lg p-2 text-white h-20 resize-none focus:outline-none" />
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="text-zinc-400 block mb-1">Example Input</label>
                          <input value={newProblem.example_input} onChange={e => setNewProblem({ ...newProblem, example_input: e.target.value })} required
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg p-2 text-white focus:outline-none" />
                        </div>
                        <div>
                          <label className="text-zinc-400 block mb-1">Example Output</label>
                          <input value={newProblem.example_output} onChange={e => setNewProblem({ ...newProblem, example_output: e.target.value })} required
                            className="w-full bg-zinc-800 border border-zinc-700 rounded-lg p-2 text-white focus:outline-none" />
                        </div>
                      </div>
                      <button type="submit" disabled={loading} className="w-full py-2 bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-bold rounded-xl">
                        {loading ? 'Adding...' : 'Add Problem to Database'}
                      </button>
                    </form>
                  </div>
                </div>
              )}

              {/* ── PROFILE / SETTINGS ── */}
              {sidebarTab === 'profile' && (
                <div className="max-w-xl space-y-5">
                  <div className="bg-zinc-900 border border-zinc-800 rounded-2xl p-6 space-y-5">
                    <h3 className="text-base font-bold border-b border-zinc-800 pb-3">Profile & Settings</h3>
                    <div className="grid grid-cols-2 gap-4 text-xs">
                      {[
                        ['Name', userProfile?.full_name || '-'],
                        ['Email', userProfile?.email || '-'],
                        ['Role', userProfile?.role || '-'],
                        ['Experience', userProfile?.experience_level || '-'],
                        ['XP', `${userProfile?.xp || 0} XP`],
                        ['Level', `Level ${userProfile?.level || 1}`],
                        ['Target Roles', userProfile?.target_roles?.join(', ') || '-'],
                        ['Education', userProfile?.education || '-'],
                      ].map(([l, v]) => (
                        <div key={String(l)} className="bg-zinc-800 rounded-xl p-3">
                          <div className="text-[10px] text-zinc-500 uppercase font-semibold mb-0.5">{String(l)}</div>
                          <div className="text-white font-semibold truncate">{String(v)}</div>
                        </div>
                      ))}
                    </div>
                    <div className="flex items-center justify-between pt-2">
                      <div>
                        <div className="text-xs font-semibold">Theme</div>
                        <div className="text-[10px] text-zinc-400 mt-0.5">Toggle dark / light mode</div>
                      </div>
                      <div className="flex gap-2">
                        {(['dark', 'light'] as const).map(t => (
                          <button key={t} onClick={() => setThemeMode(t)}
                            className={`px-3 py-1.5 rounded-lg text-[10px] font-bold border transition-colors capitalize ${themeMode === t ? 'bg-indigo-600 border-indigo-600 text-white' : 'border-zinc-700 text-zinc-400 hover:bg-zinc-800'}`}>
                            {t}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="flex justify-between pt-3 border-t border-zinc-800">
                      <button onClick={() => {
                        const a = document.createElement('a');
                        a.href = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(userProfile));
                        a.download = 'gapx_profile.json'; a.click();
                      }} className="px-4 py-2 border border-zinc-700 hover:bg-zinc-800 text-xs font-bold rounded-xl transition-colors">
                        Export Data
                      </button>
                      <button onClick={() => { if (confirm('Delete account and log out?')) logout(); }}
                        className="px-4 py-2 bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500 hover:text-white text-xs font-bold rounded-xl transition-colors">
                        Delete Account
                      </button>
                    </div>
                  </div>
                </div>
              )}
              </motion.div>
              </AnimatePresence>
            </div>
          </main>
        </div>
      )}
      </motion.div>
      )}
      </AnimatePresence>

      {/* ── INTERACTIVE DETAILED ACADEMIC STUDY NOTES MODAL ── */}
      <AnimatePresence>
        {selectedNotesTopic && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-zinc-900 border border-zinc-700/80 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden"
            >
              {/* Modal Header */}
              <div className="p-5 border-b border-zinc-800 flex items-start justify-between bg-zinc-950/80 flex-shrink-0">
                <div className="min-w-0 flex-1 pr-4">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="text-[10px] font-extrabold uppercase tracking-wider text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                      {selectedNotesTopic.stageTitle || `Stage ${selectedNotesTopic.stageId}`}
                    </span>
                    <span className="text-[10px] font-bold text-zinc-400 bg-zinc-800 px-2 py-0.5 rounded">
                      Role Track: {userProfile?.target_roles?.[0] || 'Software Engineer'}
                    </span>
                  </div>
                  <h3 className="text-xl font-extrabold text-white truncate">{selectedNotesTopic.title}</h3>
                  <p className="text-xs text-zinc-400 mt-0.5">{selectedNotesTopic.description}</p>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  <button
                    type="button"
                    disabled={notesLoading === `${selectedNotesTopic.stageId}-${selectedNotesTopic.id}`}
                    onClick={() => downloadNotesPdf(selectedNotesTopic.stageId, selectedNotesTopic.id, selectedNotesTopic.title)}
                    className="px-3.5 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-md shadow-indigo-600/30 disabled:opacity-50"
                  >
                    {notesLoading === `${selectedNotesTopic.stageId}-${selectedNotesTopic.id}` ? (
                      <>
                        <Loader2 className="w-3.5 h-3.5 animate-spin" /> Compiling PDF...
                      </>
                    ) : (
                      <>
                        <Download className="w-3.5 h-3.5" /> Download PDF
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => setSelectedNotesTopic(null)}
                    className="p-2 text-zinc-400 hover:text-white rounded-xl bg-zinc-800 hover:bg-zinc-700 transition-colors cursor-pointer"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>
              </div>

              {/* Modal Scrollable Content Body */}
              <div className="flex-1 overflow-y-auto p-6 space-y-6 text-sm text-zinc-300">
                {activeNotesLoading ? (
                  <div className="py-24 text-center">
                    <Loader2 className="w-10 h-10 text-indigo-500 animate-spin mx-auto mb-3" />
                    <p className="text-sm font-bold text-white">Compiling Exhaustive Academic Study Notes...</p>
                    <p className="text-xs text-zinc-500 mt-1">Generating definitions, memory internals, complexity tables, code implementations, and interview FAQs.</p>
                  </div>
                ) : activeNotes ? (
                  <>
                    {/* Narrated concept explainer ("video lesson") */}
                    <div className="space-y-2">
                      <button type="button" onClick={() => setExplainerOpen(o => !o)}
                        className="w-full flex items-center justify-between px-4 py-2.5 rounded-xl bg-fuchsia-500/10 border border-fuchsia-500/30 text-fuchsia-200 text-xs font-bold cursor-pointer">
                        <span className="flex items-center gap-2"><PlayCircle className="w-4 h-4" /> Concept explainer: an animated, narrated lesson for this topic</span>
                        {explainerOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>
                      {explainerOpen && <ConceptPlayer notes={activeNotes} topicTitle={activeNotes.title || selectedNotesTopic.title} />}
                    </div>

                    {/* Last-minute revision notes */}
                    {Array.isArray(activeNotes.last_minute_notes) && activeNotes.last_minute_notes.length > 0 && (
                      <div className="bg-emerald-950/20 border border-emerald-500/25 rounded-xl p-5">
                        <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-wider mb-2">
                          <Zap className="w-4 h-4" /> Last-minute notes
                        </div>
                        <ul className="space-y-1.5">
                          {activeNotes.last_minute_notes.map((n: string, i: number) => (
                            <li key={i} className="text-xs sm:text-sm text-zinc-200 leading-relaxed flex gap-2"><span className="text-emerald-400">•</span><span>{renderInlineMarkdown(n)}</span></li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Videos & documentation */}
                    {activeNotes.resources && ((activeNotes.resources.videos || []).length + (activeNotes.resources.docs || []).length) > 0 && (
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {(activeNotes.resources.videos || []).length > 0 && (
                          <div className="bg-zinc-950/70 border border-zinc-800 rounded-xl p-4">
                            <div className="flex items-center gap-2 text-red-400 text-xs font-bold uppercase tracking-wider mb-2"><Youtube className="w-4 h-4" /> Video lessons</div>
                            {activeNotes.resources.videos.map((v: any, i: number) => (
                              <a key={i} href={v.url} target="_blank" rel="noreferrer" className="block text-xs text-zinc-200 hover:text-red-300 py-1 hover:underline">▶ {v.title}</a>
                            ))}
                          </div>
                        )}
                        {(activeNotes.resources.docs || []).length > 0 && (
                          <div className="bg-zinc-950/70 border border-zinc-800 rounded-xl p-4">
                            <div className="flex items-center gap-2 text-indigo-400 text-xs font-bold uppercase tracking-wider mb-2"><ExternalLink className="w-4 h-4" /> Read the docs</div>
                            {activeNotes.resources.docs.map((d: any, i: number) => (
                              <a key={i} href={d.url} target="_blank" rel="noreferrer" className="block text-xs text-zinc-200 hover:text-indigo-300 py-1 hover:underline">{d.title}</a>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* 1. Executive Definition & Overview */}
                    <div className="bg-zinc-950/70 border border-zinc-800 rounded-xl p-5">
                      <div className="flex items-center gap-2 text-indigo-400 text-xs font-bold uppercase tracking-wider mb-2">
                        <BookOpen className="w-4 h-4" /> 1. Executive Definition &amp; Conceptual Overview
                      </div>
                      <p className="text-xs sm:text-sm text-zinc-200 leading-relaxed font-normal">
                        {activeNotes.executive_summary || activeNotes.introduction}
                      </p>
                    </div>

                    {/* 2. Low-Level Architecture & Internals */}
                    {activeNotes.internals_and_architecture && (
                      <div className="bg-zinc-950/70 border border-zinc-800 rounded-xl p-5">
                        <div className="flex items-center gap-2 text-violet-400 text-xs font-bold uppercase tracking-wider mb-2">
                          <Cpu className="w-4 h-4" /> 2. Deep Memory Layout, Pointers &amp; Runtime Execution
                        </div>
                        <p className="text-xs sm:text-sm text-zinc-300 leading-relaxed">
                          {activeNotes.internals_and_architecture}
                        </p>
                      </div>
                    )}

                    {/* 3. Core Theoretical Concepts */}
                    {activeNotes.key_concepts && activeNotes.key_concepts.length > 0 && (
                      <div className="bg-zinc-950/70 border border-zinc-800 rounded-xl p-5">
                        <div className="flex items-center gap-2 text-indigo-400 text-xs font-bold uppercase tracking-wider mb-3">
                          <Sparkles className="w-4 h-4" /> 3. Core Theoretical Principles &amp; Mechanisms
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          {activeNotes.key_concepts.map((c: any, idx: number) => (
                            <div key={idx} className="p-3 rounded-lg bg-zinc-900 border border-zinc-800">
                              <div className="text-xs font-bold text-white mb-1 flex items-center gap-1.5">
                                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                                {c.name}
                              </div>
                              <p className="text-[11px] text-zinc-400 leading-relaxed">{c.explanation}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 4. Complexity Analysis Table */}
                    {activeNotes.complexity_analysis && activeNotes.complexity_analysis.length > 0 && (
                      <div className="bg-zinc-950/70 border border-zinc-800 rounded-xl p-5">
                        <div className="flex items-center gap-2 text-amber-400 text-xs font-bold uppercase tracking-wider mb-3">
                          <Clock className="w-4 h-4" /> 4. Formal Time &amp; Space Complexity Analysis
                        </div>
                        <div className="overflow-x-auto">
                          <table className="w-full text-left text-xs border-collapse">
                            <thead>
                              <tr className="border-b border-zinc-800 text-zinc-400 bg-zinc-900/60">
                                <th className="p-2.5 font-bold">Operation / Routine</th>
                                <th className="p-2.5 font-bold">Time Complexity</th>
                                <th className="p-2.5 font-bold">Space Complexity</th>
                                <th className="p-2.5 font-bold">Trade-offs &amp; Mechanics</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-zinc-800/60 text-[11px]">
                              {activeNotes.complexity_analysis.map((item: any, idx: number) => (
                                <tr key={idx} className="hover:bg-zinc-900/40">
                                  <td className="p-2.5 font-semibold text-white">{item.operation}</td>
                                  <td className="p-2.5 text-emerald-400 font-mono font-bold">{item.time_complexity}</td>
                                  <td className="p-2.5 text-indigo-400 font-mono font-bold">{item.space_complexity}</td>
                                  <td className="p-2.5 text-zinc-400">{item.explanation}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* 5. Production Code Implementation */}
                    {activeNotes.code_example && (
                      <div className="bg-zinc-950 border border-zinc-800 rounded-xl overflow-hidden">
                        <div className="px-4 py-2.5 bg-zinc-900 border-b border-zinc-800 flex items-center justify-between">
                          <div className="flex items-center gap-2 text-xs font-bold text-zinc-300">
                            <Code2 className="w-4 h-4 text-indigo-400" /> Production-Grade Reference Implementation
                          </div>
                          <button
                            type="button"
                            onClick={() => {
                              navigator.clipboard.writeText(activeNotes.code_example);
                              setCopiedCode(true);
                              setTimeout(() => setCopiedCode(false), 2000);
                            }}
                            className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-[11px] font-bold transition-all flex items-center gap-1 cursor-pointer"
                          >
                            {copiedCode ? (
                              <>
                                <CheckCircle className="w-3.5 h-3.5 text-green-400" /> Copied!
                              </>
                            ) : (
                              <>
                                <Copy className="w-3.5 h-3.5" /> Copy Code
                              </>
                            )}
                          </button>
                        </div>
                        <pre className="p-4 text-xs font-mono text-zinc-200 overflow-x-auto bg-zinc-950 leading-relaxed">
                          <code>{activeNotes.code_example}</code>
                        </pre>
                      </div>
                    )}

                    {/* 6. High-Scale Industry & FAANG Applications */}
                    {activeNotes.industry_use_cases && activeNotes.industry_use_cases.length > 0 && (
                      <div className="bg-zinc-950/70 border border-zinc-800 rounded-xl p-5">
                        <div className="flex items-center gap-2 text-blue-400 text-xs font-bold uppercase tracking-wider mb-3">
                          <ExternalLink className="w-4 h-4" /> 5. High-Scale Production &amp; FAANG Industry Use Cases
                        </div>
                        <div className="space-y-2.5">
                          {activeNotes.industry_use_cases.map((uc: any, idx: number) => (
                            <div key={idx} className="p-3 rounded-lg bg-zinc-900 border border-zinc-800/80">
                              <div className="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                                🏢 {uc.company}
                              </div>
                              <p className="text-[11px] text-zinc-300 mt-1">{uc.use_case}</p>
                              {uc.architecture_impact && (
                                <p className="text-[10px] text-emerald-400 font-semibold mt-1">Impact: {uc.architecture_impact}</p>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 7. Placement Interview FAQs & Model Answers */}
                    {activeNotes.interview_questions && activeNotes.interview_questions.length > 0 && (
                      <div className="bg-zinc-950/70 border border-zinc-800 rounded-xl p-5">
                        <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-wider mb-3">
                          <MessageSquare className="w-4 h-4" /> 6. Top Technical Screening &amp; FAANG Placement Questions
                        </div>
                        <div className="space-y-3">
                          {activeNotes.interview_questions.map((qa: any, idx: number) => (
                            <div key={idx} className="p-3.5 rounded-lg bg-zinc-900 border border-zinc-800">
                              <div className="flex items-start justify-between gap-2 mb-1.5">
                                <div className="text-xs font-bold text-emerald-300">Q{idx}: {qa.question}</div>
                                {qa.difficulty && (
                                  <span className={`text-[9px] px-1.5 py-0.5 rounded font-bold flex-shrink-0 ${qa.difficulty === 'Hard' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : qa.difficulty === 'Medium' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-green-500/10 text-green-400 border border-green-500/20'}`}>
                                    {qa.difficulty}
                                  </span>
                                )}
                              </div>
                              <div className="text-[11px] text-zinc-300 bg-zinc-950/80 p-2.5 rounded-lg border border-zinc-800/60 leading-relaxed">
                                <span className="font-bold text-indigo-400">Ideal Model Answer: </span>
                                {qa.ideal_answer}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 8. Common Traps & Best Practices */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {activeNotes.common_pitfalls && activeNotes.common_pitfalls.length > 0 && (
                        <div className="bg-zinc-950/70 border border-red-500/20 rounded-xl p-4">
                          <div className="text-xs font-bold text-red-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                            <AlertCircle className="w-4 h-4" /> Common Traps to Avoid
                          </div>
                          <ul className="space-y-1.5 text-[11px] text-zinc-400">
                            {activeNotes.common_pitfalls.map((p: string, idx: number) => (
                              <li key={idx} className="flex items-start gap-1.5">
                                <span className="text-red-400 font-bold">•</span>
                                <span>{p}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      {activeNotes.best_practices && activeNotes.best_practices.length > 0 && (
                        <div className="bg-zinc-950/70 border border-green-500/20 rounded-xl p-4">
                          <div className="text-xs font-bold text-green-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                            <CheckCircle className="w-4 h-4" /> Production Best Practices
                          </div>
                          <ul className="space-y-1.5 text-[11px] text-zinc-400">
                            {activeNotes.best_practices.map((pr: string, idx: number) => (
                              <li key={idx} className="flex items-start gap-1.5">
                                <span className="text-green-400 font-bold">✓</span>
                                <span>{pr}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    {/* 9. Key Takeaways & Fast Revision Summary */}
                    {activeNotes.summary && (
                      <div className="bg-gradient-to-r from-indigo-950/40 to-violet-950/40 border border-indigo-500/30 rounded-xl p-4">
                        <div className="text-xs font-bold text-indigo-300 uppercase tracking-wider mb-1 flex items-center gap-1.5">
                          <Sparkles className="w-4 h-4 text-indigo-400" /> Fast Revision Summary
                        </div>
                        <p className="text-xs text-zinc-300 leading-relaxed font-medium">
                          {activeNotes.summary}
                        </p>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="py-12 text-center text-zinc-500">
                    <AlertCircle className="w-8 h-8 mx-auto mb-2 text-zinc-600" />
                    <p className="text-xs">No notes details available for this topic.</p>
                  </div>
                )}
              </div>

              {/* Modal Footer */}
              <div className="p-4 border-t border-zinc-800 bg-zinc-950/80 flex items-center justify-between flex-shrink-0">
                <span className="text-[11px] text-zinc-500">GapX AI Placement Preparation Engine</span>
                <button
                  type="button"
                  onClick={() => setSelectedNotesTopic(null)}
                  className="px-4 py-2 bg-zinc-800 hover:bg-zinc-700 text-white rounded-xl text-xs font-bold transition-all cursor-pointer"
                >
                  Close Notes
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
