from TopCompiler import Parser
from TopCompiler import Error
from TopCompiler import Types
from TopCompiler import Scope
from TopCompiler import Struct
from TopCompiler import FuncParser
from TopCompiler import ExprParser
import AST as Tree
import collections as coll

len = lambda i: i.__len__()

def enumParser(parser, name, decl, generic):
    const = coll.OrderedDict()
    enum = Types.Enum(parser.package, name, const, generic)

    if decl:
        del parser.structs[parser.package][name]# = Struct.Struct(name, args, fields, coll.OrderedDict())
        parser.interfaces[parser.package][name] = enum

    """if parser.lookInfront().token == "\n":
        parser.nextToken()
        Parser.callToken(parser)
        parser.nextToken()"" \
    """

    while not Parser.isEnd(parser):
        t = parser.nextToken()

        if t.token == "\n" or t.type == "indent":
            Parser.callToken(parser)
            continue

        if t.type != "identifier":
            Error.parseError(parser, "expecting identifier")

        varName = t.token

        if varName[0].upper() != varName[0]:
            Error.parseError(parser, "constructor type must be capitalized")

        args = []
        nextT = parser.nextToken()
        #print(varName)
        #print(nextT)
        if nextT.token == "(":
            args = Types.parseType(parser).list

        const[varName] = args

        if decl:
            Scope.addVar(Tree.PlaceHolder(parser), parser, varName, Scope.Type(True,
                Types.FuncPointer(args, enum, generic = generic) if len(args) > 0 else enum
            ), _global=True)

        t = parser.thisToken()
        if t.token == "\n" or t.type == "indent":
            Parser.callToken(parser)

    parser.currentNode.addNode(Tree.Enum(const, name, parser))

    Scope.decrScope(parser)

from TopCompiler import ElseExpr

def checkCase(parser, case, typ, first=False):
    if type(case) is Tree.FuncCall:
        if not typ.isType(Types.Enum):
            case.nodes[0].error("cannot pattern match on type "+str(typ)+", as if it were a ADT")

        if not case.nodes[0].name in typ.const:
            case.nodes[0].error("ADT "+str(typ)+", does not have case "+case.nodes[0].name)

        pattern = typ.const[case.nodes[0].name]

        if len(pattern) < (len(case.nodes) - 1):
            case.nodes[-1].error(str((len(case.nodes) - 1) - len(pattern)) + " to many arguments")

        for iter in range(1, len(case.nodes)):
            checkCase(parser, case.nodes[iter], pattern[iter-1])
        case.nodes[0].type = Types.FuncPointer([], Types.Null(), do=False)

        if case.curry:
            case.nodes[-1].error("missing "+str(len(pattern) - (len(case.nodes)-1))+" arguments")

        case.type = typ
    elif type(case) is Tree.ReadVar and case.name[0].lower() == case.name[0]:
        Scope.addVar(case, parser, case.name, Scope.Type(True, typ))
    elif type(case) is Tree.ReadVar:
        if not typ.isType(Types.Enum):
            case.error("cannot pattern match on type " + str(typ) + ", as if it were a ADT")

        if not case.name in typ.const:
            case.error("ADT " + str(typ) + ", does not have case " + case.name)

        case.type = typ
    elif type(case) is Tree.Operator and case.kind == "concat" and not case.curry and not case.partial:
        if not typ.isType(Types.String):
            case.nodes[0].error("unexpected string")

        """
        if type(case.nodes[1]) is Tree.Tuple:
            print("adding name "+case.nodes[1].nodes[0].name)
            Scope.addVar(case.nodes[1].nodes[0], parser, case.nodes[1].nodes[0].name, Scope.Type(True, typ))
        else:
        """

        checkCase(parser, case.nodes[0], typ)
        checkCase(parser, case.nodes[1], typ)

        case.type = typ
        case.nodes[0].type = typ
        case.nodes[1].type = typ
    elif type(case) is Tree.Tuple:
        if len(case.nodes) == 1:
            node = case.nodes[0]
            checkCase(parser, node, typ)
        else:
            if not typ.isType(Types.Tuple):
                case.error("Cannot pattern match on "+str(typ)+", as if it were a tuple")

            for iter in range(len(case.nodes)):
                node = case.nodes[iter]
                checkCase(parser, node, typ.list[iter])
    elif type(case) is Tree.Array:
        if not typ.isType(Types.Array):
            case.error("pattern, matches on an array but is supposed to match on "+str(typ))
        for iter in range(len(case.nodes)):
            node = case.nodes[iter]
            checkCase(parser, node, typ.elemT)
    elif type(case) is Tree.Operator and case.kind == "or" and not case.curry and not case.partial:
        #typT = case.nodes[0].type
        for node in case.nodes:
            checkCase(parser, node, typ)

        #if not typT.isType(case.nodes[1].type):
        #    case.nodes[1].error("expecting type to be "+str(typ)+" and not "+str(case.nodes[1].type))

        #if not typT.isType(typ):
        #    case.error("expecting result of or, to be of type "+str(typ)+" not "+str(typT))
        case.type = Types.Bool()
        case.opT = Types.Bool()
    elif type(case) in [Tree.String, Tree.Int, Tree.Float]:
        if not typ.isType(case.type):
            case.error("expecting type "+str(case.type)+", not "+str(typ))
    elif type(case) is Tree.Operator and case.kind == ".." and not case.curry and not case.partial:
        checkCase(parser, case.nodes[0], Types.Array(False, typ))
    elif type(case) is Tree.Operator and case.kind == "as" and not case.curry and not case.partial:
        castTyp = case.type
        if not typ.isType(Types.Union):
            case.error("Type "+str(typ) + ", cannot be pattern matched on as if it were a union.")
        if not str(castTyp) in [str(i) for i in typ.different_types]:
            case.error("Type "+str(castTyp)+", not in "+str(typ))
        checkCase(parser, case.nodes[0], castTyp)
    elif not type(case) is Tree.Under:
        case.error("unknown pattern")

