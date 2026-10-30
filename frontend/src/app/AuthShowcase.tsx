'use client';

import React, { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { CheckCircle2, Code2, FileText, Map, Mic, Play, ShieldCheck, Sparkles, Trophy, Video } from 'lucide-react';
import GapXLogo from './GapXLogo';

// ───────────────────────── editor: three problems in three languages, typed in a loop ─────────────────────────
type Tok = [string, string];
const C: Record<string, string> = { kw: '#c084fc', fn: '#60a5fa', s: '#fbbf24', n: '#34d399', p: '#e4e4e7', c: '#71717a' };
const SNIPPETS: { title: string; lang: string; level: string; levelColor: string; ms: number; lines: Tok[][] }[] = [
  {
    title: '1. Two Sum', lang: 'Python', level: 'Easy', levelColor: '#34d399', ms: 41,
    lines: [
      [['kw', 'def '], ['fn', 'two_sum'], ['p', '(nums, target):']],
      [['p', '    seen = {}']],
      [['kw', '    for '], ['p', 'i, n '], ['kw', 'in '], ['fn', 'enumerate'], ['p', '(nums):']],
      [['kw', '        if '], ['p', 'target - n '], ['kw', 'in '], ['p', 'seen:']],
      [['kw', '            return '], ['p', '[seen[target - n], i]']],
      [['p', '        seen[n] = i']],
    ],
  },
  {
    title: '20. Valid Parentheses', lang: 'JavaScript', level: 'Easy', levelColor: '#34d399', ms: 52,
    lines: [
      [['kw', 'function '], ['fn', 'isValid'], ['p', '(s) {']],
      [['kw', '  const '], ['p', 'stack = [], pair = { '], ['s', "')'"], ['p', ': '], ['s', "'('"], ['p', ' };']],
      [['kw', '  for '], ['p', '('], ['kw', 'const '], ['p', 'c '], ['kw', 'of '], ['p', 's) {']],
      [['kw', '    if '], ['p', '(!pair[c]) stack.'], ['fn', 'push'], ['p', '(c);']],
      [['kw', '    else if '], ['p', '(stack.'], ['fn', 'pop'], ['p', '() !== pair[c]) '], ['kw', 'return '], ['n', 'false'], ['p', ';']],
      [['p', '  }']],
      [['kw', '  return '], ['p', 'stack.length === '], ['n', '0'], ['p', ';']],
      [['p', '}']],
    ],
  },
  {
    title: '121. Best Time to Buy Stock', lang: 'Java', level: 'Easy', levelColor: '#34d399', ms: 63,
    lines: [
      [['kw', 'public int '], ['fn', 'maxProfit'], ['p', '('], ['kw', 'int'], ['p', '[] prices) {']],
      [['kw', '    int '], ['p', 'min = Integer.MAX_VALUE, best = '], ['n', '0'], ['p', ';']],
      [['kw', '    for '], ['p', '('], ['kw', 'int '], ['p', 'x : prices) {']],
      [['p', '        min = Math.'], ['fn', 'min'], ['p', '(min, x);']],
      [['p', '        best = Math.'], ['fn', 'max'], ['p', '(best, x - min);']],
      [['p', '    }']],
      [['kw', '    return '], ['p', 'best;']],
      [['p', '}']],
    ],
  },
];
const lengthOf = (lines: Tok[][]) => lines.reduce((a, l) => a + l.reduce((b, [, t]) => b + t.length, 0), 0);

function EditorCard() {
  const [idx, setIdx] = useState(0);
  const [n, setN] = useState(0);
  const snip = SNIPPETS[idx];
  const total = lengthOf(snip.lines);
  useEffect(() => {
    const id = setInterval(() => {
      setN(v => {
        if (v >= total + 70) {               // typed + results shown for a while: next problem
          setIdx(i => (i + 1) % SNIPPETS.length);
          return 0;
        }
        return v + 1;
      });
    }, 34);
    return () => clearInterval(id);
  }, [total]);
  const done = n >= total;
  let left = n;
  return (
    <div className="rounded-2xl overflow-hidden shadow-2xl" style={{ background: '#111113', border: '1px solid #27272a' }}>
      <div className="flex items-center gap-2 px-4 py-2.5" style={{ borderBottom: '1px solid #27272a', background: '#0c0c0e' }}>
        <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#f87171' }} />
        <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#fbbf24' }} />
        <span className="w-2.5 h-2.5 rounded-full" style={{ background: '#34d399' }} />
        <AnimatePresence mode="wait">
          <motion.span key={snip.title} initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 6 }}
            className="ml-3 text-xs font-medium flex items-center gap-2" style={{ color: '#a1a1aa' }}>
            {snip.title}
            <span className="text-[10px] font-bold px-1.5 py-0.5 rounded" style={{ background: 'rgba(16,185,129,.12)', color: snip.levelColor }}>{snip.level}</span>
          </motion.span>
        </AnimatePresence>
        <div className="ml-auto flex items-center gap-1.5">
          {SNIPPETS.map((s, i) => (
            <span key={s.lang} className="text-[10px] px-1.5 py-0.5 rounded transition-colors"
              style={{ background: i === idx ? '#27272a' : 'transparent', color: i === idx ? '#e4e4e7' : '#52525b' }}>{s.lang}</span>
          ))}
          <motion.span animate={done ? { scale: [1, 1.12, 1] } : {}} transition={{ duration: 0.4 }}
            className="ml-1 flex items-center gap-1 text-[11px] px-2 py-0.5 rounded-md" style={{ background: done ? 'rgba(16,185,129,.15)' : '#18181b', color: done ? '#34d399' : '#d4d4d8' }}>
            <Play className="w-3 h-3" /> Run
          </motion.span>
        </div>
      </div>
      <div className="px-4 py-3 font-mono text-[12px] leading-[21px] min-h-[206px]">
        {snip.lines.map((line, li) => {
          const lineStart = left;
          return (
            <div key={`${idx}-${li}`} className="flex">
              <span className="w-7 text-right pr-3 select-none" style={{ color: '#52525b' }}>{li + 1}</span>
              <span className="whitespace-pre">
                {line.map(([kind, text], ti) => {
                  const shown = text.slice(0, Math.max(0, left));
                  left -= text.length;
                  return <span key={ti} style={{ color: C[kind] }}>{shown}</span>;
                })}
                {lineStart > 0 && left <= 0 && !done && <span className="inline-block w-[7px] h-4 align-middle animate-pulse" style={{ background: '#a78bfa' }} />}
              </span>
            </div>
          );
        })}
        <div className="mt-2 pt-2 flex flex-wrap items-center gap-2" style={{ borderTop: '1px solid #27272a' }}>
          {[1, 2, 3, 4].map(i => (
            <motion.span key={i} initial={false} animate={{ opacity: done ? 1 : 0.25, scale: done ? 1 : 0.95 }} transition={{ delay: done ? i * 0.12 : 0 }}
              className="text-[11px] px-2 py-0.5 rounded-md flex items-center gap-1" style={{ background: done ? 'rgba(16,185,129,.12)' : '#18181b', color: done ? '#34d399' : '#71717a' }}>
              <CheckCircle2 className="w-3 h-3" /> Test {i}
            </motion.span>
          ))}
          <motion.span initial={false} animate={{ opacity: done ? 1 : 0 }} transition={{ delay: 0.6 }} className="ml-auto text-[11px] font-semibold" style={{ color: '#34d399' }}>
            Accepted · {snip.ms} ms
          </motion.span>
        </div>
      </div>
    </div>
  );
}

