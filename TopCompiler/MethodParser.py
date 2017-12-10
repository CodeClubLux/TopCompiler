__author__ = 'antonellacalvia'

from TopCompiler import Parser
from TopCompiler import Error
import AST as Tree
from TopCompiler import Types
from TopCompiler import Scope
from TopCompiler import FuncParser
from TopCompiler import Struct

def addMethod(node, parser, attachTyp, name, func, otherNode= False):
    if type(attachTyp) is Types.Struct:
        parser.structs[attachTyp.package][attachTyp.normalName].addMethod(node, parser, name,func)
    elif type(attachTyp) is Struct.Struct:
        if type(func) is Types.FuncPointer:
            if len(func.args) == 0:
                node.error("the function attached must have a first parameter with type "+attachTyp.package+"."+attachTyp.name)

            Types.Struct(False, attachTyp.name, attachTyp.types, attachTyp.package, attachTyp.generic).duckType(parser, func.args[0], node, otherNode, 0)

        attachTyp.addMethod(parser, name, func)
    elif type(attachTyp) is Types.Enum:
        parser.interfaces[attachTyp.package][attachTyp.normalName].addMethod(node, parser, name, func)
    else:
        node.error("Can't add method to "+str(attachTyp))

def checkIfOperator(parser, attachTyp, name, func):
    operators = {
        "add": Types.FuncPointer([attachTyp, attachTyp], attachTyp),
        "sub": Types.FuncPointer([attachTyp, attachTyp], attachTyp),
        "mul": Types.FuncPointer([attachTyp, attachTyp], attachTyp),
        "div": Types.FuncPointer([attachTyp, attachTyp], attachTyp),
        "eq": Types.FuncPointer([attachTyp, attachTyp], Types.Bool()),
        "ne": Types.FuncPointer([attachTyp, attachTyp], Types.Bool()),
        "mod": Types.FuncPointer([attachTyp, attachTyp], attachTyp),
        "pow": Types.FuncPointer([attachTyp, attachTyp], attachTyp),
        "gt": Types.FuncPointer([attachTyp, attachTyp], Types.Bool()),
        "lt": Types.FuncPointer([attachTyp, attachTyp], Types.Bool()),
        "set": Types.FuncPointer([attachTyp, Types.All], Types.Null(), do=True),
    }

    unary = {
        "add": Types.FuncPointer([attachTyp], attachTyp),
        "sub": Types.FuncPointer([attachTyp], attachTyp),
        "mul": Types.FuncPointer([attachTyp], attachTyp),
        "read": Types.FuncPointer([attachTyp], Types.All, do= True),
    }

    if name.startswith("op_"):
        op = name[len("op_"):]
        if not op in operators:
            Error.parseError(parser, "overload not found for op_"+op)

        try:
            func.duckType(parser, operators[op], Tree.PlaceHolder(parser), Tree.PlaceHolder(parser), 0)
        except EOFError as e:
            Error.beforeError(e, "Operator overload: ")
    elif name.startswith("unary_"):
        op = name[len("unary_"):]
        if not op in unary:
            Error.parseError(parser, "overload not found for unary_"+op)

        try:
            unary[op].duckType(parser, func, Tree.PlaceHolder(parser), Tree.PlaceHolder(parser), 0)
        except EOFError as e:
            Error.beforeError(e, "Unary overload: ")