__author__ = 'antonellacalvia'


import AST as Tree
from .Scope import *
from .Error import *
import collections as coll


def checkUnion(parser, u):
    usedTypes = []
    for i in u.different_types:
        if type(i) in [Struct, Enum, Union, T]:
            if type(i) is Union:
                Error.parseError(parser, "Cannot have union type be one of the possible union types.")
        elif type(i) in usedTypes:
            kind = {
                I32: "int",
                Interface: "object",
                String: "string",
                Bool: "bool",
            }
            Error.parseError(parser, "Duplicate kind of type " + kind[type(i)])
        else:
            usedTypes.append(type(i))

def parseType(parser, _package= "", _mutable= False, _attachTyp= False, _gen= {}):

    def before():
        if _package == "":
            package = parser.package
        else:
            package = _package

        gen = _gen
        attachTyp = _attachTyp
        mutable = _mutable

        token = parser.thisToken().token
        if token == "i32":
            return I32()
        elif token == "float":
            return Float()
        elif token == "string":
            return String(0)
        elif token == "int":
            return I32()
        elif token == "bool":
            return Bool()
        elif token == "(":
            args = []
            parser.nextToken()
            while parser.thisToken().token != ")":
                if parser.thisToken().token == ",":
                    if parser.lookBehind().token == ",":
                        parseError(parser, "unexpected ,")
                    parser.nextToken()
                    continue
                args.append(parseType(parser))

                parser.nextToken()

            return Tuple(args)
        elif token == "enum":
            return EnumT()
        elif token == "[" or parser.thisToken().type == "whiteOpenS":
            incrScope(parser)
            if parser.lookInfront().token != "]":
                from TopCompiler import FuncParser
                gen = FuncParser.generics(parser, "_")
                if parser.thisToken().token != "|":
                    parseError(parser, "expecting |")

                res = parseType(parser, package, mutable, attachTyp, gen)

                decrScope(parser)

                return res
            else:
                parser.nextToken()
                parser.nextToken()
                decrScope(parser)
                return Array(False, parseType(parser, package))
        elif token == "|":
            parser.nextToken()


            args = []
            while not (parser.thisToken().token == "|" and parser.lookInfront().token in ["->", "do"]):
                if parser.thisToken().token == ",":
                    if parser.lookBehind().token == ",":
                        parseError(parser, "unexpected ,")
                    parser.nextToken()
                    continue

                args.append(parseType(parser))

                parser.nextToken()

            ret = Null()

            do = False

            if parser.lookInfront().token == "->":
                parser.nextToken()
                parser.nextToken()

                ret = parseType(parser, package)

            if parser.lookInfront().token == "do":
                parser.nextToken()
                parser.nextToken()

                ret = parseType(parser, package)
                do = True

            return FuncPointer(args, ret, gen, do)
        elif token == "none":
            return Null()
        elif token in parser.imports:
            if parser.lookInfront().token == ".":
                parser.nextToken()
                parser.nextToken()
                return parseType(parser, token)
            else:
                parseError(parser, "expecting .")

        elif token == "{" or parser.thisToken().type == "bracketOpenS":
            args = {}
            parser.nextToken()
            while parser.thisToken().token != "}":
                if parser.thisToken().token == ",":
                    pass
                else:
                    name = parser.thisToken().token
                    if parser.thisToken().type != "identifier":
                        Error.parseError(parser, "expecting identifier")
                    if parser.nextToken().token != ":":
                        Error.parseError(parser, "expecting :")

                    parser.nextToken()
                    typ = parseType(parser)
                    args[name] = typ

                parser.nextToken()

            return Interface(False, args)

        elif (token in parser.interfaces[package]) or (token in parser.interfaces["_global"] and parser.package == package):
            if token in parser.interfaces["_global"]:
                package = "_global"

            if parser.interfaces[package][token].generic != coll.OrderedDict():
                if parser.lookInfront().token != "[":
                    #parseError(parser, "must specify generic parameters for generic type")
                    pass
                else:
                    parser.nextToken()
                    gen = parseGeneric(parser, parser.interfaces[package][token])
                    return replaceT(parser.interfaces[package][token], gen)

            return parser.interfaces[package][token]

        elif token in parser.structs[package]:
            gen = coll.OrderedDict()
            if attachTyp:

                return parser.structs[package][token]
            if parser.structs[package][token].generic != {}:
                if parser.nextToken().token != "[":
                    parseError(parser, "must specify generic parameters for generic type")
                gen = parseGeneric(parser, parser.structs[package][token])
            elif parser.lookInfront().token == "[":
                parser.nextToken()
                parseError(parser, "unexpected [, type isn't generic")

            return Struct(mutable, token, parser.structs[package][token]._types, parser.structs[package][token].package, gen)

        elif varExists(parser, package, token):
            t = typeOfVar(Tree.PlaceHolder(parser), parser, package, token)
            if type(t) is T:
                return t
            parseError(parser, "unkown type "+token)
        elif token == "_":
            return Underscore()
        else:
            parseError(parser, "unknown type "+token)

    res = before()

    if parser.lookInfront().token == "{":
        parser.nextToken()
        if parser.nextToken().token != "}":
            Error.parseError(parser, "expecting }")
        return Assign(res)
    elif parser.lookInfront().token == "or":
        parser.nextToken()
        parser.nextToken()
        newRes = parseType(parser, _package, _mutable, _attachTyp, _gen)
        u = Union(combineUnionTypes([res, newRes]))

        checkUnion(parser, u)
        return u
    else:
        return res

