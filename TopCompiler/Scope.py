__author__ = 'antonellacalvia'


from TopCompiler import Parser
from TopCompiler import Error
from TopCompiler import Types

class Type :
    def __init__(self, imutable, type, target= "full"):
        if not target:
            target = "full"

        self.imutable = imutable
        self.type = type
        self.target = target
        self.imported = False

    def __repr__(self):
        return str(self.type)

def incrScope(parser):
    parser.scope[parser.package].append({})

def addVar(node, parser, name, type, _global=False):
    if not parser.repl and varExists(parser, parser.package, name):
        node.error( "variable "+name+" already exists")

    if _global:
        parser.scope[parser.package][0][name] = type
    else:
        if len(parser.scope[parser.package]) == 0:
            print("error")
        else:
            parser.scope[parser.package][-1][name] = type

def addFunc(node, parser, name, typ, target= True):
    imutable = True
    if not parser.repl and varExists(parser, parser.package, name):
        node.error("function "+name+" already exists")

    parser.scope[parser.package][-2][name] = Type(type= typ, imutable= imutable, target=target)
    return

def decrScope(parser):
    parser.scope[parser.package].pop()

def varExists(parser, package, name):
    if package == parser.package:
        for i in parser.scope["_global"]:
            if name in i:
                return True

    for i in parser.scope[package]:
        if name in i:
            return True
    return False

def changeType(parser, name, newType):
    for i in parser.scope[parser.package]:
        try:
            i[name].type = newType
        except: pass

def changeTarget(parser, name, target):
    for i in parser.scope[parser.package]:
        try:
            i[name].target = target
        except: pass

def isMutable(parser, package, name):
    if name in parser.imports: return False
    if package == parser.package:
        for i in parser.scope["_global"]:
            if name in i:
                return i[name].imutable

    for i in parser.scope[package]:
        try:
            return not i[name].imutable
        except KeyError: pass

def typeOfVar(node, parser, package, name):
    if name in parser.imports and not name in parser.from_imports: return Types.Package()
    if package == parser.package:
        for i in parser.scope["_global"]:
            if name in i:
                return i[name].type

    for i in parser.scope[package]:
        try:
            return i[name].type
        except: pass
    node.error("variable "+name+" does not exist")


def targetOfVar(node, parser, package, name):
    if name in parser.imports and not name in parser.from_imports: return parser.global_target
    if package == parser.package:
        for i in parser.scope["_global"]:
            if name in i:
                return i[name].target

    for i in parser.scope[package]:
        try:
            return i[name].target
        except: pass
    node.error("variable "+name+" does not exist")

def packageOfVar(parser, package, name):
    if name in parser.imports and not name in parser.from_imports: return ""
    if package == parser.package:
        for i in parser.scope["_global"]:
            if name in i:
                return ""

    return package

def isGlobal(parser, package, name):
    if name in parser.imports: return True
    if package == parser.package:
        if name in parser.scope["_global"][0]: return True
    return name in parser.scope[package][0]

def addPackage(parser, name):
    if not name in parser.scope:
        parser.scope[name] = [{}]
        parser.func[name] = {}
        parser.structs[name] = {}
        parser.interfaces[name] = {}




