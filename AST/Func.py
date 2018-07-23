__author__ = 'antonellacalvia'

from .node import *
import AST as Tree
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

class Lambda(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

    def __str__(self):
        return "lambda"

    def validate(self, parser): pass

    def compileToJS(self, codegen):
        codegen.append("(function(")
        codegen.incrScope()
        self.nodes[0].compileToJS(codegen)
        self.nodes[1].compileToJS(codegen)
        codegen.append(")")

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

        if type(self.owner) is Root or (type(self.owner) is Tree.Block and type(self.owner.owner) is Tree.Root):
            codegen.inFunction()

        if self.method:

            attachTyp = self.attachTyp
            codegen.append(attachTyp.package+"_"+attachTyp.normalName+".prototype."+self.normalName+"=(function(")
            names = [codegen.getName() for i in self.types]
            if self.do:
                names.append(codegen.getName())

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
        self.returnType = ""
        self.before = []
        self.method = False
        self.tail = False

    def __str__(self):
        return "}"

    def case(self, codegen, number, node):
        codegen.append("case "+str(number)+":")

    def compileToJS(self, codegen):
        if type(self.returnType) is str:
            codegen.append("}")
            return

        if self.do:
            self.res = codegen.getName()
            self._name = codegen.getName()
            self._context = codegen.getName()

            for i in self.before:
                i.compileToJS(codegen)

            codegen.append("var "+self._context+"=0;")
            codegen.append("return function "+self._name+"("+self.res+"){")
            codegen.append("while(1){")
            codegen.append("switch("+self._context+"){")
            codegen.append("case 0:")
        elif self.tail:
            self._continue = codegen.getName()
            self.returnVar = codegen.getName()

            codegen.append("var "+self._continue+"= true;")
            codegen.append("var "+self.returnVar+";")
            codegen.append("while (" + self._continue + ") {")
            codegen.append(self._continue+"=false;")

        for i in self.nodes[:-1]:
            i.compileToJS(codegen)
            #if not type(i) in [Tree.FuncCall,Tree.If,Tree.Match,Tree.FuncBody,Tree.Create,Tree.Assign,Tree.CreateAssign,Tree.Tree.FuncBraceOpen,Tree.FuncStart] and i.type.name == "none":
            #    codegen.append(";")

        did = False

        y = False
        if len(self.nodes) > 0 and self.do:
            y = yields(self.nodes[-1]) or (type(self.nodes[-1]) in [Tree.If, Tree.Match] and self.nodes[-1].yielding)

        if not self.tail and self.returnType != Types.Null():
            if self.do:
                if not y:
                    did = True
                    codegen.append(";return " + self._next + "(")
            else:
                codegen.append(";return ")
        elif self.tail:
            codegen.append(self.returnVar+"=")

        if len(self.nodes) > 0:
            self.nodes[-1].compileToJS(codegen)

        if self.do:
            if not did:
                if self.returnType != Types.Null():
                    codegen.append(";return " + self._next + "(" + self.res + ")")
                else:
                    codegen.append(";return "+self._next + "()")
            else:
                codegen.append(")")
        elif self.tail:
            codegen.append("}")
            if self.returnType != Types.Null():
                codegen.append("return "+self.returnVar+";")

        codegen.append(";}")

        codegen.decrScope()

        if self.do:
            codegen.append("}}()}")

        if type(self.owner) is Root or (type(self.owner) is Tree.Block and type(self.owner.owner) is Tree.Root):
            codegen.outFunction()

    def validate(self, parser):
        checkUseless(self)

        actReturnType = Types.Null()

        if type(self.returnType) is str:
            Scope.decrScope(parser)
            return

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
        else:
            tailRecursive(self)

        Scope.decrScope(parser)

syncFuncs = [
    "println",
    "log",
]

def yields(i):
    if type(i) is Tree.FuncCall and i.nodes[0].type.do and not (i.curry or i.partial):
        if not (type(i.nodes[0]) is Tree.ReadVar and i.nodes[0].name in syncFuncs):
            return True
    elif type(i) is Tree.Operator and i.kind == "<-":
        return True
    elif type(i) in [Tree.If, Tree.Match] and i.yielding:
        return True
    return False

def tailRecursive(body):
    def loop(node):
        for i in node.nodes[-1:]:
            if not i.isEnd() and type(i) in [Tree.Match, Tree.If]:
                for node in i.nodes:
                    if type(node) is Tree.Block:
                        loop(node)

                loop(i)

            if type(i) is FuncCall and not i.curry and not i.partial and i.nodes[0].name == body.name and body.name != "":
                i.tail = True
                body.tail = True
                i.body = body

    loop(body)

def transform(body):
    outer_scope = [body]

    def loop(node, o_iter, match= False, inTailCallPosition=True):
        iter = -1
        isOuter = type(node) in [Tree.Block, Tree.FuncBody, Tree.Root]
        for i in node:
            iter += 1

            if type(i) == Tree.Block:
                i.outer_scope = outer_scope[-1]
                i.body = body

                outer_scope.append(i)

            if not i.isEnd() and not type(i) in [Tree.FuncStart, Tree.FuncBody, Tree.FuncBraceOpen]:
                x = loop(i, 0 if type(i) in [Tree.Block] else o_iter, True if type(i) is Tree.MatchCase else match, type(i) in [Tree.Block, Tree.FuncBody])
                if not type(i) in [Tree.Block]:
                    if isOuter:
                        iter += x - o_iter
                    o_iter = x

            if yields(i):
                if inTailCallPosition and iter == len(node.nodes)-1 and type(i) is FuncCall and i.nodes[0].name == body.name and body.name != "":
                    i.tail = True
                    i.body = body
                else:
                    i.body = body
                    i.outer_scope = outer_scope[-1]

                    i.outer_scope.yielding = True

                    if type(i.outer_scope) in [Tree.Block]:
                        i.outer_scope.owner.yielding = True

                    if not i.owner == outer_scope[-1]:
                        i.global_target = outer_scope[-1].nodes[o_iter].global_target
                        outer_scope[-1].nodes.insert(o_iter, i)

                        c = Context(body, i)
                        c.type = i.type
                        c.owner = i.owner

                        i.owner.nodes[iter] = c

                        i.owner = outer_scope[-1]

                        o_iter += 1

            if type(i) in [Tree.If, Tree.Match] and i.yielding:
                i.outer_scope = outer_scope[-1]

                if not i.owner == outer_scope[-1]:
                    outer_scope[-1].nodes.insert(o_iter, i)

                    c = Context(body, i)
                    c.type = i.type
                    c.owner = i.owner

                    i.owner.nodes[iter] = c

                    i.owner = outer_scope[-1]

                    o_iter += 1

            elif type(i) is Tree.CreateAssign:
                body.before.append(i.nodes[0])
                i.nodes[0].global_target = i.global_target
                i.nodes[0].owner = body

                assign = i.nodes[1]
                assign.global_target = i.global_target
                assign.owner = i.owner

                i.owner.nodes[iter] = assign

            elif type(i) is Tree.ReadVar and match and i.name[0].lower() == i.name[0]:
                r = Tree.Create(i.name, i.type, i)
                r.package = i.package
                r.owner = body
                r.global_target = i.global_target

                body.before.append(r)

            if isOuter:
                o_iter += 1

            if type(i) in [Tree.Block]:
                if i.yielding:
                    i.owner.yielding = True
                outer_scope.pop()

        return o_iter

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
        self.tail = False

    def __str__(self):
        return ""

    def compileToJS(self, codegen):
        yilds = yields(self) and not self.inline and not self.partial and not self.curry and not self.tail
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

        if self.tail and not self.nodes[0].type.do:
            pass
        elif self.partial:
            names = [codegen.getName() for i in self.nodes[1:]]

            partial = []
            missing = []
            for i in range(len(names)):
                if type(self.nodes[i+1]) is Under:
                    missing.append(names[i])
                else:
                    partial.append(names[i])
            if self.nodes[0].type.do:
                names.append(codegen.getName())
                missing.append(names[-1])
            codegen.append("(function("+",".join(partial)+"){return function("+",".join(missing)+"){")
            codegen.append("return ")
            self.nodes[0].compileToJS(codegen)
            codegen.append("("+",".join(names)+");}})(")
        else:
            if self.nodes[0].type.do and self.tail:
                codegen.append("return setTimeout(function(){")

            self.nodes[0].compileToJS(codegen)
            if self.curry and len(self.nodes[1:]) == 0:
                return

            if self.curry:
                codegen.append(".bind(null,")
            else:
                codegen.append("(")

        if self.tail and not self.nodes[0].type.do:
            genNames = []
            for iter in range(len(self.nodes)-1):
                i = self.nodes[iter+1]

                name = codegen.readName(self.body.package + "_" + self.body.names[iter])
                print(name)
                tmp = codegen.getName()
                codegen.append("var "+tmp+"=")
                i.compileToJS(codegen)
                codegen.append(";")
                genNames.append((name,tmp))

            for (realName,tmp) in genNames:
                codegen.append(realName+"="+tmp+";")

            codegen.append(self.body._continue+"=true;")
            return
        else:
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

        if self.nodes[0].type.do and self.tail:
            print("name is " + self.nodes[0].name)
            codegen.append(("," if len(self.nodes) > 1 else "")+self.body._next)

        codegen.append(")")

        if yilds:
            codegen.append(";")
            if str(self.nodes[0]) == ".send":
                if str(self.nodes[0].nodes[0]) == ".author":
                    print("Error")

            self.outer_scope.case(codegen, nextNum, self)

        if self.nodes[0].type.do and self.tail:
            codegen.append("; }, 0); }")

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

class Func(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

    def __str__(self):
        return "func"

    def validate(self, parser): pass

    def compileToJS(self, codegen):
        for i in self:
            i.compileToJS(codegen)

class Under(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

    def __str__(self):
        return "under"

    def validate(self, parser): pass

    def compileToJS(self, codegen):
        codegen.append("null")

class Generic(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

    def __str__(self):
        return "::[]"

    def validate(self, parser): pass

    def compileToJS(self, codegen):
        self.nodes[0].compileToJS(codegen)