// ───────────────────────── interviewer: a live conversation that keeps going ─────────────────────────
const CHAT = [
  { q: "Tell me about a project you're proud of.", a: 'I built a React dashboard with live charts.', tag: 'Follow-up generated from your answer', color: '#a78bfa' },
  { q: 'You mentioned live charts. How did you keep re-renders fast?', a: 'I memoized the chart data with useMemo.', tag: 'Score 82 · Strong answer', color: '#34d399' },
  { q: "What's the time complexity of a hash map lookup?", a: 'O(1) on average, O(n) in the worst case.', tag: 'Concept covered ✓', color: '#34d399' },
  { q: 'How would you design a URL shortener?', a: 'Hash the URL, store it in a key-value store, add a cache.', tag: 'Difficulty increased → Medium', color: '#fbbf24' },
];

function Waveform({ active, color }: { active: boolean; color: string }) {
  return (
    <div className="flex items-end gap-[3px] h-4">
      {[0, 1, 2, 3, 4].map(i => (
        <motion.span key={i} className="w-[3px] rounded-full" style={{ background: color }}
          animate={active ? { height: [4, 14, 6, 12, 4] } : { height: 4 }}
          transition={active ? { repeat: Infinity, duration: 0.9, delay: i * 0.12 } : { duration: 0.2 }} />
      ))}
    </div>
  );
}

