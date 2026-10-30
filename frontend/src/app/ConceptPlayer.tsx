'use client';

import React, { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Pause, Play, SkipBack, SkipForward, Volume2, VolumeX, Lightbulb, BookOpen, Target, Sparkles, MessageSquare, Loader2 } from 'lucide-react';
import { prefetchSpeech, speak, stopSpeaking, SPEEDS, getSpeed, setSpeed, onSpeedChange, isQuotaReached, onVoiceNotice } from './voice';

type Slide = { kind: 'intro' | 'concept' | 'notes' | 'question' | 'outro'; label: string; title: string; body: string[]; narration: string };

const CONNECTORS = ['First up', 'Next', "Now let's look at", 'Another important idea', 'Here is one more', 'And finally'];

/**
 * A narrated "video lesson" for a roadmap topic: animated slides that explain each idea in simple words,
 * read aloud in a natural voice (Gemini TTS when available, otherwise the best browser voice).
 */
export default function ConceptPlayer({ notes, topicTitle, apiBase, token }: { notes: any; topicTitle: string; apiBase: string; token: string | null }) {
  const slides: Slide[] = useMemo(() => {
    const out: Slide[] = [];
    const summary = String(notes?.executive_summary || '').replace(/Estimated study time.*$/i, '').trim();
    out.push({ kind: 'intro', label: 'Concept explainer', title: topicTitle, body: summary ? [summary] : [],
      narration: `Let's learn about ${topicTitle}. ${summary} I'll explain each idea in simple words, one at a time.` });

    const explained: { point: string; explanation: string }[] = notes?.explained?.length
      ? notes.explained
      : (notes?.key_concepts || []).map((c: any) => ({ point: c.name, explanation: c.explanation }));
    explained.forEach((e, i) => {
      const connector = i === explained.length - 1 && explained.length > 2 ? CONNECTORS[CONNECTORS.length - 1] : CONNECTORS[Math.min(i, CONNECTORS.length - 2)];
      out.push({ kind: 'concept', label: `Idea ${i + 1} of ${explained.length}`, title: e.point, body: [e.explanation],
        narration: `${connector}: ${e.point}. ${e.explanation}` });
    });

    const lm: string[] = notes?.last_minute_notes || [];
    for (let i = 0; i < lm.length; i += 3) {
      const chunk = lm.slice(i, i + 3);
      out.push({ kind: 'notes', label: 'Quick recap', title: i === 0 ? 'Remember these before your interview' : 'A few more things to remember', body: chunk,
        narration: `${i === 0 ? "Here's a quick recap before your interview." : 'A few more points.'} ${chunk.join(' ')}` });
    }
    (notes?.interview_questions || []).slice(0, 2).forEach((qa: any, i: number) => {
      out.push({ kind: 'question', label: 'Interview question', title: qa.question, body: [qa.ideal_answer],
        narration: `${i === 0 ? "Here's a question interviewers love to ask" : "And here's another one"}: ${qa.question} A strong answer would be: ${qa.ideal_answer}` });
    });
    out.push({ kind: 'outro', label: 'Done', title: 'Nice work!', body: ['Download the PDF notes for revision, and watch the linked videos for a deeper dive.'],
      narration: `That's ${topicTitle} covered. Try answering the interview questions out loud, and revise the notes once more before your interview. Good luck!` });
    return out;
  }, [notes, topicTitle]);

  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [muted, setMuted] = useState(false);
  const [buffering, setBuffering] = useState(false);
  const [progress, setProgress] = useState(0);
  const [rate, setRate] = useState(1);
  useEffect(() => { setRate(getSpeed()); return onSpeedChange(setRate); }, []);
  const runRef = useRef(0);
  const [playFrom, setPlayFrom] = useState(0);   // where playback (re)starts; index follows the voice
  const [quota, setQuota] = useState(false);
  useEffect(() => { setQuota(isQuotaReached()); return onVoiceNotice(setQuota); }, []);

  // Slides are narrated in short passages (about 110 words each) to use fewer daily voice clips.
  // Within a passage, the slide changes in step with the voice (by word position).
  const chunks = useMemo(() => {
    const out: { start: number; end: number; text: string; bounds: number[] }[] = [];
    let start = 0;
    while (start < slides.length) {
      let end = start, words = slides[start].narration.split(/\s+/).length;
      while (end + 1 < slides.length && words + slides[end + 1].narration.split(/\s+/).length <= 110) {
        end++;
        words += slides[end].narration.split(/\s+/).length;
      }
      const counts = slides.slice(start, end + 1).map(sl => sl.narration.split(/\s+/).length);
      const total = counts.reduce((a, b) => a + b, 0);
      const bounds = counts.map((_, k) => counts.slice(0, k).reduce((a, b) => a + b, 0) / total);
      out.push({ start, end, text: slides.slice(start, end + 1).map(sl => sl.narration).join(' '), bounds });
      start = end + 1;
    }
    return out;
  }, [slides]);

  const goTo = (i: number) => { const k = Math.max(0, Math.min(slides.length - 1, i)); setIndex(k); setPlayFrom(k); };

  useEffect(() => () => { runRef.current++; stopSpeaking(); }, []);

  useEffect(() => {
    const run = ++runRef.current;
    stopSpeaking();
    setProgress(0);
    if (!playing) return;
    const ci = chunks.findIndex(c => playFrom >= c.start && playFrom <= c.end);
    const chunk = chunks[ci];
    if (!chunk) return;
    if (!muted && chunks[ci + 1]) prefetchSpeech(apiBase, token, chunks[ci + 1].text);

    const finish = () => {
      if (run !== runRef.current) return;
      if (chunk.end < slides.length - 1) { setIndex(chunk.end + 1); setPlayFrom(chunk.end + 1); }
      else setPlaying(false);
    };
    const showFraction = (f: number) => {
      if (run !== runRef.current) return;
      let k = chunk.start;
      for (let j = chunk.start; j <= chunk.end; j++) if (f >= chunk.bounds[j - chunk.start] - 0.001) k = j;
      setIndex(k);
      const segStart = chunk.bounds[k - chunk.start];
      const segEnd = k < chunk.end ? chunk.bounds[k - chunk.start + 1] : 1;
      setProgress(Math.min(1, Math.max(0, (f - segStart) / Math.max(0.0001, segEnd - segStart))));
    };
    let tick: any = null;
    (async () => {
      if (muted) {
        for (let j = playFrom; j <= chunk.end; j++) {
          if (run !== runRef.current) return;
          setIndex(j);
          const ms = Math.max(2500, (slides[j].narration.split(/\s+/).length * 400) / getSpeed());
          const started = Date.now();
          clearInterval(tick);
          tick = setInterval(() => setProgress(Math.min(1, (Date.now() - started) / ms)), 100);
          await new Promise(r => setTimeout(r, ms));
        }
        clearInterval(tick);
      } else {
        setBuffering(true);
        await speak(apiBase, token, chunk.text, 'teacher', {
          startFraction: chunk.bounds[playFrom - chunk.start],
          onStart: () => setBuffering(false),
          onProgress: showFraction,
        });
        setBuffering(false);
      }
      if (run === runRef.current) setTimeout(finish, 400 / getSpeed());
    })();
    return () => { clearInterval(tick); };
  }, [playing, playFrom, muted, chunks, slides, apiBase, token]);


  const slide = slides[index];
  const Icon = { intro: Sparkles, concept: Lightbulb, notes: BookOpen, question: MessageSquare, outro: Target }[slide.kind];
  const accent = { intro: 'from-indigo-600 to-violet-600', concept: 'from-violet-600 to-fuchsia-600', notes: 'from-emerald-600 to-teal-600', question: 'from-amber-500 to-orange-600', outro: 'from-indigo-600 to-sky-600' }[slide.kind];

  return (
    <div className="rounded-2xl overflow-hidden border border-zinc-800 bg-zinc-950">
      <div className={`relative min-h-[260px] sm:min-h-[300px] w-full bg-gradient-to-br ${accent} flex items-center justify-center p-6 sm:p-10 overflow-hidden`}>
        <motion.div className="absolute -top-16 -right-16 w-56 h-56 rounded-full bg-white/10" animate={{ scale: [1, 1.15, 1] }} transition={{ repeat: Infinity, duration: 6 }} />
        <motion.div className="absolute -bottom-20 -left-10 w-64 h-64 rounded-full bg-black/10" animate={{ scale: [1.1, 1, 1.1] }} transition={{ repeat: Infinity, duration: 7 }} />
        <AnimatePresence mode="wait">
          <motion.div key={index} initial={{ opacity: 0, y: 24, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -24, scale: 0.97 }}
            transition={{ duration: 0.45 }} className="relative z-10 text-center max-w-2xl" style={{ color: '#ffffff' }}>
            <motion.div initial={{ rotate: -20, scale: 0.6 }} animate={{ rotate: 0, scale: 1 }} transition={{ type: 'spring', stiffness: 180 }}
              className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-white/20 backdrop-blur flex items-center justify-center">
              <Icon className="w-6 h-6" style={{ color: '#ffffff' }} />
            </motion.div>
            <div className="text-[10px] uppercase tracking-[0.2em] font-bold opacity-80 mb-1">{slide.label}</div>
            <h4 className="text-lg sm:text-2xl font-extrabold leading-snug">{slide.title}</h4>
            <div className="mt-3 space-y-1.5">
              {slide.body.map((b, i) => (
                <motion.p key={i} initial={{ opacity: 0, x: -10 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.25 + i * 0.35 }}
                  className="text-sm sm:text-base leading-relaxed opacity-95">
                  {slide.kind === 'notes' ? `• ${b}` : b}
                </motion.p>
              ))}
            </div>
          </motion.div>
        </AnimatePresence>
        {buffering && playing && (
          <div className="absolute top-3 right-3 flex items-center gap-1.5 text-[10px] font-semibold bg-black/30 rounded-full px-2 py-1" style={{ color: '#ffffff' }}>
            <Loader2 className="w-3 h-3 animate-spin" /> Preparing voice…
          </div>
        )}
        <div className="absolute bottom-2 right-3 text-[10px] font-mono opacity-80" style={{ color: '#ffffff' }}>{index + 1} / {slides.length}</div>
      </div>
      {quota && (
        <div className="px-3 pt-2 text-[10px] text-amber-400">
          Today's free natural-voice limit is used up, so a backup voice is playing. Lessons you've already played still use the natural voice, and the limit resets daily.
        </div>
      )}

      <div className="flex gap-1 px-3 pt-2">
        {slides.map((_, i) => (
          <button key={i} onClick={() => goTo(i)} className="flex-1 h-1 rounded-full bg-zinc-800 overflow-hidden" aria-label={`Go to slide ${i + 1}`}>
            <div className="h-full bg-indigo-500 transition-[width] duration-100" style={{ width: i < index ? '100%' : i === index ? `${(playing && !buffering ? progress : 0) * 100}%` : '0%' }} />
          </button>
        ))}
      </div>

      <div className="flex items-center justify-between px-3 py-2">
        <div className="flex items-center gap-1.5">
          <button onClick={() => goTo(index - 1)} className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:bg-zinc-800" aria-label="Previous slide"><SkipBack className="w-3.5 h-3.5" /></button>
          <button onClick={() => { if (!playing) setPlayFrom(index === slides.length - 1 ? 0 : index); if (!playing && index === slides.length - 1) setIndex(0); setPlaying(p => !p); }}
            className="px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-bold flex items-center gap-1.5">
            {playing ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />} {playing ? 'Pause' : index === 0 ? 'Play lesson' : 'Resume'}
          </button>
          <button onClick={() => goTo(index + 1)} className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:bg-zinc-800" aria-label="Next slide"><SkipForward className="w-3.5 h-3.5" /></button>
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center rounded-lg border border-zinc-800 bg-zinc-900 p-0.5" role="group" aria-label="Playback speed">
            {SPEEDS.map(sp => (
              <button key={sp} type="button" onClick={() => setSpeed(sp)}
                className={`px-2 py-1 rounded-md text-[10px] font-bold transition-colors ${rate === sp ? 'bg-indigo-600 text-white' : 'text-zinc-400 hover:text-zinc-200'}`}
                aria-pressed={rate === sp} title={`Play at ${sp}x speed`}>
                {sp}x
              </button>
            ))}
          </div>
          <button onClick={() => setMuted(m => !m)} className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:bg-zinc-800" aria-label={muted ? 'Unmute narration' : 'Mute narration'}>
            {muted ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>
    </div>
  );
}
