__author__ = 'antonellacalvia'

from TopCompiler import Parser
import AST as Tree
from TopCompiler import Error
from TopCompiler import ExprParser
from TopCompiler import Scope
from TopCompiler import FuncParser
from TopCompiler import ExprParser
from TopCompiler import Types
from TopCompiler import Struct
from TopCompiler import Lexer


def pattern(name, names, parser, getName):
    if type(name) in [Tree.Tuple, Tree.PlaceHolder]:
        node = name.nodes[0]
        if type(node) is Tree.Tuple:
            for i in node:
                pattern(i, names, parser, getName)
        elif type(node) is Tree.InitStruct:
            for i in node:
                if type(i) is Tree.Assign:
                    if not type(i.nodes[0]) is Tree.ReadVar:
                        i.error("Expecting variable name")
                    pattern(i.nodes[1], names, parser, getName)
                elif type(i) is Tree.ReadVar:
                    pattern(i, names, parser, getName)
                else:
                    i.error("Expecting variable name")
        return name
    elif type(name) is Tree.ReadVar:
        names.append(name.name)
        return getName(name.token)
    elif type(name) is Tree.Under:
        names.append(name.name)
    elif type(name) is Lexer.Token and name.type == "identifier":
        return getName(name)
    else:
        if type(name) is Lexer.Token:
            Error.parseError(parser, "Unexpected token "+name.token)
        else:
            name.error("Unexpected token")

def createParser(parser, name= "", typ= None, check= True, imutable= True, attachTyp= False, ignoreTarget=False): # : creation
    if name == "":
        name = parser.lookBehind()

    names = []

    def getName(name):
        if name.type != "identifier":
            Error.parseError(parser, "variable name must be of type identifier, not " + parser.lookBehind().type)

        name = name.token

        if name[0].lower() != name[0]:
            Error.parseError(parser, "variable name must be lower case")

        return name

    name = pattern(name, names, parser, getName)

    node = Tree.Create(name, Types.Null(), parser)
    node.package = parser.package
    node.imutable = imutable
    node.names = names
    node.ignoreTarget = ignoreTarget

    if attachTyp:
        node.attachTyp = attachTyp

    parser.currentNode.addNode(node)

    node.varType = typ
    if check and typ is None:
        parser.nextToken()
        typ = Types.parseType(parser)

        node.varType = typ

def assignParser(parser, name= "", init= False, package = ""):
    if not init:
        i = parser.currentNode.nodes[-1]
        del parser.currentNode.nodes[-1]

    if package == "": package = parser.package

    if name == "":
        node = Tree.Assign("", parser=parser)
        node.addNode(i)
    else:
        node = Tree.Assign(name, parser=parser)

    parser.nodeBookmark.append(0)

    node.package = package
    node.init = init

    parser.currentNode.addNode(node)
    parser.currentNode = node

    curr = parser.thisToken()

    while not Parser.isEnd(parser):
        parser.nextToken()
        Parser.callToken(parser)

    ExprParser.endExpr(parser)

    parser.currentNode = node.owner
    parser.nodeBookmark.pop()

    self = node

    if self.init:
        if len(node.nodes) > 1 or len(node.nodes) == 0:
            self.error("expecting single expression, not "+str(len(node.nodes)))
    else:
        if len(node.nodes) > 2 or len(node.nodes) == 1:
            self.error("expecting single expression, not "+str(len(node.nodes)-1))

