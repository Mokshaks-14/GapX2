'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Pause, Play, SkipBack, SkipForward, Volume2, VolumeX, Lightbulb, BookOpen, Target, Sparkles, MessageSquare } from 'lucide-react';

type Slide = { kind: 'intro' | 'concept' | 'notes' | 'question' | 'outro'; title: string; body: string[]; narration: string };

/**
 * A narrated, auto-advancing "video lesson" built from a topic's notes.
 * Slides animate in and are read aloud with the browser's speech synthesis.
 */
export default function ConceptPlayer({ notes, topicTitle }: { notes: any; topicTitle: string }) {
  const slides: Slide[] = useMemo(() => {
    const out: Slide[] = [];
    const summary = notes?.executive_summary || '';
    out.push({ kind: 'intro', title: topicTitle, body: summary ? [summary] : [], narration: `${topicTitle}. ${summary}` });
    (notes?.key_concepts || []).forEach((c: any) => {
      const expl = c.explanation && c.explanation !== c.name ? c.explanation : '';
      out.push({ kind: 'concept', title: c.name, body: expl ? [expl] : [], narration: `${c.name}. ${expl}` });
    });
    const lm: string[] = notes?.last_minute_notes || [];
    for (let i = 0; i < lm.length; i += 3) {
      const chunk = lm.slice(i, i + 3);
      out.push({ kind: 'notes', title: 'Remember this', body: chunk, narration: chunk.join(' ') });
    }
    const qa = (notes?.interview_questions || [])[0];
    if (qa) out.push({ kind: 'question', title: qa.question, body: [qa.ideal_answer], narration: `Interview question: ${qa.question} A strong answer: ${qa.ideal_answer}` });
    out.push({ kind: 'outro', title: 'Recap complete', body: ['Download the PDF notes for revision and watch the linked videos for deeper explanations.'], narration: `That's the recap of ${topicTitle}. Revise the notes and practise the interview question out loud.` });
    return out;
  }, [notes, topicTitle]);

  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [progress, setProgress] = useState(0);
  const timerRef = useRef<any>(null);
  const tickRef = useRef<any>(null);

  const stopAll = () => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) window.speechSynthesis.cancel();
    clearTimeout(timerRef.current);
    clearInterval(tickRef.current);
  };

  useEffect(() => () => stopAll(), []);

  useEffect(() => {
    stopAll();
    setProgress(0);
    if (!playing) return;
    const slide = slides[index];
    if (!slide) return;
    const advance = () => {
      if (index < slides.length - 1) setIndex(i => i + 1);
      else setPlaying(false);
    };
    // Estimated duration drives the progress bar (and advancing when muted)
    const ms = Math.max(3500, slide.narration.split(/\s+/).length * 380);
    const started = Date.now();
    tickRef.current = setInterval(() => setProgress(Math.min(1, (Date.now() - started) / ms)), 100);
    const canSpeak = !muted && typeof window !== 'undefined' && 'speechSynthesis' in window;
    if (canSpeak) {
      const u = new SpeechSynthesisUtterance(slide.narration);
      u.rate = 1.0;
      const voice = window.speechSynthesis.getVoices().find(v => v.lang.startsWith('en') && /Google|Natural|Neural|Samantha|Zira/.test(v.name));
      if (voice) u.voice = voice;
      u.onend = () => { timerRef.current = setTimeout(advance, 600); };
      window.speechSynthesis.speak(u);
    } else {
      timerRef.current = setTimeout(advance, ms);
    }
    return () => stopAll();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index, playing, muted, slides]);

  const slide = slides[index];
  const Icon = { intro: Sparkles, concept: Lightbulb, notes: BookOpen, question: MessageSquare, outro: Target }[slide.kind];
  const accent = { intro: 'from-indigo-600 to-violet-600', concept: 'from-violet-600 to-fuchsia-600', notes: 'from-emerald-600 to-teal-600', question: 'from-amber-500 to-orange-600', outro: 'from-indigo-600 to-sky-600' }[slide.kind];

  return (
    <div className="rounded-2xl overflow-hidden border border-zinc-800 bg-zinc-950">
      {/* Stage */}
      <div className={`relative aspect-video max-h-[340px] w-full bg-gradient-to-br ${accent} flex items-center justify-center p-6 sm:p-10 overflow-hidden`}>
        <motion.div className="absolute -top-16 -right-16 w-56 h-56 rounded-full bg-white/10" animate={{ scale: [1, 1.15, 1] }} transition={{ repeat: Infinity, duration: 6 }} />
        <motion.div className="absolute -bottom-20 -left-10 w-64 h-64 rounded-full bg-black/10" animate={{ scale: [1.1, 1, 1.1] }} transition={{ repeat: Infinity, duration: 7 }} />
        <AnimatePresence mode="wait">
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 24, scale: 0.97 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -24, scale: 0.97 }}
            transition={{ duration: 0.45 }}
            className="relative z-10 text-center max-w-2xl"
            style={{ color: '#ffffff' }}
          >
            <motion.div initial={{ rotate: -20, scale: 0.6 }} animate={{ rotate: 0, scale: 1 }} transition={{ type: 'spring', stiffness: 180 }}
              className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
              <Icon className="w-6 h-6" style={{ color: '#ffffff' }} />
            </motion.div>
            <div className="text-[10px] uppercase tracking-[0.2em] font-bold opacity-80 mb-1">
              {slide.kind === 'concept' ? 'Key concept' : slide.kind === 'notes' ? 'Last-minute notes' : slide.kind === 'question' ? 'Interview question' : 'Concept explainer'}
            </div>
            <h4 className="text-lg sm:text-2xl font-extrabold leading-snug">{slide.title}</h4>
            <div className="mt-3 space-y-1.5">
              {slide.body.map((b, i) => (
                <motion.p key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.25 + i * 0.35 }}
                  className="text-xs sm:text-sm leading-relaxed opacity-95">
                  {slide.kind === 'notes' ? `• ${b}` : b}
                </motion.p>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>
        <div className="absolute bottom-2 right-3 text-[10px] font-mono opacity-80" style={{ color: '#ffffff' }}>{index + 1} / {slides.length}</div>
      </div>

      {/* Progress */}
      <div className="flex gap-1 px-3 pt-2">
        {slides.map((_, i) => (
          <button key={i} onClick={() => { setIndex(i); }} className="flex-1 h-1 rounded-full bg-zinc-800 overflow-hidden" aria-label={`Go to slide ${i + 1}`}>
            <div className="h-full bg-indigo-500 transition-[width] duration-100" style={{ width: i < index ? '100%' : i === index ? `${(playing ? progress : 0) * 100}%` : '0%' }} />
          </button>
        ))}
      </div>

      {/* Controls */}
      <div className="flex items-center justify-between px-3 py-2">
        <div className="flex items-center gap-1.5">
          <button onClick={() => setIndex(i => Math.max(0, i - 1))} className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:bg-zinc-800" aria-label="Previous slide"><SkipBack className="w-3.5 h-3.5" /></button>
          <button onClick={() => { if (!playing && index === slides.length - 1) setIndex(0); setPlaying(p => !p); }}
            className="px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1.5">
            {playing ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />} {playing ? 'Pause' : index === 0 ? 'Play lesson' : 'Resume'}
          </button>
          <button onClick={() => setIndex(i => Math.min(slides.length - 1, i + 1))} className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:bg-zinc-800" aria-label="Next slide"><SkipForward className="w-3.5 h-3.5" /></button>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-zinc-500 hidden sm:inline">Narrated by your browser&apos;s voice</span>
          <button onClick={() => setMuted(m => !m)} className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:bg-zinc-800" aria-label={muted ? 'Unmute narration' : 'Mute narration'}>
            {muted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>
    </div>
  );
}
