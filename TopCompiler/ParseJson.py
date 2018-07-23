from TopCompiler import FuncParser
from TopCompiler import Error
from TopCompiler import Parser
from TopCompiler import Scope
from TopCompiler import Types
import AST as Tree

def parseJson(parser):
    parse = Tree.Decoder(parser)
    parser.currentNode.addNode(parse)
    parser.currentNode = parse

    parser.nextToken()

    typ = Types.parseType(parser)

    parse.type = Types.replaceT(parser.Decoder, {"Decoder.T": typ})

    parse.shouldBeTyp = typ

    parser.currentNode = parse.owner

Parser.exprToken["decoder"] = parseJson