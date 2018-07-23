from flask import Flask, request
from TopCompiler import Parser
from TopCompiler import PackageParser
from TopCompiler import Lexer
from TopCompiler import ResolveSymbols
from TopCompiler import topc
from TopCompiler import ImportParser
from TopCompiler import CodeGen
import AST as Tree
import tempfile

import os

app = Flask(__name__)

def log(height = 100):
    style = open("node_pollyfill/log.css").read()

    return """
    <style>
        {0}
    </style>
    <div id="log_div" style="height: {1}%; position: absolute; top: {2}%; {3}">
      <div id="console_title">
        Console
        <button onClick="document.getElementById('log').innerHTML = ''">Clear </button>
      </div>
      <div id="log">
    </div>
    """.format(style, str(height), str(100 - height), "" if height == 100 else "border-top: 5px solid #4e4f47;")

@app.route("/toHTML/<target>", methods=["POST"])
def compile(target):
    print(target)
    code = request.data.decode("utf-8")

    if code == "":
        return ""

    try:
        object = tempfile.TemporaryDirectory(dir= "temps")
        id = object.name
        os.chdir(id)
        os.mkdir("src")
        os.mkdir("src/main")
        os.mkdir("bin")

        ignore = {}
        for item in os.listdir("../../src"):
            if not item in ["main", "port.json"]:
                ignore[item] = True
                os.symlink("../../../src/"+item, "src/"+item, target_is_directory=True)
        os.symlink("../../js", "js")
        os.symlink("../../lib", "lib")
        os.symlink("../../node_pollyfill", "node_pollyfill")

        jsonFile = open("src/port.json", "w")

        linkWithClient = ["js/exports.js", "js/bundle.js"]
        linkWithNode = ["js/node.js"]

        if target == "node" or target == "full":
            linkWithNode.insert(0, "node_pollyfill/polyfills.js")
            linkWithNode.insert(1, "node_pollyfill/require.js")
        elif target == "client":
            linkWithClient.insert(0, "node_pollyfill/log.js")

        json = """
        {
            "name": "code",
            "target": \"""" + target + """\",
            "linkWith-client": [\"""" + ("\",\"".join(linkWithClient)) + """\"],
           "linkWith-node": [\"""" + ("\",\"".join(linkWithNode)) + """\"]
        }
        """

        jsonFile.write(json)
        jsonFile.close()

        jsonMainFile = open("src/main/port.json", "w")
        jsonMain = """
        {
            "files": ["anonymous"]
        }
        """

        jsonMainFile.write(jsonMain)
        jsonMainFile.close()

        anonymous = open("src/main/anonymous.top", "w")
        anonymous.write(code)
        anonymous.close()

        try:
            topc.modified_ = {"main": True}
            ImportParser.ignore = ignore
            topc.start(cache= core, _raise=True, _hotswap=True)

            if target == "node":
                res = open("bin/code-node.js", mode="r").read()
                os.chdir("../../")

                res =  """<html>
                    <head></head>
                    <body>
                        """ + log(100) + """
                       <script>
                            """ + res + """
                        </script>
                    </body>
                </html>"""

                f = open("temps/data.html", "w")
                f.write(res)

                return res

            elif target == "full":
                print("full")
                client = open("bin/code-client.js", mode="r").read()

                node = open("bin/code-node.js", mode="r").read()

                node += """
                (function() {
                    function evalJSFromHtml(newElement) {
                      var scripts = newElement.getElementsByTagName("script");
                      for (var i = 0; i < scripts.length; ++i) {
                        var script = scripts[i];
                        eval(script.innerHTML);
                      }
                    }
                    var file = (document.getElementById("text").textContent);

                    var html = '<div id="code"/><div>';
                    html += '<script>';
                    html += file;
                    html += "<\/script>";

                    require("fs").writeFile("index.html", html, function() {})

                    require("http").get({path: "/"}, function(res) {

                        document.getElementById("html").innerHTML = res.body;
                        evalJSFromHtml(document.getElementById("html"));
                    })
                })()
                """

                html = ("""<html>
                    <head></head>
                    <body>
                        <script type="text" id = "text">\n {0} </script>
                        <div>
                            <div id="html" style="height: 70%; width: 100%; position: absolute;"></div>
                            {2}
                        </div>
                        <script>\n {1} </script>
                    </body>
                </html>
                """).format(client, node, log(30))

                os.chdir("../../")

                f = open("temps/data.html", "w")
                f.write(html)

                client = '<div><div id="code"/><div><script>' + client + '</script></div>'

                f = open("temps/client.html", "w")
                f.write(client)

                return html

            elif target == "client":
                client = open("bin/code-Client.js").read()

                html = ("""<html>
                                   <head></head>
                                   <body>
                                       <div>
                                           <div id="code" style="height: 70%; width: 100%; position: absolute;"></div>
                                           {0}
                                       </div>
                                       <script>\n {1} </script>
                                   </body>
                               </html>
                               """).format(log(30), client)

                res = html


                #res = open("bin/code.html", mode="r").read()

                #realHtml = open("bin/code.html").read()
                os.chdir("../../")

                f = open("temps/client.html", "w")
                f.write(html)

                return res

        except EOFError as e:
            os.chdir("../../")
            print(e)
            return str(e).replace("\n", "<br>")
    except Exception as e:
        os.chdir("../../")
        raise e

if __name__ == "__main__":
    topc._modified = {"main": True}
    core = topc.start(_raise= True)
    app.run(port=8000)

