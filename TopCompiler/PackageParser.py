__author__ = 'antonellacalvia'

import AST as Tree

from TopCompiler import Types
from TopCompiler import Parser
from TopCompiler import Error
from TopCompiler import VarParser
from TopCompiler import Scope

def _packDec(parser, pack= False):
    name = parser.nextToken()
    if name.type != "identifier":
        Error.parseError(parser, "package name must be an identifier")
    name = name.token

    packDec(parser, name, pack)

def packDec(parser, name, pack= False):
    import os
    parser.opackage = name
    parser.package = os.path.basename(name)

    if pack:
        Scope.addPackage(parser, name)

def index(parser, name):
    parser.currentNode.nodes.pop()

    parser.nextToken()
    VarParser.read(parser, parser.thisToken().token, package= name)


