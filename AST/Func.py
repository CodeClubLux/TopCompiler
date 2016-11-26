__author__ = 'antonellacalvia'

from .node import *
from TopCompiler import Scope

class InitArg(Node):
    def __init__(self, name, parser):
        Node.__init__(self, parser)
        self.name = name
        self.varType = ""

    def __str__(self):
        return self.name + " init "

    def compileToJS(self, codegen):
        pass

    def validate(self, parser):
        pass

class FuncStart(Node):
    def __init__(self, name, returnType, parser):
        Node.__init__(self, parser)
        self.returnType = returnType
        self.name = name
        self.method = False

    def __str__(self):
        return "def "+self.name+"("

    def compileToJS(self, codegen):
        import AST as Tree
        if not type(self.owner) is Tree.Root:
            name = codegen.createName(self.package+"_"+self.name)
        else:
            name = self.package+"_"+self.name

        codegen.incrScope()
        codegen.inFunction()
        if self.method:

            attachTyp = self.attachTyp
            codegen.append(attachTyp.package+"_"+attachTyp.normalName+".prototype."+self.normalName+"=(function(")
            names = [codegen.getName() for i in self.types]
            codegen.append(",".join(names)+"){return ")
            codegen.append(name+"("+",".join(["this"]+names)+")});")

        codegen.append("function "+name+"(")

    def validate(self, parser):
        Scope.incrScope(parser)

