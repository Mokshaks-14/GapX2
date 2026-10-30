"""Runs user code against a problem's test cases.

Every language gets a small driver program that reads the test input from stdin, converts it
to the right types using the problem's signature (arrays, strings, grids, linked lists, trees),
calls the user's function, and prints the result after a marker so the user's own print()
output can be shown separately.

Execution backends:
  * Judge0 (sandboxed) when JUDGE0_API_KEY is configured — use this in production.
  * Local subprocesses (python / node / javac+java / g++) for development only.
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

from app.core.config import settings

MARKER = "\x1eGAPX_RESULT\x1e"
TIME_LIMIT = 3.0          # seconds per test case
COMPILE_LIMIT = 25.0      # seconds for javac / g++
MAX_OUTPUT = 64 * 1024    # bytes of stdout/stderr kept per run
SUPPORTED = ("python", "javascript", "java", "cpp", "c")
LANG_ALIASES = {"py": "python", "python3": "python", "js": "javascript", "node": "javascript", "c++": "cpp", "openjdk": "java",
                "gcc": "c", "c11": "c"}
C_MARKER_LITERAL = r'"\x1e" "GAPX_RESULT" "\x1e"'  # the result marker as a C/C++ string literal


def local_execution_allowed() -> bool:
    return settings.ALLOW_LOCAL_CODE_EXECUTION and not settings.is_production


# ═════════════════════════════ DRIVERS ═════════════════════════════
PY_PRELUDE = '''import sys, json, io
from typing import *
from collections import *
import heapq, math, bisect, itertools, functools

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right
'''

PY_RUNNER = r'''

# ───────── GapX test runner ─────────
def __gx_scalar(t):
    t = t.strip()
    if t == "": return t
    low = t.lower()
    if low == "true": return True
    if low == "false": return False
    if low in ("null", "none"): return None
    try: return int(t)
    except ValueError: pass
    try: return float(t)
    except ValueError: pass
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "\"'": return t[1:-1]
    return t

def __gx_list(s):
    s = s.strip()
    if s == "" or s == "[]": return []
    if s.startswith("["):
        for candidate in (s, "[" + s + "]"):
            try:
                v = json.loads(candidate)
                return v if isinstance(v, list) else [v]
            except Exception:
                pass
        s = s.strip("[]")
    return [__gx_scalar(p) for p in s.split(",")]

def __gx_build_list(vals):
    dummy = ListNode(); cur = dummy
    for v in vals:
        cur.next = ListNode(v); cur = cur.next
    return dummy.next

def __gx_build_tree(vals):
    if not vals or vals[0] is None: return None
    root = TreeNode(vals[0]); queue = [root]; i = 1
    while queue and i < len(vals):
        node = queue.pop(0)
        if i < len(vals) and vals[i] is not None:
            node.left = TreeNode(vals[i]); queue.append(node.left)
        i += 1
        if i < len(vals) and vals[i] is not None:
            node.right = TreeNode(vals[i]); queue.append(node.right)
        i += 1
    return root

def __gx_find(root, val):
    stack = [root]
    while stack:
        n = stack.pop()
        if n is None: continue
        if n.val == val: return n
        stack += [n.left, n.right]
    return TreeNode(val)

def __gx_convert(raw, typ, ctx):
    if typ in ("int", "long"): return int(raw.strip())
    if typ == "double": return float(raw.strip())
    if typ == "bool": return raw.strip().lower() == "true"
    if typ == "string":
        s = raw.rstrip("\r")
        return s[1:-1] if len(s) >= 2 and s[0] == s[-1] == '"' else s
    if typ in ("int[]", "string[]", "double[]", "bool[]"):
        vals = __gx_list(raw)
        return [str(v) for v in vals] if typ == "string[]" else vals
    if typ in ("int[][]", "string[][]"):
        v = __gx_list(raw)
        return [v] if v and not isinstance(v[0], list) else v
    if typ == "ListNode": return __gx_build_list(__gx_list(raw))
    if typ == "TreeNode":
        t = __gx_build_tree(__gx_list(raw))
        if ctx.get("tree") is None: ctx["tree"] = t
        return t
    if typ == "TreeNodeRef": return __gx_find(ctx.get("tree"), __gx_scalar(raw))
    return __gx_scalar(raw)

def __gx_grid(rows):
    return [r.strip().split(",") if "," in r else list(r.strip()) for r in rows if r.strip() != ""]

def __gx_fmt(v, typ=None):
    if typ == "TreeNodeVal": return "null" if v is None else str(v.val)
    if v is None and typ in ("ListNode", "TreeNode"): return ""
    if isinstance(v, bool): return "true" if v else "false"
    if v is None: return "null"
    if isinstance(v, ListNode):
        out = []; seen = 0
        while v is not None and seen < 10000: out.append(str(v.val)); v = v.next; seen += 1
        return ",".join(out)
    if isinstance(v, TreeNode):
        out, q = [], [v]
        while q:
            n = q.pop(0)
            if n is None: out.append("null"); continue
            out.append(str(n.val)); q += [n.left, n.right]
        while out and out[-1] == "null": out.pop()
        return ",".join(out)
    if isinstance(v, (list, tuple)):
        if v and all(isinstance(x, (list, tuple)) for x in v):
            return "; ".join(",".join(__gx_fmt(y) for y in x) for x in v)
        return ",".join(__gx_fmt(x) for x in v)
    if isinstance(v, float) and v.is_integer() and typ != "double": return str(int(v))
    return str(v)

def __gx_main():
    sig = json.loads(__GX_SIG__)
    data = sys.stdin.read().replace("\r", "")
    lines = data.split("\n")
    params = sig.get("params") or []
    while len(lines) > max(1, len(params)) and lines[-1].strip() == "": lines.pop()
    ctx = {}
    real_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        if sig.get("design"):
            ops, argl = json.loads(lines[0]), json.loads(lines[1])
            cls = globals()[sig["design"]]
            obj, out = None, []
            for op, a in zip(ops, argl):
                if obj is None: obj = cls(*a); out.append(None)
                else: out.append(getattr(obj, op)(*a))
            result, rtype = out, None
        else:
            fn_name = sig.get("fn")
            target = None
            if "Solution" in globals():
                inst = globals()["Solution"]()
                if fn_name and hasattr(inst, fn_name): target = getattr(inst, fn_name)
                else:
                    names = [k for k, v in type(inst).__dict__.items() if callable(v) and not k.startswith("_")]
                    if names: target = getattr(inst, names[0])
            if target is None and fn_name in globals(): target = globals()[fn_name]
            if target is None: raise NameError("Could not find your solution function" + (f" '{fn_name}'" if fn_name else ""))
            args, idx = [], 0
            if params:
                for i, (_, typ) in enumerate(params):
                    remaining = len(params) - i - 1
                    if typ == "char[][]":
                        take = max(1, len(lines) - idx - remaining)
                        args.append(__gx_grid(lines[idx:idx + take])); idx += take
                    else:
                        args.append(__gx_convert(lines[idx] if idx < len(lines) else "", typ, ctx)); idx += 1
            else:
                args = [__gx_scalar(l) if "," not in l and not l.strip().startswith("[") else __gx_list(l) for l in lines if l.strip() != ""]
            result = target(*args)
            rtype = sig.get("returns")
            if result is None and (rtype in (None, "void")) and args and isinstance(args[0], list):
                result = args[0]  # in-place problems: print the modified array
    finally:
        user_out = sys.stdout.getvalue()
        sys.stdout = real_stdout
    if user_out:
        sys.stderr.write("__GX_STDOUT__" + user_out[:4000])
    print(__GX_MARKER__ + __gx_fmt(result, rtype))

__gx_main()
'''

JS_RUNNER = r'''

// ───────── GapX test runner ─────────
function ListNode(val, next) { this.val = (val === undefined ? 0 : val); this.next = (next === undefined ? null : next); }
function TreeNode(val, left, right) { this.val = (val === undefined ? 0 : val); this.left = (left === undefined ? null : left); this.right = (right === undefined ? null : right); }
const __gxSig = JSON.parse(__GX_SIG__);
function __gxScalar(t) {
  t = String(t).trim(); const low = t.toLowerCase();
  if (t === '') return t;
  if (low === 'true') return true; if (low === 'false') return false; if (low === 'null') return null;
  if (/^-?\d+(\.\d+)?(e-?\d+)?$/i.test(t)) return Number(t);
  if (t.length >= 2 && (t[0] === '"' || t[0] === "'") && t[t.length - 1] === t[0]) return t.slice(1, -1);
  return t;
}
function __gxList(s) {
  s = String(s).trim();
  if (s === '' || s === '[]') return [];
  if (s.startsWith('[')) {
    for (const c of [s, '[' + s + ']']) { try { const v = JSON.parse(c); return Array.isArray(v) ? v : [v]; } catch (e) {} }
  }
  return s.replace(/^\[|\]$/g, '').split(',').map(__gxScalar);
}
function __gxBuildList(vals) { const d = new ListNode(); let c = d; for (const v of vals) { c.next = new ListNode(v); c = c.next; } return d.next; }
function __gxBuildTree(vals) {
  if (!vals.length || vals[0] === null) return null;
  const root = new TreeNode(vals[0]); const q = [root]; let i = 1;
  while (q.length && i < vals.length) {
    const n = q.shift();
    if (i < vals.length && vals[i] !== null) { n.left = new TreeNode(vals[i]); q.push(n.left); } i++;
    if (i < vals.length && vals[i] !== null) { n.right = new TreeNode(vals[i]); q.push(n.right); } i++;
  }
  return root;
}
function __gxFind(root, val) { const st = [root]; while (st.length) { const n = st.pop(); if (!n) continue; if (n.val === val) return n; st.push(n.left, n.right); } return new TreeNode(val); }
function __gxConvert(raw, typ, ctx) {
  switch (typ) {
    case 'int': case 'long': return parseInt(raw.trim(), 10);
    case 'double': return parseFloat(raw.trim());
    case 'bool': return raw.trim().toLowerCase() === 'true';
    case 'string': { const s = raw.replace(/\r$/, ''); return (s.length >= 2 && s[0] === '"' && s[s.length - 1] === '"') ? s.slice(1, -1) : s; }
    case 'int[]': case 'double[]': case 'bool[]': return __gxList(raw);
    case 'int[][]': case 'string[][]': { const v = __gxList(raw); return v.length && !Array.isArray(v[0]) ? [v] : v; }
    case 'string[]': return __gxList(raw).map(String);
    case 'ListNode': return __gxBuildList(__gxList(raw));
    case 'TreeNode': { const t = __gxBuildTree(__gxList(raw)); if (ctx.tree === undefined) ctx.tree = t; return t; }
    case 'TreeNodeRef': return __gxFind(ctx.tree, __gxScalar(raw));
    default: return __gxScalar(raw);
  }
}
function __gxFmt(v, typ) {
  if (typ === 'TreeNodeVal') return v == null ? 'null' : String(v.val);
  if (v == null && (typ === 'ListNode' || typ === 'TreeNode')) return '';
  if (v === null || v === undefined) return 'null';
  if (typeof v === 'boolean') return v ? 'true' : 'false';
  if (v instanceof ListNode) { const o = []; let n = 0; while (v && n < 10000) { o.push(String(v.val)); v = v.next; n++; } return o.join(','); }
  if (v instanceof TreeNode) {
    const o = [], q = [v];
    while (q.length) { const n = q.shift(); if (!n) { o.push('null'); continue; } o.push(String(n.val)); q.push(n.left, n.right); }
    while (o.length && o[o.length - 1] === 'null') o.pop();
    return o.join(',');
  }
  if (Array.isArray(v)) {
    if (v.length && v.every(Array.isArray)) return v.map(r => r.map(x => __gxFmt(x)).join(',')).join('; ');
    return v.map(x => __gxFmt(x)).join(',');
  }
  return String(v);
}
function __gxFindFn(name) {
  const scope = { Solution: typeof Solution !== 'undefined' ? Solution : undefined };
  if (name) { try { const f = eval(name); if (typeof f === 'function') return f; } catch (e) {} }
  if (scope.Solution) {
    const inst = new scope.Solution();
    const proto = Object.getPrototypeOf(inst);
    const names = Object.getOwnPropertyNames(proto).filter(m => m !== 'constructor');
    const pick = name && names.includes(name) ? name : names[0];
    if (pick) return inst[pick].bind(inst);
  }
  if (__GX_DETECTED__) { try { const f = eval(__GX_DETECTED__); if (typeof f === 'function') return f; } catch (e) {} }
  return null;
}
(function main() {
  const data = require('fs').readFileSync(0, 'utf8').replace(/\r/g, '');
  const lines = data.split('\n');
  const params = __gxSig.params || [];
  while (lines.length > Math.max(1, params.length) && lines[lines.length - 1].trim() === '') lines.pop();
  const realLog = console.log; const captured = [];
  console.log = (...a) => captured.push(a.map(x => typeof x === 'string' ? x : JSON.stringify(x)).join(' '));
  let result, rtype = __gxSig.returns;
  try {
    if (__gxSig.design) {
      const ops = JSON.parse(lines[0]), argl = JSON.parse(lines[1]);
      const Cls = eval(__gxSig.design); let obj = null; result = [];
      ops.forEach((op, i) => { if (!obj) { obj = new Cls(...argl[i]); result.push(null); } else { const r = obj[op](...argl[i]); result.push(r === undefined ? null : r); } });
      rtype = null;
    } else {
      const fn = __gxFindFn(__gxSig.fn);
      if (!fn) { console.error('FUNCTION_NOT_FOUND: could not find your solution function' + (__gxSig.fn ? ` '${__gxSig.fn}'` : '')); process.exit(2); }
      const ctx = {}; const args = []; let idx = 0;
      if (params.length) {
        params.forEach(([_, typ], i) => {
          const remaining = params.length - i - 1;
          if (typ === 'char[][]') {
            const take = Math.max(1, lines.length - idx - remaining);
            args.push(lines.slice(idx, idx + take).filter(r => r.trim()).map(r => r.includes(',') ? r.trim().split(',') : r.trim().split('')));
            idx += take;
          } else { args.push(__gxConvert(idx < lines.length ? lines[idx] : '', typ, ctx)); idx++; }
        });
      } else {
        lines.filter(l => l.trim()).forEach(l => args.push(l.includes(',') || l.trim().startsWith('[') ? __gxList(l) : __gxScalar(l)));
      }
      result = fn(...args);
      if (result === undefined && (!rtype || rtype === 'void') && Array.isArray(args[0])) result = args[0];
    }
  } finally { console.log = realLog; }
  if (captured.length) process.stderr.write('__GX_STDOUT__' + captured.join('\n').slice(0, 4000));
  console.log(__GX_MARKER__ + __gxFmt(result, rtype));
})();
'''

JAVA_SUPPORT = r'''
class ListNode { int val; ListNode next; ListNode() {} ListNode(int val) { this.val = val; } ListNode(int val, ListNode next) { this.val = val; this.next = next; } }
class TreeNode { int val; TreeNode left; TreeNode right; TreeNode() {} TreeNode(int val) { this.val = val; } TreeNode(int val, TreeNode left, TreeNode right) { this.val = val; this.left = left; this.right = right; } }
'''

JAVA_RUNNER = r'''
public class SolutionRunner {
    static final String FN = __GX_FN__;
    static final String RET = __GX_RET__;
    static final String DESIGN = __GX_DESIGN__;
    static TreeNode firstTree = null;

    static String strip(String s) {
        s = s.trim();
        if (s.startsWith("[") && s.endsWith("]")) {
            int depth = 0;
            for (int i = 0; i < s.length(); i++) {
                char c = s.charAt(i); if (c == '[') depth++; if (c == ']') depth--;
                if (depth == 0 && i < s.length() - 1) return s;  // e.g. "[1,3],[2,6]"
            }
            s = s.substring(1, s.length() - 1);
        }
        return s.trim();
    }
    static String unq(String s) { s = s.trim(); if (s.length() >= 2 && s.startsWith("\"") && s.endsWith("\"")) return s.substring(1, s.length() - 1); return s; }
    static java.util.List<String> parts(String s) {
        s = strip(s); java.util.List<String> out = new java.util.ArrayList<>();
        if (s.isEmpty()) return out;
        int depth = 0; StringBuilder cur = new StringBuilder();
        for (char c : s.toCharArray()) {
            if (c == '[') depth++; if (c == ']') depth--;
            if (c == ',' && depth == 0) { out.add(cur.toString().trim()); cur.setLength(0); } else cur.append(c);
        }
        out.add(cur.toString().trim());
        return out;
    }
    static Integer[] boxed(String s) {
        java.util.List<String> p = parts(s); Integer[] a = new Integer[p.size()];
        for (int i = 0; i < a.length; i++) a[i] = p.get(i).equalsIgnoreCase("null") ? null : Integer.parseInt(p.get(i));
        return a;
    }
    static TreeNode tree(String s) {
        Integer[] v = boxed(s); if (v.length == 0 || v[0] == null) return null;
        TreeNode root = new TreeNode(v[0]); java.util.ArrayDeque<TreeNode> q = new java.util.ArrayDeque<>(); q.add(root); int i = 1;
        while (!q.isEmpty() && i < v.length) {
            TreeNode n = q.poll();
            if (i < v.length && v[i] != null) { n.left = new TreeNode(v[i]); q.add(n.left); } i++;
            if (i < v.length && v[i] != null) { n.right = new TreeNode(v[i]); q.add(n.right); } i++;
        }
        return root;
    }
    static TreeNode find(TreeNode r, int val) {
        java.util.ArrayDeque<TreeNode> st = new java.util.ArrayDeque<>(); if (r != null) st.push(r);
        while (!st.isEmpty()) { TreeNode n = st.pop(); if (n.val == val) return n; if (n.left != null) st.push(n.left); if (n.right != null) st.push(n.right); }
        return new TreeNode(val);
    }
    static Object convert(String s, Class<?> t) {
        if (t == int.class || t == Integer.class) return Integer.parseInt(s.trim());
        if (t == long.class || t == Long.class) return Long.parseLong(s.trim());
        if (t == double.class || t == Double.class) return Double.parseDouble(s.trim());
        if (t == boolean.class || t == Boolean.class) return Boolean.parseBoolean(s.trim());
        if (t == char.class) return s.trim().charAt(0);
        if (t == String.class) return unq(s);
        if (t == int[].class) { java.util.List<String> p = parts(s); int[] a = new int[p.size()]; for (int i = 0; i < a.length; i++) a[i] = Integer.parseInt(p.get(i)); return a; }
        if (t == long[].class) { java.util.List<String> p = parts(s); long[] a = new long[p.size()]; for (int i = 0; i < a.length; i++) a[i] = Long.parseLong(p.get(i)); return a; }
        if (t == double[].class) { java.util.List<String> p = parts(s); double[] a = new double[p.size()]; for (int i = 0; i < a.length; i++) a[i] = Double.parseDouble(p.get(i)); return a; }
        if (t == String[].class) { java.util.List<String> p = parts(s); String[] a = new String[p.size()]; for (int i = 0; i < a.length; i++) a[i] = unq(p.get(i)); return a; }
        if (t == int[][].class) { java.util.List<String> rows = parts(s); int[][] g = new int[rows.size()][]; for (int i = 0; i < g.length; i++) g[i] = (int[]) convert(rows.get(i), int[].class); return g; }
        if (t == java.util.List.class) { java.util.List<Integer> l = new java.util.ArrayList<>(); for (String p : parts(s)) l.add(Integer.parseInt(p)); return l; }
        if (t == ListNode.class) { ListNode d = new ListNode(), c = d; for (String p : parts(s)) { c.next = new ListNode(Integer.parseInt(p)); c = c.next; } return d.next; }
        if (t == TreeNode.class) {
            if (firstTree == null) { firstTree = tree(s); return firstTree; }
            return find(firstTree, Integer.parseInt(s.trim()));
        }
        return s;
    }
    static char[][] grid(java.util.List<String> rows) {
        java.util.List<char[]> out = new java.util.ArrayList<>();
        for (String r : rows) { r = r.trim(); if (r.isEmpty()) continue; out.add(r.contains(",") ? r.replace(",", "").toCharArray() : r.toCharArray()); }
        return out.toArray(new char[0][]);
    }
    static String fmt(Object o) {
        if (o == null) return (RET.equals("ListNode") || RET.equals("TreeNode")) ? "" : "null";
        if (RET.equals("TreeNodeVal") && o instanceof TreeNode) return String.valueOf(((TreeNode) o).val);
        if (o instanceof int[]) { int[] a = (int[]) o; StringBuilder b = new StringBuilder(); for (int i = 0; i < a.length; i++) { if (i > 0) b.append(','); b.append(a[i]); } return b.toString(); }
        if (o instanceof long[]) { long[] a = (long[]) o; StringBuilder b = new StringBuilder(); for (int i = 0; i < a.length; i++) { if (i > 0) b.append(','); b.append(a[i]); } return b.toString(); }
        if (o instanceof double[]) { double[] a = (double[]) o; StringBuilder b = new StringBuilder(); for (int i = 0; i < a.length; i++) { if (i > 0) b.append(','); b.append(a[i]); } return b.toString(); }
        if (o instanceof boolean[]) { boolean[] a = (boolean[]) o; StringBuilder b = new StringBuilder(); for (int i = 0; i < a.length; i++) { if (i > 0) b.append(','); b.append(a[i]); } return b.toString(); }
        if (o instanceof char[]) return new String((char[]) o);
        if (o instanceof Object[] && !(o instanceof int[][])) { Object[] a = (Object[]) o; StringBuilder b = new StringBuilder(); for (int i = 0; i < a.length; i++) { if (i > 0) b.append(a[i] instanceof Object[] || a[i] instanceof int[] || a[i] instanceof char[] ? "; " : ","); b.append(fmt(a[i])); } return b.toString(); }
        if (o instanceof int[][]) { int[][] g = (int[][]) o; StringBuilder b = new StringBuilder(); for (int i = 0; i < g.length; i++) { if (i > 0) b.append("; "); b.append(fmt(g[i])); } return b.toString(); }
        if (o instanceof java.util.List) {
            java.util.List<?> l = (java.util.List<?>) o; StringBuilder b = new StringBuilder();
            boolean nested = !l.isEmpty() && l.get(0) instanceof java.util.List;
            for (int i = 0; i < l.size(); i++) { if (i > 0) b.append(nested ? "; " : ","); b.append(fmt(l.get(i))); }
            return b.toString();
        }
        if (o instanceof ListNode) { StringBuilder b = new StringBuilder(); ListNode n = (ListNode) o; int c = 0; while (n != null && c++ < 10000) { if (b.length() > 0) b.append(','); b.append(n.val); n = n.next; } return b.toString(); }
        if (o instanceof TreeNode) {
            java.util.List<String> out = new java.util.ArrayList<>(); java.util.ArrayDeque<Object> q = new java.util.ArrayDeque<>(); q.add(o);
            java.util.LinkedList<TreeNode> lq = new java.util.LinkedList<>(); lq.add((TreeNode) o);
            while (!lq.isEmpty()) { TreeNode n = lq.poll(); if (n == null) { out.add("null"); continue; } out.add(String.valueOf(n.val)); lq.add(n.left); lq.add(n.right); }
            while (!out.isEmpty() && out.get(out.size() - 1).equals("null")) out.remove(out.size() - 1);
            return String.join(",", out);
        }
        if (o instanceof Double) { double d = (Double) o; return d == Math.rint(d) && !RET.equals("double") ? String.valueOf((long) d) : String.valueOf(d); }
        return String.valueOf(o);
    }
    public static void main(String[] argv) throws Exception {
        java.io.BufferedReader br = new java.io.BufferedReader(new java.io.InputStreamReader(System.in));
        java.util.List<String> lines = new java.util.ArrayList<>(); String l; while ((l = br.readLine()) != null) lines.add(l);
        java.io.PrintStream real = System.out; java.io.ByteArrayOutputStream captured = new java.io.ByteArrayOutputStream();
        System.setOut(new java.io.PrintStream(captured, true));
        String result;
        try {
            if (!DESIGN.isEmpty()) {
                result = runDesign(lines);
            } else {
                Class<?> solCls = Class.forName("Solution");
                java.lang.reflect.Method m = null;
                for (java.lang.reflect.Method x : solCls.getDeclaredMethods()) if (x.getName().equals(FN)) { m = x; break; }
                if (m == null) for (java.lang.reflect.Method x : solCls.getDeclaredMethods()) if (!java.lang.reflect.Modifier.isPrivate(x.getModifiers()) && !x.getName().equals("main")) { m = x; break; }
                if (m == null) { System.err.println("FUNCTION_NOT_FOUND: no method '" + FN + "' in class Solution"); System.exit(2); }
                m.setAccessible(true);
                Class<?>[] pt = m.getParameterTypes();
                while (lines.size() > Math.max(1, pt.length) && lines.get(lines.size() - 1).trim().isEmpty()) lines.remove(lines.size() - 1);
                Object[] args = new Object[pt.length]; int idx = 0;
                for (int i = 0; i < pt.length; i++) {
                    int remaining = pt.length - i - 1;
                    if (pt[i] == char[][].class) { int take = Math.max(1, lines.size() - idx - remaining); args[i] = grid(lines.subList(idx, Math.min(lines.size(), idx + take))); idx += take; continue; }
                    args[i] = convert(idx < lines.size() ? lines.get(idx) : "", pt[i]); idx++;
                }
                java.lang.reflect.Constructor<?> ctor = solCls.getDeclaredConstructor(); ctor.setAccessible(true);
                Object res = m.invoke(ctor.newInstance(), args);
                if (m.getReturnType() == void.class && args.length > 0) res = args[0];
                result = fmt(res);
            }
        } catch (java.lang.reflect.InvocationTargetException e) {
            System.setOut(real);
            Throwable c = e.getCause(); System.err.println("JAVA_RUNTIME_ERR:" + c.getClass().getSimpleName() + ": " + c.getMessage());
            for (StackTraceElement el : c.getStackTrace()) System.err.println("    at " + el);
            System.exit(1); return;
        } finally { System.setOut(real); }
        String u = captured.toString(); if (!u.isEmpty()) System.err.print("__GX_STDOUT__" + (u.length() > 4000 ? u.substring(0, 4000) : u));
        System.out.println(__GX_MARKER__ + result);
    }
    static String runDesign(java.util.List<String> lines) throws Exception {
        java.util.List<String> ops = parts(lines.get(0)); java.util.List<String> argl = parts(lines.get(1));
        Class<?> cls = Class.forName(DESIGN); Object obj = null; java.util.List<String> out = new java.util.ArrayList<>();
        for (int i = 0; i < ops.size(); i++) {
            String op = unq(ops.get(i)); java.util.List<String> a = parts(argl.get(i));
            if (obj == null) {
                java.lang.reflect.Constructor<?> c = cls.getDeclaredConstructors()[0]; c.setAccessible(true);
                Object[] ca = new Object[c.getParameterCount()]; for (int k = 0; k < ca.length; k++) ca[k] = convert(a.get(k), c.getParameterTypes()[k]);
                obj = c.newInstance(ca); out.add("null"); continue;
            }
            java.lang.reflect.Method m = null; for (java.lang.reflect.Method x : cls.getDeclaredMethods()) if (x.getName().equals(op) && x.getParameterCount() == a.size()) m = x;
            m.setAccessible(true);
            Object[] ma = new Object[m.getParameterCount()]; for (int k = 0; k < ma.length; k++) ma[k] = convert(a.get(k), m.getParameterTypes()[k]);
            Object r = m.invoke(obj, ma); out.add(r == null ? "null" : fmt(r));
        }
        return String.join(",", out);
    }
}
'''

CPP_PRELUDE = r'''#include <bits/stdc++.h>
using namespace std;
struct ListNode { int val; ListNode *next; ListNode() : val(0), next(nullptr) {} ListNode(int x) : val(x), next(nullptr) {} ListNode(int x, ListNode *n) : val(x), next(n) {} };
struct TreeNode { int val; TreeNode *left; TreeNode *right; TreeNode() : val(0), left(nullptr), right(nullptr) {} TreeNode(int x) : val(x), left(nullptr), right(nullptr) {} TreeNode(int x, TreeNode *l, TreeNode *r) : val(x), left(l), right(r) {} };
'''

CPP_HELPERS = r'''
// ───────── GapX test runner ─────────
static string gx_trim(string s) { size_t a = s.find_first_not_of(" \t\r\n"); if (a == string::npos) return ""; size_t b = s.find_last_not_of(" \t\r\n"); return s.substr(a, b - a + 1); }
static string gx_strip(string s) {
    s = gx_trim(s);
    if (s.size() >= 2 && s.front() == '[' && s.back() == ']') {
        int depth = 0;
        for (size_t i = 0; i < s.size(); i++) { if (s[i] == '[') depth++; if (s[i] == ']') depth--; if (depth == 0 && i + 1 < s.size()) return s; }
        s = s.substr(1, s.size() - 2);
    }
    return gx_trim(s);
}
static string gx_unq(string s) { s = gx_trim(s); if (s.size() >= 2 && s.front() == '"' && s.back() == '"') return s.substr(1, s.size() - 2); return s; }
static vector<string> gx_parts(string s) {
    s = gx_strip(s); vector<string> out; if (s.empty()) return out;
    int depth = 0; string cur;
    for (char c : s) { if (c == '[') depth++; if (c == ']') depth--; if (c == ',' && depth == 0) { out.push_back(gx_trim(cur)); cur.clear(); } else cur += c; }
    out.push_back(gx_trim(cur)); return out;
}
template <typename T> T gx_parse(const string& s);
template <> int gx_parse<int>(const string& s) { return stoi(gx_trim(s)); }
template <> long long gx_parse<long long>(const string& s) { return stoll(gx_trim(s)); }
template <> long gx_parse<long>(const string& s) { return stol(gx_trim(s)); }
template <> double gx_parse<double>(const string& s) { return stod(gx_trim(s)); }
template <> bool gx_parse<bool>(const string& s) { return gx_trim(s) == "true"; }
template <> char gx_parse<char>(const string& s) { return gx_trim(s)[0]; }
template <> string gx_parse<string>(const string& s) { return gx_unq(s); }
template <> vector<int> gx_parse<vector<int>>(const string& s) { vector<int> v; for (auto& p : gx_parts(s)) v.push_back(stoi(p)); return v; }
template <> vector<long long> gx_parse<vector<long long>>(const string& s) { vector<long long> v; for (auto& p : gx_parts(s)) v.push_back(stoll(p)); return v; }
template <> vector<double> gx_parse<vector<double>>(const string& s) { vector<double> v; for (auto& p : gx_parts(s)) v.push_back(stod(p)); return v; }
template <> vector<string> gx_parse<vector<string>>(const string& s) { vector<string> v; for (auto& p : gx_parts(s)) v.push_back(gx_unq(p)); return v; }
template <> vector<vector<int>> gx_parse<vector<vector<int>>>(const string& s) { vector<vector<int>> g; for (auto& r : gx_parts(s)) g.push_back(gx_parse<vector<int>>(r)); return g; }
template <> ListNode* gx_parse<ListNode*>(const string& s) { ListNode d; ListNode* c = &d; for (auto& p : gx_parts(s)) { c->next = new ListNode(stoi(p)); c = c->next; } return d.next; }
static TreeNode* gx_first_tree = nullptr; static bool gx_has_tree = false;
static TreeNode* gx_find(TreeNode* r, int v) { vector<TreeNode*> st; if (r) st.push_back(r); while (!st.empty()) { auto n = st.back(); st.pop_back(); if (n->val == v) return n; if (n->left) st.push_back(n->left); if (n->right) st.push_back(n->right); } return new TreeNode(v); }
template <> TreeNode* gx_parse<TreeNode*>(const string& s) {
    if (gx_has_tree) return gx_find(gx_first_tree, stoi(gx_trim(s)));
    auto p = gx_parts(s); gx_has_tree = true;
    if (p.empty() || p[0] == "null") return gx_first_tree = nullptr;
    TreeNode* root = new TreeNode(stoi(p[0])); deque<TreeNode*> q{root}; size_t i = 1;
    while (!q.empty() && i < p.size()) {
        auto n = q.front(); q.pop_front();
        if (i < p.size() && p[i] != "null") { n->left = new TreeNode(stoi(p[i])); q.push_back(n->left); } i++;
        if (i < p.size() && p[i] != "null") { n->right = new TreeNode(stoi(p[i])); q.push_back(n->right); } i++;
    }
    return gx_first_tree = root;
}
static vector<vector<char>> gx_grid(const vector<string>& rows) { vector<vector<char>> g; for (auto r : rows) { r = gx_trim(r); if (r.empty()) continue; vector<char> row; for (char c : r) if (c != ',') row.push_back(c); g.push_back(row); } return g; }
static string gx_fmt(int v) { return to_string(v); }
static string gx_fmt(long v) { return to_string(v); }
static string gx_fmt(long long v) { return to_string(v); }
static string gx_fmt(double v) { ostringstream o; o << setprecision(10) << v; return o.str(); }
static string gx_fmt(bool v) { return v ? "true" : "false"; }
static string gx_fmt(char v) { return string(1, v); }
static string gx_fmt(const string& v) { return v; }
static string gx_fmt(ListNode* n) { string o; int c = 0; while (n && c++ < 10000) { if (!o.empty()) o += ","; o += to_string(n->val); n = n->next; } return o; }
static string gx_fmt(TreeNode* r) {
    if (__GX_RET_VAL__) return r ? to_string(r->val) : "null";
    vector<string> out; deque<TreeNode*> q{r};
    while (!q.empty()) { auto n = q.front(); q.pop_front(); if (!n) { out.push_back("null"); continue; } out.push_back(to_string(n->val)); q.push_back(n->left); q.push_back(n->right); }
    while (!out.empty() && out.back() == "null") out.pop_back();
    string s; for (size_t i = 0; i < out.size(); i++) { if (i) s += ","; s += out[i]; } return s;
}
template <typename T> static string gx_fmt(const vector<T>& v);
template <typename T> static string gx_fmt(const vector<vector<T>>& v) { string s; for (size_t i = 0; i < v.size(); i++) { if (i) s += "; "; s += gx_fmt(v[i]); } return s; }
template <typename T> static string gx_fmt(const vector<T>& v) { string s; for (size_t i = 0; i < v.size(); i++) { if (i) s += ","; s += gx_fmt(v[i]); } return s; }
'''

CPP_TYPE_MAP = {
    "int": "int", "long": "long", "long long": "long long", "double": "double", "bool": "bool", "char": "char", "string": "string",
    "vector<int>": "vector<int>", "vector<long long>": "vector<long long>", "vector<double>": "vector<double>",
    "vector<string>": "vector<string>", "vector<vector<int>>": "vector<vector<int>>", "vector<vector<char>>": "vector<vector<char>>",
    "vector<vector<string>>": "vector<vector<string>>", "ListNode*": "ListNode*", "TreeNode*": "TreeNode*", "void": "void",
}


def _normalize_cpp_type(t: str) -> str:
    t = re.sub(r"\bconst\b", "", t).replace("&", "").replace("std::", "")
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"\s*([<>,*])\s*", r"\1", t)
    return t


def _parse_cpp_signature(code: str, fn: Optional[str]) -> Optional[Tuple[str, str, List[str]]]:
    body = code[code.find("class Solution"):] if "class Solution" in code else code
    pattern = re.compile(r"([\w:<>,\s\*&]+?)\s+(\w+)\s*\(([^)]*)\)\s*(?:const\s*)?\{")
    for m in pattern.finditer(body):
        ret, name, params = m.group(1).strip(), m.group(2), m.group(3)
        if name in ("if", "for", "while", "switch") or (fn and name != fn):
            continue
        ret = _normalize_cpp_type(re.sub(r"^.*\b(public|private|protected)\s*:\s*", "", ret, flags=re.S).strip())
        if not ret or ret in (",", ":"):
            continue
        ptypes = []
        for p in [x for x in params.split(",") if x.strip()] if "<" not in params else _split_cpp_params(params):
            p = p.strip()
            name_match = re.match(r"(.+?)([\w]+)$", p)
            ptypes.append(_normalize_cpp_type(name_match.group(1) if name_match else p))
        return ret, name, ptypes
    return None


def _split_cpp_params(params: str) -> List[str]:
    out, depth, cur = [], 0, ""
    for ch in params:
        if ch == "<": depth += 1
        if ch == ">": depth -= 1
        if ch == "," and depth == 0:
            out.append(cur); cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def _cpp_main(ret: str, name: str, ptypes: List[str]) -> str:
    lines = ["int main() {", "    ios::sync_with_stdio(false);", "    vector<string> lines; string line; while (getline(cin, line)) lines.push_back(line);",
             f"    while ((int)lines.size() > max(1, {len(ptypes)}) && gx_trim(lines.back()).empty()) lines.pop_back();",
             "    size_t idx = 0; auto next = [&]() { return idx < lines.size() ? lines[idx++] : string(); };"]
    for i, t in enumerate(ptypes):
        remaining = len(ptypes) - i - 1
        if t == "vector<vector<char>>":
            lines.append(f"    size_t take{i} = max<long>(1, (long)lines.size() - (long)idx - {remaining});")
            lines.append(f"    vector<string> rows{i}(lines.begin() + idx, lines.begin() + min(lines.size(), idx + take{i})); idx += take{i};")
            lines.append(f"    vector<vector<char>> a{i} = gx_grid(rows{i});")
        else:
            lines.append(f"    {t} a{i} = gx_parse<{t}>(next());")
    args = ", ".join(f"a{i}" for i in range(len(ptypes)))
    lines.append("    Solution sol;")
    lines.append("    streambuf* real = cout.rdbuf(); ostringstream captured; cout.rdbuf(captured.rdbuf());")
    if ret == "void":
        lines.append(f"    sol.{name}({args});")
        lines.append("    cout.rdbuf(real);")
        lines.append(f"    string result = gx_fmt(a0);" if ptypes else "    string result = \"null\";")
    else:
        lines.append(f"    auto res = sol.{name}({args});")
        lines.append("    cout.rdbuf(real);")
        lines.append("    string result = gx_fmt(res);")
    lines.append("    if (!captured.str().empty()) cerr << \"__GX_STDOUT__\" << captured.str().substr(0, 4000);")
    lines.append("    cout << __GX_MARKER__ << result << endl;")
    lines.append("    return 0;")
    lines.append("}")
    return "\n".join(lines)


def _js_detect_fn(code: str) -> Optional[str]:
    m = re.search(r"(?:var|let|const)\s+(\w+)\s*=\s*(?:async\s*)?(?:function\b|\()", code) or re.search(r"function\s+(\w+)\s*\(", code)
    return m.group(1) if m else None


def build_program(code: str, language: str, signature: Optional[Dict[str, Any]]) -> Tuple[str, str]:
    """Returns (source, filename) of a runnable program wrapping the user's code."""
    sig = signature or {}
    sig_json = json.dumps(json.dumps(sig))
    marker = json.dumps(MARKER)
    if language == "python":
        source = PY_PRELUDE + "\n" + code + "\n" + PY_RUNNER.replace("__GX_SIG__", sig_json).replace("__GX_MARKER__", marker)
        return source, "solution.py"
    if language == "javascript":
        detected = json.dumps(_js_detect_fn(code))
        source = code + "\n" + JS_RUNNER.replace("__GX_SIG__", sig_json).replace("__GX_MARKER__", marker).replace("__GX_DETECTED__", detected)
        return source, "solution.js"
    if language == "java":
        support = JAVA_SUPPORT
        if re.search(r"\bclass\s+ListNode\b", code):
            support = support.replace(support.splitlines()[1], "")
        if re.search(r"\bclass\s+TreeNode\b", code):
            support = support.replace(support.splitlines()[2], "")
        imports = "import java.util.*;\nimport java.io.*;\n"
        user = re.sub(r"\bpublic\s+class\s+Solution\b", "class Solution", code)
        runner = (JAVA_RUNNER.replace("__GX_FN__", json.dumps(sig.get("fn") or "")).replace("__GX_RET__", json.dumps(sig.get("returns") or ""))
                  .replace("__GX_DESIGN__", json.dumps(sig.get("design") or "")).replace("__GX_MARKER__", marker))
        return imports + user + "\n" + support + runner, "SolutionRunner.java"
    if language == "cpp":
        if sig.get("design"):
            raise ValueError("Design problems aren't supported by the C++ runner yet. Please use Python, Java or JavaScript for this one.")
        parsed = _parse_cpp_signature(code, sig.get("fn"))
        if not parsed:
            raise ValueError("Couldn't find your solution method inside `class Solution { public: ... }`.")
        ret, name, ptypes = parsed
        unknown = [t for t in [ret] + ptypes if t not in CPP_TYPE_MAP]
        if unknown:
            raise ValueError(f"The C++ runner doesn't support the type(s) {', '.join(unknown)} yet. Please use Python, Java or JavaScript.")
        user = re.sub(r"#include\s*<[^>]+>\s*", "", code).replace("using namespace std;", "")
        user = re.sub(r"struct\s+(ListNode|TreeNode)\s*\{[^}]*\};", "", user)
        helpers = CPP_HELPERS.replace("__GX_RET_VAL__", "true" if sig.get("returns") == "TreeNodeVal" else "false")
        source = CPP_PRELUDE + helpers + "\n" + user + "\n" + _cpp_main(ret, name, ptypes).replace("__GX_MARKER__", C_MARKER_LITERAL)
        return source, "solution.cpp"
    if language == "c":
        from app.services.c_support import build_c_program
        return build_c_program(code, sig, C_MARKER_LITERAL), "solution.c"
    raise ValueError(f"Unsupported language: {language}")


