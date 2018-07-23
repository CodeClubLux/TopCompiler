from .Types import *
from TopCompiler import Scope

class State:
    pass


class FakeDict:
    def __init__(self, unknown):
        self.unknown = unknown

    def __contains__(self, item):
        return self.unknown.contains(item)

    def __getitem__(self, item):
        return self.unknown.getProperty(item)

    def keys(self):
        return self.unknown.typ.const.keys()

    def __len__(self):
        class FakeLength:
            def __lt__(self, other):
                return False

            def __gt__(self, other):
                return False

        return FakeLength()

class FakeList:
    def __init__(self, unknown, offset=0):
        self.unknown = unknown
        self.offset = 0

    def __len__(self):
        return self.unknown.lengthOfArgs()

    def __getitem__(self, item):
        if type(item) is slice:
            return self.unknown.getArg(slice(item.start+self.offset, 0, item.stop))
        else:
            return self.unknown.getArg(item+self.offset)

    def iter(self):
        for i in range(self.unknown.lengthOfArgs()):
            yield self[i]

    def __iter__(self):
        return self.iter()


class FakeBool:
    def __init__(self, unknown):
        self.unknown = unknown

    def __bool__(self):
        return self.unknown.rDo

    def __eq__(self, other):
        self.unknown.switchDo(other)
        return self.unknown.rDo == other

    def __ne__(self, other):
        self.unknown.switchDo(other)
        return self.unknown.rDo != other

state = State()
state.count = 0

import string


def mergeDict(a, b):
    return dict([(k, v) for k, v in a.items()] + [(k, v) for k, v in b.items()])


constraint = {
    bool: -1,
    Null: 0,
    Bool: 0,
    FuncPointer: 0,
    String: 0,
    I32: 0,
    Float: 1,
    Struct: 2,
    Enum: 2,
    Interface: 3,
    Alias: 3,
    T: 3,
    Union: 4,
}

isUnknown = -1


def unificaction(o_self, o_other, parser):
    if str(o_other) == "html.onEvent.T":
        print("changing to html.onEvent.T")

    if str(o_other) == "none":
        pass
        #print("none type")


    if type(o_other) is Unknown:
        other = o_other.typ
    else:
        other = o_other

    if type(o_self) is Unknown:
        self = o_self.typ
    else:
        self = o_self

    other_c = constraint[type(other)]
    self_c = constraint[type(self)]

    def find():
        if self_c > -1 and self_c < other_c:
            return self
        if type(self) is type(other):
            if type(self) is Interface:
                return Interface(False, mergeDict(self.types, other.types), self.generic, self.normalName)
            if type(self) is T:
                return other

            if self_c == isUnknown:
                return newT(parser)

            return other
        elif type(self) in [Interface, T] and type(other) in [Interface, T]:
            if type(self) is Interface:
                return T(other.realName, unificaction(self, other.type, parser), other.owner)
            else:
                return T(self.realName, unificaction(other, self.type, parser), self.owner)
        else:
            if not other:
                return self
            return other

    res = find()

    if not o_other is other and not res is other:
        o_other.typ = res
        o_other.callback(res)
        o_other.name = res.name
    if not o_self is self and not res is self:
        o_self.typ = res
        o_self.callback(res)
        o_self.name = res.name

    if type(o_self) is Unknown and type(o_other) is Unknown:
        sync(o_self, o_other)

    return res

class FakeType:
    name = ""


def newT(parser):
    t = T(string.ascii_uppercase[state.count], All, parser.package + "._")
    state.count += 1
    return t

def sync(a, b):
    o_a_callback = a.callback
    o_b_callback = b.callback

    def callback_a(newTyp):
        if not b.typ is newTyp:
            b.typ = newTyp
            b.name = newTyp.name
            o_b_callback(newTyp)

    def callback_b(newTyp):
        if not a.typ is newTyp:
            a.typ = newTyp
            a.name = newTyp.name
            o_a_callback(newTyp)

    a.callback = callback_a
    b.callback = callback_b


