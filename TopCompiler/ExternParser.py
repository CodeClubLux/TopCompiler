from TopCompiler import Parser
from TopCompiler import Error
import AST as Tree

from TopCompiler import Types
from TopCompiler import Scope
from TopCompiler import VarParser

def externVar(parser):
    target = parser.nextToken()

    if target.type != "identifier":
        Error.parseError(parser, "expecting target")

    target = target.token

    if not target in ["client", "full", "node"]:
        Error.parseError(parser, target+" is not a valid compilation target")

    VarParser.createAndAssignParser(parser)

    parser.currentNode.nodes[-1].extern = True
    parser.currentNode.nodes[-1].global_target = target
    parser.currentNode.nodes[-1].nodes[1].extern = True

Parser.stmts["ext"] = externVar