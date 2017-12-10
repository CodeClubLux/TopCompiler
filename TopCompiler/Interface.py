from TopCompiler import Parser
from TopCompiler import Error
from TopCompiler import Types
from TopCompiler import Scope
from TopCompiler import Struct
from TopCompiler import FuncParser
import collections as coll
import AST as Tree

def traitParser(parser, name, decl, generic):
    meth = {}
    while not Parser.isEnd(parser):
        parser.nextToken()

        t = parser.thisToken()

        Parser.declareOnly(parser, noVar=True)

    names = {i.name: i.varType for i in parser.currentNode}
    args = [i.varType for i in parser.currentNode]
    fields = parser.currentNode.nodes

    if decl:
        del parser.structs[parser.package][name]# = Struct.Struct(name, args, fields, coll.OrderedDict())

        i = Types.Interface(False, names, generic, parser.package+"."+name)
        parser.interfaces[parser.package][name] = i
    else:
        typ = Tree.Type(parser.package, name, parser)
        typ.package = parser.package
        typ.normalName = name
        typ.interface = True

        parser.currentNode.addNode(typ)

    Scope.decrScope(parser)