'use client';

import React, { useRef, useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

// Dynamic import of Monaco Editor with SSR disabled
const Editor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

export interface SyntaxErrorItem {
  line: number;
  column: number;
  message: string;
}

interface MonacoCodeEditorProps {
  code: string;
  language: string; // 'python' | 'javascript' | 'java' | 'cpp'
  onChange: (newCode: string) => void;
  onSyntaxErrorChange?: (errors: SyntaxErrorItem[]) => void;
  theme?: 'dark' | 'light';
}

export default function MonacoCodeEditor({
  code,
  language,
  onChange,
  onSyntaxErrorChange,
  theme = 'dark'
}: MonacoCodeEditorProps) {
  const editorRef = useRef<any>(null);
  const monacoRef = useRef<any>(null);
  const [syntaxErrors, setSyntaxErrors] = useState<SyntaxErrorItem[]>([]);
  const [isEditorReady, setIsEditorReady] = useState(false);

  // Map frontend language identifier to Monaco language ID
  const getMonacoLanguage = (lang: string) => {
    switch (lang.toLowerCase()) {
      case 'python':
        return 'python';
      case 'javascript':
      case 'js':
        return 'javascript';
      case 'java':
        return 'java';
      case 'cpp':
      case 'c++':
        return 'cpp';
      case 'c':
        return 'c';
      default:
        return 'python';
    }
  };

  // --- CLIENT-SIDE REAL-TIME SYNTAX CHECKER ---
  const validateSyntax = useCallback((sourceCode: string, lang: string): SyntaxErrorItem[] => {
    const errors: SyntaxErrorItem[] = [];
    const lines = sourceCode.split('\n');

    // 1. Bracket / Parentheses Matching (All languages)
    const stack: { char: string; line: number; col: number }[] = [];
    const pairs: Record<string, string> = { ')': '(', '}': '{', ']': '[' };

    lines.forEach((line, lineIdx) => {
      let inString: string | null = null;
      let isEscaped = false;

      for (let col = 0; col < line.length; col++) {
        const ch = line[col];

        // Handle string literals to avoid flagging brackets inside strings
        if (inString) {
          if (ch === inString && !isEscaped) {
            inString = null;
          }
          isEscaped = (ch === '\\' && !isEscaped);
          continue;
        }

        if (ch === '"' || ch === "'") {
          // Check for triple quotes in python
          if (lang === 'python' && line.slice(col, col + 3) === '"""') {
            inString = '"""';
            col += 2;
            continue;
          }
          inString = ch;
          continue;
        }

        // Ignore comments
        if (lang === 'python' && ch === '#') break;
        if ((lang === 'javascript' || lang === 'java' || lang === 'cpp' || lang === 'c') && line.slice(col, col + 2) === '//') break;

        if (ch === '(' || ch === '{' || ch === '[') {
          stack.push({ char: ch, line: lineIdx + 1, col: col + 1 });
        } else if (ch === ')' || ch === '}' || ch === ']') {
          if (stack.length === 0 || stack[stack.length - 1].char !== pairs[ch]) {
            errors.push({
              line: lineIdx + 1,
              column: col + 1,
              message: `SyntaxError: Mismatched closing bracket '${ch}' with no matching opening '${pairs[ch]}'`
            });
          } else {
            stack.pop();
          }
        }
      }
    });

    // Unclosed brackets
    stack.forEach(unclosed => {
      errors.push({
        line: unclosed.line,
        column: unclosed.col,
        message: `SyntaxError: Unclosed bracket '${unclosed.char}' was never closed`
      });
    });

    // 2. Python specific syntax checks (missing colons, def keywords, indentation)
    if (lang === 'python') {
      const blockKeywords = ['def', 'class', 'if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with'];
      lines.forEach((rawLine, idx) => {
        const trimmed = rawLine.trim();
        if (!trimmed || trimmed.startsWith('#')) return;

        // Check for missing colon
        for (const kw of blockKeywords) {
          const regex = new RegExp(`^${kw}\\b`);
          if (regex.test(trimmed)) {
            // Lines like 'else:' or 'try:' or 'def solve():' must end with ':'
            if (!trimmed.endsWith(':') && !trimmed.endsWith('\\')) {
              errors.push({
                line: idx + 1,
                column: rawLine.length,
                message: `SyntaxError: Missing colon ':' at the end of '${kw}' statement header`
              });
            }
            break;
          }
        }

        // Check for double assignment error e.g. "if x = 5:"
        if (/^\s*(if|elif|while)\b.*[^=!<>]=[^=]/.test(rawLine) && !rawLine.includes('==') && !rawLine.includes('!=')) {
          errors.push({
            line: idx + 1,
            column: 1,
            message: "SyntaxError: Assignment '=' used in conditional expression. Did you mean '==' for comparison?"
          });
        }
      });
    }

    // 3. JavaScript / Java / C++ / C specific checks
    if (lang === 'javascript' || lang === 'java' || lang === 'cpp' || lang === 'c') {
      lines.forEach((rawLine, idx) => {
        const trimmed = rawLine.trim();
        if (!trimmed || trimmed.startsWith('//') || trimmed.startsWith('/*') || trimmed.startsWith('#')) return;

        // Check unclosed quotes on single line
        const doubleQuotes = (rawLine.match(/(?<!\\)"/g) || []).length;
        const singleQuotes = (rawLine.match(/(?<!\\)'/g) || []).length;
        if (doubleQuotes % 2 !== 0 && !rawLine.includes('`')) {
          errors.push({
            line: idx + 1,
            column: rawLine.length,
            message: 'SyntaxError: Unterminated string literal (unclosed double quote)'
          });
        } else if (singleQuotes % 2 !== 0 && !rawLine.includes('`')) {
          errors.push({
            line: idx + 1,
            column: rawLine.length,
            message: 'SyntaxError: Unterminated string literal (unclosed single quote)'
          });
        }
      });
    }

    return errors;
  }, []);

  // Update Monaco markers whenever code or syntax errors change
  useEffect(() => {
    const errors = validateSyntax(code, language);
    setSyntaxErrors(errors);
    if (onSyntaxErrorChange) onSyntaxErrorChange(errors);

    if (editorRef.current && monacoRef.current) {
      const monaco = monacoRef.current;
      const model = editorRef.current.getModel();
      if (model) {
        // Map our syntax errors into Monaco red squiggly markers
        const markers = errors.map(err => ({
          severity: monaco.MarkerSeverity.Error,
          startLineNumber: err.line,
          startColumn: err.column,
          endLineNumber: err.line,
          endColumn: err.column + 10,
          message: err.message,
          source: 'Syntax Checker'
        }));

        monaco.editor.setModelMarkers(model, 'syntax_validator', markers);
      }
    }
  }, [code, language, validateSyntax, onSyntaxErrorChange]);

  const handleEditorDidMount = (editor: any, monaco: any) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    setIsEditorReady(true);

    // Set editor options
    editor.updateOptions({
      fontSize: 13,
      fontFamily: "'Fira Code', 'Cascadia Code', 'JetBrains Mono', Consolas, monospace",
      fontLigatures: true,
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      automaticLayout: true,
      lineNumbers: 'on',
      renderLineHighlight: 'all',
      bracketPairColorization: { enabled: true },
      matchBrackets: 'always',
      tabSize: language === 'javascript' ? 2 : 4,
      wordWrap: 'off',
      cursorBlinking: 'smooth',
      smoothScrolling: true,
      suggestOnTriggerCharacters: true
    });
  };

  return (
    <div className="relative w-full h-full flex flex-col min-h-0 bg-[#1e1e1e] rounded-b-2xl overflow-hidden">
      {/* Monaco Editor Container */}
      <div className="flex-1 w-full h-full min-h-0">
        <Editor
          height="100%"
          language={getMonacoLanguage(language)}
          value={code}
          theme={theme === 'light' ? 'vs' : 'vs-dark'}
          onChange={(val) => onChange(val || '')}
          onMount={handleEditorDidMount}
          options={{
            fontSize: 13,
            fontFamily: "'Fira Code', 'Cascadia Code', 'JetBrains Mono', Consolas, monospace",
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            automaticLayout: true,
            lineNumbers: 'on',
            lineNumbersMinChars: 3,
            bracketPairColorization: { enabled: true },
            glyphMargin: false,
            folding: true,
            tabSize: 4
          }}
          loading={
            <div className="w-full h-full flex items-center justify-center bg-zinc-950 text-zinc-500 font-mono text-xs">
              Initializing Monaco Code Engine...
            </div>
          }
        />
      </div>

      {/* Syntax Error Live Ribbon (if syntax errors exist) */}
      {syntaxErrors.length > 0 && (
        <div className="px-4 py-1.5 bg-red-950/80 border-t border-red-800/80 flex items-center justify-between text-[11px] text-red-300 font-mono flex-shrink-0 animate-fadeIn">
          <div className="flex items-center gap-2 overflow-hidden text-ellipsis whitespace-nowrap">
            <AlertCircle className="w-3.5 h-3.5 text-red-400 flex-shrink-0 animate-pulse" />
            <span className="font-semibold text-red-400">Syntax Error (Line {syntaxErrors[0].line}):</span>
            <span className="truncate">{syntaxErrors[0].message}</span>
          </div>
          <span className="text-[10px] text-red-400/80 bg-red-900/40 px-2 py-0.5 rounded ml-2 flex-shrink-0 font-sans">
            {syntaxErrors.length} {syntaxErrors.length === 1 ? 'issue' : 'issues'} found
          </span>
        </div>
      )}
    </div>
  );
}
