"""C language support: LeetCode-style starter code and a generated test harness.

Conventions (same as LeetCode's C track):
  int[] param   ->  int* nums, int numsSize
  string        ->  char* s
  string[]      ->  char** strs, int strsSize
  returns int[] ->  int* fn(..., int* returnSize)      (array must be malloc'd)
  returns char* ->  char* fn(...)
  in-place      ->  void fn(int* nums, int numsSize)   (the array is printed afterwards)
  ListNode / TreeNode -> struct ListNode* / struct TreeNode*
"""
from typing import Any, Dict, List, Optional

C_PARAM = {"int": "int", "double": "double", "bool": "bool", "string": "char*", "ListNode": "struct ListNode*",
           "TreeNode": "struct TreeNode*", "TreeNodeRef": "struct TreeNode*"}
C_RETURN = {"int": "int", "double": "double", "bool": "bool", "string": "char*", "int[]": "int*", "string[]": "char**",
            "ListNode": "struct ListNode*", "TreeNode": "struct TreeNode*", "TreeNodeVal": "struct TreeNode*", "void": "void"}
SUPPORTED_PARAMS = set(C_PARAM) | {"int[]", "string[]"}
DEFAULT_RETURN = {"int": "0", "double": "0.0", "bool": "false", "string": "NULL", "int[]": "NULL", "string[]": "NULL",
                  "ListNode": "NULL", "TreeNode": "NULL", "TreeNodeVal": "NULL"}

LIST_DEF = """/**
 * Definition for singly-linked list.
 * struct ListNode {
 *     int val;
 *     struct ListNode *next;
 * };
 */
"""
TREE_DEF = """/**
 * Definition for a binary tree node.
 * struct TreeNode {
 *     int val;
 *     struct TreeNode *left;
 *     struct TreeNode *right;
 * };
 */
"""


def c_supported(sig: Optional[Dict[str, Any]]) -> bool:
    if not sig or sig.get("design"):
        return False
    return all(t in SUPPORTED_PARAMS for _, t in sig.get("params", [])) and sig.get("returns") in C_RETURN


def _c_params(sig: Dict[str, Any]) -> List[str]:
    out = []
    for name, typ in sig["params"]:
        if typ == "int[]":
            out += [f"int* {name}", f"int {name}Size"]
        elif typ == "string[]":
            out += [f"char** {name}", f"int {name}Size"]
        else:
            out.append(f"{C_PARAM[typ]} {name}")
    if sig["returns"] in ("int[]", "string[]"):
        out.append("int* returnSize")
    return out


def c_starter(sig: Optional[Dict[str, Any]]) -> Optional[str]:
    if not c_supported(sig):
        return None
    ret = sig["returns"]
    types = {t for _, t in sig["params"]} | {ret}
    header = ""
    if "ListNode" in types:
        header += LIST_DEF
    if types & {"TreeNode", "TreeNodeRef", "TreeNodeVal"}:
        header += TREE_DEF
    if ret in ("int[]", "string[]"):
        header += "/**\n * Note: The returned array must be malloced, assume caller calls free().\n */\n"
    body = "    // Write your code here\n"
    if ret in ("int[]", "string[]"):
        body += "    *returnSize = 0;\n"
    if ret != "void":
        body += f"    return {DEFAULT_RETURN[ret]};\n"
    return f"{header}{C_RETURN[ret]} {sig['fn']}({', '.join(_c_params(sig))}) {{\n{body}}}\n"


