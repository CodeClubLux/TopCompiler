__author__ = 'antonellacalvia'

import subprocess
import os
import AST as Tree
from time import *
from TopCompiler import Error

import optimization
import os
import copy

class CodeGen:
    def __init__(self, filename, tree, externFunctions, target, opt, main=True):
        self.tree = tree
        self.filename = filename

        self.opt = opt

        self.out = ""

        self.out_parts = []
        self.main_parts = []

        self.global_target = target
        self.target = target

        self.client_out_parts = []
        self.client_main_parts = []

        self.node_out_parts = []
        self.node_main_parts = []

        self.main = ""

        self.externs = externFunctions

        self.inAFunction = False
        self.names = [{}]
        self.nameCount = 0

        self.info = Info()
        self._level = []
        self._pointer = 0

        self.gen = genNames(self.info)

        self.indent = 0

        self.out_scopes = []
        self.count = 0

    def toJSHelp(self, tree=None, isGlobal=True):
        if tree is None:
            tree = self.tree
        out = ""

        tree.res = self.getName()
        tree._name = self.getName()
        tree._context = self.getName()

        if self.opt > 0:
            # variable declarations
            self.inAFunction = True
            for i in tree.before:
                self.target = i.global_target
                i.compileToJS(self)
            self.inAFunction = False

        for i in tree:
            self.target = i.global_target
            i.compileToJS(self)
            #if not type(i) in [Tree.FuncCall,Tree.If,Tree.Match,Tree.FuncBody,Tree.Create,Tree.Assign,Tree.CreateAssign,Tree.Tree.FuncBraceOpen,Tree.FuncStart] and i.type.name == "none":
            #    self.append(";")

    def toCppHelp(self, tree=None, isGlobal=True):
        if tree is None:
            tree = self.tree
        out = ""

        tree.res = self.getName()
        tree._name = self.getName()
        tree._context = self.getName()

        if self.opt > 0:
            # variable declarations
            self.inAFunction = True
            for i in tree.before:
                self.target = i.global_target
                i.compileToCpp(self)
            self.inAFunction = False

        for i in tree:
            self.target = i.global_target
            i.compileToCpp(self)

    def toEvalHelp(self):
        tree = self.tree

        tree.res = self.getName()
        tree._name = self.getName()
        tree._context = self.getName()

        for i in tree.nodes[:-1]:
            i.compileToJS(self)

        from TopCompiler import Types
        import AST

        if AST.yields(tree.nodes[-1]):
            tree.nodes[-1].compileToJS(self)
            self.append(";reply(" + tree.res + ", '" + str(tree.nodes[-1].type) + "')")
            self.append(";return;")
        elif not type(tree.nodes[-1].type) is Types.Null:
            self.append(";reply(")
            tree.nodes[-1].compileToJS(self)
            self.append(", '" + str(tree.nodes[-1].type) + "')")
            self.append(";return")
        else:
            tree.nodes[-1].compileToJS(self)
            self.append("reply(undefined, 'none')")

    def getName(self):
        return next(self.gen)

    def createName(self, name):
        if True or self.opt == 0:
            self.names[-1][name] = name
            return name
        else:
            self.names[-1][name] = self.getName()
            return self.names[-1][name]

    def readName(self, name):
        for i in reversed(self.names):
            try:
                return i[name]
            except:
                pass

    def incrScope(self):
        self.names.append({})

    def decrScope(self):
        self.names.pop()

    def toJS(self, _target):
        if self.filename == "main":
            _next = ""
        else:
            _next = self.getName()

        def _compile(out, main, target):
            return "function " + str(self.filename) + "_" + target + "Init("+_next+"){var " + self.tree._context + "=0;" + \
                   "return function " + self.tree._name + "(" + self.tree.res + "){" + \
                   "while(1){switch (" + self.tree._context + "){case 0:" + main + "; return "+(_next+"();" if _next != "" else ";") + "}}}()}" + \
                   out

        if _target == "full":
            main = self.filename == "main"

            self.toJSHelp()

            self.node_out = "".join(self.node_out_parts)
            self.node_main = "".join(self.node_main_parts)

            self.client_out = "".join(self.client_out_parts)
            self.client_main = "".join(self.client_main_parts)

            return (
            _compile(self.node_out, self.node_main, "node"), _compile(self.client_out, self.client_main, "client"))
        else:
            main = self.filename == "main"

            self.toJSHelp()

            self.out = "".join(self.out_parts)
            self.main = "".join(self.main_parts)

            return _compile(self.out, self.main, self.global_target)


    def toCpp(self):
        if self.filename == "main":
            _next = ""
        else:
            _next = self.getName()

        def _compile(out, main, target):
            return "void " + str(self.filename) + "_" + "Init("+_next+"){var " + self.tree._context + "=0;" + \
                   "return function " + self.tree._name + "(" + self.tree.res + "){" + \
                   "while(1){switch (" + self.tree._context + "){case 0:" + main + "; return "+(_next+"();" if _next != "" else ";") + "}}}()}" + \
                   out

            main = self.filename == "main"

            self.toCPPHelp()

            self.out = "".join(self.out_parts)
            self.main = "".join(self.main_parts)

            return _compile(self.out, self.main, self.global_target)

    def toEval(self):
        main = "main"

        self.toEvalHelp()

        self.out = "".join(self.out_parts)
        self.main = "".join(self.main_parts)

        out = self.out
        main = self.main

        result = out + "(function(){var " + self.tree._context + "=0;" + \
                 "return function " + self.tree._name + "(" + self.tree.res + "){" + \
                 "while(1){switch (" + self.tree._context + "){case 0:" + main + ";return;}}}()}" + \
                 ")();"

        return result

    def append(self, value):
        if self.target == "mustFull":
            self.target = "full"

        if value is None:
            raise Error.error("expecting type string and got none, internal error")

        if self.target in [self.global_target, "full"]:
            if self.global_target == "full":
                if self.inAFunction:
                    self.client_out_parts.append(value)
                    self.node_out_parts.append(value)
                else:
                    self.client_main_parts.append(value)
                    self.node_main_parts.append(value)
            else:
                if self.inAFunction:
                    self.out_parts.append(value)
                else:
                    self.main_parts.append(value)
        elif self.target == "client":
            if self.inAFunction:
                self.client_out_parts.append(value)
            else:
                self.client_main_parts.append(value)
        elif self.target == "node":
            if self.inAFunction:
                self.node_out_parts.append(value)
            else:
                self.node_main_parts.append(value)
        elif self.target == "full":
            if self.inAFunction:
                self.out_parts.append(value)
            else:
                self.main_parts.append(value)

    def inFunction(self):
        self.inAFunction = True
        self._level = copy.copy(self.info.array)
        self._pointer = self.info.pointer

        self.info.reset([0], 0)

    def outFunction(self):
        self.inAFunction = False
        self.info.reset(self._level, self._pointer)

    def compile(self, opt=0):
        target = self.global_target
        if target == "mustFull": target = "full"

        if target == "full":
            (node, client) = self.toJS(target)

            #node = node.replace(";", ";\n")
            #client = client.replace(";", ";\n")

            try:
                f = open("lib/" + self.filename.replace("/", ".") + "-node.js", mode="w")
                f.write(node)
                f.close()
            except Exception as e:
                Error.error("Compilation failed, " + str(e))

            try:
                f = open("lib/" + self.filename.replace("/", ".") + "-client.js", mode="w")
                f.write(client)
                f.close()
            except Exception as e:
                Error.error("Compilation failed, " + str(e))
        else:
            js = self.toJS(target)

            try:
                f = open("lib/" + self.filename.replace("/", ".") + "-"+ target +".js", mode="w")
                f.write(js)
                f.close()
            except Exception as e:
                Error.error("Compilation failed, " + str(e))