def combineUnionTypes(unions):
    arr = []
    for i in unions:
        if type(i) is Union:
            arr += combineUnionTypes(i.different_types)
        else:
            arr.append(i)
    return arr

def parseGeneric(parser, typ):
    generic = []

    parser.nextToken()

    gen = typ.generic
    genL = list(gen.values())

    count = -1
    while parser.thisToken().token != "]":
        count += 1
        if parser.thisToken().token == ",":
            parser.nextToken()
            continue

        if parser.thisToken().token == "_":
            generic.append(genL[count].type)
        else:
            generic.append(parseType(parser))
        parser.nextToken()

    if len(gen) > len(generic):
        parseError(parser, "missing "+str(len(gen)-len(generic))+" generic parameters")
    elif len(gen) < len(generic):
        parseError(parser, str(len(generic)-len(gen))+" too many generic parameters")

    v = list(gen.keys())
    replace = {v[index]: i for index, i in enumerate(generic)}

    return replace

class Type:
    name = "type"
    normalName = ""

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    #def __hash__(self):
    #    return hash(self.name)

    def toRealType(self):
        return self

    def getMethod(self, parser, name):
        pass

    def __eq__(self, other):
        if type(self) is Alias:
            self = self.typ
        if type(other) is Alias:
            other = other.typ
        if type(other) is bool:
            print("error")

        return other.name == self.name

    def __ne__(self, other):
        return not self == other

    def duckType(self, parser, other, node, mynode, iter):
        if type(other) is Unknown:
            other.duckType(parser, self, node, mynode, iter)
            return

        if self != other:
            mynode.error("expecting type "+str(self)+" and got type "+str(other))
    
    def isType(self, other):
        if type(other) is not type:
            if type(other) is Unknown:
                return other.isType(type(self))
            else:
                return type(self) is type(other)

        return type(self) is other

    def hasMethod(self, parser, field): pass

class EnumT(Type):
    def __init__(self):
        self.name = "enumT"
        self.types = {}

    def duckType(self, parser, other, node, mynode, iter):
        if not type(other) in [Enum, EnumT]:
            node.error("type "+str(other)+" is not an enum")

class Assign(Type):
    def __init__(self, const):
        self.const = const
        self.name = str(self.const) + "{}"
        self.types = {}

    def duckType(self, parser, other, node, mynode, iter):
        
        
        const = self.const.types
        typ = other.types

        for i in typ:
            if not i in const:
                node.error("type "+str(other)+" has the field "+i+" to much to be casted into "+str(self))
            else:
                if not type(typ[i]) is Null:
                    try:
                        const[i].duckType(parser, typ[i], node, mynode, iter)
                    except EOFError as e:
                        Error.beforeError(e, "In field "+i+" : ")

