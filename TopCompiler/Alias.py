from TopCompiler import Parser
from TopCompiler import Error
from TopCompiler import Types
from TopCompiler import Scope
from TopCompiler import Struct
from TopCompiler import FuncParser
import collections as coll
import secrets

def aliasParser(parser, name, decl, generic):
    parser.nextToken()

    randomName = secrets.token_hex(nbytes=4)

    typ = False

    alias = Types.Alias(parser.package, name, Types.T(randomName,Types.All,parser.package+"."+name), generic)

    if decl:
        del parser.structs[parser.package][name]# = Struct.Struct(name, args, fields, coll.OrderedDict())

        parser.interfaces[parser.package][name] = alias

    while not Parser.isEnd(parser):
        if parser.thisToken().token != "\n" and parser.thisToken().type != "indent":
            if typ:
                Error.parseError(parser, "Unexpected token " + parser.thisToken().token)
            typ = Types.parseType(parser)
        parser.nextToken()

    if decl:
        if name == "Resolvers":
            print("parsing resolver")

        alias.typ = Types.replaceT(typ, {parser.package+"."+name+"."+randomName: typ}, unknown=True)
        alias.types = alias.typ.types

    Scope.decrScope(parser)

Parser.exprToken["is"] = lambda parser: Error.parseError(parser, "Unexpected token 'is', 'is' is only used when defining aliases")