def getRuntime():
    runtimeName = __file__[0:__file__.rfind("/") + 1] + "runtime.js"
    file = open(runtimeName, mode="r")
    return file.read()


def getRuntimeNode():
    runtimeName = __file__[0:__file__.rfind("/") + 1] + "runtime_node.js"
    file = open(runtimeName, mode="r")
    return file.read()

def linkCPP(filenames, output, run, debug, opt, dev, linkWith, target, hotswap):
    buildsteps = """
    IDIR =../include
CC=g++
CFLAGS=-I$(IDIR)

ODIR=obj
LDIR =../lib

LIBS=-lm

_DEPS = hellomake.h
DEPS = $(patsubst %,$(IDIR)/%,$(_DEPS))

_OBJ = hellomake.o hellofunc.o
OBJ = $(patsubst %,$(ODIR)/%,$(_OBJ))


$(ODIR)/%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS)

hellomake: $(OBJ)
	gcc -o $@ $^ $(CFLAGS) $(LIBS)

.PHONY: clean

clean:
	rm -f $(ODIR)/*.o *~ core $(INCDIR)/*~ """

    for filename in filenames:
        buildsteps += ""

    makefile = open(output + "-makefile")
    makefile.write(buildsteps)




def link(filenames, output, run, debug, opt, dev, linkWith, linkWithCSS, target, hotswap):
    if target == "cpp":
        linkCPP(filenames, output, run, debug, opt, dev, linkWith, target, hotswap)

    needSocket = False
    socket = ""

    terminal = ""
    if target == "client" and debug:
        terminal = open(__file__[0:__file__.rfind("/") + 1] + "terminal/debugger.js").read()

        needSocket = True
        linked = ""
        socket = ""
    else:
        linked = ""

    if opt == 3:
        linked = "(function(){ var production = true;"
    else:
        linked = "var production = false;"

    import sys

    runtime = "" if hotswap and target == "client" else getRuntime() if target == "client" else getRuntimeNode()

    linked += runtime

    css = ""

    if target == "client" and debug:
            linked += """log= function(d) {
                terminal.echo(d);
            };

            log_unop = function(data, next) {
                terminal.echo(data);
                next();
            };

            function newAtom(arg) {
                previousState = {
                    unary_read: unary_read,
                    op_set: op_set,
                    arg: arg,
                    watch: atom_watch,
                    events: [],
                    toString: function(){ return "" }
                }

                calledBy.push("init -> ");
                recordNewValue(arg, function(){});

                previousState.events.push(recordNewValue);

            return previousState
        }
        """
    elif target == "client" and (dev and not hotswap):
        linked += """
        function newAtom(arg) {
                previousState = {
                    unary_read: unary_read,
                    op_set: op_set,
                    arg: arg,
                    watch: atom_watch,
                    events: [],
                    toString: function(){ return "" }
                }
                return previousState
        }

        (function() {
            var socket = io.connect('http://127.0.0.1:9000/');
            socket.on("connect", function() {
                socket.emit("new");
            })

            socket.on('reload', function (data) {
                log("=== reloaded ===");

                document.getElementById("code").innerHTML = "";
                document.getElementById("error").innerHTML = "";
                eval(data);
            });

            socket.on('comp_error', function (data) {
                document.getElementById("error").innerHTML = "<br>"+data+"<br>";
            });

            socket.on('style', function (data) {
                var name = data.name;
                var content = data.content;
                document.getElementById(name).innerHTML = content;
            });

            socket.on("error", function(err) {
                isCode = false;
                terminal.set_prompt("> ");
                terminal.error(err);
                isCode = true;
            })
            })()
        """

        css += '<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/1.3.6/socket.io.min.js"></script>'

    if target == "client":
        if (dev and not hotswap):
            linked += terminal
            socket = '<script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/1.3.6/socket.io.min.js"></script>'
            socket += ('<div id="error" style="z-index: 10000000; width: 100%; background-color: #42f4eb; position: fixed; bottom: 0; font-family: "Segoe UI", Frutiger, "Frutiger Linotype", "Dejavu Sans", "Helvetica Neue", Arial, sans-serif; padding-left: calc(50% - 123px);"></div>')
            #socket += terminal

            files = """https://cdnjs.cloudflare.com/ajax/libs/jquery/3.2.1/jquery.min.js
https://cdn.jsdelivr.net/npm/jquery-resizable@1.0.6/resizable.js
https://cdn.jsdelivr.net/npm/jquery-resizable@1.0.6/resizable.css
https://cdnjs.cloudflare.com/ajax/libs/jquery.terminal/1.11.0/css/jquery.terminal.min.css
https://cdnjs.cloudflare.com/ajax/libs/jquery.terminal/1.11.0/js/jquery.terminal.min.js"""

            if debug:
                for cdnFile in files.split("\n"):
                    if cdnFile.endswith(".css"):
                        socket += '<link rel="stylesheet" type="text/css" href="'+cdnFile+'"></link>'
                    else:
                        socket += '<script src="' + cdnFile + '"></script>'

                socket += '<div id="container" style="padding-top: 50px; margin-top: -10px; padding-bottom: 100px; color: white; margin-right: 10px; position: fixed; display: inline-block; float: left; height: 100%; background-color: black; width: 30%;"><button id="switchMode" style="position: fixed; color: black; z-index: 100000; top: 20; margin-left: 10px;so">Time Travel</button><div id="terminal" style="position: fixed; width: inherit; height: 90%;"></div></div>'

            socket = socket.replace('"', "'").replace("\n", " ")
        else:
            socket = ""
        f = open("bin/assets.json", "w")
        f.write("""{
            "css": [ """+",".join(('"'+i+'"' for i in linkWithCSS))+""" ],
            "js": [ \"bin/""" + output + (".min" if opt == 3 else "") + '-client.js"' + """],
            "hotSwappingCode": \"""" + socket + """\"
        }""")

    array = []
    # print("====", target)
    for i in linkWith:
        try:
            f = open(i, mode="r")
        except:
            f.close()

            Error.error("cannot find file " + i + " to link")
        array.append(f.read())
        f.close()

    linked += ";".join(array)

    if target == "client":
        for i in linkWithCSS:
            try:
                f = open(i, mode="r")
            except:
                f.close()

                Error.error("cannot find file " + i + " to link")
            css += '<style id="' + i + '">' + f.read() + "</style>"
            f.close()

    linked += "\n"

    #linked += ("var types = {};\n")

    for i in filenames:
        f = open("lib/" + i.replace("/", ".") + "-" + target + ".js", mode="r")
        #linked += "\ntypes['" + i + "'] = {};\n"
        linked += f.read()
        f.close()

    fjs = open("bin/" + output + "-" + target + ".js", mode="w")

    preCall = linked
    linked += "main_" + target + "Init();"
    if opt == 3:
        linked += "})()"

    #import jsbeautifier
    #linked = jsbeautifier.beautify(linked)

    fjs.write(linked)
    fjs.close()

    if opt == 3 and target == "client":
        args = ["uglifyjs", "--noerr", "--warn" "--compress", "unused,dead_code", "--output", output + ".min-" + target + ".js", "--mangle", "--",
              output + "-" + target + ".js"]

        #args = ["closure-compiler", "--js", output + "-" + target + ".js", "--js_output_file", output + ".min-"+target+ ".js", "--warning_level", "QUIET", "--compilation_level", "ADVANCED"]

        subprocess.check_call(args, shell=False, cwd="bin")
        output += ".min"
        linked = open("bin/" + output + "-" + target + ".js", "r").read()

    if target == "node":
        if run:
            execNode(output, dev)
        return

    if target == "full":
        return linked

    if opt == 3:
        output = output[:-len(".min")]

    f = open("bin/" + output + ".html", mode="w")

    html = """
<!DOCTYPE html">
<HTML>
    <head>
        <meta charset="UTF-8">
        <TITLE>""" + output + """</TITLE>
        <link rel="icon" href="favicon.ico" type="image/x-icon" />
        """ + css + """
    </head>
    <body>
        """ + ('<div id="container" style="padding-top: 50px; margin-top: -10px; padding-bottom: 100px; color: white; margin-right: 10px; position: fixed; display: inline-block; float: left; height: 100%; background-color: black; width: 30%;"><button id="switchMode" style="position: fixed; color: black; z-index: 100000; top: 20; margin-left: 10px;so">Time Travel</button><div id="terminal" style="position: fixed; width: inherit; height: 90%;"></div></div><div id= "code" style= "float: right; width: 70%; position: relative;"></div>' if needSocket else '<div id= "code"></div>') + """
        """+ socket + """
        <script>
        """ + linked + """
        </script>
    </body>
</HTML>"""

    f.write(html)

    f.close()
    fjs.close()

    if run: exec(output)