class StructInit(Type):
    def __init__(self, name):
        self.name= name+" type"
        self.types= {}

    def __str__(self):
        return self.name

""""
def newType(n):
    class BasicType(Type):
        name=n
        normalName=n
        package= "_global"
        types = {"toString": FuncPointer([], String(0))}

    return BasicType
"""

class String(Type):
    def __init__(self, length=0):
        self.name = "string"
        self.types = {"toString": FuncPointer([], self), "toInt": FuncPointer([], I32()), "toFloat": FuncPointer([], Float()),
            "slice": FuncPointer([I32(), I32()], self),
            "length": I32(),
            "indexOf": FuncPointer([self], I32()),
            "replace": FuncPointer([self, self], self),
            "toLowerCase": FuncPointer([], self),
            "op_eq": FuncPointer([self], Bool()),
            "op_add": FuncPointer([self], self),
            "op_gt": FuncPointer([self], Bool()),
            "op_lt": FuncPointer([self], Bool()),
            "split": FuncPointer([self], Array(False, self)),
            "get": FuncPointer([Types.I32()], self),
            "endsWith": FuncPointer([self], Bool())
        }

class FuncPointer(Type):
    def __init__(self, argtypes, returnType, generic= coll.OrderedDict(), do= False, ignore=[]):
        self.args = argtypes
        self.name = "|"+", ".join([(ignore[count]+" " if count in ignore else "") + i.name for (count, i) in enumerate(argtypes)])+"| " +  ("do " if do else "-> ") +returnType.name

        self.returnType = returnType
        self.generic = generic
        self.types = {}
        self.do = do
        self.isLambda = False
        self.ignore = ignore

    def check(self):
        pass

    def duckType(self, parser, other, node, mynode, iter= 0):
        if not other.isType(FuncPointer):
            mynode.error("expecting function type "+str(self)+" and got type "+str(other))

        other = other.toRealType()
        if other.args.__len__() != len(self.args):
            mynode.error("expecting function type "+str(self)+" and got type "+str(other))

        if not self.do and other.do:
            mynode.error("Expecting pure function " + str(self) + " and got effectfull function " + str(other))
        elif self.do and not (other.do == True):
            mynode.error("Expecting effectfull function " + str(self) + " and got pure function " + str(other))

        count = -1
        for a in self.args:
            count += 1
            i = other.args[count]
            if type(i) is FakeList:
                print("error")

            try:
                i.duckType(parser, a, mynode, node, iter)
            except EOFError as e:
                beforeError(e, "Function type argument "+str(count)+": ")

        #if type(self.returnType) is Types.Null:
        #    return

        try:
            self.returnType.duckType(parser, other.returnType, node, mynode, iter)
        except EOFError as e:
            beforeError(e, "Function type return type: ")

def isPart(i, name):
    return ".".join(i.split(".")[:-1]) == name

import copy

class Union(Type):
    def __init__(self, different_types):
        self.different_types = different_types
        self.types = {}
        for type in different_types:
            for field in type.types:
                if not field in self.types:
                    self.types[field] = type.types[field]

            for field in copy.copy(self.types):
                if not field in type.types:
                    del self.types[field]
                else:
                    if not self.types[field] == type.types[field]: #not sure if should duck type or not
                        del self.types[field]

        self.name = (" or ").join((str(i) for i in self.different_types))

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        if self.name == other.name: return True
        return other in self.different_types


    def duckType(self, parser, other, node, mynode, iter):
        if other.isType(Union):
            for typ in other.different_types:
                if not typ in self.different_types:
                    node.error("Type " + str(other) + ", contains unsupported type "+str(typ))
            for typ in self.different_types:
                if typ in other.different_types:
                    return

            node.error("Type " + str(other.realType()) + ", isn't " + str(self))
            return

        for typ in self.different_types:
            try:
                if str(other) == "Dict[string,|| do string]":
                    print("should work")
                typ.duckType(parser, other, node, mynode, iter)
                return
            except EOFError:
                pass

        node.error("Type "+str(other)+", isn't "+str(self))

    @property
    def const(self):
        return self.different_types

    def __str__(self):
        return (" or ").join((str(i) for i in self.different_types))

