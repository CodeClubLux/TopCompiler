__author__ = 'antonellacalvia'

from TopCompiler import topc
from TopCompiler import CodegenJS
from TopCompiler import Error
from TopCompiler import Module

import sys
import logging
import os
import time
from TopCompiler import socketRepl
from TopCompiler import HindleyMilner
socketRepl.topdev = globals()
import threading

mutex = threading.Lock()

def removeTransforms(parser):

    for i in parser.transforms:
        try:
            tr = parser.transforms[i]
        except KeyError:
            tr = []

        for i in tr:
            Module.removeModule(i)

def main():
    debug = False
    if len(sys.argv) > 1:
        if sys.argv[1] == "--" and sys.argv[2] == "debug":
            debug = True
        else:
            print("Unexpected", sys.argv[1])
            sys.exit()

    try:
        if True:
            error = ""
            mutex.acquire()
            while True:
                try:
                    parser = topc.start(run= True, dev=True, debug=debug)
                    time.sleep(0.2)
                    error = False
                    break
                except EOFError as e:
                    e = str(e)
                    if error != e:
                        print(e, file=sys.stderr)

                    removeTransforms(topc.global_parser)
                    HindleyMilner.count = 0
                    error = e
                    time.sleep(0.2)

            mutex.release()

            socketRepl.init()
            socketRepl.parser = parser

            server = threading.Thread(target=initRepl).start()

            while True:
                time.sleep(0.2)
                mutex.acquire()
                try:
                    parser = topc.start(run= False, dev= True, _hotswap= True, cache=parser, debug = debug)

                    if parser.didCompile:
                        reloadCSS(parser.cssFiles, parser.outputFile, parser.global_target)
                        socketRepl.socketio.emit("reload", open("bin/"+parser.outputFile+"-client.js").read())
                    error = False
                except EOFError as e:
                    e = str(e)
                    if error != e:
                        print(e, file=sys.stderr)
                        #socketRepl.socketio.emit("error", "Compile Error\n\n"+str(e))
                        socketRepl.socketio.emit("comp_error", str(e).replace("\t", "    ").replace(" ", "&nbsp;").replace("\n", "<br>"))
                    error = e
                    removeTransforms(topc.global_parser)
                finally:
                    HindleyMilner.count = 0
                    mutex.release()
    except (KeyboardInterrupt, SystemExit):
        pass

    parser = topc.global_parser
    topc.clearMain(parser)

    from TopCompiler import saveParser
    saveParser.save(parser)

import datetime
def reloadCSS(files, outputfile, target):
    for i in files:
        content = open(i[1], "r").read()
        socketRepl.socketio.emit("style", {"name": i[1], "content": content})

def initRepl():
    socketRepl.lock = mutex
    socketRepl.socketio.run(socketRepl.app, port=9000)

if __name__ == '__main__':
    main()