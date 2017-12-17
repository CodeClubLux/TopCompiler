__author__ = 'antonellacalvia'

from .node import *
from AST import Vars

class InitPack(Node):
    def __init__(self, package, parser):
        Node.__init__(self, parser)
        self.package = package
        self.target = parser.output_target
        self.thisPackage = parser.package

    def compileToJS(self, codegen):
        nextNum = str(codegen.count + 1)
        codegen.count += 1

        codegen.append(codegen.tree._context + "=" + nextNum)
        codegen.append(";return ")

        if self.target == "full":
            codegen.client_main_parts.append(self.package + "_clientInit(" + codegen.tree._name + ");")
            codegen.node_main_parts.append(self.package + "_nodeInit(" + codegen.tree._name + ");")
        else:
            codegen.append(self.package + "_" + self.target + "Init("+ codegen.tree._name +");")

        codegen.tree.case(codegen, nextNum, self)

    def validate(self, parser): pass

class Import(Node):
    def __init__(self, package, thisPackage, names, parser):
        Node.__init__(self, parser)
        self.package = package
        self.thisPackage = thisPackage
        self.names = names

    def compileToJS(self, codegen):
        for (i, target) in self.names:
            if target == "mustFull":
                target = "full"

            codegen.target = target
            varName = self.package+"_"+i

            codegen.append(self.thisPackage+"_"+i+"= typeof "+varName+"=='undefined'||"+varName+";")

    def validate(self, parser):
        for (i, target) in self.names:
            c = Vars.Create(i, Types.Null(), self)
            c.package = self.thisPackage;
            c.target = "full" if target == "mustFull" else target
            c.isGlobal = True

            self.owner.before.append(c)