class Struct(Type):
    def __init__(self, mutable, name, types, package, gen=coll.OrderedDict()):
        self.types = types

        self.types = {i: replaceT(types[i], gen) for i in types}

        self.package = package

        self.normalName = name
        self.mutable = mutable

        self.gen = gen
        self.remainingGen = areParts(gen, package+"."+name)

        gen = self.remainingGen

        #print(self.gen)

        genericS = "[" + ",".join([str(gen[i]) for i in gen]) + "]" if len(gen) > 0 else ""

        self.name = package + "." + name + genericS
        #print(self.name)

    def hasMethod(self, parser, field):
        try:
            m = parser.structs[self.package][self.normalName].hasMethod(parser, field)
        except KeyError:
            try:
                m = parser.interfaces[self.package][self.normalName].types[field]
            except KeyError:
                m = False

        if m:
            return replaceT(m, self.gen)

    def duckType(self, parser, other, node, mynode, iter=0):
        
        if self.gen != {} and self.name == other.name:
            return

        if not other.isType(Struct):
            node.error("expecting type "+str(self)+", not "+str(other))
        if self.package == other.package and self.normalName != other.normalName:
            node.error("expecting type "+str(self)+", not "+str(other))

        """
        for key in other.remainingGen:
            i = self.gen[key]
            othk = other.gen[key]

            try:
                i.duckType(parser, othk, node, mynode, iter)
            except EOFError as e:
                beforeError(e, "Generic argument "+key+": ")
        """

        for name in self.remainingGen:
            a = self.gen[name]
            b = other.gen[name]

            if not (b.isType(T) and b.owner == self.package+"."+self.normalName):
                try:
                    a.duckType(parser, b, node, mynode, iter)
                except EOFError as e:
                    beforeError(e, "For generic parameter " + name + ": " + "Expecting type " + str(a) + ", but got type " + str(b))

class Tuple(Type):
    def __init__(self, types):
        self.list = types
        self.types = dict([(str(index), i) for (index, i) in enumerate(types)])

        array = list(range(0, len(self.types)))
        for i in self.types:
            array[int(i)] = str(self.types[i])
        self.name = "(" + ",".join(array) + ")"

    def duckType(self, parser, other, node, mynode, iter):
        
        if not other.isType(Tuple):
            node.error("expecting type "+str(self)+", not "+str(other))

        if len(self.types) != len(other.types):
            node.error("expecting tuple of length "+str(len(self.types))+", not "+str(len(other.types)))

        for key in self.types:
            i = self.types[key]
            othk = other.types[key]

            try:
                i.duckType(parser, othk, node, mynode, iter)
            except EOFError as e:
                beforeError(e, "Tuple element #" + key + ": ")