# ═════════════════════════════ OUTPUT COMPARISON ═════════════════════════════
def _norm(s: str) -> str:
    s = (s or "").replace("\r", "").strip().lower()
    s = re.sub(r"\s+", "", s)
    s = s.replace("],[", ";").replace("[", "").replace("]", "").replace('"', "").replace("'", "")
    return s


def outputs_match(actual: str, expected: str, unordered: bool = False) -> bool:
    if " || " in (expected or ""):  # several valid answers
        return any(outputs_match(actual, alt, unordered) for alt in expected.split(" || "))
    a, e = _norm(actual), _norm(expected)
    if a == e:
        return True
    try:
        return abs(float(a) - float(e)) <= 1e-5
    except ValueError:
        pass
    # Problems whose answer is a collection of groups accept any order (e.g. 3Sum, Group Anagrams, Subsets)
    if ";" in a or ";" in e:
        ga = sorted(",".join(sorted(g.split(","))) for g in a.split(";"))
        ge = sorted(",".join(sorted(g.split(","))) for g in e.split(";"))
        return ga == ge
    if unordered:
        return sorted(a.split(",")) == sorted(e.split(","))
    return False


# ═════════════════════════════ EXECUTION ═════════════════════════════
def _limits():  # pragma: no cover - POSIX only
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
    resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, 1024 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
    os.setsid()