def exec(outputFile):
    args = ["open", "bin/" + outputFile + ".html"]
    subprocess.check_call(args, shell=False)

def execNode(outputFile, dev):
    if dev:
        args = ["node", outputFile + "-node.js"]

        subprocess.Popen(args, cwd="bin/")
    else:
        args = ["node", outputFile + "-node.js"]
        subprocess.call(args, cwd="bin/")

def execCpp(outputFile, dev):
    args = ["./"+""]

class Info:
    def __init__(self):
        self.pointer = 0
        self.array = [0]

    def reset(self, lastArr, pointer):
        self.array = lastArr
        self.pointer = pointer


def genNames(info):
    import string

    def overflow(id):
        return len(letters) <= info.array[id]

    letters = [i for i in string.ascii_letters if not i.lower() in ('a', 'e', 'i', 'o', 'u')]
    info.pointer = 0
    skip = False

    while True:
        if overflow(info.pointer):
            info.array[info.pointer] = 0
            if info.pointer == 0:
                info.array = [0] * (len(info.array) + 1)
                info.pointer = len(info.array) - 1
            else:
                info.pointer -= 1
                info.array[info.pointer] += 1
        elif info.pointer != len(info.array) - 1:

            yield ("".join((letters[i] for i in info.array)))
            info.pointer += 1
            info.array[info.pointer] += 1
        else:

            yield ("".join((letters[i] for i in info.array)))
            info.array[info.pointer] += 1