class Array(Type):
    def __init__(self, mutable, elemT, empty=False):
        self.name = "[]"+elemT.name

        self.elemT = elemT

        self.package = "_global"
        self.normalName = "array"

        self.mutable = mutable
        self.__types = None
        self.empty = empty

    @property
    def types(self):
        if not self.__types:
            self.__types = {
                "toString": FuncPointer([], String(0)),
                "append": FuncPointer([self.elemT], self),
                "insert": FuncPointer([I32(), self.elemT], self),
                "map": FuncPointer(
                    [FuncPointer([self.elemT], T("T", All, "Array"))],
                    Array(False, T("T", All,  "Array")),
                    coll.OrderedDict([("Array.T", All)])
                ),
                "remove": FuncPointer([I32()], self),
                "serial": FuncPointer(
                    [FuncPointer([self.elemT], T("T", All, "Array"), do=True)],
                    Array(False, T("T", All, "Array")),
                    generic=coll.OrderedDict([("Array.T", All)]),
                    do=True
                ),
                "parallel": FuncPointer(
                    [FuncPointer([self.elemT], T("T", All, "Array"), do=True)],
                    Array(False, T("T", All, "Array")),
                    generic=coll.OrderedDict([("Array.T", All)]),
                    do=True
                ),
                "set": FuncPointer([I32(), self.elemT], self)
                ,
                "filter": FuncPointer(
                    [FuncPointer([self.elemT], Bool())],
                    self,
                ),
                "get": FuncPointer([I32()], self.elemT),
                "reduce": FuncPointer(
                    [FuncPointer([self.elemT, self.elemT], self.elemT)],
                    self.elemT,
                ),
                "has": FuncPointer(
                    [self.elemT],
                    Bool()
                ),
                "indexOf": FuncPointer(
                    [self.elemT],
                    I32()
                ),
                "op_add": FuncPointer(
                    [self.elemT],
                    Array(False, self.elemT)
                ),
                "length": I32(),
                "join": FuncPointer([String(0)], String(0)),
                "shorten": FuncPointer([Types.I32()], self),
                "slice": FuncPointer([Types.I32(), Types.I32()], self)
            }

        return self.__types
    def duckType(self, parser, other, node, mynode, iter):
        
        if not other.isType(Array):
            mynode.error("expecting array type "+str(self)+" not "+str(other))

        if other.empty:
            return

        try:
            self.elemT.duckType(parser, other.elemT, node, mynode, iter)
        except EOFError as e:
            beforeError(e, "Element type in array: ")

def isMutable(typ):
    if type(typ) in [Struct, Array]:
        return typ.mutable
    return False

def areParts(generic, name):
    c = coll.OrderedDict()

    for i in generic:
        if isPart(i, name):
            c[i] = generic[i]

    return c

class Interface(Type):
    def __init__(self, mutable, args, generic= coll.OrderedDict(), name=""):
        generic = areParts(generic, name)
        if name != "":
            gen = generic
            genericS = "[" + ",".join([str(gen[i]) for i in gen]) + "]" if len(gen) > 0 else ""
            self.name = name+genericS
        else:
            self.name = "{"+", ".join([str(i + ": " + str(args[i])) for i in args])+"}"
        self.mutable = False
        self.types = args
        self.generic = generic
        self.normalName = name

    def fromObj(self, obj):
        self.name = obj.name
        self.types = obj.types
        self.generic = obj.generic
        self.normalName = obj.normalName

        return self

    def hasMethod(self, parser, field):
        """if field in self.types:
            return self.types[field]
        """
        pass
    def duckType(self, parser, other, node, mynode, iter):
        if self.generic != {} and self.name == other.name:
            return

        try:
            isStruct = other
            isStruct.types
            isStruct.hasMethod
        except:
            mynode.error("expecting type "+str(self)+" not "+str(other))

        notInField = False

        ended = False

        if self.normalName == other.normalName and len(self.generic) > 0:
            for name in self.generic:
                a = self.generic[name]
                try:
                    b = other.generic[name]
                except:
                    ended = False
                    continue

                if not (b.isType(T) and b.owner == self.normalName):
                    try:
                        a.duckType(parser, b, node, mynode, iter)
                    except EOFError:
                        mynode.error("For generic parameter " + name + ": " + "Expecting type " + str(
                            a) + ", but got type " + str(b))

                    #if a != b:
                    #    ended = False
                    #    break
                    #    mynode.error("For generic parameter " + name + ": " + "Expecting type " + str(a) + ", but got type " + str(b))
            return

        if ended and len(self.generic) > 0: return

        i = 0
        try:
            for field in self.types:
                if field in isStruct.types:
                    self.types[field].duckType(parser, isStruct.types[field], node, mynode, iter)
                else:
                    meth = isStruct.hasMethod(parser, field)
                    if meth:
                        if meth.isType(FuncPointer):
                            self.types[field].duckType(parser, FuncPointer(meth.args[1:], meth.returnType, do= meth.do, generic=meth.generic), node, mynode, iter)
                        else:
                            self.types[field].duckType(parser, meth, node, mynode, iter)
                            #mynode.error("field "+str(other)+"."+field+" is supposed to be type "+str(self.types[field])+", not "+str(meth))
                    else:
                        notInField = True
                        mynode.error("type "+str(other)+" missing field "+field+" to be upcasted to "+str(self))

                i += 1
        except EOFError as e:
            if notInField:
                beforeError(e, "")
            else:
                beforeError(e, "Field '" + field + "' in " + str(other) + ": ")