def createAndAssignParser(parser, imutable= True): # let i assignment
    node = parser.currentNode

    parser.nextToken() #get current token to position of =

    checkIt = False
    attachTyp = False

    """if parser.lookInfront().token == ".":
        attachTyp = Types.parseType(parser, _attachTyp= True)
        parser.nextToken()
        if not imutable or not type(node) is Tree.Root:
            Error.parseError(parser, "expecting =, not .")
        parser.nextToken()
    """

    name = parser.thisToken()

    typ = None
    create = False
    pattern = False

    isPattern = False

    t = parser.thisToken()
    if t.token == "{":
        Error.parseError(parser, "Expecting space")

    if t.token in ["("] or t.type == "bracketOpenS":
        isPattern = True
        owner = parser.currentNode
        pattern = Tree.PlaceHolder(parser)
        parser.currentNode = pattern

        Parser.callToken(parser)

        paren = parser.paren
        while parser.paren > paren:
            parser.nextToken()
            Parser.callToken(parser)

        parser.currentNode = owner
        name = pattern

    if parser.nextToken().token == ":":
        checkIt = True

        parser.nextToken()
        typ = Types.parseType(parser)

        parser.nextToken()

        if parser.thisToken().token != "=":
            create = True
    elif parser.thisToken().token != "=":
        Error.parseError(parser, "expecting =, not "+parser.thisToken().token)

    if not create:
        n = Tree.CreateAssign(parser)
        parser.currentNode.addNode(n)
        parser.currentNode = n

        createParser(parser, name=name, typ=typ, check=checkIt, imutable=imutable, attachTyp=attachTyp)

        if attachTyp:
            assignParser(parser, name=parser.package+"_"+attachTyp.normalName+"_"+name.token, package= attachTyp.package, init=True)
            n.nodes[1].attachName = parser.package+"_"+attachTyp.normalName
            n.nodes[1].varName = name.token
        else:
            c = name if type(name) is Tree.PlaceHolder else name.token
            assignParser(parser, name= c, init= True)

        n.nodes[1].isGlobal = n.nodes[0].isGlobal
        n.nodes[1].createTyp = n.nodes[0].varType


        parser.currentNode = node
    else:
        createParser(parser, name=name, typ=typ, check=checkIt, imutable=imutable, attachTyp=attachTyp)

Parser.stmts["let"] = createAndAssignParser
Parser.stmts["var"] = lambda parser: createAndAssignParser(parser, imutable= False)
Parser.stmts["="] = assignParser
Parser.stmts[":"] = createParser

def ignoreTarget(parser):
    targetIgnored = parser.thisToken().token
    name = parser.nextToken()
    if name.type != "identifier":
        Error.parseError(parser, "Expecting identifier")
    colon = parser.nextToken()
    if colon.token != ":":
        Error.parseError(parser, "Expecting :")
    createParser(parser, name, check=True, ignoreTarget=targetIgnored)

Parser.exprToken["ignoreOnClient"] = ignoreTarget
Parser.exprToken["ignoreOnServer"] = ignoreTarget
Parser.exprToken["i32"] = lambda parser: Error.parseError(parser, "unexpected type int")
Parser.exprToken["|"] = lambda parser: Error.parseError(parser, "unexpected function declaration")
Parser.exprToken["int"] = lambda parser: Error.parseError(parser, "unexpected type int")
Parser.exprToken["float"] = lambda parser: Error.parseError(parser, "unexpected type float")
Parser.exprToken["bool"] = lambda parser: Error.parseError(parser, "unexpected type bool")

def read(parser, name, package= ""):
    if package == "": package = parser.package

    node = Tree.ReadVar(name,  False, parser)
    node.package = package

    parser.currentNode.addNode(node)

def equalAnd(parser, operator, package= ""):
    if package == "": package = parser.package
    assignParser(parser, "", init= False, package= package)

    name = parser.currentNode.nodes[-1].nodes[0].name

    node = parser.currentNode.nodes[-1]

    add = Tree.Operator(operator, parser)
    add.addNode(node.nodes[1])

    r = Tree.ReadVar(name, False, parser)
    r.package = node.package
    r.type = node.nodes[0].type
    add.nodes.insert(0, r)
    r.owner = add

    add.owner = node

    node.nodes[1] = add

Parser.exprType["identifier"] = read

Parser.stmts["+="] = lambda parser: equalAnd(parser, "+")
Parser.stmts["-="] = lambda parser: equalAnd(parser, "-")
Parser.stmts["*="] = lambda parser: equalAnd(parser,  "*")
Parser.stmts["/="] = lambda parser: equalAnd(parser,  "/")
Parser.stmts["%="] = lambda parser: equalAnd(parser,  "%")
Parser.stmts["^="] = lambda parser: equalAnd(parser,  "^")