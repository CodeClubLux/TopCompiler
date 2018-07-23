__author__ = 'antonellacalvia'

from .node import *
from TopCompiler import IfExpr

class If(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

        self.returnTo = ""
        self.next = ""
        self.returnVar = ""
        self.var = ""
        self.ternary = False
        self.yielding = False

    def __str__(self):
        return "IF"

    def compileToJS(self, codegen):
        if self.ternary:
            codegen.append("(")
            for i in self.nodes:
                i.compileToJS(codegen)
            codegen.append(")")
        elif self.type != Types.Null() and not self.yielding:
            codegen.append("(function(){")
            for i in self.nodes:
                i.compileToJS(codegen)
            codegen.append("})()")
        else:
            if self.yielding:
                codegen.count += 1
                self.ending = str(codegen.count)

                for i in self.nodes[1:]:
                    i.yielding = True

            next = ""

            count = 0
            _l = len(self.nodes)
            while count < _l:
                if self.yielding and count > 1:
                    codegen.append("/*if*/")
                    if self.next == next:
                        codegen.count += 1
                        self.next = codegen.count

                    codegen.append("case " + str(self.next) + ":")
                    next = self.next
                    codegen.append("/*notif*/")

                self.nodes[count].compileToJS(codegen)
                self.nodes[count+1].compileToJS(codegen)

                count += 2

            if self.yielding:
                 codegen.append("case " + str(self.ending) + ":")

    def validate(self, parser):
        if self.type != Types.Null():
            if len(self.nodes) <= 2:
                self.nodes[-1].nodes[-1].error("expecting else")

class IfCondition(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)
        self.ternary = False

    def __str__(self):
        return "ifCondition"

    def compileToJS(self, codegen):
        if self.owner.ternary:
            if self.owner.nodes[0] != self:
                codegen.append(":(")
            self.nodes[0].compileToJS(codegen)
            codegen.append("?")
        else:
            codegen.append(""+("else " if self.owner.nodes[0] != self and not self.owner.yielding else "")+"if(")
            self.nodes[0].compileToJS(codegen)
            codegen.append("){")

    def validate(self, parser):
        if len(self.nodes) != 1:
            self.error( "expecting single boolean expression")

        if self.nodes[0].type != Types.Bool():
            self.nodes[0].error("expecting boolean expression not " + str(self.nodes[0].type))

class Else(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)
        self.ternary = False
        self.yielding = False

    def __str__(self):
        return "else"

    def compileToJS(self, codegen):
        if self.yielding:
            codegen.append("{")
        elif self.owner.ternary:
            codegen.append(":(")
        else:
            codegen.append("\nelse{")

    def validate(self, parser): pass

class While(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

    def __str__(self):
        return "While"

    def compileToJS(self, codegen):
        for i in self.nodes:
            i.compileToJS(codegen)

    def validate(self, parser): pass

class WhilePreCondition(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

    def __str__(self):
        return "WhilePreCondition"

    def compileToJS(self, codegen):
        codegen.append("\nwhile(")

    def validate(self, parser): pass

class Break(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

    def __str__(self):
        return " break"

    def compileToJS(self, codegen):
        codegen.append("break;")

    def validate(self, parser): pass

class Continue(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

    def __str__(self):
        return "continue"

    def compile(self, codegen):
        return "br label "+self.owner.owner.check+"\n"

    def compileToJS(self, codegen):
        codegen.append(" continue;")

    def validate(self, parser): pass

class WhileCondition(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

    def __str__(self):
        return "WhileCondition"

    def compileToJS(self, codegen):
        self.nodes[0].compileToJS(codegen)
        codegen.append("){")

    def validate(self, parser):
        cond = self
        IfExpr.isBoolCondition(parser, cond)

class WhileBlock(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

    def __str__(self):
        return "block"

    def compileToJS(self, codegen):
        for i in self.nodes:
            i.compileToJS(codegen)
        codegen.append("}")

    def validate(self, parser):
        checkUseless(self)

import AST

def actuallyYields(node):
    for i in node:
        if AST.yields(i):
            return True
    return False

class Block(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)
        self.noBrackets = False
        self.yielding = False
        self.first = True
        self.changeNext = True

    def __str__(self):
        return "block"

    def case(self, codegen, number, node):
        #not (type(node) is Tree.FuncCall and not node == self.nodes[-1]) or
        if (not type(node) is Tree.FuncCall and node != self.nodes[-1]) or self.first:
            codegen.append("}/*case*/")

        self.first = False

        if len(self.owner.nodes) > (2 if type(self.owner) is If else 3):
            num = codegen.count + 1
        else:
            num = self.owner.ending

        codegen.count += 1
        codegen.append(self.body._context + "=" + str(num) + ";break;/*case*/")

        if self.changeNext:
            self.owner.next = num
        else:
            codegen.append("/* not first */")

        if not (not type(node) is Tree.FuncCall and node != self.nodes[-1]):
            self.changeNext = False

        if type(self.outer_scope) is Tree.Block and actuallyYields(self) and self.outer_scope.first:
            self.outer_scope.first = False
            self.outer_scope.case(codegen, number, self)
        else:
            codegen.append("case " + str(number) + ":")

            #codegen.append("case " + str(number) + ":")
        self.yielding = True

    def compileToJS(self, codegen):
        if not self.noBrackets and self.owner.ternary:
            self.nodes[0].compileToJS(codegen)
            if self == self.owner.nodes[-1]:
                codegen.append(")")
        elif self.type != Types.Null():
            for i in self.nodes[:-1]:
                i.compileToJS(codegen)

            if not self.yielding:
                if type(self.nodes[-1]) is Tree.FuncCall and self.nodes[-1].tail and not self.nodes[-1].nodes[0].type.do:
                    self.nodes[-1].compileToJS(codegen)
                    codegen.append(";}")
                else:
                    codegen.append("return ")
                    self.nodes[-1].compileToJS(codegen)
                    codegen.append(";}")
            else:
                if not AST.yields(self.nodes[-1]): #type(self.nodes[-1]) is Tree.FuncCall and self.nodes[-1].nodes[0].type.do):
                    codegen.append(self.body.res+"=")

                self.nodes[-1].compileToJS(codegen)
        else:
            for i in self.nodes:
                i.compileToJS(codegen)

            if not self.noBrackets and not self.yielding: codegen.append(";}")

        if self.yielding:
            codegen.append(";"+self.body._context + "=" + self.owner.ending + ";/*block*/break;")

            if not actuallyYields(self):
                codegen.append("}")

    def validate(self, parser):
        checkUseless(self)