class FuncBraceOpen(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

    def __str__(self):
        return ")"

    def compileToJS(self, codegen):
        for i in self.nodes[:-1]:
            i.compileToJS(codegen)
            codegen.append(", ")

        if len(self.nodes) > 0:
            self.nodes[-1].compileToJS(codegen)

        if self.body.do:
            self._next = codegen.getName()
            self.body._next = self._next
            codegen.append(("," if len(self.nodes) > 0 else "")+self._next)

        codegen.append('){')

    def validate(self, parser):
        pass


class FuncBody(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)
        self.returnType = "."
    def __str__(self):
        return "}"

    def compileToJS(self, codegen):
        self.res = codegen.getName()
        self._name = codegen.getName()
        self._context = codegen.getName()

        if self.do:
            codegen.append("var "+self._context+"=0;")
            codegen.append("return function "+self._name+"("+self.res+"){")
            codegen.append("while(1){")
            codegen.append("switch("+self._context+"){")
            codegen.append("case 0:")

        for i in self.nodes[:-1]:
            i.compileToJS(codegen)

        did = False

        if self.returnType != Types.Null():
            if self.do:
                did = True
                codegen.append("return " + self._next + "(")
            else:
                codegen.append("return ")

        if len(self.nodes) > 0:
            self.nodes[-1].compileToJS(codegen)

        if self.do:
            if not did:
                codegen.append("return "+self._next + "()")
            else:
                codegen.append(")")

        codegen.append(";}")

        codegen.decrScope()

        if self.do:
            codegen.append("}}()}")

        import AST as Tree
        if type(self.owner) is Root or (type(self.owner) is Tree.Block and type(self.owner.owner) is Tree.Root):
            codegen.outFunction()

    def validate(self, parser):
        checkUseless(self)

        actReturnType = Types.Null()
        if self.returnType == Types.Null(): pass
        elif len(self.nodes) > 0:
            if self.nodes[-1].type == Types.Null():
                actReturnType = Types.Null()

            else:
                actReturnType = self.nodes[-1].type

        returnType = self.returnType
        name = self.name

        import AST as Tree

        try:
            returnType.duckType(parser,actReturnType,self, self.nodes[-1] if len(self.nodes) > 0 else Tree.Under(self),0)
        except EOFError as e:
            Error.beforeError(e, "Return Type: ")

        if self.do:
            transform(self)

        Scope.decrScope(parser)

syncFuncs = [
    "println",
    "log",
]

def yields(i):
    if type(i) is Tree.FuncCall and i.nodes[0].type.do:
        if not (type(i.nodes[0]) is Tree.ReadVar and i.nodes[0].name in syncFuncs):
            return True
    return False


def transform(body):
    outer_scope = [body]

    def loop(node, o_iter):
        iter = -1
        for i in node:
            iter += 1
            if yields(i):
                i.body = body

                if not i.owner == outer_scope[-1]:
                    outer_scope[-1].nodes.insert(o_iter, i)

                    c = Context(body, i)
                    c.type = i.type
                    c.owner = i.owner

                    i.owner.nodes[iter] = c

                    i.owner = outer_scope[-1]

                    o_iter += 1


            if type(i) in [Tree.FuncStart, Tree.FuncBody, Tree.FuncBraceOpen]:
                continue

            if not i.isEnd():
                loop(i, o_iter)

    loop(body, 0)

class Context(Node):
    def __init__(self, body, parser):
        super(Context, self).__init__(parser)
        self.body = body

    def compileToJS(self, codegen):
        codegen.append(self.body.res)

    def __str__(self):
        return "context"

    def validate(self, parser): pass


class FuncCall(Node):
    def __init__(self, parser):
        super(FuncCall, self).__init__(parser)
        self.partial = False

    def __str__(self):
        return ""

    def compileToJS(self, codegen):
        yilds = yields(self) and not self.inline and not self.partial and not self.curry
        if yilds:
            nextNum = str(codegen.count + 1)
            codegen.count += 1

            codegen.append(self.body._context + "=" + nextNum)
            codegen.append(";return ")

        if self.inline:
            if type(self.type) != Types.Null():
                codegen.append("(function(){")

            for i in self.nodes[1:-1]:
                i.compileToJS(codegen)

            if type(self.type) != Types.Null(): codegen.append("return ")
            if len(self.nodes) > 0:
                self.nodes[-1].compileToJS(codegen)
            if type(self.type) != Types.Null():
                codegen.append(";})()")
            return

        if self.partial:
            names = [codegen.getName() for i in self.nodes[1:]]

            partial = []
            missing = []
            for i in range(len(names)):
                if type(self.nodes[i+1]) is Under:
                    missing.append(names[i])
                else:
                    partial.append(names[i])

            codegen.append("(function("+",".join(partial)+"){return function("+",".join(missing)+"){")
            codegen.append("return ")
            self.nodes[0].compileToJS(codegen)
            codegen.append("("+",".join(names)+");}})(")
        else:
            self.nodes[0].compileToJS(codegen)
            if self.curry:
                codegen.append(".bind(null,")
            else:
                codegen.append("(")

        for iter in range(len(self.nodes[1:-1])):
            iter += 1
            i = self.nodes[iter]
            if not type(i) is Under:
                i.compileToJS(codegen)
                if not (iter+2 == len(self.nodes) and type(self.nodes[iter+1]) is Under):
                    codegen.append(",")

        if len(self.nodes) > 1 and not type(self.nodes[-1]) is Under:
            self.nodes[-1].compileToJS(codegen)

        if yilds:
            codegen.append(("," if len(self.nodes) > 1 else "")+self.body._name)

        codegen.append(")")

        if yilds:
            codegen.append(";")
            codegen.append("case "+nextNum+":")

        elif self.type == Types.Null():
            codegen.append(";")

    def validate(self, parser): pass

class Bind(Node):
    def __init__(self, func, module, parser):
        Node.__init__(self, parser)
        self.addNode(func)
        self.addNode(module)

    def validate(self, parser): pass

    def compileToJS(self, codegen):
        codegen.append("(")
        self.nodes[0].compileToJS(codegen)
        codegen.append(").bind(null,")
        self.nodes[1].compileToJS(codegen)
        codegen.append(")")

class ArrBind(Node):
    def __init__(self, name, what, parser):
        Node.__init__(self, parser)
        self.addNode(what)
        self.field = name

    def validate(self, parser): pass

    def compileToJS(self, codegen):
        codegen.append("Vector.prototype."+self.field+".bind(")
        self.nodes[0].compileToJS(codegen)
        codegen.append(")")


class Under(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

    def validate(self, parser): pass

    def compileToJS(self, codegen):
        codegen.append("null")

class Generic(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

    def validate(self, parser): pass

    def compileToJS(self, codegen):
        self.nodes[0].compileToJS(codegen)