class T(Type):
    def __init__(self, name, typ, owner):
        self.type = typ
        self.normalName = owner+"."+name
        self.name = owner+"."+name
        self.types = self.type.types
        self.owner = owner
        self.realName = name

    def duckType(self, parser, other, node, mynode, iter):
        
        if self.name == other.name:
            return True

        if other.isType(T) and self.normalName != other.normalName and self.type == other.type:
            return True

        Type.duckType(self, parser, other, node, mynode, iter)
        #self.type.duckType(parser, other, node, mynode, iter)

    def hasMethod(self, parser, name):
        self.type.hasMethod(parser, name)

    def __repr__(self):
        return self.name+":"+str(self.type)

class Enum(Type):
    def __init__(self, package, name, const, generic):
        self.generic = generic
        self.gen = generic

        self.const = const
        self.types = {}

        self.package = package
        self.normalName = name

        remaining = remainingT(self)

        self.remainingGen = remaining
        self.methods = {}

        gen = self.remainingGen

        # print(self.gen)

        genericS = "[" + ",".join([str(gen[i]) for i in gen]) + "]" if len(gen) > 0 else ""

        self.name = (package + "." if package != "_global" else "") + name + genericS

    def fromObj(self, other):
        self.remainingGen = other.remainingGen
        self.generic = other.generic
        self.gen = other.generic
        self.methods = other.methods

        self.name = other.name
        self.const = other.const
        self.package = other.package
        self.normalName = other.normalName

    def addMethod(self, i, parser, name, method):
        package = parser.package

        if package in self.methods:
            if name in self.methods[package]:
                i.error("Method called "+name+", already exists")
            self.methods[package][name] = method
        else:
            self.methods[package] = {name: method}

    def hasMethod(attachTyp, parser, name):
        self = parser.interfaces[attachTyp.package][attachTyp.normalName]

        packages = []
        b = None
        for i in parser.imports+[parser.package]+["_global"]:
            if not i in self.methods: continue
            if name in self.methods[i]:
                b = self.methods[i][name]
                b.package = i

                if not i in packages:
                    packages.append(i)

        if len(packages) > 1:
            self.node.error("ambiguous, multiple definitions of the method "+self.name+"."+name+" in packages: "+", ".join(packages[:-1])+" and "+packages[-1])

        return replaceT(b, attachTyp.generic)

    def duckType(self, parser, other, node, mynode, iter):
        if self.normalName != other.normalName:
            node.error("expecting type "+self.name+", not "+str(other))

        for name in self.remainingGen:
            try:
                a = self.generic[name].toRealType()
            except KeyError:
                print("generic===")
                print(self.generic)
                print(self.remainingGen)
                mynode.error("Cannot compare " + str(self) + " and " + str(other))
            b = other.generic[name].toRealType()

            if not (b.isType(T) and b.owner == (self.package+"." if self.package != "_global" else "")+self.normalName):
                if a.isType(Union):
                    try:
                        a.duckType(parser, b, node, mynode, iter)
                    except EOFError as e:
                        Error.beforeError(e, "For generic parameter "+name+": ")
                else:
                    if a != b:
                        mynode.error("For generic parameter "+name+": "+"Expecting type "+str(a)+", but got type "+str(b))

