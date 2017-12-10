__author__ = 'antonellacalvia'

from TopCompiler import Parser
from TopCompiler import Error
from TopCompiler import topc
from TopCompiler import ResolveSymbols
from TopCompiler import VarParser
from TopCompiler import Scope
from TopCompiler import Lexer

import AST as Tree
from TopCompiler import Types

ignore = {}

def shouldCompile(decl, name, parser, mutated= ()):
    if not decl and not name in parser.compiled and not name in mutated:
        mutated += (name,)

        if name in ignore:
            return False

        if name in parser.shouldCompile:
            return parser.shouldCompile[name]

        if not name in parser.allImports:
            return True

        for i in parser.allImports[name]:
            if shouldCompile(decl, i, parser, mutated):
                parser.shouldCompile[name] = True
                return True

        res = topc.modified(parser.output_target, parser.files[name], name, jsFiles= parser.jsFiles)
        parser.shouldCompile[name] = res

        return res

    return False

from TopCompiler import Module
import datetime

def shouldParse(decl, name, parser):
    return not decl and not name in parser.compiled

def importParser(parser, decl= False, fromI=False):
    import os
    name = parser.nextToken()

    if name.type != "str":
        Error.parseError(parser, "expecting string")

    oname = name.token[1:-1]

    if not oname in parser.filenames and not oname in ignore:
        Error.parseError(parser, "package "+oname+" not found")

    if decl == "order":
        if not parser.package in parser.order:
            parser.order[parser.package] = []

        if not oname in parser.order[parser.package]:
            parser.order[parser.package].append(os.path.basename(oname))
        return

    name = os.path.basename(oname)

    if not decl:
        if not parser.hotswap:
            sp = shouldParse(decl, oname, parser)
        else:
            sp = shouldCompile(decl, oname, parser)
            outputfile = oname
            try:
                if parser.global_target == "full":
                    t = max(os.path.getmtime("lib/" + outputfile.replace("/", ".") + "-client.js"),
                    os.path.getmtime("lib/" + outputfile.replace("/", ".") + "-client.js"))
                else:
                    t = os.path.getmtime("lib/" + outputfile.replace("/", ".") + "-" + parser.global_target + ".js")
                t = datetime.datetime.fromtimestamp(int(t))
            except FileNotFoundError:
                sp = True

        if sp:
            p = Parser.Parser(parser.lexed[oname], parser.filenames[oname])
            p.package = oname

            ResolveSymbols.insert(parser, p)

            global_target = parser.global_target

            p.global_target = "full"

            sc = shouldCompile(decl, oname, parser)

            p.sc = sc

            parser.compiled[name] = None
            #parser.externFuncs[name] = []

            parsed = p.parse()

            declar = [] #parser.externFuncs[name]

            parser.compiled[name] = (sc, (parsed, declar))

            ResolveSymbols.insert(p, parser)

            parser.global_target = global_target
            parser.currentNode.addNode(Tree.InitPack(name, parser))

        else:
            if not name in parser.compiled:
                parser.compiled[name] = (False,)
                parser.currentNode.addNode(Tree.InitPack(name, parser))

    parser.imports.append(oname)
    if fromI:
        parser.from_imports.append(oname)

import copy

def fromParser(parser, decl= False, stage=False):
    place = Tree.PlaceHolder(parser)

    importParser(parser, decl, True)
    if decl == "order":
        parser.nextToken()
        return

    name = parser.imports[-1]

    if parser.nextToken().token != "import":
        Error.parseError(parser, "Expecting import keyword")

    parser.nextToken()

    names = []
    if not decl:
        parser.currentNode.addNode(Tree.Import(name, parser.package, names, parser))

    def getName(token, nameOfVar=""):
        if nameOfVar == "":
            nameOfVar = token.token
        package = parser.package

        if nameOfVar in parser.interfaces[name]:
            if not decl: return

            if stage and nameOfVar in parser.interfaces[package]:
                Error.parseError(parser, nameOfVar + " is already an interface")

            parser.interfaces[package][nameOfVar] = parser.interfaces[name][nameOfVar]
        elif nameOfVar in parser.structs[name]:
            if decl:
                if stage and nameOfVar in parser.structs[package]:
                    Error.parseError(parser, nameOfVar + " is already a struct")
                parser.structs[package][nameOfVar] = parser.structs[name][nameOfVar]
                if not nameOfVar in parser.scope[parser.package][0]:
                    Scope.addVar(place, parser, nameOfVar, Scope.Type(True, parser.structs[name][nameOfVar], "full"))
                else:
                    Scope.changeType(parser, nameOfVar, parser.structs[name][nameOfVar])
                parser.scope[parser.package][0][nameOfVar].imported = True
            names.append((nameOfVar, "full"))
        elif not decl and nameOfVar in parser.scope[name][0]:
             #can't set lambda
            Scope.addVar(place, parser, nameOfVar, copy.copy(parser.scope[name][0][nameOfVar]))
            parser.scope[parser.package][0][nameOfVar].imported = True
            names.append((nameOfVar, parser.scope[name][0][nameOfVar].target))
        elif not decl:
            Error.parseError(parser, "Package " + name + " does not have a variable, or type called " + nameOfVar)

    token = parser.thisToken()

    if token.token == "all":
        _names = set()
        for i in parser.structs[name]:
            if parser.structs[name][i].package == name:
                _names.add(i)

        for i in parser.interfaces[name]:
            if parser.interfaces[name][i].name.split(".")[0] == name:
                _names.add(i)

        for i in parser.scope[name][0]:
            if not parser.scope[name][0][i].imported:
                _names.add(i)

        for i in _names:
            getName(token, i)
        return

    Parser.callToken(parser)
    elem = parser.currentNode.nodes.pop()

    def pattern(name):
        if type(name) in [Tree.Tuple, Tree.PlaceHolder]:
            for i in name:
                pattern(i)
        elif type(name) is Tree.ReadVar:
            return getName(name.token)
        elif type(name) is Lexer.Token and name.type == "identifier":
            return getName(name)
        else:
            p = Tree.PlaceHolder(parser)
            p.token = name
            p.error("Unexpected token " + name.token)

    pattern(elem)

Parser.stmts["import"] = importParser
Parser.stmts["from"] = fromParser