__author__ = 'antonellacalvia'

from TopCompiler import FuncParser
from TopCompiler import Error
from TopCompiler import Parser
from TopCompiler import Scope
import AST as Tree
from TopCompiler import VarParser
from TopCompiler import FuncParser
from TopCompiler import Struct
from TopCompiler import Types
from TopCompiler import PackageParser
from TopCompiler import ImportParser
from TopCompiler import MethodParser
import os
import copy

def funcHead(parser):
    (name, names, types, header, returnType, do) = FuncParser.funcHead(parser, True)
    Scope.decrScope(parser)

def resolve(self):
    tokens = self.tokens
    filenames = self.filename

    for c in filenames:
        self._filename = self.filenames[c]
        PackageParser.packDec(self, c, pack=True)

        if self.hotswap and ImportParser.shouldCompile(False, self.package, self):
            self.scope[self.package] = [{}]
            self.structs[self.package] = {}
            self.interfaces[self.package] = {}

        if not c in self.allImports:
            self.allImports[c] = []

        for i in range(len(tokens[c])):
            _resolve([], self, tokens[c][i], self._filename[i][1], passN=0)

    order = []

    def findOrder(package, index=-1):
        if not package in order:
            order.insert(-1, package)

            if package in self.order:
                for i in self.order[package]:
                    findOrder(i, index - 1)
            else:
                for i in self.allImports[package]:
                    findOrder(i, index - 1)

    findOrder("main")

    usedModules = copy.copy(order)

    for package in filenames:
        if not package in order and package != "main":
            findOrder(package)

    self.order_of_modules = order
    self.orderOfUsedModules = usedModules

    for n in range(1,3):
        for c in order:
            self._filename = self.filenames[c]
            if len(filenames[c]) == 0:
                continue

            self.package = c
            self.opackage = c

            for i in range(len(tokens[c])):
                _resolve(usedModules, self, tokens[c][i], self._filename[i][1], passN=n)

    self.rootAst = Tree.Root()
    self.currentNode = self.rootAst

    self.tokens = tokens
    self.filename = filenames

    return self

from TopCompiler import ImportParser

def _resolve(usedModules, self, tokens, filename, passN= 0 ):
    target = self.global_target
    if self.package != "main":
        self.global_target = "full"

    if self.hotswap and not ImportParser.shouldCompile(False, self.package, self):
        if passN != 0 and "main" in self.allImports:
            for package in self.allImports[self.package]:
                if not usedModules:
                    self.compiled[package] = (False,)
        return

    self.filename = filename
    self.iter = 0

    self.tokens = tokens

    while self.iter < len(tokens) - 1 :
        b = self.thisToken().token

        if passN == 2:
            if b == "import":
                ImportParser.importParser(self, True)
            elif b == "from":
                ImportParser.fromParser(self, True)
            elif b == "def" :
                if self.indentLevel == 0:
                    nex = self.lookInfront()

                    Parser.addBookmark(self)
                    funcHead(self)
                    Parser.returnBookmark(self)
        elif passN == 1:
            if b == "import":
                ImportParser.importParser(self, True)
            elif b == "from":
                ImportParser.fromParser(self, True)
            elif b == "type":
                Parser.addBookmark(self)
                Struct.typeParser(self, decl= True)
                Parser.returnBookmark(self)

        elif passN == 0:
            if b == "type":
                Scope.addVar(Tree.Node(self), self, self.nextToken().token, Scope.Type(True, Types.StructInit(self.thisToken().token)))

                #"""
                self.structs[self.package][self.thisToken().token] = Struct.Struct(self.thisToken().token, [],[], {}, self, self.package)
                self.structs[self.package][self.thisToken().token].methods = {}
                #"""
            elif b == "import":
                ImportParser.importParser(self, "order")
            elif b == "from":
                ImportParser.fromParser(self, "order")

        if b == "\n":
            Parser.addBookmark(self)
            Parser.newLine(self)
            Parser.returnBookmark(self)

        self.nextToken()

    for i in self.imports:
        if not i in self.allImports[self.package]:
            self.allImports[self.package].append(i)

    self.imports = []
    self.from_imports = []

    self.lineNumber = 1
    self.normalIndent = 0

    self.global_target = target

import copy as _copy

def insert(parser, p, only= False, copy= False):
    if not only:
        p.files = parser.files
        p.filenames = parser.filenames
        p.lexed = parser.lexed

    if copy:
        scope = {}
        interfaces = {}
        structs = {}
        for package in parser.scope:
            scope[package] = [_copy.copy(parser.scope[package][0])]
            interfaces[package] = _copy.copy(parser.interfaces[package])
            structs[package] = _copy.copy(parser.structs[package])

        p.scope = scope
        p.interfaces = interfaces
        p.structs = structs
    else:
        p.scope = parser.scope
        p.structs = parser.structs
        p.interfaces = parser.interfaces

    #p.func = parser.func
    p.allImports = parser.allImports
    p.compiled = parser.compiled
    p.opt = parser.opt
    #p.externFuncs = parser.externFuncs
    p.hotswap = parser.hotswap
    p.global_target = parser.global_target
    p.shouldCompile = parser.shouldCompile
    p.atoms = parser.atoms
    p.atomTyp = parser.atomTyp
    p.jsFiles = parser.jsFiles
    p.outputFile = parser.outputFile
    p.transforms = parser.transforms
    p.output_target = parser.output_target
    p.cssFiles = parser.cssFiles
    p.usedModules = parser.usedModules
    p.run = parser.run
    p.order_of_modules = parser.order_of_modules
    p.orderOfUsedModules = parser.orderOfUsedModules

    return p