class Alias(Type):
    def __init__(self, package, name, typ, generic):
        self.typ = typ
        self.types = typ.types
        self.normalName = name

        self.generic = generic
        self.remainingGen = generic

        self.package = package

        gen = generic
        genericS = "[" + ",".join([str(gen[i]) for i in gen]) + "]" if len(gen) > 0 else ""

        self.name = (package + "." if package != "_global" else "") + name + genericS

    @property
    def args(self):
        return self.typ.args

    @property
    def returnType(self):
        return self.typ.returnType

    @property
    def list(self):
        return self.typ.list

    @property
    def different_types(self):
        return self.typ.different_types

    @property
    def empty(self):
        return self.typ.empty

    @property
    def elemT(self):
        return self.typ.elemT

    @property
    def const(self):
        return self.typ.const

    def toRealType(self):
        return self.typ

    def hasMethod(self, parser, field):
        self.typ.hasMethod(parser, field)

    def isType(self, other):
        return type(self.typ) is other

    def duckType(self, parser, other, node, mynode, iter):
        if other.isType(Alias):
            self.typ.duckType(parser, other.typ, node, mynode, iter)
        else:
            self.typ.duckType(parser, other, node, mynode, iter)

All = Interface(False, {})

def isGeneric(t, unknown=False):
    if unknown: return True
    if type(t) in [FuncPointer]:
        if not (type(t.generic) in [dict,coll.OrderedDict]):
            print(type(t.generic))

        if t.generic != {}: return True
        for i in t.args:
            if isGeneric(i): return True
        return isGeneric(t.returnType)
    elif type(t) is Array and isGeneric(t.elemT): return True
    elif type(t) is T: return True
    elif type(t) in [Interface, Struct, Alias, Enum, Union]: return t.normalName != t.name
    elif type(t) is Tuple:
        for i in t.list:
            if isGeneric(i):
                return True

    return False

class Null(Type):
    name = "none"
    types = {}

def remainingT(s, cache={}):
    if not str(s) == "type" and str(s) in cache:
        return cache[str(s)]

    args = coll.OrderedDict()

    if type(s) is FuncPointer:
        for i in s.args:
            args.update(remainingT(i))
        cache[str(s)] = args
        args.update(remainingT(s.returnType, cache))
    elif type(s) is Interface:
        for i in s.types:
            args.update(remainingT(s.types[i]))
    elif type(s) in [Struct, Enum]:
        gen = s.gen
        for i in gen:
            if s.package == "_global":
                if ".".join(i.split(".")[:-1]) == s.normalName:
                    args[i] = gen[i]
            else:
                if ".".join(i.split(".")[:-1]) == s.package+"."+s.normalName:
                    args[i] = gen[i]
    elif type(s) is T:
        args[s.name] = s
        try:
            s.count += 1
        except AttributeError:
            s.count = 1

    elif type(s) is Unknown:
        if s.typ:
            args.update(remainingT(s.typ))

    cache[str(s)] = args

    return args

class I32(Type):
    def __init__(self):
        Type.__init__(self)
        self.name = "int"

        self.__types__ = None

    @property
    def types(self):
        if self.__types__ is None:
            self.__types__ = {
                "toInt": FuncPointer([], self),
                "toFloat": FuncPointer([], Float()),
                "toString": FuncPointer([], String(0)),
                "op_add": FuncPointer([self], self),
                "op_sub": FuncPointer([self], self),
                "op_div": FuncPointer([self], self),
                "op_mul": FuncPointer([self], self),
                "op_eq": FuncPointer([self], Bool()),
                "op_gt": FuncPointer([self], Bool()),
                "op_lt": FuncPointer([self], Bool()),
            }

        return self.__types__

class Float(Type):
    def __init__(self):
        Type.__init__(self)

        self.name = "float"
        self.__types__ = None

    @property
    def types(self):
        if self.__types__ is None:
            self.__types__ = {
                "toInt": FuncPointer([], I32()),
                "toFloat": FuncPointer([], self),
                "toString": FuncPointer([], String(0)),
                "op_add": FuncPointer([self], self),
                "op_sub": FuncPointer([self], self),
                "op_div": FuncPointer([self], self),
                "op_mul": FuncPointer([self], self)
            }

        return self.__types__

    def duckType(self, parser, other, node, mynode, iter):
        if not (other.isType(I32) or other.isType(Float)):
            mynode.error("expecting type " + str(self) + ", or "+str(I32())+" and got type " + str(other))

