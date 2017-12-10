__author__ = 'antonellacalvia'

from .node import *
import AST as Tree

class Operator(Node):
    def __init__(self, kind, parser):
        self.kind = kind
        Node.__init__(self, parser)

        self.overload = False
        self.unary = False
        self.curry = False
        self.partial = False
        self.interface = False
        self.name = False
        self.opT = Types.Null()


    def __str__(self):
        return self.kind

    def compileToJS(self, codegen):
        if self.kind == "|>":
            self.nodes[1].compileToJS(codegen)
            codegen.append("(")
            self.nodes[0].compileToJS(codegen)
            codegen.append(")")
            return
        elif self.kind == "as":
            self.nodes[0].compileToJS(codegen)
            return
        elif self.kind == ">>":
            a = self.nodes[0].type
            b = self.nodes[1].type

            if not (a.do and b.do):
                codegen.append("function(")
                names = ",".join([codegen.getName() for i in self.nodes[0].type.args])
                codegen.append(names)
                codegen.append("){return ")
                self.nodes[1].compileToJS(codegen)
                codegen.append("(")
                self.nodes[0].compileToJS(codegen)
                codegen.append("("+names+"))}")
            else:
                codegen.append("function(")
                callback = codegen.getName()
                _names = [codegen.getName() for i in self.nodes[0].type.args]
                names = ",".join(_names+[callback])
                codegen.append(names)
                codegen.append("){")

                if a.do and b.do:
                    self.nodes[0].compileToJS(codegen)
                    n = codegen.getName()
                    codegen.append("("+",".join(_names+["function("+n+"){"]))
                    self.nodes[1].compileToJS(codegen)
                    codegen.append("("+n+","+callback+")});")
                elif a.do:
                    self.nodes[0].compileToJS(codegen)
                    n = codegen.getName()
                    codegen.append("("+",".join(_names+["function("+n+"){"]))
                    codegen.append(callback+"(")
                    self.nodes[1].compileToJS(codegen)
                    codegen.append(")}")
                elif b.do:
                    self.nodes[1].compileToJS(codegen)
                    codegen.append("(")
                    self.nodes[0].compileToJS(codegen)
                    codegen.append("("+",".join(_names))
                    codegen.append("),"+callback+")}")
            return

            #todo: implement do function

        yilds = Tree.yields(self) and not self.partial and not self.curry
        if yilds:
            nextNum = str(codegen.count + 1)
            codegen.count += 1

            codegen.append(self.body._context + "=" + nextNum)
            codegen.append(";return ")

        if self.overload or self.curry or self.partial:
            if self.interface:
                if len(self.nodes) == 0:
                    codegen.append(self.name)
                    return

                self.nodes[0].compileToJS(codegen)
                codegen.append("."+self.name+"(")
            elif self.overload:
                codegen.append(self.package+"_"+self.name)
                codegen.append("(")
                self.nodes[0].compileToJS(codegen)
            elif self.curry:
                name = self.package + "_" + self.name if self.package != "" else self.name
                codegen.append(name+(".bind(null,"if self.curry and len(self.nodes) > 0 else "("))

                self.nodes[0].compileToJS(codegen)
            else:
                #partial application
                name = self.package + "_" + self.name if self.package != "" else self.name
                names = [codegen.getName() for i in self.nodes]

                partial = []
                missing = []
                for i in range(len(names)):
                    if type(self.nodes[i]) is Tree.Under:
                        missing.append(names[i])
                    else:
                        partial.append(names[i])

                codegen.append("(function("+",".join(partial)+"){return function("+",".join(missing)+"){")
                codegen.append("return "+name)
                codegen.append("("+",".join(names)+");}})(")

                for iter in range(len(self.nodes)-1):
                    i = self.nodes[iter]
                    if not type(i) is Tree.Under:
                        i.compileToJS(codegen)
                        if not (iter+2 == len(self.nodes) and type(self.nodes[iter+1]) is Tree.Under):
                            codegen.append(",")

                if len(self.nodes) > 1 and not type(self.nodes[-1]) is Tree.Under:
                    self.nodes[-1].compileToJS(codegen)


                codegen.append(")")

                return

            if len(self.nodes) > 1:
                codegen.append(",") if not self.interface else 0
                self.nodes[1].compileToJS(codegen)

            if yilds:
                codegen.append(("," if len(self.nodes) > 1 else "") + self.body._name)

            codegen.append(")")

            if yilds:
                codegen.append(";")
                self.outer_scope.case(codegen, nextNum, self)
                codegen.append(";")


            return

        codegen.append("(")

        if self.kind == "concat" and not self.nodes[1].type == Types.String():
            codegen.append("(")

        if self.type == Types.I32():
            codegen.append("(")

        if self.kind == "^":
            codegen.append("Math.pow(")

        if self.kind in ["+", "-", "*", "/", "<", ">", "<=", ">="]:
            op = self.kind

        else:
            translate = {
                "==": "===",
                "!=": "!==",
                "not": "!",
                "and": "&&",
                "or": "||",
                "%": "%",
                "concat": ")+(",
                "^": ",",
            }

            op = translate[self.kind]

        if self.unary:
            codegen.append(op)
        self.nodes[0].compileToJS(codegen)

        if not self.unary:
            codegen.append(op)
            self.nodes[1].compileToJS(codegen)
            if self.kind == "concat" and not self.nodes[1].type == Types.String():
                codegen.append(").toString()")
            if self.kind == "^":
                codegen.append(")")

        codegen.append(")")

        if self.type == Types.I32():
            codegen.append("|0)")



