__author__ = 'antonellacalvia'

import collections

from TopCompiler import Error

class Token:
    def __init__(self,token,type,line,column):
        self.token = str(token)
        self.type = type
        self.line = line
        self.column = column + (len(str(token)) // 2)

    def error(self, msg):
        Error.parseError(topc.global_parser, msg)

    def __repr__(self):
        return str((self.token,self.type, self.line, self.column ))

from TopCompiler import topc

def lex(target, stream, filename, modifiers, hotswap, lexed, transforms):
    for c in stream:
        try:
            t = transforms[c]
        except KeyError:
            t = []

        for i in t:
            Module.initModule(i)

        if not hotswap or (hotswap and topc.modified(target, modifiers[c], c)):
            lexed[c] = []
            for i in range(len(stream[c])):
                lexed[c].append(tokenize(stream[c][i], filename[c][i]))

        for i in t:
            Module.removeModule(i)

    return lexed

import re

keywords = [
        'import',
        'def',
        'then', 'do', 'if', 'elif', 'else', 'while',
        'int', 'float', 'bool', 'string', 'as',
        'break', 'continue',
        'true', 'false',
        'let',
        'ext',
        'type',
        'string',
        'var',
        "not", "or", "and",
        "lens",
        "match",
        "with",
        "from",
        "decoder",
        "extension",
        "is",
    ]

token_specification = [
        ("comment", r"/\*([\s\S]*?)\*/"),
        ("indent", r'\n[ ]*'),
        ('commentLine', r'//.*'),
        ('newline', r'\n'),
        ('openB', '{'),
        ('closeB', '}'),
        ('openC', '\('),
        ('closeC', '\)'),
        ('hex', r'0[xX][0-9a-fA-F]+'),
        ('f32', r'\d*[\d_]*\d+(\.\d*[\d_]*(\d+)|f)'),
        ('i32', r'\d*[\d_]*(\d+)'),
        ('arrow', r'->'),
        ('equal',  r'=='),
        ('doublecolon', r'::'),
        ("colon", r":"),
        ("semi", r";"),
        ('ne', r'!='),
        ('assign',  r'='),
        ('whiteOpenS', r' +\['),
        ('bracketOpenS', r' +\{'),
        ('doubleDot', '\.\.'),
        ('spaceDoubleDot', ' +\.\.'),
        ('dotS', r' +\.'),
        ('openS', r'\['),
        ('closeS', r'\]'),
        ('assignPlus', r'\+='),
        ('assignSub', r'\-='),
        ('assignMul', r'\*='),
        ('assignDiv', r'\/='),
        ('setAtom', '<\-[ ]+'),
        ('operator',  r'(\|>|>>|<-)|[+*\/\-%><^\\]'),
        ('line', r'\|'),
        ('identifier', r'[^\d\W](\w|(-[^\d\W]))*'),
        ('underscore', '_'),
        ('skip', r'[ \t]'),
        ("single", r"'(?:[^'\\])*'"),
        ("str", r'"(?:\\.|({.*})|[^"\\])*"'),
        ('dot', '\.'),
        ('tab', '\t'),
        ('comma', ','),
        ('bang', '!'),
        ('dollar', '\$'),
        ('set', '=>'),
    ]

normalLength = len(token_specification)

special = ["dollar", "bang", "arrow", "doublecolon", "line", "underscore", "assign", "assignPlus", "assignSub",
               "assignMul", "assignDiv", 'colon', 'dot', 'openC', 'openB', 'closeC', 'closeB', 'comma', 'closeS',
               'openS', 'doubleDot', 'semi']

from TopCompiler import Module

def tokenize(s, filename, spos= 0, sline= 0, slinePos= 0):
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    get_token = re.compile(tok_regex).match
    line = 1

    pos = spos
    mo = get_token(s)

    lastIndent = 0
    lastTyp = None
    linePos = slinePos

    line = sline

    extension = False

    array = []

    while mo is not None:
        typ = mo.lastgroup

        next = get_token(s, mo.end())

        if typ == "indent" or typ == "newline":
            val = mo.group(typ)
            array.append(Token("\n", "symbol", line, pos))
            line += 1

            linePos = mo.end()

            if next == None:
                array.append(Token(0,"indent", line, pos))
                break
            if next.lastgroup == "indent":
                array.append(Token(lastIndent, "indent", line, pos ))
            else:
                array.append(Token(len(val)-1, "indent", line, pos))
                lastIndent = len(val)-1
        elif typ == "comment":
            val = mo.group(typ)
            c = mo.end()
            r = val.rfind("\n")
            linePos = c + r
            line += len(val) - len(val.replace("\n", ""))
            array.append(Token(val, "comment", line, pos ))
        elif typ == "setAtom":
            array.append(Token("set", "operator", line, pos))
        elif typ in ["str"]:
            template = False
            val = mo.group(typ)
            def notBack(iter):
                if iter == 0: return True
                if val[iter-1] != "\\": return True
                return not notBack(iter-1)

            start = 0
            inBrace = False
            tokens = []
            val = val[1:-1]
            bcount = 0
            shouldBe = 0
            v = list(val)
            for iter in range(len(val)):
                i = val[iter]
                if notBack(iter) and i == "{" and not inBrace:
                    tokens.append(Token('"'+val[start: iter]+'"', "str", line, pos))
                    inBrace = True
                    start = iter+1
                    shouldBe = bcount
                    template = True

                if i == "{":
                    bcount += 1
                elif notBack(iter) and i == "}":
                    bcount -= 1
                    if bcount == shouldBe and inBrace:
                        tokens.append(Token("concat", "operator", line, pos+iter))
                        tokens.append(Token("(", "symbol", line, pos+iter))

                        t = tokenize(val[start: iter], filename)

                        for i in t[:-2]:
                            i.line += line
                            i.column += pos+start
                            tokens.append(i)
                        tokens.append(Token(")", "symbol", line, pos+iter))
                        tokens.append(Token("concat", "operator", line, pos+iter))
                        start = iter + 1
                        inBrace = False
                elif i == "\n":
                    line += 1

            tokens.append(Token('"'+val[start:]+'"', "str", line, pos))
            if template:
                tokens.insert(0, Token("(", "symbol", line, pos))
                tokens.append(Token(")", "symbol", line, pos + iter))
            array += tokens
        elif typ == "single":
            val = mo.group(typ)
            array.append(Token(val, "str", line, pos))
        elif typ == "spaceDoubleDot":
            _val = mo.group(typ)
            val = _val.replace(" ", "")
            pos = pos + (len(_val) - len(val))
            array.append(Token(val, "symbol", line, pos))
        elif typ != 'skip' and not typ in ["comment", "commentLine"]:
            val = mo.group(typ)
            if typ == "identifier":
                def my_replace(match):
                    match = match.group()
                    return match[1].upper()

                val = re.sub(r'\-[A-Za-z]', my_replace, val)

            if typ == 'identifier' and val in keywords:
                if val in ["true", "false"]:
                    typ = "bool"
                elif val in ["_"]:
                    typ = "symbol"
                else:
                    typ = "keyword"
                    extension = True

            elif typ == "f32":
                val = val[:-1]+".0" if val[-1] == "f" else val
            elif typ == "hex":
                typ = "i32"

            if typ == "i32" or typ == "f32":
                val = val.replace("_", "")

            elif typ in special:
                typ = "symbol"
            elif typ == "equal" or typ == "mut" or typ == "ne":
                typ = "operator"

            if val != " ": array.append(Token(val, typ, line, pos))
            elif val == "\t":
                Error.compileError(filename[1], line, "tabs are not allowed")

        lastTyp = typ

        #mo.start() - line_start

        pos = mo.start() - linePos
        mo = next

    if spos == 0 and sline == 0:
        array.append(Token("\n", "symbol", line-1, pos))
        array.append(Token(0, "indent", line, pos))

    return array





