from TopCompiler import Parser
from TopCompiler import Error
import AST as Tree
from TopCompiler import ExprParser
from TopCompiler import Scope
from TopCompiler import ElseExpr
from TopCompiler import Types
import copy
from TopCompiler import MethodParser
from TopCompiler import Struct
from TopCompiler import Enum
from collections import OrderedDict as ODict
from TopCompiler import Lens

checkTyp = []

len = lambda i: i.__len__()

def infer(parser, tree):
    origTree = tree
    varTypes = {}
    sc = parser.sc

    parser.func = []

    def loop(n, o_iter, tree= tree):
        count = 0
        for i in n:
            if n is origTree:
                o_iter += 1

            treeBefore = tree
            o_iterBefore = o_iter

            if type(n) is Tree.FuncCall and count > 0:
                typ = n.nodes[0].type
                if type(typ) is Types.FuncPointer and (count - 1) in typ.ignore and typ.ignore[count - 1]:
                    ignoreTarget = typ.ignore[count - 1]
                    n.global_target = ignoreTarget.replace("ignoreTargetOn", "")
                    tree = n
                    o_iter = count

            if not sc and type(i) in [Tree.FuncStart, Tree.FuncBraceOpen, Tree.FuncBody]:
                count += 1
                continue

            if type(i) is Tree.FuncStart:
                if not type(n) is Tree.Root:
                    Scope.addVar(i, parser, i.name, Scope.Type(True, i.ftype))
                Scope.incrScope(parser)

            elif type(i) in [Tree.Block, Tree.While]:
                Scope.incrScope(parser)

            if type(i) is Tree.Lambda:
                count = Types.state.count
                Scope.incrScope(parser)

            if not (i.isEnd() or type(i) in [Tree.MatchCase, Tree.Lens] or (type(i) is Tree.Block and type(i.owner) is Tree.Match)):
                if type(i) is Tree.FuncBody:
                    if i.method:
                        parser.func.append(parser.package+"."+i.name[:i.name.find("_")])

                    parser.func.append(parser.package+"."+i.name.replace("_", "."))
                    if i.name != "":
                        loop(i, count, tree= i.owner)
                    else:
                        loop(i, o_iter, tree=tree)
                else:
                    loop(i, o_iter, tree=tree)

                if type(i) is Tree.FuncBody and len(parser.func) > 0:
                    if i.method:
                        parser.func.pop()
                    parser.func.pop()

            if type(i) is Tree.Lens:
                Lens.typeCheckLens(parser, i)
            elif type(i) is Tree.Lambda:

                if not i.returnTyp:
                    if len(i.nodes) > 0:
                        returnTyp = i.nodes[1].nodes[-1].type
                    else:
                        returnTyp = Types.Null()
                else:
                    returnTyp = i.returnTyp

                args = []
                gen = ODict()
                for c in i.args:
                    if type(c) is Types.Unknown:
                        if not c.typ:
                            c.compareType(Types.newT(parser))

                        args.append(c.typ)
                        genInC = Types.remainingT(c.typ)
                        for d in genInC:
                            gen[d] = genInC[d]
                    else:
                        args.append(c)



                if type(returnTyp) is Types.Unknown and not returnTyp.typ:
                    i.error("Cannot infer return type of this function")


                replaces = {}

                #should only replace if only used once

                #"""
                inReturn = Types.remainingT(returnTyp)
                processGen = ODict()
                uselessGen = ODict()

                for c in gen:
                    if c in inReturn:
                        processGen[c] = gen[c]
                    else:
                        uselessGen[c] = gen[c]

                replaces = {}
                for c in uselessGen:
                    replaces[c] = Types.replaceT(uselessGen[c].type, {}, unknown=True)

                gen = processGen
                #"""



                i.args = []
                i.returnTyp = 0
                i.type = Types.replaceT(Types.FuncPointer(args, returnTyp, do=i.do, generic=gen), replaces, unknown = True)

                i.nodes[1].returnType = i.type.returnType

                i.nodes[1].do = i.do


                #print(gen)
                #print(i.type)

                Types.state.count = count

            elif type(i) is Tree.Match:
                typ = i.nodes[0].type
                first = False
                for c in range(1,len(i.nodes),2):
                    body = i.nodes[c+1]

                    Scope.incrScope(parser)
                    Enum.checkCase(parser, i.nodes[c].nodes[0], typ, True)

                    loop(body, o_iter)
                    body.type = body.nodes[-1].type if len(body.nodes) > 0 else Types.Null()
                    Scope.decrScope(parser)
                    if first:
                        try:
                            thisTyp = body.type
                            first.duckType(parser, thisTyp, body, i, 0)
                        except EOFError as e:
                            try:
                                thisTyp.duckType(parser, first, body, i, 0)
                                first = thisTyp
                            except EOFError:
                                Error.beforeError(e, "Type mismatch, this arm has a different type : ")

                        #if body.type != first:
                        #    (body.nodes[-1] if len(body.nodes) > 0 else body).error(
                        #        "type mismatch in arms of match, " + str(body.type) + " and " + str(first))
                    else:
                        if len(i.nodes[2].nodes) > 0:
                            first = i.nodes[2].nodes[-1].type
                        else:
                            first = Types.Null()
                        i.nodes[2].type = first

                Enum.missingPattern(typ, i)
                i.type = first if first else Types.Null()

            elif type(i) is Tree.CreateAssign:
                if type(i.nodes[0].name) is Tree.PlaceHolder:
                    p = i.nodes[0].name.nodes[0]
                    node = i.nodes[1].nodes[0]

                    def recur(typ, pattern):
                        if type(pattern) is Tree.Tuple:
                            if not typ.isType(Types.Tuple):
                                node.error("expecting tuple not "+str(typ))
                            if len(pattern) > len(typ.list):
                                diff = len(pattern) - len(typ.list)
                                node.error(diff+" too few values to unpack")
                            elif len(pattern) < len(typ.list):
                                diff = len(typ.list) - len(pattern)
                                node.error(diff+" too many values to unpack")

                            for (index, p) in enumerate(pattern):
                                recur(typ.list[index],p)
                        elif type(pattern) is Tree.InitStruct:
                            for p in pattern:
                                if type(p) is Tree.Assign:
                                    name = p.nodes[0].name
                                    p = p.nodes[1]
                                else:
                                    name = p.name

                                if not name in typ.types:
                                    node.error("Object has no field "+name)
                                recur(typ.types[name],p)
                        else:
                            Scope.addVar(node, parser, pattern.name, Scope.Type(True, typ, i.global_target))
                            pattern.isGlobal = Scope.isGlobal(parser, parser.package, pattern.name)

                    recur(node.type, p)
                elif i.nodes[0].varType is None and i.nodes[0].name != "_":
                    if i.extern:
                        i.error("expecting type declaration, for external variable declaration")
                    i.nodes[0].varType = i.nodes[1].nodes[0].type

                    if i.nodes[0].attachTyp:
                        MethodParser.addMethod(i, parser, i.nodes[0].attachTyp, i.nodes[0].name, i.nodes[1].nodes[0].type)
                        i.nodes[0].isGlobal = True
                    else:
                        Scope.addVar(i, parser, i.nodes[0].name, Scope.Type(i.nodes[0].imutable, i.nodes[1].nodes[0].type, i.global_target))
                        i.nodes[0].isGlobal = Scope.isGlobal(parser, i.nodes[0].package, i.nodes[0].name)

                if i.global_target != parser.global_target:
                    Scope.changeTarget(parser, i.nodes[0].name, i.global_target)
                    #print("this variable can only be used in a specific target", i.global_target)
            elif type(i) is Tree.FuncBody:
                Scope.decrScope(parser)
                def check(n, _i):
                    for c in n:
                        if type(c) is Tree.FuncCall:
                            if not _i.do and not c.partial and not c.curry and c.nodes[0].type.do:
                                c.nodes[0].error("cannot call function with side effects in a pure function")

                        if type(c) is Tree.FuncBody:
                            pass
                        #   check(c, c)

                        elif not c.isEnd():
                            check(c, _i)
                check(i, i)
                if i.global_target != parser.global_target:
                    Scope.changeTarget(parser, i.name, i.global_target)
                    #print("this function can only be used in a specific target", i.global_target)

            elif type(i) is Tree.Create:
                if not i.varType is None:
                    #print(i.owner.global_target)
                    if parser.package != "main" and parser.global_target != "full":
                        print("should be full")

                    Scope.addVar(i, parser, i.name, Scope.Type(i.imutable, i.varType, i.owner.global_target))
                    i.isGlobal = Scope.isGlobal(parser, i.package, i.name)

            elif type(i) is Tree.ReadVar:
                if i.name == "newAtom":
                    if not (type(i.owner) is Tree.FuncCall and i.owner.nodes[0] == i and not i.owner.curry and not i.owner.partial):
                        i.error("expecting function call, with no currying or partial application")

                    if parser.atoms > 0:
                        i.error("can only have one atom per application")

                if not (type(i.owner) is Tree.Assign and type(i.owner.owner) is Tree.InitStruct and i.owner.nodes[0] == i):
                    if i.name in parser.imports and not i.name in parser.from_imports:
                        if not type(i.owner) is Tree.Field:
                            i.error("expecting . after " + i.name + ", cannot directly mention package name")
                    elif type(i.type) is Tree.Type:
                        i.error("unexpected type "+str(i.type))

                    i.type = Scope.typeOfVar(i, parser, i.package, i.name)
                    self = i
                    self.imutable = not Scope.isMutable(parser, self.package, self.name)
                    self.isGlobal = Scope.isGlobal(parser, self.package, self.name)
                    self.package = Scope.packageOfVar(parser, parser.package, self.name)

                    target = Scope.targetOfVar(i, parser, parser.package, self.name)
                    realT = tree.nodes[o_iter].global_target

                    if target == "mustFull":
                        target = "full"

                    if target != parser.global_target and (parser.global_target == "full"):
                        if i.name == "scroll":
                            print(parser.func)

                        root = tree.nodes[o_iter]

                        if type(root) is Tree.FuncBody:
                            try:
                                tree.nodes[o_iter-1].global_target = target
                                tree.nodes[o_iter-2].global_target = target
                            except IndexError:
                                pass

                        if realT != "full" and realT != target:
                            if realT == "mustFull": realT = "full"
                            i.error("variable "+i.name+" is of target "+target+ ", but being used in a context requiring "+realT+" target")

                        root.global_target = target

                    elif realT != target and target != "full" and realT != "full":
                        if realT == "mustFull": realT = "full"
                        i.error("variable "+i.name+" is of target "+target + ", but being used in a "+realT+" target")

            elif type(i) is Tree.Field:
                if i.unary:
                    field = i.field

                    T = Types.T("T", Types.All, "get"+i.field[0].upper()+i.field[1:])

                    I = Types.Interface(False, {field: T})

                    i.type = Types.FuncPointer([I], T, generic=ODict([("T", T)]))
                    count += 1
                    continue

                def bind():
                    if type(i.owner) is Tree.FuncCall and i.owner.nodes[0] == i: return
                    typ = type(i.type)

                    if typ is Types.FuncPointer:
                        if not type(i.nodes[0].type) in [Types.Struct]:
                            bind = Tree.ArrBind(i.field, self.nodes[0], self)
                            bind.type = i.type
                        else:
                            bind = Tree.Bind(r, self.nodes[0], self)
                            bind.type = Types.FuncPointer(self.type.args[1:], self.type.returnType, generic= self.type.generic, do= self.type.do)
                        self.owner.nodes[count] = bind
                        bind.owner = self.owner


                typ = i.nodes[0].type
                t = i.nodes[0]

                if type(typ) is Types.Package:
                    i.indexPackage = True
                    i.type = Scope.typeOfVar(i, parser, i.nodes[0].name, i.field)

                    target = Scope.targetOfVar(i, parser, i.nodes[0].name, i.field)

                    if target != parser.global_target:
                        root = parser.currentNode.nodes[o_iter]

                        if type(root) is Tree.FuncBody:
                            tree.nodes[o_iter-1].global_target = target
                            tree.nodes[o_iter-2].global_target = target

                        root.global_target = target

                    i.nodes[0].package = i.nodes[0].name
                    i.nodes[0].name = ""
                else:
                    if type(typ) is Types.FuncPointer:
                        i.error("type "+str(typ) + " has no field " + i.field)

                    struct = typ

                    self = i
                    try:
                        i.type = struct.types[self.field]

                        if type(i.nodes[0].type) is Types.Array:
                            bind()
                    except KeyError:
                        method = struct.hasMethod(parser, self.field)

                        if not method:
                            self.error("type "+str(typ) + " has no field " + self.field)

                        self.type = method

                        r = Tree.ReadVar(typ.normalName + "_" + self.field, self.type, self)
                        r.type = self.type
                        r.package = typ.package if not typ.package == "_global" else ""
                        r.owner = self.owner

                        if type(i.owner) is Tree.FuncCall and i.owner.nodes[0] == i:
                            self.owner.nodes[0] = r
                            self.owner.nodes.insert(1, self.nodes[0])
                            count += 1
                        else: bind()

            elif type(i) is Tree.Operator and not i.kind == "|>":
                if i.kind == "|>" or i.kind == ">>":
                    self = i

                    if len(self.nodes) != 2:
                        self.error("chain operator cannot be curried")

                    a = self.nodes[0].type
                    b = self.nodes[1].type

                    if i.kind == ">>":
                        if not type(a) is Types.FuncPointer:
                            self.nodes[1].error("right argument must be a function")
                        a = a.returnType

                    if not type(b) is Types.FuncPointer:
                        self.nodes[1].error("left argument must be a function")

                    if len(b.args) != 1:
                        self.nodes[1].error("expecting one function argument that matches return type of piped function")

                    try:
                        b.args[0].duckType(parser, a, self.nodes[0], self.nodes[1], 1)
                    except EOFError as e:
                        if i.kind == ">>":
                            Error.beforeError(e, "Function combining with: ")
                        else:
                            Error.beforeError(e, "Function piping to: ")

                    if i.kind == ">>":
                        a = self.nodes[0].type
                        self.type = Types.FuncPointer(a.args, b.returnType, do= a.do or b.do, generic=a.generic)
                    else:
                        self.type = b.returnType

                        f = Tree.FuncCall(parser)
                        f.addNode(self.nodes[1])
                        f.addNode(self.nodes[0])
                        f.owner = self.owner
                        f.type = b.returnType

                        self.owner.nodes[count] = f
                elif i.kind == "as":
                    i.type.duckType(parser, i.nodes[0].type, i, i.nodes[0], 0)
                elif i.kind == "<-":
                    if i.unary:
                        try:
                            meth = i.nodes[0].type.types["unary_read"]
                        except KeyError:
                            meth = i.nodes[0].type.hasMethod(parser, "unary_read")

                        if meth:
                            i.type = meth.returnType
                            i.opT = i.nodes[0].type
                        else:
                            i.error("type "+str(i.nodes[0].type)+", missing method unary_read")
                    else:
                        try:
                            meth = i.nodes[0].type.types["op_set"]
                        except KeyError:
                            meth = i.nodes[0].type.hasMethod(parser, "op_set")
                        except IndexError as e:
                            print(i.nodes)
                            i.error("can' find nodes[0]")

                        meth.isType(Types.FuncPointer)

                        if meth:
                            meth.args[0].duckType(parser, i.nodes[1].type, i.nodes[1], i, 1)
                            i.opT = i.nodes[0].type
                        else:
                            i.error("type " + str(i.nodes[0].type) + ", missing method op_set")

                        #else:
                        #    i.nodes[0].error("Type " + str(i.nodes[0].type) + ", missing method op_set")

                elif i.kind == "concat":
                    stringable = Types.Interface(False, {"toString": Types.FuncPointer([], Types.String(0))})
                    for c in i:
                        stringable.duckType(parser,c.type,i,i,0)
                    i.type = Types.String(0)
                    i.partial = False
                    i.curry = False
                else:
                    if len(i.nodes) == 0:
                        import collections as coll
                        if i.kind in ["not", "or", "and"]:
                            T = Types.Bool()
                            gen = []
                        else:
                            T = Types.T("T", Types.All, "Operator")
                            gen = [("Operator.T", Types.All)]

                        returnT = T

                        if i.kind in ["==", "!=", "not", "and", "or", "<", ">", "<=", ">="]:
                            returnT = Types.Bool()

                        i.opT = T
                        i.type = Types.FuncPointer([T,T], returnT, coll.OrderedDict(gen))

                        if i.kind != "not":
                            i.unary = False
                    else:
                        partial = False
                        if type(i.nodes[0]) is Tree.Under:
                            partial = True
                            startType = False
                        else:
                            startType = i.nodes[0].type
                            if i.kind in ["not", "and", "or"]:
                                if startType != Types.Bool():
                                    i.nodes[0].error("logical operator "+i.kind+" only works on boolean")

                        for c in i.nodes[1:]:
                            if type(c) is Tree.Under:
                                partial = True
                            elif startType:
                                try:
                                    c.type.duckType(parser, startType, i, c, 0)
                                    startType = c.type
                                except EOFError:
                                    startType.duckType(parser, c.type, c, i, 0)
                            else:
                                startType = c.type
                        i.partial = partial
                        typ = startType
                        if i.kind in ["==", "!=", "not", "and", "or", "<", ">", "<=", ">="]:
                            typ = Types.Bool()

                        if i.curry or i.partial:
                            normal = (1 if i.unary else 2) - len(i.nodes)
                            for c in i.nodes:
                                if type(c) is Tree.Under:
                                    normal += 1

                            if not startType:
                                import collections as coll
                                if i.kind in ["not", "or", "and"]:
                                    T = Types.Bool()
                                    gen = []
                                else:
                                    T = Types.T("t", Types.All, "Operator")
                                    gen = [("t", Types.All)]
                                typ = Types.FuncPointer([T,T], T, coll.OrderedDict(gen))

                                if normal == (1 if i.unary else 2):
                                    i.partial = False
                                    i.curry = True
                                    i.nodes = []
                            else:
                                typ = Types.FuncPointer([startType] * normal, typ)

                        i.type = typ
                        i.opT = startType

                Tree.checkOperator(i, parser)

            elif type(i) is Tree.FuncCall or (type(i) is Tree.Operator and i.kind == "|>"):
                if type(i) is Tree.Operator and i.kind == "|>":
                    i.nodes.reverse()
                    newNode = Tree.FuncCall(i)
                    newNode.nodes = i.nodes

                    i.owner.nodes[count] = newNode
                    newNode.owner = i.owner
                    i = newNode

                c = i

                partial = False

                if not i.nodes[0].type.isType(Types.FuncPointer):
                    i.nodes[0].error("type "+str(i.nodes[0].type)+" is not callable")

                i.nodes[0].type = i.nodes[0].type.toRealType()

                do = i.nodes[0].type.do
                returnType = i.nodes[0].type.returnType

                args = i.nodes[0].type.args
                newArgs = []

                if args.__len__() < len(i.nodes)-1:
                    c = str(len(i.nodes) - 1 - len(args))
                    i.error(("1 argument" if c == "1" else c+" arguments")+" too many, expecting "+str(len(args))+" arguments")

                generics = {}
                for iter in range(len(i.nodes[1:])):
                    if type(i.nodes[iter+1]) is Tree.Under:
                        partial = True
                        newArgs.append(args[iter])
                    else:
                        xnormalTyp = args[iter]
                        myNode = i.nodes[iter+1]
                        myTyp = myNode.type
                        normalNode = i

                        isGen = Types.isGeneric(myTyp)

                        if i.nodes[0].name == "expectLens":
                            print("expecting lens")

                        if Types.isGeneric(xnormalTyp) or isGen:
                            if i.nodes[0].name == "xduce":
                                print("xducing")
                            normalTyp = resolveGen(xnormalTyp, myNode.type, generics, parser, myNode, i)
                            if isGen:
                                myTyp = Types.replaceT(myTyp, generics)
                        else:
                            normalTyp = xnormalTyp


                        normalTyp.duckType(parser, myTyp, i, myNode, iter + 1)

                if i.nodes[0].name == "newAtom":
                    i = i.nodes[0]

                    if parser.dev and parser.hotswap and parser.atomTyp and not parser.run:
                        print("hotswap")
                        parser.atomTyp.duckType(parser, i.owner.nodes[1].type, i.owner.nodes[1], i, 0)

                        f = Tree.Field(0, i.owner.nodes[1].type, i)
                        f.field = "arg"
                        f.type = parser.atomTyp
                        r = Tree.ReadVar("previousState", True, i)
                        r.package = ""
                        f.addNode(r)

                        i.owner.nodes[1] = f
                        f.owner = i.owner

                    parser.atomTyp = i.owner.nodes[1].type
                    parser.atoms += 1

                i = c

                if args.__len__() > len(i.nodes)-1:
                    i.curry = True
                    previosIgnore = i.nodes[0].type.ignore
                    ignore = {(i - len(c.nodes) + 1): previosIgnore[i] for i in previosIgnore}

                    i.type = Types.replaceT(Types.FuncPointer(args[len(i.nodes)-1:], i.nodes[0].type.returnType, generic=i.nodes[0].type.generic, do = i.nodes[0].type.do, ignore= ignore), generics)

                    #i.type = Types.FuncPointer([Types.replaceT(c, generics) for c in args[len(i.nodes)-1:]], Types.replaceT(i.nodes[0].type.returnType, generics),generic= newGenerics, do= do)

                elif not partial:
                    i.type = Types.replaceT(i.nodes[0].type.returnType, generics)
                else:
                    i.partial = True
                    i.type = Types.replaceT(Types.FuncPointer(newArgs, i.nodes[0].type.returnType, do= do, ignore=i.nodes[0].type.ignore), generics)

            elif type(i) is Tree.If:
                ElseExpr.checkIf(parser, i)
            elif type(i) is Tree.Block:
                i.type = i.nodes[-1].type if len(i.nodes) > 0 else Types.Null()
            elif type(i) is Tree.Assign:
                if type(i.owner) is Tree.InitStruct:
                    pass
                elif not (type(i.owner) is Tree.CreateAssign and i.owner.nodes[0].varType is None):
                    if type(i.owner) is Tree.CreateAssign and i.owner.extern:
                        if not type(i.nodes[0].type) is Types.String:
                            i.error("expecting String")
                    else:
                        normalNode = i.owner.nodes[0] if i.init else i.nodes[1]
                        normalTyp = i.owner.nodes[0].varType if i.init else i.nodes[0].type
                        myNode = (i.nodes[0] if i.init else i.nodes[1])

                        normalTyp.duckType(parser, myNode.type, normalNode, myNode, (0 if i.init else 1))

            elif type(i) is Tree.Tuple:
                if len(i.nodes) == 0:
                    i.error("unexpected )")
                elif len(i.nodes) > 1:
                    i.type = Types.Tuple([c.type for c in i])
                else:
                    i.type = i.nodes[0].type
            elif type(i) is Tree.Array:
                arr = i

                if len(i.nodes) > 0:
                    if arr.init or arr.range:
                        if arr.nodes[0].type != Types.I32():
                            arr.nodes[0].error("expecting integer for range start, not "+str(arr.nodes[1].type))

                        if arr.range:
                            if arr.nodes[1].type != Types.I32():
                                arr.nodes[1].error("expecting integer for range end, not "+str(arr.nodes[1].type))
                            typ = Types.I32()
                        else:
                            if len(arr.nodes) > 1:
                                typ = arr.nodes[1].type
                            else:
                                arr.nodes[0].error("expecting value after :")

                    else:
                        c = arr.nodes[0]
                        if type(c) is Tree.Operator and c.kind == "..":
                            if not type(c.nodes[0].type) is Types.Array:
                                c.nodes[0].error("Expecting array")
                            typ = c.nodes[0].type.elemT
                        else:
                            typ = c.type
                        if typ == Types.Null():
                            arr.error("array elements must be non none")

                        count = 0
                        for c in arr.nodes[1:]:
                            err = False
                            if typ != c.type:
                                if type(c) is Tree.Operator and c.kind == "..":
                                    if not type(c.nodes[0].type) is Types.Array:
                                        c.nodes[0].error("Expecting array")
                                    ctype = c.nodes[0].type.elemT
                                else:
                                    ctype = c.type
                                try:
                                    typ.duckType(parser, ctype, i, c, count)
                                except EOFError as prevE:
                                    try:
                                        ctype.duckType(parser, typ, c, i, count)
                                        typ = ctype
                                    except EOFError as e:
                                        """try:
                                            u = Types.Union([ctype, typ])
                                            Types.checkUnion(parser, u)
                                            typ = u"""

                                        err = prevE

                                if err:
                                    Error.beforeError(err, "Element type in array: ")

                            count += 1

                    arr.type = Types.Array(arr.mutable, typ)
            elif type(i) is Tree.InitPack:
                parser.imports.append(i.package)
            elif type(i) is Tree.InitStruct:
                unary = i.unary
                if not unary:
                    typ = i.constructor.type
                    i.typ = typ

                    assign = True
                    if typ.isType(Struct.Struct):
                        s = typ
                        assign = False
                        i.paramNames = Struct.offsetsToList(s.offsets)
                    elif typ.isType(Types.Interface) or typ.isType(Types.Struct):
                        assign = True
                        s = typ
                    else:
                        i.constructor.error("type "+str(typ)+" can not be used as a constructor")

                    i.s = s
                    name = s.name

                    types = normalTyp = s._types if type(s) is Struct.Struct else s.types

                    if len(types) < len(i.nodes) - 1:
                        c = str(len(i.nodes) - 1 - len(s.types))
                        i.error(("1 argument" if c == "1" else c + " arguments") + " too many")
                    elif not assign and len(types) > len(i.nodes) - 1:
                        c = str(len(types) + 1 - len(i.nodes))
                        i.error(("1 argument" if c == "1" else c + " arguments") + " too few")
                else:
                    assign = True


                gen = {}
                randomOrder = False
                order = {}

                for iter in range(0 if unary else 1, len(i.nodes)):
                    if type(i.nodes[iter]) is Tree.Assign:
                        randomOrder = True
                    elif assign:
                        i.nodes[iter].error("expecting =")

                    if not randomOrder:
                        order[i.paramNames[iter-1]] = i.nodes[iter]
                        myNode = i.nodes[iter]
                        normalTyp = s.fieldType[iter-1]
                    else:
                        if not type(i.nodes[iter]) is Tree.Assign:
                            i.nodes[iter].error("positional argument follows keyword argument")
                        if i.nodes[iter].nodes[0].name in order:
                            i.nodes[iter].nodes[0].error("duplicate parameter")
                        order[i.nodes[iter].nodes[0].name] = i.nodes[iter]
                        myNode = i.nodes[iter].nodes[1]
                        xname = i.nodes[iter].nodes[0].name

                        if not unary:
                            try:
                                normalTyp = types[xname]
                            except KeyError:
                                i.nodes[iter].nodes[0].error("type "+str(s)+" does not have the field "+ xname)

                    normalNode = i

                    if not unary:
                        xnormalTyp = normalTyp

                        if i.package == "main":
                            dcx = 90

                        isGen = Types.isGeneric(normalTyp)
                        myIsGen = Types.isGeneric(myNode.type)

                        myTyp = myNode.type

                        if isGen:
                            normalTyp = resolveGen(normalTyp, myNode.type, gen, parser, myNode, i)

                            if myIsGen:
                                myTyp = Types.replaceT(myNode.type, gen)
                            else:
                                myTyp = myNode.type

                        normalTyp.duckType(parser, myTyp, i, myNode, iter)

                        #resolveGen(xnormalTyp, myNode.type, gen, parser, myNode, i)

                if not assign:
                    for c in order:
                        i.nodes[s.offsets[c]] = order[c]
                i.assign = assign

                if i.assign:
                    if unary:
                        types = {c: order[c].nodes[1].type for c in order}
                        i.type = Types.Interface(False, types)
                    else:
                        i.type = typ
                else:
                    package = parser.structs[i.package][name].package
                    i.type = Types.Struct(i.mutable, name, s._types, package, gen)

            elif type(i) is Tree.ArrRead:
                if len(i.nodes) == 2:
                    typ = i.nodes[0].type
                    try:
                        func = typ.types["get"]
                    except KeyError:
                        func = typ.getMethod(parser, "get")
                        if not func:
                            i.nodes[0].error("Type "+str(i.nodes[0].type)+" is not indexable, missing method get")

                    arrRead = i
                    if len(arrRead.nodes) != 2:
                        i.nodes[1].error("expecting single index")

                    if len(func.args) != 1:
                        i.nodes[0].error(str(typ) + " is not indexable, method get should take 1 paramter, not "+len(func.args))

                    try:
                        func.args[0].duckType(parser, i.nodes[1].type, i.nodes[1], i, 0)
                    except EOFError as e:
                        Error.beforeError(e, "Index : ")

                    arrRead.type = func.returnType
                else:
                    i.error("expecting single index")
            elif type(i) is Tree.Generic:
                if not Types.isGeneric(i.nodes[0].type):
                    i.nodes[0].error("expecting generic type")

                gen = i.nodes[0].type.generic

                if len(gen) > len(i.generic):
                    i.error("missing "+str(len(gen)-len(i.generic))+" generic parameters")
                elif len(gen) < len(i.generic):
                    i.error(str(len(i.generic)-len(gen))+" too many generic parameters")

                v = list(gen.keys())
                replace = {v[index]: c for index, c in enumerate(i.generic)}

                for index, c in enumerate(gen):
                    if not type(i.generic[index]) is Types.Underscore:
                        g = gen[c].type if type(gen[c]) is Types.T else gen[c]
                        g.duckType(parser, i.generic[index], i.nodes[0], i, 0)
                    else:
                        del replace[c]

                i.type = Types.replaceT(i.nodes[0].type, replace)

                #i.nodes[0].type.duckType(parser, i.type, i, i.nodes[0])
            elif type(i) is Tree.Block:
                if len(i.nodes) > 0:
                    i.type = i.nodes[-1].type
            else:
                for c in checkTyp:
                    if checkTyp[c](i):
                        break

            if type(i) in [Tree.Block, Tree.While]:
                Scope.decrScope(parser)

            tree = treeBefore
            o_iter = o_iterBefore
            count += 1

    loop(tree, -1)

