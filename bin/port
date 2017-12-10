from TopCompiler import topc
from TopCompiler import Error
import os
import sys
import subprocess
import requests

import json

server = "http://127.0.0.1:3000/"

def installPackage():
    if not os.path.exists("packages"):
        os.makedirs("packages")

    os.chdir("packages")

    if len(sys.argv) > 2:
        name = sys.argv[2]
        url = server + 'query/[1,"'+name+'",0]'

        j = str(requests.get(url).content)[2:-1]
        data = json.loads(j)

        if len(data) == 0:
            print("No such package "+name, file=sys.stderr)
            sys.exit()
        elif len(data) > 1:
            print("Multiple packages with the same name, please add the Author", file=sys.stderr)
            sys.exit()

        data = data[0]

        arr = ["git", "clone", data["git"]]
        subprocess.call(arr)
    else:
        print("Missing url", file=sys.stderr)

import re
from TopCompiler import Scope
from TopCompiler import Types
from TopCompiler import Struct

import AST as Tree

class PlaceHolder():
    def __init__(self, opackage, filename, token):
        self.selfpackage = opackage
        self.filename = filename
        self.token = token

    def error(self, message):
        Error.errorAst(message, self.selfpackage, self.filename, self.token)

import pypandoc

def doc(port):
    docs = []
    try:
        readme = pypandoc.convert_file("README.md", "html5", "markdown_github")

        docs.append(["", readme])

    except FileNotFoundError:
        print("Missing README.md", file=sys.stderr)
        sys.exit()

    try:
        parser = topc.start(doc=True)
    except EOFError as e:
        print(e, file=sys.stderr)
        sys.exit()

    lexed = parser.lexed

    def splitBy(content):
        arr = [i.split(" ") for i in content.split("\n")]

        tmp = []
        for c in arr:
            for i in c:
                tmp.append(i)
                tmp.append(" ")
            tmp.append("\n")

        return tmp

    def gen(generics):
        if len(generics) == 0:
            return ""
        else:
            i = "["
            for name in generics:
                typ = generics[name].type
                n = generics[name].realName
                if type(typ) is Types.Interface and len(typ.types) == 0:
                    i += n
                else:
                    i += n+":"+generics[name].type.name

                i += ", "
            i = i[:-2] + "]"

            return i

    def parse(package, filename, cont, token):
        comment = token.token[4:-2]
        split = splitBy(comment)
        inCode = False

        for i in split:
            if len(i) > 0 and i[:3] == "```" and inCode:
                inCode = False
                cont.append(i)
            elif len(i) > 0 and i[:3] == "```" and not inCode:
                cont.append("```scala"+i[3:])
                inCode = True
            elif len(i) > 0 and i[0] == "@":
                name = i[1:]

                cont.append("```scala\n")


                if name in parser.structs[package]:
                    typ = parser.structs[package][name]
                    cont.append("type " + name + gen(typ.generic) + " =")
                    for c in Struct.offsetsToList(parser.structs[package][name].offsets):
                        cont.append("\n   " + c + ": " + typ.types[c].name + "")
                elif name in parser.interfaces[package]:
                    typ = parser.interfaces[package][name]

                    if type(typ) is Types.Interface:
                        cont.append("type " + name + " with\n")
                        for c in typ.types:
                            cont.append("   " + c + ": " + typ.types[c].name + "\n")
                    elif type(typ) is Types.Enum:
                        cont.append("type " + name + " either\n")
                        for c in typ.types:
                            args = typ.types[c]
                            if len(args) == 0:
                                cont.append("   " + c + "\n")
                            else:
                                cont.append("   " + c + "(" + ", ".join([d.name for d in args]) + ")\n")
                else:
                    try:

                        n = Scope.typeOfVar(PlaceHolder(package, filename, token), parser, package, name)
                        cont.append(name+": "+str(n))
                    except EOFError:
                        try:
                            PlaceHolder(package, filename, token).error("no variable named "+name)
                        except EOFError as e:
                            print(e, file=sys.stderr)
                            sys.exit()

                cont.append("\n```")
            else:
                cont.append(i)

    for package in lexed:
        if package == "main":
            continue


        content = []
        count = -1
        for file in lexed[package]:
            count += 1
            filename = parser.filenames[package][count][1]
            for token in file:
                if token.type in ["comment", "commentLine"] and token.token[2] == "*":
                    parse(package, filename, content, token)

        f = open("src/"+package+"/README.md", "w")
        s = "".join(content)
        f.write(s)
        f.close()

        #print( open("src/"+package+"/README.md", "r").read())

        html = pypandoc.convert_file("src/"+package+"/README.md", "html5", "markdown_github")

        docs.append([package, html])
    return docs
import shutil

def uninstallPackage():
    if len(sys.argv) > 2:
        name = sys.argv[2]
        try:
            shutil.rmtree("packages/"+name)
        except BaseException as e:
            print("No package " + name + " installed", file=sys.stderr)
    else:
        print("Expecting name of package to be uninstalled", file=sys.stderr)

def deploy(port):
    for i in ["description", "git", "name"]:
        if not i in port:
            print("missing field '"+i+"' in port.json")
            sys.exit()

    docs = doc(port)
    desc = port["description"]
    git = port["git"]
    name = port["name"]

    args = ["git", "config", "user.name"]
    pipe = subprocess.check_output(args)


    args = ["git", "commit", "-a", "-m", "Deploying"]
    subprocess.call(args)

    try:
        args = ["git", "push"]
        subprocess.check_call(args)
    except:
        print("\nCould not deploy", file=sys.stderr)
        sys.exit()

    owner = str(pipe)[2:-3]

    data = {
        "name": name,
        "description": desc,
        "git": git,
        "owner": owner,
        "docs": docs,
    }

    requests.post(server+"query", "[0,"+json.dumps(data)+",0]")

def main():
    err = False
    try:
        f = open("src/port.json")
    except:
        err = True

    if err:
        try:
            Error.error("cannot find port.json")
        except EOFError as e:
            print(e, file=sys.stderr)
            sys.exit()

    file = f.read()
    port = json.loads(file)

    if len(sys.argv) > 1:
        if sys.argv[1] == "install":
            installPackage()
        elif sys.argv[1] == "uninstall":
            uninstallPackage()
        elif sys.argv[1] == "deploy":
            deploy(port)
        elif sys.argv[1] == "doc":
            doc(port)
        else:
            print("Unknown command "+sys.argv[1], file=sys.stderr)
    else:
        print("Need command", file=sys.stderr)

main()