function InterviewerChat() {
  const [turn, setTurn] = useState(0);
  const [t, setT] = useState(0);   // ticks within the turn
  const item = CHAT[turn];
  const qEnd = item.q.length;
  const aStart = qEnd + 14;
  const aEnd = aStart + item.a.length;
  const tagAt = aEnd + 10;
  const turnEnd = tagAt + 55;
  useEffect(() => {
    const id = setInterval(() => {
      setT(v => {
        if (v >= turnEnd) { setTurn(x => (x + 1) % CHAT.length); return 0; }
        return v + 1;
      });
    }, 40);
    return () => clearInterval(id);
  }, [turnEnd]);
  const speaking = t < qEnd;
  const listening = t >= aStart - 6 && t < aEnd;
  const qShown = item.q.slice(0, t);
  const aShown = t > aStart ? item.a.slice(0, t - aStart) : '';

  return (
    <div className="w-[384px] max-w-full overflow-hidden rounded-2xl">
    <AnimatePresence mode="wait" initial={false}>
    <motion.div key={turn} initial={{ x: '110%', opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: '-110%', opacity: 0 }}
      transition={{ type: 'spring', stiffness: 170, damping: 24 }}
      className="w-full rounded-2xl p-3.5 space-y-2.5" style={{ background: 'rgba(17,17,19,.92)', border: '1px solid #27272a', backdropFilter: 'blur(8px)' }}>
      <div className="flex items-center gap-2.5">
        <div className="relative w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0" style={{ background: 'linear-gradient(135deg,#7c3aed,#db2777)' }}>
          <span className="text-xs font-black">A</span>
          {speaking && <motion.span className="absolute inset-0 rounded-full" style={{ border: '2px solid #a78bfa' }} animate={{ scale: [1, 1.35], opacity: [0.8, 0] }} transition={{ repeat: Infinity, duration: 1.1 }} />}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-semibold" style={{ color: '#fafafa' }}>Alex · AI interviewer</div>
          <div className="text-[10px]" style={{ color: speaking ? '#c4b5fd' : listening ? '#f87171' : '#71717a' }}>
            {speaking ? 'Speaking…' : listening ? 'Listening to you…' : 'Thinking about your answer…'}
          </div>
        </div>
        <Waveform active={speaking} color="#a78bfa" />
      </div>
      <div className="text-[12px] leading-snug min-h-[34px]" style={{ color: '#e4e4e7' }}>
        &ldquo;{qShown}{speaking && <span className="inline-block w-[2px] h-3 ml-0.5 align-middle animate-pulse" style={{ background: '#a78bfa' }} />}{!speaking && '”'}
      </div>
      <div className="flex items-start gap-2 justify-end min-h-[30px]">
        <AnimatePresence>
          {t >= aStart - 6 && (
            <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              className="text-[11.5px] leading-snug rounded-xl rounded-tr-sm px-3 py-1.5 max-w-[85%]" style={{ background: '#27272a', color: '#d4d4d8' }}>
              {aShown || <span style={{ color: '#71717a' }}>…</span>}
            </motion.div>
          )}
        </AnimatePresence>
        <div className="w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5" style={{ background: listening ? 'rgba(239,68,68,.18)' : '#18181b' }}>
          <Mic className="w-3 h-3" style={{ color: listening ? '#f87171' : '#71717a' }} />
        </div>
      </div>
      <div className="h-5">
        <AnimatePresence>
          {t >= tagAt && (
            <motion.div key={turn} initial={{ opacity: 0, scale: 0.9, x: -6 }} animate={{ opacity: 1, scale: 1, x: 0 }} exit={{ opacity: 0 }}
              className="inline-flex items-center gap-1.5 text-[10.5px] font-semibold px-2 py-0.5 rounded-full"
              style={{ background: `${item.color}1f`, color: item.color, border: `1px solid ${item.color}55` }}>
              <Sparkles className="w-3 h-3" /> {item.tag}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
      {/* which exchange we're on */}
      <div className="flex justify-center gap-1.5 pt-0.5">
        {CHAT.map((_, i) => <span key={i} className="h-1 rounded-full transition-all" style={{ width: i === turn ? 16 : 6, background: i === turn ? '#a78bfa' : '#3f3f46' }} />)}
      </div>
    </motion.div>
    </AnimatePresence>
    </div>
  );
}

// ───────────────────────── small helpers ─────────────────────────
function CountUp({ to, suffix = '' }: { to: number; suffix?: string }) {
  const [v, setV] = useState(0);
  useEffect(() => {
    let raf = 0;
    const start = performance.now();
    const step = (now: number) => {
      const p = Math.max(0, Math.min(1, (now - start) / 1400));
      setV(Math.round(to * (1 - Math.pow(1 - p, 3))));
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [to]);
  return <>{v}{suffix}</>;
}

// Fixed positions (no randomness, so server and browser render the same thing)
const PARTICLES = [[8, 18, 7], [22, 72, 9], [35, 30, 11], [48, 85, 8], [62, 12, 10], [75, 58, 12], [88, 36, 9], [15, 48, 13], [55, 45, 10], [92, 80, 8], [40, 62, 12], [70, 90, 9]];

function Particles({ color = 'rgba(167,139,250,.55)' }: { color?: string }) {
  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden">
      {PARTICLES.map(([x, y, d], i) => (
        <motion.span key={i} className="absolute w-1 h-1 rounded-full" style={{ left: `${x}%`, top: `${y}%`, background: color }}
          animate={{ y: [0, -28, 0], opacity: [0.2, 0.9, 0.2] }} transition={{ repeat: Infinity, duration: d, delay: i * 0.45, ease: 'easeInOut' }} />
      ))}
    </div>
  );
}

// ───────────────────────── left panel ─────────────────────────
export default function AuthShowcase() {
  return (
    <div className="hidden lg:flex relative overflow-hidden flex-col h-screen px-10 py-7 xl:px-14" style={{ background: '#09090b', color: '#fafafa' }}>
      <motion.div className="absolute inset-0" animate={{ backgroundPosition: ['0px 0px', '40px 40px'] }} transition={{ repeat: Infinity, duration: 6, ease: 'linear' }}
        style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,.045) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.045) 1px, transparent 1px)', backgroundSize: '40px 40px', maskImage: 'radial-gradient(ellipse at 40% 40%, black 30%, transparent 75%)', WebkitMaskImage: 'radial-gradient(ellipse at 40% 40%, black 30%, transparent 75%)' }} />
      <motion.div className="absolute w-[520px] h-[520px] rounded-full blur-3xl" style={{ background: 'radial-gradient(circle, rgba(124,58,237,.35), transparent 65%)', top: '-10%', left: '-10%' }}
        animate={{ x: [0, 60, 0], y: [0, 40, 0] }} transition={{ repeat: Infinity, duration: 14 }} />
      <motion.div className="absolute w-[420px] h-[420px] rounded-full blur-3xl" style={{ background: 'radial-gradient(circle, rgba(236,72,153,.2), transparent 65%)', bottom: '-10%', right: '-5%' }}
        animate={{ x: [0, -50, 0], y: [0, -30, 0] }} transition={{ repeat: Infinity, duration: 16 }} />
      <Particles />

      <FitToFrame>
      {/* top bar */}
      <div className="relative z-10 flex items-center gap-3">
        <motion.div animate={{ rotate: [0, 6, -6, 0] }} transition={{ repeat: Infinity, duration: 6 }}><GapXLogo size={34} /></motion.div>
        <span className="text-lg font-black tracking-tight">GapX</span>
        <span className="text-[10px] font-bold uppercase tracking-widest px-2 py-0.5 rounded-full" style={{ background: 'rgba(124,58,237,.18)', color: '#c4b5fd', border: '1px solid rgba(124,58,237,.35)' }}>AI</span>
        <span className="ml-auto flex items-center gap-1.5 text-[11px]" style={{ color: '#a1a1aa' }}>
          <motion.span className="w-2 h-2 rounded-full" style={{ background: '#34d399' }} animate={{ opacity: [1, 0.3, 1] }} transition={{ repeat: Infinity, duration: 1.6 }} />
          All systems live
        </span>
      </div>

      <div className="relative z-10 flex flex-col max-w-xl mt-7">
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
          className="inline-flex self-start items-center gap-2 text-xs font-medium px-3 py-1 rounded-full mb-4" style={{ background: 'rgba(255,255,255,.06)', border: '1px solid rgba(255,255,255,.1)', color: '#d4d4d8' }}>
          <motion.span animate={{ rotate: [0, 20, -20, 0], scale: [1, 1.2, 1] }} transition={{ repeat: Infinity, duration: 3 }}><Sparkles className="w-3.5 h-3.5" style={{ color: '#fbbf24' }} /></motion.span>
          Your placement prep, all in one place
        </motion.div>
        <motion.h1 initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.05 }}
          className="text-[2.5rem] xl:text-[2.8rem] font-black leading-[1.08] tracking-tight">
          Practice like it&apos;s<br />
          <motion.span animate={{ backgroundPosition: ['0% 50%', '100% 50%', '0% 50%'] }} transition={{ repeat: Infinity, duration: 6, ease: 'linear' }}
            style={{ backgroundImage: 'linear-gradient(90deg,#a78bfa,#f472b6,#fb923c,#a78bfa)', backgroundSize: '200% 100%', WebkitBackgroundClip: 'text', backgroundClip: 'text', color: 'transparent' }}>
            the real interview.
          </motion.span>
        </motion.h1>
        <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.15 }} className="mt-3 text-[14.5px] leading-relaxed" style={{ color: '#a1a1aa' }}>
          Solve coding problems, face an AI interviewer that listens and asks follow-ups, and follow a roadmap built for the role you want.
        </motion.p>

        <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.25 }} className="mt-6">
          <motion.div animate={{ y: [0, -5, 0] }} transition={{ repeat: Infinity, duration: 6, ease: 'easeInOut' }}><EditorCard /></motion.div>
        </motion.div>

        <motion.div initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.5 }} className="-mt-2 self-end relative z-10 mr-[-12px]">
          <InterviewerChat />
        </motion.div>
      </div>

      <div className="relative z-10 mt-5"><BottomSlider /></div>
      </FitToFrame>
    </div>
  );
}

