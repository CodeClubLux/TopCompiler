#import js2py

from TopCompiler import CodegenJS as CodeGen
from TopCompiler import Lexer
from TopCompiler import Parser
from TopCompiler import ResolveSymbols
from TopCompiler import PackageParser
from TopCompiler import topc

import AST as Tree

import jsbeautifier

from flask import Flask, render_template
from flask_socketio import SocketIO

import eventlet
eventlet.monkey_patch()

import logging

app = Flask(__name__)

socketio = SocketIO(app, logging=False, async_mode="eventlet")

app.logger.disabled = True

log = logging.getLogger('werkzeug')
log.disabled = True

import sys

"""
def myPrint(*args):
    if args

print = myPrint
"""

lock = False

def init():
    global indent
    global parser
    global parenThing
    global indent
    global tokens

    tokens = [[]]
    parenThing = 0

    text = ""
    indent = 0

    if __name__ == "__main__":
        parser = Parser.Parser(tokens, [("main", "_")])
        parser.compiled = {}
        parser.global_target = "client"
        parser.opt = 0
        parser.externFuncs = {"main": []}
        parser.repl = True
        parser.hotswap = False
        parser._tokens = parser.tokens
        parser._filename = parser.filename
        parser.filenames = {}
        PackageParser.packDec(parser, "main", pack=True)

if __name__ == "__main__":
    @socketio.on('new')
    def handle_new():
        init()

@socketio.on('data')
def handle_message(line):
    global indent
    global parenThing

    #if indent == 0:
    #    print("> "+line)
    #else:
    #    print("." * indent + " "+line)

    text = line + "\n"
    #

    if lock:
        lock.acquire()
    try:
        topc.filenames_sources["main"]["_"] = text
    except KeyError:
        topc.filenames_sources = {"main": {"_": text}}

    parser.dev = False

    try:
        t = Lexer.tokenize(line, "_")
        if indent == 0:
            tokens[0] = t
        else:
            tokens[0] += t

        count = 0
        for i in t:
            if i.token in ["(", "{", "["] or i.type == "whiteOpenS":
                count += 1
            elif i.token in [")", "}", "]"]:
                count -= 1

        parenThing += count

        if count > 0:
            indent += 4
        elif count < 0 and parenThing == 0:
            indent -= 4

        if len(t) > 2:
            c = t[-3]
            if c.token in["do", "=", "with", "either", "then", "else"]:
                indent += 4
        elif len(t) == 2:
            if indent == 0:
                if lock:
                    lock.release()
                return
            else:
                indent -= 4

        tokens[0][-1].token = str(indent)

        if indent == 0:
            # ResolveSymbols.insert(parser, parser, only= True)
            parser.package = "main"
            parser.opackage = "main"

            if lock:
                filename = parser.filename
                lexed = parser.tokens
                compiled = parser.compiled
                target = parser.global_target

                # parser = Parser.Parser(tokens, [("main", "_")])
                parser.filename = [("main", "_")]
                parser.tokens = tokens
                parser.compiled = {}
                parser.global_target = "client"
                parser.opt = 0
                parser.externFuncs = {"main": []}
                parser.repl = True
                parser.hotswap = False
                parser._tokens = parser.tokens
                parser._filename = parser.filename
                parser.filenames = {}

            t = parser.tokens
            f = parser.filename

            for i in range(3):
                ResolveSymbols._resolve(tokens[0], parser, "_", i)

            parser.currentNode = Tree.Root()

            parser.tokens = t
            parser.filename = f

            parsed = parser.parse()

            compiled = (parsed, {"main": []})

            code = CodeGen.CodeGen("main", parsed, {"main": []}, "node", 0).toEval()



            # js.eval(code)
            # print("Of type: "+str(parsed.nodes[-1].type))

            socketio.emit("code", code)

            tokens[0] = []
            parser.currentNode = Tree.Root()
        else:
            socketio.emit("prefix", "." * indent)

        if lock:
                filename = parser.filename
                lexed = parser.tokens
                compiled = parser.compiled
                target = parser.global_target

                # parser = Parser.Parser(tokens, [("main", "_")])
                parser.filename = filename
                parser.tokens = lexed
                parser.compiled = compiled
                parser.global_target = target
                parser.opt = 0
                parser.repl = False
                parser.hotswap = True
                parser._tokens = parser.tokens
                parser._filename = parser.filename
                parser.filenames = {}

                lock.release()

    except EOFError as e:
        indent = 0

        parser.tokens = tokens
        parser.filename = parser._filename

        socketio.emit("error", str(e))
        topdev["removeTransforms"](topc.global_parser)

        if lock:
            lock.release()

if __name__ == "__main__":
    init()
    socketio.run(app, port=9000)
