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
        if self.target == "full":
            codegen.client_main_parts.append(self.package+"_clientInit();")
            codegen.node_main_parts.append(self.package+"_nodeInit();")
        else:
            codegen.append(self.package+"_" + self.target + "Init();")

    def validate(self, parser): pass

class Import(Node):
    def __init__(self, package, thisPackage, names, parser):
        Node.__init__(self, parser)
        self.package = package
        self.thisPackage = thisPackage
        self.names = names

    def compileToJS(self, codegen):
        for (i, target) in self.names:
            codegen.target = target
            varName = self.package+"_"+i

            codegen.append(self.thisPackage+"_"+i+"= typeof "+varName+"=='undefined'||"+varName+";")

    def validate(self, parser):
        for (i, target) in self.names:
            c = Vars.Create(i, Types.Null(), self)
            c.package = self.thisPackage;
            c.target = target
            c.isGlobal = True

            self.owner.before.append(c)