def validate(parser, tree):
    for i in tree:
        if type(i) is Tree.Lambda:
            Scope.incrScope(parser)
        if not i.isEnd():
            validate(parser, i)
        i.validate(parser)

    if type(tree) is Tree.Root:
        tree.validate(parser)

def resolveGen(shouldBeTyp, normalTyp, generics, parser, myNode, other):
    if shouldBeTyp.name == "main.execute.T":
        #and shouldBeTyp.name == "main._.B":
        print(normalTyp)
        print(shouldBeTyp)
        #and normalTyp.name == "main._.B":
        print("comparing execute and main.B")

    if type(normalTyp) is Types.T and not (normalTyp.owner in parser.func) and normalTyp.name != shouldBeTyp.name:
        if normalTyp.normalName in generics:
            normalTyp = generics[normalTyp.normalName]
        else:
            newTyp = Types.replaceT(shouldBeTyp, generics)

            tmp = normalTyp

            generics[normalTyp.normalName] = newTyp
            normalTyp = newTyp

            normalTyp = resolveGen(tmp.type, newTyp, generics, parser, myNode, other)

                #print(normalTyp)
                #print(newTyp)

            normalTyp.duckType(parser, newTyp, myNode, other, 0)
            normalTyp = newTyp

    if type(shouldBeTyp) is Types.T:
        if shouldBeTyp.normalName in generics:
            tmp = generics[shouldBeTyp.normalName]
            normalTyp = Types.replaceT(normalTyp, generics)
            try:
                tmp.duckType(parser, normalTyp, myNode, other, 0)
            except EOFError as e:
                normalTyp.duckType(parser, tmp, myNode, other, 0)

                generics[shouldBeTyp.normalName] = normalTyp
            return tmp
        else:
            generics[shouldBeTyp.normalName] = normalTyp
            if normalTyp.name != shouldBeTyp.name:
                tmp = shouldBeTyp.type
                tmp = resolveGen(tmp, normalTyp, generics, parser, myNode, other)
                tmp.duckType(parser, normalTyp, myNode, other, 0)
            else:
                tmp = shouldBeTyp

        #if Types.isGeneric(tmp):
        #    resolveGen(tmp, normalTyp, generics, parser, myNode, other)
        #else:
        return normalTyp

    elif type(shouldBeTyp) is Types.Array:
        if type(normalTyp) != Types.Array:
            return shouldBeTyp

        try:
            t = Types.Array(False, resolveGen(shouldBeTyp.elemT, normalTyp.elemT, generics, parser, myNode, other))
        except EOFError as e:
            Error.beforeError(e, "Element type in array: ")

        return t
    elif type(shouldBeTyp) is Types.FuncPointer:
        args = []
        if not normalTyp.isType(Types.FuncPointer):
            print("not in type", normalTyp)
            return Types.replaceT(shouldBeTyp, generics)

        if len(shouldBeTyp.args) != len(normalTyp.args):
            return Types.replaceT(shouldBeTyp, generics)

        for (count, (should, nor)) in enumerate(zip(shouldBeTyp.args, normalTyp.args)):
            try:
                res = resolveGen(nor, should, generics, parser, myNode, other)
                args.append(Types.replaceT(should, generics))
            except EOFError as e:
                Error.beforeError(e, "Function type argument "+str(count)+": ")

        try:
            returnTyp = resolveGen(shouldBeTyp.returnType, normalTyp.returnType, generics, parser, myNode, other)
        except EOFError as e:
            Error.beforeError(e, "Function type return type: ")

        return Types.FuncPointer(args, returnTyp, do=shouldBeTyp.do)

    elif type(shouldBeTyp) is Types.Union:
        if type(normalTyp) is Types.Union:
            shouldBeTyp = Types.replaceT(shouldBeTyp, generics)
            return shouldBeTyp
        else:
            shouldBeTyp = Types.replaceT(shouldBeTyp, generics)
            try:
                index = shouldBeTyp.different_types.index(normalTyp)
            except ValueError:
                return shouldBeTyp

            resolveGen(shouldBeTyp.different_types[index], normalTyp, generics, parser, myNode, other)
            return Types.replaceT(shouldBeTyp, generics)

    elif type(shouldBeTyp) is Types.Tuple:
        if not type(normalTyp) is Types.Tuple:
            return shouldBeTyp

        arr = []
        for (key, (should, nor)) in enumerate(zip(shouldBeTyp.list, normalTyp.list)):
            try:
                arr.append(resolveGen(should, nor, generics, parser, myNode, other))
            except EOFError as e:
                Error.beforeError(e, "Tuple element #" + str(key) + ": ")

        return Types.Tuple(arr)
    elif type(shouldBeTyp) is Types.Alias:
        resolveGen(shouldBeTyp.typ, normalTyp, generics, parser, myNode, other)
        return Types.replaceT(shouldBeTyp, generics)
    elif type(shouldBeTyp) in [Types.Struct, Types.Enum]:
        gen = generics
        if not type(normalTyp) is type(shouldBeTyp):
            return shouldBeTyp
        self = shouldBeTyp
        other = normalTyp
        if self.package+"_"+self.normalName != other.package+"_"+other.normalName:
            return shouldBeTyp

        types = {}
        shouldGeneric = shouldBeTyp.remainingGen
        if type(shouldBeTyp) in [Types.Enum, Types.Alias]:
            normalGeneric = normalTyp.generic
        else:
            normalGeneric = normalTyp.gen

        for i in shouldGeneric:
            try:
                generics[i] = resolveGen(shouldGeneric[i], normalGeneric[i], generics, parser, myNode, other)
            except EOFError as e:
                Error.beforeError(e, "Field '" + i + "' in " + str(shouldBeTyp) + ": ")

        if type(shouldBeTyp) is Types.Enum:
            return Types.Enum(self.package, self.normalName, self.const, generics)
        else:
            return Types.Struct(False, self.normalName, self.types, self.package, generics)

    elif type(shouldBeTyp) is Types.Assign:
        const = shouldBeTyp.const
        return Types.Assign(Types.replaceT(const, generics))
    elif type(shouldBeTyp) is Types.Interface:
        types = {}
        for i in shouldBeTyp.types:
            try:
                types[i] = resolveGen(shouldBeTyp.types[i], normalTyp.types[i], generics, parser, myNode, other)
            except EOFError as e:
                Error.beforeError(e, "Field '" + i + "' in " + str(shouldBeTyp) + ": ")
            except KeyError:
                try:
                    meth = normalTyp.hasMethod(parser, i)
                    if type(meth) is Types.FuncPointer:
                        types[i] = resolveGen(shouldBeTyp.types[i], Types.FuncPointer(meth.args[1:], meth.returnType, generic= meth.generic, do= meth.do), generics, parser, myNode, other)
                    elif meth:
                        types[i] = meth
                    else:
                        types[i] = shouldBeTyp.types[i]
                except AttributeError:
                    types[i] = shouldBeTyp.types[i]

        gen = ODict()

        for key in shouldBeTyp.generic:
            gen[key] = Types.replaceT(shouldBeTyp.generic[key], generics)

        #gen = {i: generics[i] for i in generics if ".".join(i.split(".")[:-1]) == shouldBeTyp.normalName}
        r = Types.Interface(False, types, gen, shouldBeTyp.normalName)
        return r
    else:
        return shouldBeTyp