C_PRELUDE = r'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <limits.h>
#include <math.h>
#include <ctype.h>
#include <stdint.h>
struct ListNode { int val; struct ListNode *next; };
struct TreeNode { int val; struct TreeNode *left; struct TreeNode *right; };
'''

C_HELPERS = r'''
/* ───────── GapX test runner ───────── */
static char* gx_trim(char* s) {
    while (*s && isspace((unsigned char)*s)) s++;
    char* e = s + strlen(s);
    while (e > s && isspace((unsigned char)e[-1])) *--e = 0;
    return s;
}
static char* gx_strip(char* s) {
    s = gx_trim(s);
    size_t n = strlen(s);
    if (n >= 2 && s[0] == '[' && s[n - 1] == ']') {
        int depth = 0;
        for (size_t i = 0; i < n; i++) {
            if (s[i] == '[') depth++;
            if (s[i] == ']') depth--;
            if (depth == 0 && i + 1 < n) return s;
        }
        s[n - 1] = 0; s++;
    }
    return gx_trim(s);
}
static char* gx_unq(char* s) {
    s = gx_trim(s);
    size_t n = strlen(s);
    if (n >= 2 && s[0] == '"' && s[n - 1] == '"') { s[n - 1] = 0; s++; }
    return s;
}
static char** gx_parts(char* src, int* count) {
    char* s = gx_strip(src);
    int cap = 16; char** out = malloc(sizeof(char*) * cap); *count = 0;
    if (!*s) return out;
    int depth = 0; char* start = s;
    for (char* p = s; ; p++) {
        if (*p == '[') depth++;
        if (*p == ']') depth--;
        if ((*p == ',' && depth == 0) || *p == 0) {
            char end = *p; *p = 0;
            if (*count == cap) { cap *= 2; out = realloc(out, sizeof(char*) * cap); }
            out[(*count)++] = gx_trim(start);
            if (end == 0) break;
            start = p + 1;
        }
    }
    return out;
}
static char* gx_dup(const char* s) { char* d = malloc(strlen(s) + 1); strcpy(d, s); return d; }
static int* gx_int_array(char* s, int* size) {
    char** p = gx_parts(s, size); int* a = malloc(sizeof(int) * (*size > 0 ? *size : 1));
    for (int i = 0; i < *size; i++) a[i] = atoi(p[i]);
    return a;
}
static char** gx_str_array(char* s, int* size) {
    char** p = gx_parts(s, size); char** a = malloc(sizeof(char*) * (*size > 0 ? *size : 1));
    for (int i = 0; i < *size; i++) a[i] = gx_dup(gx_unq(p[i]));
    return a;
}
static struct ListNode* gx_list(char* s) {
    int n; int* v = gx_int_array(s, &n);
    struct ListNode dummy = {0, NULL}; struct ListNode* cur = &dummy;
    for (int i = 0; i < n; i++) { cur->next = calloc(1, sizeof(struct ListNode)); cur = cur->next; cur->val = v[i]; }
    return dummy.next;
}
static struct TreeNode* gx_first_tree = NULL; static int gx_has_tree = 0;
static struct TreeNode* gx_new_tree_node(int v) { struct TreeNode* t = calloc(1, sizeof(struct TreeNode)); t->val = v; return t; }
static struct TreeNode* gx_find(struct TreeNode* r, int v) {
    if (!r) return NULL; if (r->val == v) return r;
    struct TreeNode* l = gx_find(r->left, v); return l ? l : gx_find(r->right, v);
}
static struct TreeNode* gx_tree(char* s) {
    if (gx_has_tree) { struct TreeNode* f = gx_find(gx_first_tree, atoi(gx_trim(s))); return f ? f : gx_new_tree_node(atoi(gx_trim(s))); }
    gx_has_tree = 1;
    int n; char** p = gx_parts(s, &n);
    if (n == 0 || strcmp(p[0], "null") == 0) return gx_first_tree = NULL;
    struct TreeNode** q = malloc(sizeof(struct TreeNode*) * (n + 1)); int head = 0, tail = 0;
    struct TreeNode* root = gx_new_tree_node(atoi(p[0])); q[tail++] = root; int i = 1;
    while (head < tail && i < n) {
        struct TreeNode* node = q[head++];
        if (i < n && strcmp(p[i], "null") != 0) { node->left = gx_new_tree_node(atoi(p[i])); q[tail++] = node->left; } i++;
        if (i < n && strcmp(p[i], "null") != 0) { node->right = gx_new_tree_node(atoi(p[i])); q[tail++] = node->right; } i++;
    }
    return gx_first_tree = root;
}
static void gx_print_ints(int* a, int n) { for (int i = 0; i < n; i++) printf(i ? ",%d" : "%d", a[i]); }
static void gx_print_strs(char** a, int n) { for (int i = 0; i < n; i++) printf(i ? ",%s" : "%s", a[i] ? a[i] : "null"); }
static void gx_print_list(struct ListNode* h) { int first = 1, c = 0; while (h && c++ < 10000) { printf(first ? "%d" : ",%d", h->val); first = 0; h = h->next; } }
static void gx_print_tree(struct TreeNode* r) {
    if (!r) return;
    struct TreeNode** q = malloc(sizeof(struct TreeNode*) * 20000); int head = 0, tail = 0; q[tail++] = r;
    int last = 0; char** out = malloc(sizeof(char*) * 20000); int n = 0;
    while (head < tail && tail < 19990) {
        struct TreeNode* t = q[head++];
        char buf[24];
        if (!t) { out[n++] = gx_dup("null"); continue; }
        snprintf(buf, sizeof buf, "%d", t->val); out[n++] = gx_dup(buf); last = n;
        q[tail++] = t->left; q[tail++] = t->right;
    }
    for (int i = 0; i < last; i++) printf(i ? ",%s" : "%s", out[i]);
}
static void gx_print_double(double d) { printf("%.10g", d); }
'''


def build_c_program(code: str, sig: Dict[str, Any], marker_literal: str) -> str:
    if not c_supported(sig):
        raise ValueError("This problem isn't available in C yet (it uses grids, 2-D arrays or a class). Please use C++, Java, Python or JavaScript.")
    import re
    user = re.sub(r"struct\s+(ListNode|TreeNode)\s*\{[^}]*\}\s*;", "", code)
    params, ret = sig["params"], sig["returns"]
    lines = [
        "int main(void) {",
        "    static char buf[1 << 22]; size_t len = fread(buf, 1, sizeof(buf) - 1, stdin); buf[len] = 0;",
        "    char* lines[4096]; int nl = 0; char* p = buf; lines[nl++] = p;",
        "    for (; *p; p++) { if (*p == '\\r') *p = 0; if (*p == '\\n') { *p = 0; if (nl < 4096) lines[nl++] = p + 1; } }",
        f"    while (nl > ({len(params)} > 1 ? {len(params)} : 1) && strlen(gx_trim(lines[nl - 1])) == 0) nl--;",
        "    int li = 0; static char empty[1] = \"\";",
        "    #define GX_NEXT (li < nl ? lines[li++] : empty)",
    ]
    args = []
    for i, (name, typ) in enumerate(params):
        v = f"a{i}"
        if typ == "int":
            lines.append(f"    int {v} = atoi(gx_trim(GX_NEXT));"); args.append(v)
        elif typ == "double":
            lines.append(f"    double {v} = atof(gx_trim(GX_NEXT));"); args.append(v)
        elif typ == "bool":
            lines.append(f"    bool {v} = strcmp(gx_trim(GX_NEXT), \"true\") == 0;"); args.append(v)
        elif typ == "string":
            lines.append(f"    char* {v} = gx_dup(gx_unq(GX_NEXT));"); args.append(v)
        elif typ == "int[]":
            lines.append(f"    int {v}n; int* {v} = gx_int_array(GX_NEXT, &{v}n);"); args += [v, f"{v}n"]
        elif typ == "string[]":
            lines.append(f"    int {v}n; char** {v} = gx_str_array(GX_NEXT, &{v}n);"); args += [v, f"{v}n"]
        elif typ == "ListNode":
            lines.append(f"    struct ListNode* {v} = gx_list(GX_NEXT);"); args.append(v)
        elif typ in ("TreeNode", "TreeNodeRef"):
            lines.append(f"    struct TreeNode* {v} = gx_tree(GX_NEXT);"); args.append(v)
    if ret in ("int[]", "string[]"):
        lines.append("    int rs = 0;")
        args.append("&rs")
    call = f"{sig['fn']}({', '.join(args)})"
    printers = {
        "int": f"int r = {call}; fflush(stdout); printf(\"%s%d\\n\", GX_MARKER, r);",
        "double": f"double r = {call}; fflush(stdout); printf(\"%s\", GX_MARKER); gx_print_double(r); printf(\"\\n\");",
        "bool": f"bool r = {call}; fflush(stdout); printf(\"%s%s\\n\", GX_MARKER, r ? \"true\" : \"false\");",
        "string": f"char* r = {call}; fflush(stdout); printf(\"%s%s\\n\", GX_MARKER, r ? r : \"null\");",
        "int[]": f"int* r = {call}; fflush(stdout); printf(\"%s\", GX_MARKER); gx_print_ints(r, rs); printf(\"\\n\");",
        "string[]": f"char** r = {call}; fflush(stdout); printf(\"%s\", GX_MARKER); gx_print_strs(r, rs); printf(\"\\n\");",
        "ListNode": f"struct ListNode* r = {call}; fflush(stdout); printf(\"%s\", GX_MARKER); gx_print_list(r); printf(\"\\n\");",
        "TreeNode": f"struct TreeNode* r = {call}; fflush(stdout); printf(\"%s\", GX_MARKER); gx_print_tree(r); printf(\"\\n\");",
        "TreeNodeVal": f"struct TreeNode* r = {call}; fflush(stdout); if (r) printf(\"%s%d\\n\", GX_MARKER, r->val); else printf(\"%snull\\n\", GX_MARKER);",
    }
    if ret == "void":
        first = params[0][1] if params else None
        lines.append(f"    {call}; fflush(stdout);")
        if first == "int[]":
            lines.append("    printf(\"%s\", GX_MARKER); gx_print_ints(a0, a0n); printf(\"\\n\");")
        else:
            lines.append("    printf(\"%snull\\n\", GX_MARKER);")
    else:
        lines.append("    " + printers[ret])
    lines += ["    return 0;", "}"]
    return C_PRELUDE + f"#define GX_MARKER {marker_literal}\n" + C_HELPERS + "\n" + user + "\n\n" + "\n".join(lines) + "\n"