/** Shrinks its content (never enlarges) so everything fits inside the panel without scrolling. */
function FitToFrame({ children }: { children: React.ReactNode }) {
  const outer = useRef<HTMLDivElement>(null);
  const inner = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const useIso = typeof window === 'undefined' ? useEffect : useLayoutEffect;
  useIso(() => {
    const fit = () => {
      if (!outer.current || !inner.current) return;
      const avail = outer.current.clientHeight;
      const natural = inner.current.offsetHeight;      // layout height, unaffected by the transform
      const next = natural > 0 ? Math.min(1, avail / natural) : 1;
      setScale(prev => (Math.abs(prev - next) < 0.02 && next >= prev ? prev : next));   // ignore tiny changes (no jitter)
    };
    fit();
    const ro = new ResizeObserver(fit);
    if (outer.current) ro.observe(outer.current);
    if (inner.current) ro.observe(inner.current);
    window.addEventListener('resize', fit);
    return () => { ro.disconnect(); window.removeEventListener('resize', fit); };
  }, []);
  return (
    <div ref={outer} className="relative flex-1 min-h-0 w-full">
      <div ref={inner} className="absolute left-0 right-0 top-1/2 flex flex-col"
        style={{ transform: `translateY(-50%) scale(${scale})`, transformOrigin: 'center center' }}>
        {children}
      </div>
    </div>
  );
}

