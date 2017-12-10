
import AST as Tree

from TopCompiler import Types
from TopCompiler import Parser
from TopCompiler import Error
from TopCompiler import VarParser
from TopCompiler import Scope
from TopCompiler import ExprParser
import collections as coll
from TopCompiler import Struct

def parseLens(parser):
    #parser.nextToken()
    Scope.incrScope(parser)
    #lensType = Types.parseType(parser)
    Scope.decrScope(parser)

    place = Tree.Place(parser)

    lens = Tree.Lens(parser)
    lens.place = place

    parser.currentNode.addNode(lens)

    parser.currentNode = lens

    lens.addNode(place)

    #parser.nextToken()

    while not Parser.isEnd(parser):
        parser.nextToken()
        if parser.thisToken().token == "$":
            Struct.index(parser, unary=False)
            parser.currentNode.nodes[-1].pattern = True
        else:
            Parser.callToken(parser)

    ExprParser.endExpr(parser)

    parser.currentNode = lens.owner


def typeCheckLens(parser, lens):
    global B #hack
    global maybe
    B = Types.T("B", Types.All, "Lens")
    oB = B

    maybe = False

    def loop(n, typ):
        global B #hack
        global maybe
        if type(n) is Tree.Field:
            if n.pattern:
                t = Scope.typeOfVar(n,parser,parser.package,n.field)
                if t.isType(Types.Enum):
                    enum = t
                elif t.isType(Types.FuncPointer) and t.returnType.isType(Types.Enum):
                    enum = t.returnType
                else:
                    n.error("var " + n.field + " is not one of the cases of an enum")

                replaceGen = {}
                for i in enum.remainingGen:
                    replaceGen[i] = typ

                if not n.field in enum.const:
                    n.error(n.field + "not a case of the enum "+str(enum))
                else:
                    n.enum = enum
                    case = enum.const[n.field]

                before_enum = enum
                enum = Types.replaceT(enum, replaceGen)

                n.const = enum.const

                if len(case) == 1:
                    r = case[0]
                elif len(case) == 0:
                    n.error("This case of enum takes 0 values, thus cannot be used in lens")
                else:
                    r = Types.Tuple(case)

                maybe = True
                B = r
                return loop(n.nodes[0], enum)
            else:
                ob = B #have to check if B, changed after loop was called

                res = loop(n.nodes[0], Types.Interface(False, {
                    n.field: typ
                }))

                if not B is ob:
                    if n.field in B.types:
                        B = B.types[n.field]
                    else:
                        meth = B.getMethod(parser, n.field)
                        if meth:
                            B = meth
                        else:
                            n.error("Type "+str(B)+", has no field "+n.field)

                return res

        elif type(n) is Tree.ArrRead:
            return loop(n.nodes[0], Types.Array(False,typ))
        elif type(n) in [Tree.Place, Tree.PlaceHolder]:
            return typ
        else:
            n.error("unexpected token "+n.token.token)

    lens_typ = loop(lens.nodes[0], B)
    lens.maybe = maybe

    A = Types.T("A", Types.All, "Lens")

    """"
    replaceGen = {}
    for i in enum.remainingGen:
        replaceGen[i] = B
    r = Types.replaceT(r, replaceGen)

    replaceGenForB = {}
    for i in enum.remainingGen:
        replaceGenForB[i] = r

    print("====")
    print(before_enum)
    print(replaceGen)

    B = Types.replaceT(before_enum, replaceGen)
    maybe = True
    return loop(n.nodes[0], enum)
    """

    oB = B

    if maybe:
        B = Types.replaceT(parser.Maybe, {"Maybe.T" : oB})
        name = "MaybeLens"
        A.owner = name
        B.owner = name
    else:
        B = B
        name = "Lens"
        A.owner = name


    #originalB = Types.T("B", , "Lens")

    Lens = Types.replaceT(Types.Interface(False, {
        "query": Types.FuncPointer([A], B),
        "set": Types.FuncPointer([A, oB], A),
        "toString": Types.FuncPointer([], Types.String(0)),
    }, coll.OrderedDict([(name+".A", A), (name+".B", oB)]), name=name), {"Lens.A": Types.T("A", lens_typ, name)})

    #lens.type = Types.Interface(False, {
    #    #   "query": Types.FuncPointer([i.lensType], i.nodes[0].type),
    #    "set": Types.FuncPointer([i.lensType, i.nodes[0].type], i.lensType),
    #})


    lens.type = Lens

Parser.exprToken["lens"] = parseLens
Parser.exprToken["$"] = lambda  parser: Error.parseError(parser, "Unexpected token $")