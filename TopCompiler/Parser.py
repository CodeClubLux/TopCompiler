__author__ = 'antonellacalvia'


# recursive imports


def parenOpen(parser):
    parser.paren += 1
    paren = parser.paren

    """
    if not ExprParser.isUnary(parser, parser.lookBehind()):
        FuncParser.callFunc(parser, paren= True)
    """

    if True:
        t0 = Tree.Tuple(parser)
        parser.currentNode.addNode(t0)
        parser.currentNode = t0

        parser.nodeBookmark.append(0)

        while not parser.paren < paren:
            parser.nextToken()
            if parser.thisToken().token in [",", "\n"]:
                endExpr(parser)
            else:
                callToken(parser)

        parser.nodeBookmark.pop()
        parser.currentNode = t0.owner

def parenClose(parser):
    parser.paren -= 1

    if parser.paren < 1:
        Error.parseError(parser, "unexpected )")
    layer = -1 if len(parser.bookmark) < 2 else -2

    ExprParser.endExpr(parser, layer= layer)


def newLine(parser):
    maybeEnd(parser)

    parser.lineNumber += 1

    indent = int(parser.lookInfront().token)

    if parser.iter + 2 < len(parser.tokens) and parser.tokens[parser.iter+2].token == "\n":
        parser.nextToken()

        return

    if parser.normalIndent == 0:
        if indent > parser.indent[-1]:
            # indent
            parser.normalIndent = indent / 2
    else:
        diff = indent - parser.indent[-1]
        if diff > 0 and diff % parser.normalIndent != 0:
            Error.parseError(parser, "inconsistent indentation")
        elif diff < 0 and ((-diff) / 2) % parser.normalIndent != 0:
            Error.parseError(parser, "unindent does not match any outer indentation level")

    parser.indentLevel = indent

precidences = {}  # what operator goes first!

exprType = {}  # depends on parser, needs type information to figure out
exprToken = {"\n": newLine, "(": parenOpen, ")": parenClose}  # depends on parser, needs token information
stmts = {}  # for all statements

from .Types import *

from .Lexer import *
import AST as Tree
from .Error import *
from .ExprParser import *
from .VarParser import *
from .ResolveSymbols import *
from .WhileExpr import *
from .Scope import *
from .IfExpr import *
from .PackageParser import *
from .ElseExpr import *
from .FuncParser import *
from .String import *
from .ImportParser import *
from .Lens import *
import os
from .ExternParser import *
from .Array import *
from .MethodParser import *
from .Struct import *
from .TypeInference import *
from .Enum import *
from .ParseJson import *
from .Lambda import *
from .Dict import *
from TopCompiler import Module
from .Alias import *

offsetToList = offsetsToList

def isEnd(parser):
    if parser.thisToken().token == "\n" and parser.stack != [] and parser.stack[-1].kind == "<-" and parser.package == "main":
        print(parser.stack)

    token = parser.thisToken()

    if parser.fired:
        parser.fired = False
        return True

    if token.token in ["!", "->", "\n", "with"] or parser.parenBookmark[-1] > parser.paren or parser.bracketBookmark[-1] > parser.bracket or parser.curlyBookmark[-1] > parser.curly:
        if token.token == "!" and len(parser.currentNode.nodes) > 1:
            return False

        #"""
        if token.token == "|>" and type(parser.currentNode) in [Tree.Assign, Tree.CreateAssign, Tree.Block, Tree.FuncBody, Tree.Root]:
            return False
        #"""

        if token.token in ["with"] and type(parser.currentNode) in [Tree.IfCondition, Tree.Match, Tree.PlaceHolder]:
            return False

        return maybeEnd(parser)
    return False


def declareOnly(self, noVar=False):
    s1 = selectStmt(self, self.thisToken())
    s2 = selectStmt(self, self.lookInfront())

    declaration = ["var", ":", "(", ")", ",", "\n"]
    if noVar:
        declaration = declaration[1:]

    def declare(token):
        if not (token.token in declaration):
            Error.parseError(self, "unexpected  " + token.token)

    tok = self.thisToken().token

    if self.thisToken().type == "indent":
        pass
    elif s1 != None:
        addBookmark(self)
        declare(self.thisToken())
        s1(self)
        returnBookmark(self)
    elif s2 != None and self.thisToken().token != ")" and self.thisToken().token != "(":
        declare(self.lookInfront())
    else:
        declare(self.thisToken())
        selectExpr(self, self.thisToken())