def checkOperator(self, parser):
        i = self
        if type(i.opT) is Types.Alias:
            i.opT = i.opT.typ

        unary = self.unary


        if not (i.kind == "<-" and not unary) and i.type == Types.Null():
            i.error("op "+i.kind + " cannot operate on type "+str(i.type))

        ops = {
            "int": ["+", "-", "%", "*", "/", "^", "==", "<", ">", "!=", "<=", ">="],
            "float": ["+", "-", "*", "/", "^", "==", "<", ">", "!=", "<=", ">="],
            "string": ["+", "==", "!=", "<", ">"],
            "bool": ["==", "not", "and", "or", "!="]
        }

        boolean = [
            "==",
            "not",
            "and",
            "or",
            "!=",
            "<",
            ">",
            "<=",
            ">="
        ]

        if i.kind in ["|>", ">>", "concat", "as", ".."] : return

        if not i.opT.name in ops or i.curry or i.partial:
            if unary:
               overloads = {
                    "+": "unary_add",
                    "-": "unary_sub",
                    "*": "unary_mul",
                    "/": "unary_div",
                    "^": "unary_pow",
                    "!=": "unary_ne",
                    "==": "unary_eq",
                    "not": "unary_not",
                   "<-": "unary_read",
                }
            else:
                overloads = {
                    "+": "op_add",
                    "-": "op_sub",
                    "*": "op_mul",
                    "/": "op_div",
                    "^": "op_pow",
                    "%": "op_mod",
                    "!=": "op_ne",
                    "==": "op_eq",
                    "<": "op_lt",
                    ">": "op_gt",
                    "or": "op_or",
                    "<-": "op_set",
                }

            if len(i.nodes) == 0:
                i.interface = True
                i.name = overloads[i.kind]
                return

            if type(i.opT) in [Types.Struct, Types.Interface, Types.Enum, Types.T, Types.Array, Types.Unknown, Types.Union]:
                func = i.opT.hasMethod(parser, overloads[i.kind])
                if not func:
                    try:
                        i.opT.types[overloads[i.kind]]
                        i.interface = True
                        i.name = overloads[i.kind]

                    except KeyError:
                        i.error( "Operator " + i.kind + ", cannot operate on type " + str(i.opT))
                else:
                    i.name = i.opT.normalName + "_" + overloads[i.kind]
                    i.package = i.opT.package

                i.overload = True
            else:
                if not i.kind in ops[i.opT.name]:
                    i.error("Operator " + i.kind + ", cannot operate on type " + str(i.nodes[0].type))
                i.package = ""
                i.name = overloads[i.kind]

        elif not i.kind in ops[i.opT.name]:
            i.error("Operator " + i.kind + ", cannot operate on type " + str(i.nodes[0].type))