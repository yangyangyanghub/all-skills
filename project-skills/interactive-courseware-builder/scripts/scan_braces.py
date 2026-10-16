#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JS-aware delimiter balance scanner for interactive courseware (Step 4 gate).

Why: node --check only says "Unexpected end of input" without position, and
naive bracket counters false-positive on regex literals (e.g. /https?:\\/\\//).
This scanner understands strings, template literals (incl. ${...} sub-expr),
line/block comments and regex literals, then reports the EXACT line of any
unclosed delimiter.

Usage:
  python scan_braces.py <file.html|file.js>            # balance check
  python scan_braces.py <file.html> --func showPage    # locate function span

Importable API:
  scan(text)            -> ('EOF', endline, None, stack) | ('MISMATCH', line, ch, stack)
  balance_ok(text)      -> bool
  function_span(text, name) -> (start_offset, end_offset) | None   # 0-based, end exclusive

Exit code: 0 = balanced, 1 = unbalanced/mismatch, 2 = usage error.
"""
import sys, re

REGEX_KEYWORDS = {
    'return','throw','else','do','yield','typeof','instanceof','in','of',
    'new','delete','void','await','case','default'
}

def is_ident_char(c):
    return c.isalnum() or c in '_$'

def is_operator_char(c):
    return c in '=<>!&|+-*/%^~?:.'

def regex_start(pt):
    """Decide if a '/' begins a regex literal rather than division."""
    if pt == '':
        return True
    if pt[0].isdigit():
        return False
    if pt in REGEX_KEYWORDS:
        return True
    if pt in ('(','[','{',',',';',':','?','~','^'):
        return True
    if all(ch in '=<>!&|+-*/%^~?:.' for ch in pt):
        return True
    return False    # identifier / ) / ] / }  => division

def scan(text):
    """Tokenize with a state machine; return delimiter stack status."""
    i = 0
    n = len(text)
    stack = []          # list of (open_char_or_'T', line)
    state = 'normal'    # normal|dquote|squote|tpl|linecmt|blkcmt|regex
    line = 1
    prev = ''
    cc = 0              # regex char-class depth

    while i < n:
        c = text[i]
        if c == '\n':
            line += 1
            if state == 'linecmt':
                state = 'normal'
            i += 1
            continue
        if state == 'normal':
            if c == '/':
                if i+1 < n and text[i+1] == '/':
                    state = 'linecmt'; i += 2; continue
                if i+1 < n and text[i+1] == '*':
                    state = 'blkcmt'; i += 2; continue
                if regex_start(prev):
                    state = 'regex'; cc = 0; i += 1; continue
                prev = '/'; i += 1; continue
            if c == '"':
                state = 'dquote'; i += 1; continue
            if c == "'":
                state = 'squote'; i += 1; continue
            if c == '`':
                state = 'tpl'; i += 1; continue
            if c in '([{':
                stack.append((c, line)); prev = c; i += 1; continue
            if c in ')]}':
                if c == ')' and stack and stack[-1][0] == '(':
                    stack.pop()
                elif c == ']' and stack and stack[-1][0] == '[':
                    stack.pop()
                elif c == '}' and stack and stack[-1][0] == '{':
                    stack.pop()
                elif c == '}' and stack and stack[-1][0] == 'T':
                    stack.pop(); state = 'tpl'
                else:
                    return ('MISMATCH', line, c, list(stack))
                prev = c; i += 1; continue
            if c.isalpha() or c == '_' or c == '$':
                j = i
                while j < n and is_ident_char(text[j]):
                    j += 1
                prev = text[i:j]; i = j; continue
            if c.isdigit():
                j = i
                while j < n and (text[j].isalnum() or text[j] in '._'):
                    j += 1
                prev = text[i:j]; i = j; continue
            if is_operator_char(c):
                j = i
                while j < n and is_operator_char(text[j]) and text[j] != '/':
                    j += 1
                prev = text[i:j]; i = j; continue
            i += 1; continue
        elif state == 'dquote':
            if c == '\\':
                i += 2; continue
            if c == '"':
                state = 'normal'
            i += 1; continue
        elif state == 'squote':
            if c == '\\':
                i += 2; continue
            if c == "'":
                state = 'normal'
            i += 1; continue
        elif state == 'tpl':
            if c == '\\':
                i += 2; continue
            if c == '`':
                state = 'normal'; i += 1; continue
            if c == '$' and i+1 < n and text[i+1] == '{':
                stack.append(('T', line)); state = 'normal'; i += 2; continue
            i += 1; continue
        elif state == 'linecmt':
            i += 1; continue
        elif state == 'blkcmt':
            if c == '*' and i+1 < n and text[i+1] == '/':
                state = 'normal'; i += 2; continue
            i += 1; continue
        elif state == 'regex':
            if c == '\\':
                i += 2; continue
            if c == '[':
                cc += 1; i += 1; continue
            if c == ']':
                if cc > 0: cc -= 1
                i += 1; continue
            if c == '/' and cc == 0:
                j = i+1
                while j < n and text[j].isalpha():
                    j += 1
                prev = '/'; state = 'normal'; i = j; continue
            i += 1; continue
    return ('EOF', line, None, list(stack))

def balance_ok(text):
    r = scan(text)
    return r[0] == 'EOF' and not r[3]

def extract_main_script(html):
    """Extract the main <script> block (the one containing 'function showPage').
    Falls back to whole content for bare .js files."""
    if '<script' not in html:
        return html
    opens = [m.start() for m in re.finditer(r'<script', html)]
    closes = [m.start() for m in re.finditer(r'</script>', html)]
    main_open = None
    for o in opens:
        nxt = next((c for c in closes if c > o), None)
        region = html[o:] if nxt is None else html[o:nxt]
        if 'function showPage' in region:
            main_open = o
            break
    if main_open is None:
        # no showPage courseware: take the largest script block
        best = None
        for o in opens:
            nxt = next((c for c in closes if c > o), None)
            if nxt is None:
                continue
            ln = nxt - o
            if best is None or ln > best[1]:
                best = (o, ln)
        if best is None:
            return html
        main_open = best[0]
    gt = html.find('>', main_open) + 1
    sc = html.find('</script>', gt)
    return html[gt:sc] if sc > 0 else html[gt:]

def function_span(text, name):
    """Locate 'function <name>(...)' and return (start_off, end_off) of its body,
    where end_off is the offset just AFTER its closing brace. Uses the scanner
    stack, so it is immune to braces inside strings/comments/regex."""
    m = re.search(r'function\s+' + re.escape(name) + r'\s*\(', text)
    if not m:
        return None
    # find the opening brace of the body
    j = text.find('{', m.end())
    if j < 0:
        return None
    # run scan on the prefix so stack state is correct, then continue tracking
    # from j with a fresh sub-scan: simplest correct approach = scan substring
    # from j and find where stack depth returns to 0.
    sub = text[j:]
    r = scan(sub)
    # replay to find the offset where the FIRST '{' (at sub offset 0) closes:
    # easier: incremental scan
    i = 0
    n = len(sub)
    depth = 0
    tpl_depths = []     # depth values at which a `${` sub-expression was entered
    state = 'normal'
    line = 1
    prev = ''
    cc = 0
    while i < n:
        c = sub[i]
        if c == '\n':
            line += 1
            if state == 'linecmt':
                state = 'normal'
            i += 1; continue
        if state == 'normal':
            if c == '/':
                if i+1 < n and sub[i+1] == '/':
                    state = 'linecmt'; i += 2; continue
                if i+1 < n and sub[i+1] == '*':
                    state = 'blkcmt'; i += 2; continue
                if regex_start(prev):
                    state = 'regex'; cc = 0; i += 1; continue
                prev = '/'; i += 1; continue
            if c == '"':
                state = 'dquote'; i += 1; continue
            if c == "'":
                state = 'squote'; i += 1; continue
            if c == '`':
                state = 'tpl'; i += 1; continue
            if c == '{':
                depth += 1; prev = c; i += 1; continue
            if c == '}':
                depth -= 1
                if tpl_depths and depth == tpl_depths[-1]:
                    tpl_depths.pop(); state = 'tpl'   # close of a ${...}
                elif depth == 0:
                    return (j, j + i + 1)
                prev = c; i += 1; continue
            if c.isalpha() or c == '_' or c == '$':
                k = i
                while k < n and is_ident_char(sub[k]):
                    k += 1
                prev = sub[i:k]; i = k; continue
            if c.isdigit():
                k = i
                while k < n and (sub[k].isalnum() or sub[k] in '._'):
                    k += 1
                prev = sub[i:k]; i = k; continue
            if is_operator_char(c):
                k = i
                while k < n and is_operator_char(sub[k]) and sub[k] != '/':
                    k += 1
                prev = sub[i:k]; i = k; continue
            i += 1; continue
        elif state == 'dquote':
            if c == '\\':
                i += 2; continue
            if c == '"':
                state = 'normal'
            i += 1; continue
        elif state == 'squote':
            if c == '\\':
                i += 2; continue
            if c == "'":
                state = 'normal'
            i += 1; continue
        elif state == 'tpl':
            if c == '\\':
                i += 2; continue
            if c == '`':
                state = 'normal'; i += 1; continue
            if c == '$' and i+1 < n and sub[i+1] == '{':
                tpl_depths.append(depth); depth += 1; state = 'normal'; i += 2; continue
            i += 1; continue
        elif state == 'linecmt':
            i += 1; continue
        elif state == 'blkcmt':
            if c == '*' and i+1 < n and sub[i+1] == '/':
                state = 'normal'; i += 2; continue
            i += 1; continue
        elif state == 'regex':
            if c == '\\':
                i += 2; continue
            if c == '[':
                cc += 1; i += 1; continue
            if c == ']':
                if cc > 0: cc -= 1
                i += 1; continue
            if c == '/' and cc == 0:
                k = i+1
                while k < n and sub[k].isalpha():
                    k += 1
                prev = '/'; state = 'normal'; i = k; continue
            i += 1; continue
    return None

def _line_of(text, off):
    return text[:off].count('\n') + 1

def main():
    args = sys.argv[1:]
    if not args:
        print('usage: scan_braces.py <file> [--func NAME] [--script-only]')
        return 2
    path = args[0]
    func = None
    if '--func' in args:
        func = args[args.index('--func') + 1]
    try:
        text = open(path, encoding='utf-8').read()
    except Exception as e:
        print('ERR read:', e)
        return 2
    is_html = path.endswith('.html') or path.endswith('.htm')
    if is_html:
        block = extract_main_script(text)
    else:
        block = text
    if func:
        r = function_span(block, func)
        if r is None:
            print('NOT FOUND: function', func)
            return 1
        print('function %s: block lines %d..%d' % (func, _line_of(block, r[0]), _line_of(block, r[1]-1)))
        return 0
    res = scan(block)
    if res[0] == 'EOF' and not res[3]:
        print('BALANCED: OK (0 errors)')
        return 0
    if res[0] == 'EOF':
        print('UNBALANCED at EOF. Remaining open delimiters (outermost first):')
        for ch, ln in res[3]:
            print('   open %r at line %d' % (ch, ln))
        return 1
    _, ln, ch, stack = res
    print('MISMATCH: %r at line %d' % (ch, ln))
    for x in stack[-8:]:
        print('   stack: %r line %d' % (x[0], x[1]))
    return 1

if __name__ == '__main__':
    sys.exit(main())