class Unknown(Type):
    def __init__(self, parser, callback=False, typ=False):
        Type.__init__(self)

        if not callback:
            callback = lambda t: 0

        self.name = "unknown"
        self.parser = parser
        self.typ = False
        self.callback = callback
        self.types = FakeDict(self)
        self.type = FakeType()
        self.length = None

        if typ:
            self.typ = typ
            self.name = typ.name

    def __str__(self):
        return self.name
        #return "unknown"

    def lengthOfArgs(self):
        s = self
        class FakeComparison:
            def __lt__(self, other):
                s.length = other
                return False

            def __ne__(self, other):
                s.length = other
                return False #add checks later

            def __gt__(self, other):
                return len(s.typ.args) > other

        if not self.length is None:
            return self.length
        return FakeComparison()

    def contains(self, item):
        if type(self.typ) in [bool, Types.Interface, Types.T, Types.Enum]:
            return True
        else:
            return item in self.typ.types

    def getConst(self, item):
        if self.typ.normalName != "":
            return self.typ.const[item]

        def setConst(index):
            def inner(newTyp):
                self.typ.const[item][index] = unificaction(self.typ.const[item][index], newTyp, self.parser)
                typ = self.typ
                self.typ = Enum(typ.package, typ.name, typ.const, typ.generic)
                self.name = self.typ.name
                self.callback(self.typ)

            return inner
        parser = self.parser
        c = Scope.typeOfVar(Tree.PlaceHolder(self.parser), parser, parser.package, item)

        if type(c) is FuncPointer:
            enum = c.returnType
            args = c.args
        else:
            enum = c
            args = []

        replaces = {}
        for i in enum.generic:
            replaces[i] = Unknown(parser, callback=setConst(i), typ=newT(parser))

        r = replaceT(enum, replaces)
        self.compareType(r)
        return self.typ.const[item]

    def getArg(self, item):
        if type(item) is slice:
            return FakeList(self, item.start)

        def changeArgType(newTyp):
            self.typ.args[item] = unificaction(self.typ.args[item], newTyp, self.parser)
            self.typ = FuncPointer(self.typ.args, self.typ.returnType, do= self.typ.do)
            self.name = self.typ.name
            self.callback(self.typ)

        if len(self.typ.args) > item:
            return self.typ.args[item]
        else:
            u = Unknown(self.parser, changeArgType)
            self.typ.args.append(u)
            self.typ = FuncPointer(self.typ.args, self.typ.returnType, do=self.typ.do)
            self.name = self.typ.name
            self.callback(self.typ)
            return u

    def switchDo(self, other):
        if not self.rDo:
            self.typ.do = other
            self.rDo = other
            return True
        return False

    @property
    def package(self):
        if self.typ.package == "":
            s = self
            class MockString:
                def __eq__(self, other):
                    if s.typ.package != "":
                        return other == self.typ.package
                    else:
                        s.typ.package = other
                        return True

                def __ne__(self, other):
                    return not other == self

            return MockString()
        return self.typ.package

    @property
    def normalName(self):
        if not (self.typ and self.typ.normalName != ""):
            s = self
            class MockString:
                def __eq__(self, other):
                    if other == "": return
                    if s.typ and s.typ.normalName != "":
                        return other == self.typ.normalName
                    else:
                        if s.typ:
                            s.typ.normalName = other
                            return True
                        return False

                def __ne__(self, other):
                    return not other == self

            return MockString()
        return self.typ.normalName

    def emulate(self, other):
        if other is FuncPointer:
            def changeReturnType(newTyp):
                unified = unificaction(self.typ.returnType, newTyp, self.parser)
                # self.returnType = unified
                self.typ.returnType = unified
                self.callback(self.typ)

            self.args = FakeList(self)
            self.do = FakeBool(self)
            self.rDo = False

            t = newT(self.parser)
            u = Unknown(self.parser, changeReturnType, typ=t)
            self.compareType(FuncPointer([], u))

            self.returnType = u
        elif other is Enum:
            self.const = FakeDict(self)
            self.const.__len__ = lambda: 0 if self.typ.normalName == "" else len(self.typ.const)
            self.compareType(Enum("", "", {}, {}))
        elif other in [I32, Float, String, Bool]:
            self.compareType(other())
        elif other is Struct:
            self.compareType(other(False, "", {}, "")) #todo: implement later

    def isType(self, other):
        if other is Unknown: return True
        if type(other) is not type: other = type(other)

        """print("----")
        print(other)
        print(self.typ)
        print(constraint[other])
        print(constraint[type(self.typ)])
        print(constraint[other] < constraint[type(self.typ)])
    """

        if not self.typ or constraint[other] < constraint[type(self.typ)]:
            self.emulate(other)
            return True
        return type(self.typ) is other

    def compareType(self, other):
        try:
            unificaction(self, other, self.parser)
        except Exception as e:
            raise e

    def getProperty(self, name):
        if type(self.typ) is Enum:
            return self.getConst(name)

        def changeField(newTyp):
            typ = self.typ
            if name in typ.types:
                return typ.types[name]
            else:
                if type(typ) is Interface:
                    typ.types[name] = newTyp
                else:
                    Error.parseError(self.parser, "Type " + typ + ", has no field " + name)
            self.gen = False

        if self.typ:
            if name in self.typ.types:
                return self.typ.types[name]

        if name in ["op_set", "update", "watch", "unary_read"]:
            u = Unknown(self.parser, lambda x: 0, All)
            u.emulate(FuncPointer)
            u.switchDo(True)
            u.callback = changeField
        else:
            if name.startswith("op_"):
                t = All
            else:
                t = newT(self.parser)
            u = Unknown(self.parser, changeField, typ=t)
        self.compareType(Interface(False, {name: u}))
        return u

    def __eq__(self, other):
        parser = self.parser

        """
        self.compareType(other)

        if self.typ:
            return self.typ == other
        """


    def __hash__(self):
        return id(self)

    def duckType(self, parser, other, node, mynode, iter):
        self.compareType(other)