def _run(cmd: List[str], cwd: str, stdin: str = "", timeout: float = TIME_LIMIT) -> subprocess.CompletedProcess:
    """Runs a command in a scratch directory with a minimal environment, a time limit and output caps."""
    env = {k: v for k, v in os.environ.items() if k.upper() in ("PATH", "SYSTEMROOT", "TEMP", "TMP", "JAVA_HOME", "HOME", "USERPROFILE", "LANG", "PATHEXT", "COMSPEC")}
    env["PYTHONIOENCODING"] = "utf-8"
    kwargs: Dict[str, Any] = {"cwd": cwd, "input": stdin, "capture_output": True, "text": True, "timeout": timeout,
                              "env": env, "encoding": "utf-8", "errors": "replace"}
    if os.name == "posix":
        kwargs["preexec_fn"] = _limits
    elif os.name == "nt":
        kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    # On Windows, antivirus briefly locks a freshly compiled .exe while scanning it ("Access is denied").
    # Wait a moment and try again instead of failing the student's run.
    for attempt in range(10):
        try:
            proc = subprocess.run(cmd, **kwargs)
            break
        except PermissionError:
            if os.name != "nt" or attempt == 9:
                raise
            time.sleep(0.2 + 0.2 * attempt)
    proc.stdout = (proc.stdout or "")[:MAX_OUTPUT]
    proc.stderr = (proc.stderr or "")[:MAX_OUTPUT]
    return proc