class Bool(Type):
    name = "bool"
    normalName = "bool"

    __types__ = None

    @property
    def types(self):
        if self.__types__ is None:
            self.__types__ = {
                "toString": FuncPointer([], String(0))
            }

        return self.__types__

package= "_global"
types = {"toString": FuncPointer([], String(0))}

class Func(Type):
    name = "Func"
    normalName = "Func"

class Package(Type):
    name = "package"
    normalName = "package"

class Underscore(Type):
    name = "_"
    normalName = "_"

def replaceT(typ, gen, acc=False, unknown=False): #with bool replaces all
    if not acc:
        acc = {}

    isGen = isGeneric(typ, unknown)

    if str(typ) in acc:
        return acc[str(typ)]

    if unknown and type(typ) is Unknown:
        if not typ.typ:
            return typ
        return replaceT(typ.typ, gen, acc, unknown)

    if type(typ) is T:
        if typ.normalName in gen:
            r = gen[typ.normalName]
            acc[str(typ)] = r
            if type(r) is Underscore:
                #if type(typ.type) is Assign:
                return T(typ.realName, replaceT(typ.type, gen, acc), typ.owner)
                #return typ
            if unknown:
                return r
            else:
                return replaceT(r, gen, acc, unknown)
        else:
            #if type(typ.type) is Assign:
            return T(typ.realName, replaceT(typ.type, gen, acc, unknown), typ.owner)
            #return typ
    elif type(typ) is Struct:
        rem = gen
        for i in typ.remainingGen:
            rem[i] = replaceT(typ.remainingGen[i], gen, acc, unknown)

        s = Struct(False, typ.normalName, typ.types, typ.package, rem)

        return s
    elif type(typ) is Union:
        arr = []
        for i in typ.different_types:
            arr.append(Types.replaceT(i, gen, acc, unknown))
        return Union(arr)
    elif type(typ) is Alias:
        rem = {}
        for i in typ.generic:
            rem[i] = replaceT(typ.generic[i], gen, acc)

        if unknown:
            a = Alias(typ.package, typ.normalName, Types.replaceT(typ.typ, gen, acc, unknown), rem)
        else:
            a = Alias(typ.package, typ.normalName, Types.Null(), rem)
            acc[str(a)] = a
            a.typ = replaceT(typ.typ, gen, acc, unknown)
            a.types = a.typ.types
        return a
    elif type(typ) is Assign:
        return Assign(replaceT(typ.const, gen, acc, unknown))
    elif type(typ) is Interface:
        types = typ.types

        c = Interface(False,{})

        acc[str(typ)] = c

        types = {i: replaceT(types[i], gen, acc, unknown) for i in types}
        newGen = gen
        for i in typ.generic:
            newGen[i] = replaceT(typ.generic[i], gen, acc, unknown)
        c.fromObj(Interface(False, types, newGen, typ.normalName))
        return c
    elif type(typ) is Enum:
        const = coll.OrderedDict()
        g = {}

        c = Enum(typ.package, typ.normalName, const, g)

        acc[str(typ)] = c

        for name in typ.const:
            const[name] = [replaceT(i, gen, acc, unknown) for i in typ.const[name]]

        for name in typ.remainingGen:
            g[name] = replaceT(typ.generic[name], gen, acc, unknown)

        c.fromObj(Enum(typ.package, typ.normalName, const, g))
        return c

    elif type(typ) is Tuple:
        arr = []
        for i in typ.list:
            arr.append(replaceT(i, gen, acc, unknown))

        return Types.Tuple(arr)

    elif type(typ) is Array and isGen:
        return Array(False, replaceT(typ.elemT, gen, acc, unknown))
    elif type(typ) is FuncPointer:
        generics = typ.generic

        arr = []
        for i in typ.args:
            arr.append(replaceT(i, gen, acc, unknown))

        newTyp = replaceT(typ.returnType, gen, acc, unknown)
        r = FuncPointer(arr, newTyp, remainingT(newTyp), do= typ.do, ignore= typ.ignore)
        return r
    else:
        return typ

from TopCompiler import topc

from .HindleyMilner import *
