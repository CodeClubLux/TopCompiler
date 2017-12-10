__author__ = 'antonellacalvia'

from .node import *
from TopCompiler import Types
class Int(Node):
    def __init__(self, number, parser):
        Node.__init__(self, parser)
        self.number = number

        self.type = Types.I32()

    def __str__(self):
        return "int " + self.number

    def compileToJS(self, codegen):
        codegen.append(self.number)

    def validate(self, parser): pass

class Bool(Node):
    def __init__(self, bool, parser):
        Node.__init__(self, parser)
        self.bool = bool

        self.type = Types.Bool()

    def __str__(self):
        return "bool " + self.bool

    def compileToJS(self, codegen):
        codegen.append(self.bool)

    def validate(self, parser): pass

class Float(Node):
    def __init__(self, number, parser):
        Node.__init__(self, parser)
        self.number = number

        self.type = Types.Float()

    def __str__(self):
        return "double " + self.number

    def validate(self, parser): pass
    def compileToJS(self, codegen):
        codegen.append(self.number)


class String(Node):
    def __init__(self, string, parser):
        super(String, self).__init__(parser)

        self.string = string
        self.type = Types.String(len(string))
        self.target = parser.global_target

    def __str__(self):
        return self.string

    def toString(self):
        #if self.target == "node"
        if True:
            return self.string. \
                replace("\n", "\\n").\
                replace("\\{", "{"). \
                replace("\\}", "}")
        else:
            return self.string.replace("<", "&lt"). \
                replace(">", "&gt"). \
                replace("\\t", "&nbsp" * 4). \
                replace("\n", ""). \
                replace("\\{", "{"). \
                replace("\\}", "}")

    def compileToJS(self, codegen):
        codegen.append(self.toString())

    def validate(self, parser): pass

class Decoder(Node):
    def __init__(self, parser):
        Node.__init__(self, parser)

    def validate(self, parser): pass

    def compileToJS(self, codegen):
        typ = self.shouldBeTyp

        def loop(typ):
            if type(typ) in [Types.I32, Types.Float, Types.Bool, Types.String]:
                codegen.append("core_json_"+typ.name)
            elif type(typ) in [Types.Struct, Types.Interface]:
                if type(typ) is Types.Struct:
                    codegen.append("core_json_struct("+typ.package+"_"+typ.normalName+",")
                elif type(typ) is Types.Interface:
                    codegen.append("core_json_interface(")

                codegen.append("[")
                for n in typ.types:
                    codegen.append("['"+n+"',")
                    loop(typ.types[n])
                    codegen.append("],")

                codegen.append("])")
            elif type(typ) is Types.Enum:
                codegen.append("core_json_enum(")
                codegen.append(typ.package + "_" + typ.normalName)
                codegen.append(", [")

                const = typ.const
                for n in const:
                    codegen.append("[")
                    for i in const[n]:
                        loop(i)
                        codegen.append(",")

                    codegen.append("],")
                codegen.append("])")
            elif type(typ) is Types.Array:
                codegen.append("core_json_vector(")
                loop(typ.elemT)
                codegen.append(")")
            elif type(typ) is Types.Tuple:
                codegen.append("core_json_tuple([")
                for i in typ.list:
                    loop(i)
                    codegen.append(",")
                codegen.append("])")
            else:
                codegen.append("function(arg) { return arg }")

        loop(typ)