def maybeEnd(parser):
    if parser.indent[-1] >= parser.indentLevel and parser.paren <= parser.parenBookmark[-1] and parser.bracket <= parser.bracketBookmark[-1]:
        if parser.stack != [] and type(parser.currentNode) in [Tree.FuncBody, Tree.Root]:
            #parser.nodeBookmark.pop()
            ExprParser.endExpr(parser, -2)
        return True
    return False

class Opcode:
    def __init__(self, parser, opcode, func):
        self.func = func

        self.precidence = precidences[opcode][0] + (parser.paren * 1000)  # 0 is type
        self.right = precidences[opcode][1]  # 1 is if is right-associative
        self.kind = opcode

        def tryIt():
            if len(parser.bookmark) > 1:
                if len(parser.stack) - parser.bookmark[-2] > 0:  # -2 to compensate bookmark, being added by, when calling Opcode
                    same = parser.stack[-1].precidence == self.precidence and parser.stack[-1].right  # right
                    greater = parser.stack[-1].precidence > self.precidence

                    if greater or same:
                        parser.stack[-1].func()
                        parser.stack.pop()
                        tryIt()

        try:
            tryIt()
        except:
            Error.parseError(parser, "Unexpected " + opcode)

        self.pos = len(parser.currentNode.nodes)
        parser.stack.append(self)
        return

    def __repr__(self):
        return self.kind


def addBookmark(parser):
    parser.bookmark.append(len(parser.stack))
    parser.indent.append(parser.indentLevel)
    parser.parenBookmark.append(parser.paren)
    parser.bracketBookmark.append(parser.bracket)
    parser.curlyBookmark.append(parser.curly)

def returnBookmark(parser):
    parser.bookmark.pop()
    parser.indent.pop()
    parser.parenBookmark.pop()
    parser.bracketBookmark.pop()
    parser.curlyBookmark.pop()

def selectExpr(parser, token):
    addBookmark(parser)

    type = token.type
    tok = token.token

    if tok in exprToken:
        exprToken[tok](parser)
    elif type in exprType:
        exprType[type](parser, tok)

    returnBookmark(parser)

def selectStmt(parser, token):
    if token.token in stmts:
        return stmts[token.token]

def callToken(self, lam= False):

    s1 = selectStmt(self, self.thisToken())

    b = self.thisToken()

    iter = self.iter
    if s1 != None:
        addBookmark(self)
        s1(self)
        returnBookmark(self)
    else:
        if not lam and Module.shouldCall(b) and (b.token in ["!", "_", "(", "\\", "|", "<-"] or not b.type in ["symbol", "operator", "indent"]) and not b.token in ["as", "in", "not", "and", "or", "then", "with", "do", "else", "is"] and not ExprParser.isUnary(self, self.lookBehind()):
            if b.token == "$":
                ExprParser.endExpr(self, -2)
            addBookmark(self)
            FuncParser.callFunc(self, False)
            returnBookmark(self)
            return

        selectExpr(self, b)

class Func:
    def __init__(self, args, returnType):
        self.args = args
        self.returnType = returnType