def _split_output(stdout: str, stderr: str) -> Tuple[Optional[str], str, str]:
    """Separates the program's result (after the marker) from user prints and errors."""
    user_stdout = ""
    if "__GX_STDOUT__" in stderr:
        stderr, _, user_stdout = stderr.partition("__GX_STDOUT__")
    result = None
    if MARKER in stdout:
        before, _, after = stdout.rpartition(MARKER)
        result = after.strip()
        user_stdout = (before + user_stdout).strip()
    return result, user_stdout.strip(), stderr.strip()


class CodeExecutionService:

    @staticmethod
    def execute_code(code: str, language: str, test_cases: List[Dict[str, Any]],
                     signature: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        lang = LANG_ALIASES.get((language or "").lower().strip(), (language or "").lower().strip())
        if lang not in SUPPORTED:
            return CodeExecutionService._error("Unsupported Language", f"'{language}' isn't supported. Choose Python, JavaScript, Java or C++.")
        if not test_cases:
            return CodeExecutionService._error("No Test Cases", "This problem has no test cases configured.")
        if CodeExecutionService.is_unimplemented(code):
            return CodeExecutionService._unimplemented(test_cases)
        if lang == "python":
            syntax = CodeExecutionService._check_python_syntax(code)
            if syntax:
                return CodeExecutionService._compile_error(syntax, test_cases)

        try:
            source, filename = build_program(code, lang, signature)
        except ValueError as e:
            return CodeExecutionService._error("Unsupported Signature", str(e))

        if settings.JUDGE0_API_KEY:
            try:
                return CodeExecutionService._run_via_judge0(source, lang, test_cases, code, signature)
            except Exception:
                if not local_execution_allowed():
                    return CodeExecutionService._error("Execution Unavailable", "The code execution service is temporarily unavailable. Please try again.")
        if not local_execution_allowed():
            return CodeExecutionService._error("Execution Unavailable", "Code execution isn't configured on this server (set JUDGE0_API_KEY).")
        return CodeExecutionService._run_locally(source, filename, lang, test_cases, code, signature)

    # ---------- local ----------
    @staticmethod
    def _run_locally(source: str, filename: str, lang: str, test_cases: List[Dict[str, Any]], user_code: str, signature: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        tool = {"python": sys.executable, "javascript": shutil.which("node"), "java": shutil.which("javac"),
                "cpp": shutil.which("g++"), "c": shutil.which("gcc")}[lang]
        if not tool:
            name = {"javascript": "Node.js", "java": "a Java JDK (javac)", "cpp": "a C++ compiler (g++)", "c": "a C compiler (gcc)"}[lang]
            return CodeExecutionService._error("Runtime Not Installed", f"{name} isn't installed on the server, so {lang} code can't run here. Install it, configure Judge0, or pick another language.")

        workdir = tempfile.mkdtemp(prefix="gapx_run_")
        try:
            path = os.path.join(workdir, filename)
            with open(path, "w", encoding="utf-8") as f:
                f.write(source)

            if lang == "python":
                cmd = [sys.executable, "-I", path]
            elif lang == "javascript":
                cmd = [tool, path]
            elif lang == "java":
                comp = _run([tool, "-encoding", "UTF-8", "-nowarn", filename], workdir, timeout=COMPILE_LIMIT)
                if comp.returncode != 0:
                    return CodeExecutionService._compile_error(CodeExecutionService._java_compile_details(comp.stderr, source, user_code), test_cases)
                java_exe = os.path.join(os.path.dirname(tool), "java.exe" if os.name == "nt" else "java")
                cmd = [java_exe if os.path.exists(java_exe) else (shutil.which("java") or "java"), "-Xmx256m", "-cp", workdir, "SolutionRunner"]
            else:
                exe = os.path.join(workdir, "solution.exe" if os.name == "nt" else "solution")
                flags = ["-std=c11", "-O2", "-o", exe, path, "-lm"] if lang == "c" else ["-std=c++17", "-O2", "-o", exe, path]
                comp = _run([tool] + flags, workdir, timeout=COMPILE_LIMIT)
                if comp.returncode != 0:
                    return CodeExecutionService._compile_error(CodeExecutionService._cpp_compile_details(comp.stderr, source, user_code), test_cases)
                cmd = [exe]

            results, first_error, status, total_ms = [], None, "Accepted", 0.0
            for idx, tc in enumerate(test_cases):
                stdin = str(tc.get("input", ""))
                expected = str(tc.get("output", "")).strip()
                start = time.perf_counter()
                try:
                    proc = _run(cmd, workdir, stdin=stdin)
                    elapsed = (time.perf_counter() - start) * 1000
                    total_ms += elapsed
                    result, user_out, err = _split_output(proc.stdout, proc.stderr)
                    if proc.returncode != 0 or result is None:
                        details = CodeExecutionService._runtime_details(lang, err or proc.stdout, user_code, stdin)
                        case_status, actual = "Runtime Error", f"{details['error_type']}: {details.get('error_message', '')}".strip(": ")
                    elif outputs_match(result, expected, bool((signature or {}).get("unordered"))):
                        case_status, actual, details = "Accepted", result, None
                    else:
                        case_status, actual = "Wrong Answer", result or "(empty)"
                        details = {"error_type": "Wrong Answer", "line_number": None, "failed_test_case_index": idx + 1,
                                   "input": stdin if not tc.get("is_hidden") else "(hidden test case)",
                                   "expected_output": expected if not tc.get("is_hidden") else "(hidden)",
                                   "actual_output": actual if not tc.get("is_hidden") else "(hidden)",
                                   "explanation": (f"Test case {idx + 1}: your code returned `{actual}` but `{expected}` was expected."
                                                   if not tc.get("is_hidden") else f"Hidden test case {idx + 1} failed. Check edge cases such as empty input, duplicates, negatives and large values."),
                                   "raw_trace": "" if tc.get("is_hidden") else f"Input:\n{stdin}\n\nYour output: {actual}\nExpected: {expected}"}
                except subprocess.TimeoutExpired:
                    case_status, actual, user_out = "Time Limit Exceeded", f"Time Limit Exceeded (> {TIME_LIMIT:g}s)", ""
                    total_ms += TIME_LIMIT * 1000
                    details = {"error_type": "Time Limit Exceeded", "line_number": None, "failed_test_case_index": idx + 1,
                               "explanation": f"Your code took longer than {TIME_LIMIT:g} seconds. Look for infinite loops or a faster algorithm.",
                               "raw_trace": "Process killed after exceeding the time limit."}

                if case_status != "Accepted" and status == "Accepted":
                    status = case_status
                if details and first_error is None:
                    first_error = details
                results.append(CodeExecutionService._case(idx, tc, stdin, expected, actual, case_status, user_out))

            return CodeExecutionService._summary(status, results, first_error, total_ms)
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    # ---------- Judge0 ----------
    @staticmethod
    def _run_via_judge0(source: str, lang: str, test_cases: List[Dict[str, Any]], user_code: str, signature: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        lang_ids = {"python": 71, "javascript": 63, "cpp": 54, "java": 62, "c": 50}
        headers = {"X-RapidAPI-Key": settings.JUDGE0_API_KEY, "X-RapidAPI-Host": "judge0-ce.p.rapidapi.com", "Content-Type": "application/json"}
        if lang == "java":  # Judge0 expects the public class to be called Main
            source = source.replace("public class SolutionRunner", "public class Main")
        results, first_error, status, total_ms = [], None, "Accepted", 0.0
        for idx, tc in enumerate(test_cases):
            stdin = str(tc.get("input", ""))
            expected = str(tc.get("output", "")).strip()
            resp = requests.post(f"{settings.JUDGE0_API_URL}/submissions?base64_encoded=false&wait=true",
                                 json={"source_code": source, "language_id": lang_ids[lang], "stdin": stdin, "cpu_time_limit": TIME_LIMIT},
                                 headers=headers, timeout=20)
            if resp.status_code not in (200, 201):
                raise RuntimeError("Judge0 submission failed")
            data = resp.json()
            j_status = (data.get("status") or {}).get("description", "")
            total_ms += float(data.get("time") or 0) * 1000
            result, user_out, err = _split_output(data.get("stdout") or "", (data.get("stderr") or "") + (data.get("compile_output") or ""))
            details = None
            if "Compilation" in j_status:
                return CodeExecutionService._compile_error({"error_type": "Compile Error", "line_number": None, "explanation": "Your code didn't compile.", "raw_trace": err}, test_cases)
            if "Time Limit" in j_status:
                case_status, actual = "Time Limit Exceeded", "Time Limit Exceeded"
                details = {"error_type": "Time Limit Exceeded", "explanation": "Your code exceeded the time limit.", "raw_trace": ""}
            elif result is None:
                details = CodeExecutionService._runtime_details(lang, err, user_code, stdin)
                case_status, actual = "Runtime Error", details["error_type"]
            elif outputs_match(result, expected, bool((signature or {}).get("unordered"))):
                case_status, actual = "Accepted", result
            else:
                case_status, actual = "Wrong Answer", result
                details = {"error_type": "Wrong Answer", "failed_test_case_index": idx + 1,
                           "explanation": f"Test case {idx + 1} returned a different answer.", "raw_trace": ""}
            if case_status != "Accepted" and status == "Accepted":
                status = case_status
            if details and first_error is None:
                first_error = details
            results.append(CodeExecutionService._case(idx, tc, stdin, expected, actual, case_status, user_out))
        return CodeExecutionService._summary(status, results, first_error, total_ms)

    # ---------- result helpers ----------
    @staticmethod
    def _case(idx, tc, stdin, expected, actual, status, user_out) -> Dict[str, Any]:
        hidden = bool(tc.get("is_hidden"))
        return {"test_case_index": idx, "is_hidden": hidden, "passed": status == "Accepted",
                "input": "(hidden test case)" if hidden else stdin, "expected": "(hidden)" if hidden else expected,
                "actual": ("(hidden)" if hidden and status == "Accepted" else actual), "status": status,
                "stdout": "" if hidden else (user_out or "")[:2000]}

    @staticmethod
    def _summary(status: str, results: List[Dict[str, Any]], first_error: Optional[Dict[str, Any]], total_ms: float) -> Dict[str, Any]:
        passed = sum(1 for r in results if r["passed"])
        if status == "Accepted":
            message = f"All {len(results)} test cases passed!"
        elif status == "Wrong Answer":
            message = f"Wrong Answer: {passed}/{len(results)} test cases passed."
        else:
            message = f"{status}: {passed}/{len(results)} test cases passed."
        return {"status": status, "execution_time": round(total_ms / max(1, len(results)), 2), "memory_usage": 0.0,
                "message": message, "test_results": results, "error_details": first_error}

    @staticmethod
    def _error(kind: str, message: str) -> Dict[str, Any]:
        return {"status": kind, "execution_time": 0.0, "memory_usage": 0.0, "message": message, "test_results": [],
                "error_details": {"error_type": kind, "line_number": None, "explanation": message, "raw_trace": ""}}

    @staticmethod
    def _compile_error(details: Dict[str, Any], test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        msg = details.get("error_message") or details.get("explanation") or "Compilation failed"
        line = details.get("line_number")
        return {"status": "Compile Error", "execution_time": 0.0, "memory_usage": 0.0,
                "message": f"Compile Error{f' (line {line})' if line else ''}: {msg}"[:300], "test_results": [], "error_details": details}

    @staticmethod
    def _unimplemented(test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        first = test_cases[0] if test_cases else {}
        return {"status": "Wrong Answer", "execution_time": 0.0, "memory_usage": 0.0,
                "message": "No implementation yet: your function still contains only the starter template.",
                "test_results": [{"test_case_index": 0, "is_hidden": False, "passed": False, "input": first.get("input", ""),
                                  "expected": first.get("output", ""), "actual": "(no implementation)", "status": "Wrong Answer", "stdout": ""}],
                "error_details": {"error_type": "Incomplete Implementation", "line_number": None,
                                  "explanation": "Write your solution inside the function body, then run the test cases.", "raw_trace": ""}}

    @staticmethod
    def is_unimplemented(code: str) -> bool:
        """True when the code is empty or is just a starter template with no logic."""
        if not code or not code.strip():
            return True
        lines = [l.strip() for l in code.splitlines() if l.strip() and not l.strip().startswith(("#", "//", "/*", "*", "*/"))]
        clean = " ".join(lines)
        if not clean:
            return True
        patterns = [
            r"^class\s+Solution\s*:\s*def\s+\w+\s*\(.*?\)\s*(->\s*[^:]+)?\s*:\s*(pass|return\s*(None|\[\]|\{\}|0|False|-1|\"\"|''))\s*$",
            r"^(var|let|const)\s+\w+\s*=\s*function\s*\(.*?\)\s*\{\s*\}\s*;?\s*$",
            r"^(import\s+[^;]+;\s*)*(public\s+)?class\s+Solution\s*\{\s*public\s+[^{]+\{\s*(return\s+(null|false|0|-1|new\s+int\[\]\s*\{\s*\}|new\s+ArrayList<>\(\)|\"\")\s*;)?\s*\}\s*\}\s*$",
            r"^(#include\s*<[^>]+>\s*)*(using\s+namespace\s+std;\s*)?class\s+Solution\s*\{\s*public:\s*[^{]+\{\s*(return\s+(\{\}|false|0|-1|nullptr|\"\")\s*;)?\s*\}\s*\};\s*$",
            # C starter: a single function whose body only resets *returnSize and returns a default
            r"^(#include\s*<[^>]+>\s*)*[\w\s\*]+?\b\w+\s*\([^)]*\)\s*\{\s*(\*returnSize\s*=\s*0\s*;\s*)?(return\s+(NULL|0|0\.0|false|-1|\"\")\s*;)?\s*\}\s*$",
        ]
        return any(re.match(p, clean, re.DOTALL) for p in patterns)

    # ---------- diagnostics ----------
    @staticmethod
    def _check_python_syntax(code: str) -> Optional[Dict[str, Any]]:
        try:
            ast.parse(code)
            return None
        except SyntaxError as e:
            lines = code.split("\n")
            idx = (e.lineno - 1) if e.lineno and e.lineno <= len(lines) else 0
            err_line = lines[idx] if idx < len(lines) else ""
            return {"error_type": type(e).__name__, "line_number": e.lineno or 1, "column_offset": e.offset or 1, "line_code": err_line,
                    "error_message": e.msg, "explanation": CodeExecutionService._explain_syntax_error(e.msg, err_line, e.lineno),
                    "raw_trace": f'  File "solution.py", line {e.lineno}\n    {err_line}\n    {" " * max(0, (e.offset or 1) - 1)}^\nSyntaxError: {e.msg}'}

    @staticmethod
    def _explain_syntax_error(msg: str, line_code: str, lineno: Optional[int]) -> str:
        low = msg.lower()
        if "expected ':'" in low or ("invalid syntax" in low and re.search(r"\b(if|elif|else|for|while|def|class|try|except|with)\b", line_code) and not line_code.rstrip().endswith(":")):
            return f"Line {lineno}: missing ':' at the end of this statement."
        if "never closed" in low or "unclosed" in low or "unmatched" in low:
            return f"Line {lineno}: a bracket or quote isn't closed. Check that every (, [, {{ and quote has a matching pair."
        if "indent" in low:
            return f"Line {lineno}: indentation problem. Blocks inside functions, loops and if-statements must be indented consistently."
        return f"Line {lineno}: {msg}."

    @staticmethod
    def _explain_runtime_error(error_type: str, error_msg: str, line_num: Optional[int], test_input: str) -> str:
        where = f"Line {line_num}: " if line_num else ""
        hints = {
            "IndexError": "an index is out of range. Check loop bounds (i < len(nums)) and accesses like i + 1 or i - 1.",
            "KeyError": f"key {error_msg} isn't in the dictionary. Use `if key in d` or d.get(key, default).",
            "ZeroDivisionError": "division by zero. Guard denominators before dividing or using %.",
            "TypeError": f"type mismatch ({error_msg}). Check the types of your variables and return value.",
            "NameError": f"{error_msg}. A variable or function is used before it's defined.",
            "AttributeError": f"{error_msg}. You're probably accessing a property of None (e.g. node.next when node is None).",
            "RecursionError": "maximum recursion depth exceeded. Check your base case.",
            "ArrayIndexOutOfBoundsException": "an array index is out of bounds. Check your loop limits.",
            "NullPointerException": "you used a null reference. Check for null before accessing fields such as node.next.",
            "StringIndexOutOfBoundsException": "a string index is out of range.",
            "ArithmeticException": "arithmetic error, usually division by zero.",
            "StackOverflowError": "infinite or very deep recursion. Check your base case.",
            "TypeError (JS)": "you called something that isn't a function or read a property of undefined/null.",
        }
        return where + hints.get(error_type, f"{error_type}: {error_msg}")

    @staticmethod
    def _runtime_details(lang: str, err: str, user_code: str, stdin: str) -> Dict[str, Any]:
        err = err or ""
        user_lines = user_code.split("\n")
        error_type, message, line_num = "Runtime Error", err.strip().splitlines()[-1] if err.strip() else "Program exited without output", None
        if "FUNCTION_NOT_FOUND" in err:
            return {"error_type": "Function Not Found", "error_message": err.split("FUNCTION_NOT_FOUND:")[-1].strip(), "line_number": None,
                    "explanation": "Keep the function name and class from the starter code so the test runner can call it.", "raw_trace": err}
        if lang == "python":
            last = err.strip().splitlines()[-1] if err.strip() else ""
            if ":" in last:
                error_type, message = [x.strip() for x in last.split(":", 1)]
            elif last:
                error_type = last.strip()
            prelude = PY_PRELUDE.count("\n") + 1
            for m in reversed(list(re.finditer(r'File ".*?solution\.py", line (\d+)', err))):
                ln = int(m.group(1)) - prelude
                if 1 <= ln <= len(user_lines):
                    line_num = ln
                    break
            if "MemoryError" in err:
                error_type = "Memory Limit Exceeded"
        elif lang == "javascript":
            m = re.search(r"^(\w*Error): (.*)$", err, re.M)
            if m:
                error_type, message = m.group(1), m.group(2)
            ml = re.search(r"solution\.js:(\d+)", err)
            if ml and int(ml.group(1)) <= len(user_lines):
                line_num = int(ml.group(1))
        elif lang == "java":
            m = re.search(r"JAVA_RUNTIME_ERR:(\w+): ?(.*)", err)
            if m:
                error_type, message = m.group(1), m.group(2)
            ml = re.search(r"Solution\.\w+\(SolutionRunner\.java:(\d+)\)", err)
            if ml:
                line_num = max(1, int(ml.group(1)) - 2)
        else:
            if "Segmentation" in err or not err:
                error_type, message = "Runtime Error", "your program crashed (segmentation fault, null pointer or out-of-bounds access)."
        line_code = user_lines[line_num - 1] if line_num and line_num <= len(user_lines) else ""
        return {"error_type": error_type, "error_message": message, "line_number": line_num, "line_code": line_code,
                "explanation": CodeExecutionService._explain_runtime_error(error_type, message, line_num, stdin),
                "raw_trace": re.sub(r'File ".*?solution\.py"', 'File "solution.py"', err)[-3000:]}

    @staticmethod
    def _java_compile_details(stderr: str, source: str, user_code: str) -> Dict[str, Any]:
        offset = source.find(user_code[:40]) if user_code else -1
        header_lines = source[:offset].count("\n") if offset > 0 else 2
        m = re.search(r"SolutionRunner\.java:(\d+): error: (.*)", stderr)
        line = max(1, int(m.group(1)) - header_lines) if m else None
        msg = m.group(2) if m else "Compilation failed"
        return {"error_type": "Compile Error", "line_number": line, "error_message": msg,
                "line_code": user_code.split("\n")[line - 1] if line and line <= len(user_code.split("\n")) else "",
                "explanation": f"Line {line}: {msg}" if line else msg, "raw_trace": stderr[-3000:]}

    @staticmethod
    def _cpp_compile_details(stderr: str, source: str, user_code: str) -> Dict[str, Any]:
        m = re.search(r"solution\.cpp:(\d+):\d+: error: (.*)", stderr)
        msg = m.group(2) if m else "Compilation failed"
        return {"error_type": "Compile Error", "line_number": None, "error_message": msg, "explanation": msg, "raw_trace": stderr[-3000:]}
