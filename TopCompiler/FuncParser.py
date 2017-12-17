__author__ = 'antonellacalvia'

from TopCompiler import Parser
from TopCompiler import Error
import AST as Tree
from TopCompiler import Scope
import copy
from TopCompiler import ExprParser
from TopCompiler import VarParser
from TopCompiler import Types
from TopCompiler import MethodParser
import collections as coll

def parserMethodGen(parser, gen, struct):
    sgen = struct.generic

    if len(gen) > len(sgen):
        Error.parseError(parser, str(len(gen)-len(sgen))+" generic arguments too many")
    elif len(gen) < len(sgen):
        Error.parseError(parser, str(len(gen) - len(sgen)) + " generic arguments too few")

    newGen = coll.OrderedDict()
    for a, b in zip(gen, sgen):
        if gen[a].type != Types.All: Error.parseError(parser, "unexpected :")
        newGen[a] = sgen[b]
        Scope.changeType(parser, a, sgen[b])

    return newGen

def generics(parser, fname):
    generic = coll.OrderedDict()

    while parser.thisToken().token != "]":
        name = parser.nextToken().token

        typ = Types.T(name, Types.All, parser.package+"."+fname)
        if parser.thisToken().type != "identifier":
            Error.parseError(parser, "type name must be an identifier")

        if not parser.nextToken().token in [":", ",", "]"]:
            Error.parseError(parser, "expecting ,")

        if parser.thisToken().token == ":":
            parser.nextToken()
            interface = Types.parseType(parser)

            if not type(interface) in [Types.Interface, Types.EnumT, Types.Assign]:
                Error.parseError(parser, "Type variable "+name+", must either be a interface or enumT, not "+str(interface))

            typ = Types.T(name, interface, parser.package+"."+fname)

            if parser.lookInfront().token != "]":
                parser.nextToken()

        Scope.addVar(Tree.PlaceHolder(parser), parser, name, Scope.Type(False, typ))
        generic[typ.name] = typ

        if parser.lookInfront().token == "]":
            parser.nextToken()
            break

    parser.nextToken()
    return generic

def funcHead(parser, decl= False, dontAdd= False, method= False, attachTyp = False):
    target = "full"
    if parser.tokens[parser.iter+2].token == ".":
        if attachTyp: Error.parseError(parser, "unexpected .")
        parser.nextToken()
        name = parser.thisToken().token
        parser.nextToken()

        try:
            attachTyp = Types.Struct(False, name, parser.structs[parser.package][name]._types, parser.package)
        except KeyError:
            try:
                attachTyp = parser.interfaces[parser.package][name]
                if not type(attachTyp) is Types.Enum:
                    Error.parseError(parser, "no attachable data structure found, called "+name)

            except KeyError:
                Error.parseError(parser, "no attachable data structure found, called "+name)
        Scope.incrScope(parser)
        return funcHead(parser, decl, dontAdd, True, attachTyp)
    elif not method:
        Scope.incrScope(parser)

    name = parser.nextToken()

    if name.token in ["client", "full", "node"]:
        target = name.token
        if target == "full":
            target = "mustFull"
        name = parser.nextToken()

    if name.type != "identifier":
        Error.parseError(parser, "function name must be of type identifier, not "+name.type)
    parser.nextToken()

    name = name.token

    g = {}
    if parser.thisToken().token != "(":
        if parser.thisToken().token == "[":
            g = generics(parser, (attachTyp.normalName+"." if method else "")+name)
            if parser.thisToken().token == ".":
                if attachTyp: Error.parseError(parser, "unexpected .")
                if not Scope.varExists(parser, parser.package, name): Error.parseError(parser,
                     "cannot attach method to unknown type main."+name)

                try:
                    attachTyp = Types.Struct(False, name, parser.structs[parser.package][name]._types, parser.package,
                                         parserMethodGen(parser, g, parser.structs[parser.package][name]))
                except KeyError:
                    try:
                        tmp = parser.interfaces[parser.package][name]
                        if not type(tmp) is Types.Enum:
                            raise KeyError

                        attachTyp = Types.replaceT(tmp, parserMethodGen(parser, g, tmp))
                    except KeyError:
                        Error.parseError(parser, "no attachable data structure found, called " + name)

                return funcHead(parser, decl, dontAdd, True, attachTyp)

        if parser.thisToken().token != "(":
            Error.parseError(parser, "expecting (")

    if method and not type(parser.currentNode) is Tree.Root and not decl:
        Error.parseError(parser, "method extension must be in out-most scope")

    header = Tree.FuncStart(name, Types.Null(), parser)
    header.package = parser.package
    parser.currentNode.addNode(header)
    header.global_target = target

    brace = Tree.FuncBraceOpen(parser)
    brace.name = name
    brace.package = parser.package
    brace.global_target = target

    parser.currentNode.addNode(brace)

    parser.currentNode = brace

    if method:
        typ = attachTyp
        self = parser.nextToken()
        if self.type != "identifier": Error.parseError(parser, "binding name must be identifier not "+self.type)
        self = self.token

        selfNode = Tree.Create(self, typ, parser)
        selfNode.package = parser.package
        selfNode.imutable = True

        parser.currentNode.addNode(selfNode)

        if not parser.lookInfront().token in [")", ","]:
            Error.parseError(parser, "expecting comma not "+parser.thisToken().token)


    if name[0].lower() != name[0]:
        Error.parseError(parser, "function name must be lower case")

    returnType = Types.Null()

    parser.paren += 1
    parser.nextToken()

    while parser.paren != parser.parenBookmark[-1] :
        b = parser.thisToken().token
        if b == ",":
            parser.nextToken()
            continue
        elif b == ")":
            parser.paren -= 1
            parser.nextToken()
            continue
        elif b == "(":
            Error.parseError(parser, "unexpected (")
        Parser.declareOnly(parser)
        parser.nextToken()

    t = parser.thisToken()
    do = False

    if t.token != "=" and t.token != "do":
        returnType = Types.parseType(parser)

        t = parser.nextToken()
        if t.token != "=" and t.token != "do":
            Error.parseError(parser, "expecting = or do")

    if t.token == "do":
        do = True

    parser.currentNode = brace.owner

    names = [i.name for i in brace.nodes]
    types = [i.varType for i in brace.nodes]

    ignore = {}

    for (count, i) in enumerate(brace.nodes):
        if i.ignoreTarget:
            ignore[count] = i.ignoreTarget

    func = Types.FuncPointer(
        types,
        returnType,
        g,
        do,
        ignore= ignore
    )

    header.do = do

    if method:
        header.method = True
        header.types = types[1:]
        header.attachTyp = attachTyp
        header.normalName = name
        header.name = attachTyp.normalName+"_"+header.normalName

        MethodParser.checkIfOperator(parser, attachTyp, name, func)

        if decl:
            MethodParser.addMethod(brace, parser, attachTyp, name, func)

        return attachTyp.normalName+"_"+name, names, types, brace, returnType, do

    #parser.func[parser.package][name] = func

    header.ftype = func
    if decl:
        if not dontAdd:
            Scope.addFunc(header, parser, name, func, target)

    return name, names, types, brace, returnType, do