class Parser:  # all mutable state
    def nextToken(parser):
        parser.iter += 1
        if parser.iter < len(parser.tokens):
            return parser.tokens[parser.iter]
            #if t.token == "," and parser.lookBehind().token == ",":
            #    Error.parseError(parser, "unexpected ,")
            #return t
        else:
            parser.iter -= 1
            if parser.paren > 1:
                Error.parseError(parser, "unmatched (")
            if parser.bracket > 0:
                Error.parseError(parser, "unmatched [")
            if parser.curly > 0:
                print(parser.curly)
                Error.parseError(parser, "unmatched {")
            Error.parseError(parser, "EOF")

    def lookBehind(parser):
        return parser.tokens[parser.iter - 1]

    def lookInfront(parser):
        try:
            return parser.tokens[parser.iter + 1]
        except:
            if parser.paren != 1:
                Error.parseError(parser, "unmatched (")
            Error.parseError(parser, "EOF")

    def thisToken(parser):
        return parser.tokens[parser.iter]

    def __init__(self, tokens, filename):
        self.paren = 1  # must be atleast 1, otherwise multiplication = 0
        self.bracket = 0
        self.curly = 0
        self.parenBookmark = [0]
        self.bracketBookmark = [0]
        self.curlyBookmark = [0]
        self.indentLevel = 0

        self.order_of_modules = []
        self.orderOfUsedModules = []

        self.fired = False
        self.dev = False

        self.lineNumber = 1
        self.stack = []

        self.nodeBookmark = [0]

        self.indent = []
        self.normalIndent = 0

        self.bookmark = [0]

        self.sc = True
        self.repl = False

        All = Types.All

        Stringable = Types.Interface(False, {"toString": Types.FuncPointer([], Types.String(0) )}, name= "Stringable")
        self.Stringable = Stringable

        Lengthable = Types.Interface(False, {"length": Types.I32()})
        Intable = Types.Interface(False, {"toInt": Types.FuncPointer([], Types.I32() )})
        Floatable = Types.Interface(False, {"toFloat": Types.FuncPointer([], Types.Float())})

        T = Types.T("T", Types.All, "Atom")

        Atom = Types.Interface(False, {
            "unary_read": FuncPointer([], T, do= True),
            "op_set": FuncPointer([T], Null(), do= True),
            "watch": FuncPointer([FuncPointer([T], Types.Null(), do= True)], Types.Null(), do= True),
            "toString": FuncPointer([], Types.String(0)),
            "update": FuncPointer([FuncPointer([T], T)], Types.Null(), do=True)
        }, coll.OrderedDict([("Atom.T", T)]), "Atom")

        A = Types.T("A", All, "Lens")
        B = Types.T("B", All, "Lens")

        Lens = Types.Interface(False, {
            "query": Types.FuncPointer([A], B),
            "set": Types.FuncPointer([A, B], A),
            "toString": Types.FuncPointer([], Types.String(0))
        }, coll.OrderedDict([("Lens.A", A), ("Lens.B", B)]), name="Lens")

        defer_T = Types.T("T", All, "defer")
        defer_X = Types.T("X", All, "defer")

        defer = Types.FuncPointer([Types.FuncPointer(
            [defer_T], defer_X, do= True)], Types.FuncPointer([defer_T], Types.FuncPointer([], defer_X, do= True))
        , generic= coll.OrderedDict([("defer.T", defer_T), ("defer.X", defer_X)]))

        parallel_T = Types.T("T", All, "parallel")

        parallel = Types.FuncPointer([Types.Array(False,
            Types.FuncPointer([], parallel_T, do=True)
        )], Types.Array(False, parallel_T), do= True, generic=coll.OrderedDict([("parallel.T", parallel_T)]))

        serial_T = Types.T("T", All, "serial")

        serial = Types.FuncPointer([Types.Array(False,
            Types.FuncPointer([], serial_T, do=True)
        )], Types.Array(False, serial_T), do=True, generic=coll.OrderedDict([("serial.T", serial_T)]))
        Maybe_T = Types.T("T", All, "Maybe")
        Maybe_R = Types.T("R", All, "Maybe")

        Maybe_gen = coll.OrderedDict([("Maybe.T", Maybe_T)])

        Maybe = Types.Enum("_global", "Maybe", coll.OrderedDict([("Some", [Maybe_T]), ("None", [])]), generic=Maybe_gen)
        Maybe.methods["_global"] = {}
        Maybe.methods["_global"]["withDefault"] = Types.FuncPointer(
            [Types.All, Maybe_T],
            Maybe_T
        )

        Maybe.methods["_global"]["map"] = Types.FuncPointer(
            [Types.All, Types.FuncPointer([Maybe_T], Maybe_R)],
            Types.replaceT(Maybe, {"Maybe.T": Maybe_R}),
            generic = coll.OrderedDict([("R", Maybe_R)])
        )

        A = Types.T("A", All, "MaybeLens")
        B = Types.T("B", All, "MaybeLens")

        MaybeLens = Types.Interface(False, {
            "query": Types.FuncPointer([A], Types.replaceT(Maybe, {"Maybe.T": B})),
            "set": Types.FuncPointer([A, B], A),
            "toString": Types.FuncPointer([], Types.String(0))
        }, coll.OrderedDict([("MaybeLens.A", A), ("MaybeLens.B", B)]), name="MaybeLens")

        self.Maybe = Maybe

        assign_T = Types.T("T", All, "assign")

        parseT = Types.T("T", All, "parseJson")

        self.scope = {"_global": [{
            "assign": Scope.Type(True, Types.FuncPointer([assign_T, Types.Assign(assign_T)], assign_T, generic= coll.OrderedDict([("assign.T", assign_T)]))),
            "alert": Scope.Type(True, Types.FuncPointer([Stringable], Types.Null(), do= True)),
            "log": Scope.Type(True, Types.FuncPointer([Stringable], Types.Null(), do= True)),
            "toString": Scope.Type(True, Types.FuncPointer([Stringable], Types.String(0))),

            "isEven": Scope.Type(True, Types.FuncPointer([Types.I32()], Types.Bool)),
            "isOdd": Scope.Type(True, Types.FuncPointer([Types.I32()], Types.Bool)),
            "len": Scope.Type(True, Types.FuncPointer([Lengthable], Types.I32())),
            "toInt": Scope.Type(True, Types.FuncPointer([Intable], Types.I32())),
            "toFloat": Scope.Type(True, Types.FuncPointer([Floatable], Types.Float())),
            "Stringable": Stringable,
            "Atom": Scope.Type(True, Atom),
            "Lens": Scope.Type(True, Lens),
            "MaybeLens": Scope.Type(True, MaybeLens),
            "All": Scope.Type(True, All),
            "newAtom": Scope.Type(True, Types.FuncPointer([T], Atom, coll.OrderedDict([("Atom.T", T)]))),
            "defer": Scope.Type(True, defer),
            "sleep": Scope.Type(True, Types.FuncPointer([Types.Float()], Types.Null(), do= True)),
            "parallel": Scope.Type(True, parallel),
            "serial": Scope.Type(True, serial),
            "Some": Scope.Type(True, FuncPointer([Maybe_T], Maybe, generic= Maybe_gen)),
            "None": Scope.Type(True, Maybe),
            "println": Scope.Type(True, Types.FuncPointer([Stringable], Types.Null(),do=True), "client"),
            "print": Scope.Type(True, Types.FuncPointer([Stringable], Types.Null(),do=True), "client"),
            "jsonStringify": Scope.Type(True, Types.FuncPointer([All], Types.String(0))),
            "parseJson": Scope.Type(True, Types.FuncPointer([Types.FuncPointer([All], parseT), Types.String(0)], parseT)),
            "dict": Scope.Type(True, dictFunc),
        }]}

        self.iter = 0

        self.package = "_global"
        self.opackage = ""
        self.imports = []
        self.from_imports = []
        self.transforms = []

        self.rootAst = Tree.Root()
        self.currentNode = self.rootAst

        self.allImports = {}

        self.filename = ""
        self.tokens = [None]

        self.order = {}

        self.structs = {"_global": {}}

        self.func = {"_global": {}}

        types = {
            "int": Types.I32(),
            "vector": Types.Array(False, Types.I32()),
            "float": Types.Float(),
            "string": Types.String(0)
        }

        for name in self.structs["_global"]:
            i = self.structs["_global"][name]
            i.addMethod(self, "toString", Types.FuncPointer([types[name]], Types.String(0)))

        self.interfaces = {
            "_global": {
                "Stringable": Stringable,
                "Atom": Atom,
                "Lens": Lens,
                "MaybeLens": MaybeLens,
                "Any": All,
                "Maybe": Maybe,
                "Dict": topDict,
            }
        }

        self.filename = filename
        self.tokens = tokens

    def parse(self):
        try:
            tr = self.transforms[self.package]
        except KeyError:
            tr = []

        for i in tr:
            Module.initModule(i)

        tokens = self.tokens
        filenames = self.filename

        self._tokens = tokens
        self._filename = filenames

        for i in range(len(tokens)):
            PackageParser.packDec(self, self.package)
            self._parse(tokens[i], filenames[i][1])

            #self.imports = []
        self.iter = 0

        infer(self, self.currentNode)

        self.tokens = tokens
        self.filename = filenames

        if self.sc:
            Tree.transform(self.currentNode)
            validate(self, self.currentNode)

        if self.package == "main" and self.dev and self.atomTyp:
            typ = self.atomTyp
            d = Tree.Decoder(self)
            d.shouldBeTyp = typ

            c = Tree.CreateAssign(self)

            cr = Tree.Create("decoderForAtom", typ, self)
            cr.package = ""
            cr.isGlobal = True

            c.addNode(cr)

            a = Tree.Assign("decoderForAtom", self)
            a.isGlobal = True
            a.init = True
            a.package = ""

            a.addNode(d)
            c.addNode(a)

            self.currentNode.addNode(c)

        for i in tr:
            Module.removeModule(i)

        return self.currentNode

    def _parse(self, tokens, filename):
        self.tokens = tokens
        self.filename = filename

        self.iter = 0
        while self.iter < len(tokens) - 1:
            t = self.thisToken()
            callToken(self)
            self.nextToken()

        ExprParser.endExpr(self)

        return self.currentNode