def missingPattern(typ, match):
    under = False
    const = []
    for iter in range(1, len(match.nodes), 2):
        m = match.nodes[iter].nodes[0]
        
        if type(m) is Tree.Under:
            under = True

            if iter != len(match.nodes)-2:
                m.error("_ must be the last pattern")
            return
        elif type(m) in [Tree.FuncCall, Tree.ReadVar]:
            if type(m) is Tree.FuncCall:
                name = m.nodes[0].name
            else:
                name = m.name

            if name in const:
                m.error("Duplicate pattern")

            const.append(name)
        elif type(m) is Tree.Operator and m.kind == "as":
            const.append(m.type)

    if not typ.isType(Types.Enum) and not typ.isType(Types.Union) and not under:
        match.error("missing _ case to match all possibilities")

    elif len(const) < len(typ.const):
        match.error("missing pattern "+", ".join([i for i in typ.const if not i in const]))

def match(parser):
    t = parser.thisToken()
    self = Tree.Match(parser)
    parser.currentNode.addNode(self)
    parser.currentNode = self

    while t.token != "with":
        t = parser.nextToken()
        if t.token == "with":
            break
        Parser.callToken(parser)
        t = parser.thisToken()

    parser.nextToken()
    Parser.callToken(parser)

    while not Parser.isEnd(parser):
        t = parser.nextToken()
        if t.token == "->":
            ExprParser.endExpr(parser)

            #print("entered ->")
            if len(self.nodes) == 0:
                Error.parseError(parser, "unexpected ->")
            previos = self.nodes[-1]
            if type(previos) is [Tree.MatchCase, Tree.Block]:
                Error.parseError(parser, "unexpected ->")

            case = Tree.MatchCase(parser)
            case.addNode(previos)

            self.nodes[-1] = case
            case.owner = self

            body = Tree.Block(parser)
            self.addNode(body)

            parser.currentNode = body

            Parser.addBookmark(parser)

            parser.nextToken()
            Parser.callToken(parser)

            while not Parser.isEnd(parser):
                parser.nextToken()
                """if Parser.isEnd(parser):
                    parser.callToken(parser)
                    #print("break", parser.thisToken())
                break
                """
                Parser.callToken(parser)
            #print("break", parser.thisToken())
            Parser.returnBookmark(parser)

            ExprParser.endExpr(parser)
            parser.currentNode = body.owner

            continue

        Parser.callToken(parser)

        if parser.thisToken().token == "->":
            parser.iter -= 1

    parser.currentNode = self.owner

Parser.exprToken["match"] = match
Parser.exprToken["with"] = lambda parser: \
    Error.parseError(parser, "unexpected with keyword") if type(parser.currentNode) == Tree.Root else ""

Parser.exprToken["->"] = lambda parser: \
    Error.parseError(parser, "unexpected with keyword") if type(parser.currentNode) == Tree.Root else ""
