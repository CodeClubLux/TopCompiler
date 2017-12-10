from __future__ import print_function

__author__ = 'antonellacalvia'

import sys
import os

def compileError(filename, line, message):
    raise EOFError("File \""+os.path.abspath(filename+".top")+"\", line "+str(line)+"\n\t"+message, file=sys.stderr)

def parseError(parser, message):
    filename = [a+"/"+parser.filename for (a,b) in parser._filename if b == parser.filename][0]

    package = parser.package

    token = parser.tokens[parser.iter]

    errorAst(message, package, filename, token)

def errorAst(message, package, filename, token):
    if message == "type MaybePosAtom type can not be used as a constructor":
        print("wierd")
    from TopCompiler import topc
    html = '<div class="error">'

    err = ("File \"" + str(filename + ".top") + "\", line " + str(token.line + 1) + "\n\t" + message[0].capitalize() + message[1:])+"\n"

    html += "<p>"+("File \"" + os.path.abspath("src/"+package + "/" + filename + ".top") + "\", line " + str(
        token.line + 1) + "</p><p style=\"text-indent: 50px;\">"+message[0].capitalize() + message[1:])+"\n"+"</p><br>"

    """f = open(os.path.abspath("src/"+ package + "/" + filename + ".top"))  # change to use already read version
    s = f.read()
    f.close()""
    """

    try:
        s = topc.filenames_sources[package][os.path.basename(filename)]
    except KeyError:
        o = os.path.basename(filename)
        o = o[0:o.find(".")]
        try:
            s = topc.filenames_sources[package][o]
        except:
            print("cannot find file")
            print(topc.filenames_sources[package])
            print(os.path.basename(o))


    divided = s.split("\n")
    line = ("\n\t" + divided[token.line])
    err += line+"\n"
    html += "<p style=\"text-indent: 50px;\">"+line+"</p>"

    err += "\t"+((" " * token.column) + "^")+"\n"
    html += "<p style=\"text-indent: 50px;\">"+(("&nbsp;"* token.column) + "^")+"</p></div>"

    topc.error = html.replace("\n", "").replace("\"", "\\\"")

    raise EOFError(err)

def error(message):
    from TopCompiler import topc

    #topc.error = ('<div class="error"><p>' +message[:-2] +'</p></div>').replace("\n", "<br>").replace("\"", "\\\"")

    raise EOFError(message)

def beforeError(prev, mesg):
    from TopCompiler import topc
    splited = str(prev).split("\n")

    header0 = splited[0]
    header1 = "\n\t"+mesg+ splited[1].replace("\t", "")
    header2 = "\n" + splited[2]
    header3 = "\n" + splited[3]
    header4 = "\n" + splited[4]

    html = '<div class="error">'
    html += '<p>'+header0+'</p>'
    html += '<p style="text-indent: 50px;">'+header1+'</p>'
    html +=  "<p style=\"text-indent: 50px;\">"+header2+"</p><br>"
    html += "<p style=\"text-indent: 50px;\">" + header3 + "</p>"
    html += "<p style=\"text-indent: 50px;\">" + header4.replace(" ", "&nbsp;") + "</p>"
    html += '</div>'

    topc.error = html.replace("\n", "").replace("\"", "\\\"")

    raise EOFError(header0 + header1 + header2 + header3 + header4)

def afterError(prev, mesg):
    splited = str(prev).split("\n")

    header = splited[0]
    header += "\n"+splited[1].replace("\t", "")+mesg
    header += "\n" + "\n".join(splited[2:])

    topc.error = "<p> Error not implemented </p>"

    error(header)

def typeError(parser, type1, type2, mesg):
    parseError(parser, "type {0}, {1} and {2}".format(mesg, str(type1), str(type2)))