// ───────────────────────── bottom row: stats and features sliding past ─────────────────────────
const STATS: [number, string, string][] = [[66, '+', 'Coding problems'], [5, '', 'Languages'], [10, '', 'Interview tracks'], [93, '', 'Roadmap topics']];

function BottomSlider() {
  const items: React.ReactNode[] = [];
  STATS.forEach(([v, suf, label], i) => {
    items.push(
      <div key={`s${i}`} className="rounded-xl px-4 py-3 min-w-[130px]" style={{ background: 'rgba(255,255,255,.03)', border: '1px solid rgba(255,255,255,.07)' }}>
        <div className="text-2xl font-black"><CountUp to={v} />{suf}</div>
        <div className="text-[11px] whitespace-nowrap" style={{ color: '#a1a1aa' }}>{label}</div>
      </div>,
    );
    const f = TICKER[i % TICKER.length];
    const g = TICKER[(i + 4) % TICKER.length];
    [f, g].slice(0, i < 2 ? 2 : 1).forEach((feat, k) => items.push(
      <div key={`f${i}-${k}`} className="rounded-xl px-4 py-3 flex items-center gap-2.5 max-w-[240px]" style={{ background: 'rgba(124,58,237,.07)', border: '1px solid rgba(124,58,237,.2)' }}>
        <feat.icon className="w-5 h-5 flex-shrink-0" style={{ color: '#a78bfa' }} />
        <span className="text-[12px] leading-snug" style={{ color: '#d4d4d8' }}>{feat.text}</span>
      </div>,
    ));
  });
  return (
    <div className="overflow-hidden" style={{ maskImage: 'linear-gradient(90deg, transparent, black 8%, black 92%, transparent)', WebkitMaskImage: 'linear-gradient(90deg, transparent, black 8%, black 92%, transparent)' }}>
      <motion.div className="flex gap-3 w-max items-stretch" animate={{ x: ['0%', '-50%'] }} transition={{ repeat: Infinity, duration: 32, ease: 'linear' }}>
        {items}
        {items.map((node, i) => <React.Fragment key={`dup${i}`}>{node}</React.Fragment>)}
      </motion.div>
    </div>
  );
}

// Features shown in the sliding row
const TICKER = [
  { icon: Video, text: 'AI interviews with follow-up questions' },
  { icon: Code2, text: '66+ problems in Python, Java, C++, C, JS' },
  { icon: Map, text: 'Roadmaps with notes, Q&A and videos' },
  { icon: FileText, text: 'ATS-ready A4 resume in one click' },
  { icon: ShieldCheck, text: 'Proctored: phone & extra-person detection' },
  { icon: Trophy, text: 'Daily challenge, XP and leaderboard' },
];