def funcBody(parser, name, names, types, brace, returnType, do):
    body = Tree.FuncBody(parser)
    body.name = name
    body.returnType = returnType
    body.package = parser.package
    body.do = do
    body.names = names

    target = brace.global_target
    body.global_target = target

    brace.body = body

    parser.currentNode.addNode(body)
    parser.currentNode = body

    for i in range(len(names)):
        n = Tree.InitArg(names[i], body)
        n.package = parser.package
        n.varType = types[i]
        n.imutable = not Scope.isMutable(parser, parser.package, names[i])
        body.addNode(n)

    parser.nextToken()
    Parser.callToken(parser) #incase next case is newline

    while not Parser.isEnd(parser):
        parser.nextToken()
        t = parser.thisToken().token
        Parser.callToken(parser)

    ExprParser.endExpr(parser)

    parser.currentNode = body.owner

    Scope.decrScope(parser)
    return body

def func(parser):
    (name, names, types, header, returnType, do) = funcHead(parser)
    body = funcBody(parser, name, names, types, header, returnType, do)
    body.method = parser.currentNode.nodes[-3].method

def funcCallBody(parser, paren):
    parser.nodeBookmark.append(1)

    def notParen():
        return not Parser.isEnd(parser)

    if paren :
        notEnd = lambda: parser.paren > parser.parenBookmark[-1]
    else:
        notEnd = notParen

    while notEnd():
        t = parser.nextToken()
        if t.token == "," :
            ExprParser.endExpr(parser)
            parser.nodeBookmark[-1] = len(parser.currentNode.nodes)
            continue

        Parser.callToken(parser)

    ExprParser.endExpr(parser)

    parser.nodeBookmark.pop()

def callFunc(parser,paren):

    tail = Tree.FuncCall(parser)

    tail.addNode(parser.currentNode.nodes[-1])

    tail.owner = parser.currentNode

    parser.currentNode.nodes[-1] = tail
    parser.currentNode = tail

    if not paren:
        Parser.selectExpr(parser, parser.thisToken())

    funcCallBody(parser, paren)

    parser.currentNode = tail.owner

def genericT(parser):
    parser.nextToken()
    if len(parser.currentNode.nodes) > 0:
        func = parser.currentNode.nodes.pop()
    else:
        Error.parseError(parser, "unexpected ::")

    generic = Tree.Generic(parser)
    parser.currentNode.addNode(generic)
    generic.addNode(func)

    generic.generic = []

    if parser.thisToken().token != "[":
        Error.parseError(parser, "expecting [")

    parser.nextToken()

    while parser.thisToken().token != "]":
        if parser.thisToken().token == ",":
            parser.nextToken()
            parser.nodeBookmark[-1] = len(parser.currentNode.nodes)
            continue

        generic.generic.append(Types.parseType(parser))
        t = parser.thisToken().token
        parser.nextToken()

def under(parser):
    parser.currentNode.addNode(Tree.Under(parser))

def comma(parser):
    parser.fired = True

Parser.stmts["def"] = func
#Parser.exprToken["none"] = lambda parser: Error.parseError(parser, "unexpected type none")
Parser.exprToken[","] = comma
Parser.exprToken["_"] = under
Parser.exprToken["::"] = genericT
Parser.exprToken["!"] = lambda parser: 0