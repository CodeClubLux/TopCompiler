var inTerminal = true;
var calledBy = [];

var debuggerCSS = `

 body {
    margin: 0px;
 }

 .dropbtn {
    background-color: black;
    border: none;
    cursor: pointer;
    outline: 0;
    padding: 0px;
    padding-left: 5px;
    margin: 0px;
    font-size: 14px;
}

.dropdown {
  padding: 0px;
  padding-right: 10px;
  font-size: 14px;
}

.dropdown-content {
    display: none !important;
    background-color: black;
    padding-left: 20px;
    margin-top: 0px;
    margin-bottom: 0px;
    font-size: 14px;
}

/* Links inside the dropdown */
.dropdown-content p {
    text-decoration: none;
    margin: 0px;
}

.show {
  display: block !important;
}
`;

document.querySelector("#code").setAttribute('style', "float: right; width: 70%; position: relative;")

var sheet = document.createElement('style');
sheet.innerHTML = debuggerCSS;
document.head.appendChild(sheet);

function createDropdown(label, inner) {
    var outer = $("<div>", {
        class: "dropdown"
    })

    var container = $("<div>", {
        class: "dropdown-content"
    });
    var dropBtn = $("<div>", {
        style: "padding: 1px",
        class: "dropbtn"
    });
    var drop = $("<button>", {
        style: "margin-right: 5px; color: rgb(100,100,100);",
        text: "▶",
        class: "dropbtn"
    });

    dropBtn.append(drop);
    dropBtn.append(label);

    for (var i = 0; i < inner.length; i++) {
        container.append(inner[i]);
    }

    drop.click(function(e) {
        e.stopPropagation();
        myFunction(container, drop);
    });

    outer.append(dropBtn);
    outer.append(container);

    return outer;
}

function myFunction(content, button) {
    content.toggleClass("show");
    var drop = button;
    if (drop.text() == "▶") {
        drop.text("▼");
    } else {
        drop.text("▶");
    }
}

function dumpObject(obj, field) {
    var field = field || "";

    if (obj instanceof Array) {
        var keys = obj.map(function(x, index) {
            return dumpObject(x, index + " = ");
        });
        return createDropdown(field + "Tuple", keys);
    } else if (obj instanceof Vector) {
        var keys = obj.map(function(x, index) {
            return dumpObject(x, index + " = ");
        });
        return createDropdown(field + "Array", keys.toArray());
    } else if (typeof obj == "object") {
        var keys = [];
        for (var i in obj) {
            keys.push(dumpObject(obj[i], i + " = "));
        }
        return createDropdown(field + "Object", keys);
    } else {
        if (typeof obj == "string") {
            obj = '"' + obj + '"';
        }

        if (field == "") {
            return obj;
        } else {
            return $("<p>", {
                text: field + obj,
                style: "padding-left: 25px;"
            })
        }
    }
}

// Close the dropdown menu if the user clicks outside of it

function addState(cont, name_value) {
    var name = name_value[0];
    var value = name_value[1];

    var div = $('<div>', {
        style: "margin-left: 10px"
    }).click(revert);

    cont.append(div);

    function revert() {
        inTerminal = true;
        previousState.op_set(value, function() {});
        terminal.values.pop();
        inTerminal = false;
    }

    if (name) {
        div.append(dumpObject(value, name));
    } else {
        div.append(dumpObject(value));
    }
}

var terminal = (function() {

    var socket = io.connect('http://127.0.0.1:9000/');
    var isCode = true;

    function newTerminal() {
        return $('#terminal').terminal(function(command) {
            try {
                socket.emit("data", command);
            } catch (e) {
                this.error(new String(e));
            }
        }, {
            greetings: '',
            height: function() {
                $(window).height() + 20
            },
            prompt: "> ",
        });
    }

    var terminal = newTerminal();
    var code = $("#code");
    var container = $("#container");

    function resizeCode() {
        code.width($(window).width() - $("#container").width());
    }

    container.resizable({
        handles: "e",
        resize: resizeCode
    })
    $(window).resize(resizeCode);

    $("#switchMode").on("click", function(ev) {
        var self = $("#switchMode");

        if (inTerminal) {
            terminal.hide();

            self.text("Repl");


            var cont = $("<div>", {
                id: "time_travel",
                style: "height: 100%"
            });

            container.append(cont);



            var state = $("<div>", {
                id: "state",
                style: "overflow:auto; height: 80%"
            })

            cont.append(state);

            for (var i = 0; i < terminal.values.length; i++) {
                addState(state, terminal.values[i]);
            }

            var div = $("<div>", {
                style: "position: fixed; bottom: 10px; margin-left: 15px;"
            });

            function onDownload() {
                console.log("changing href");
                download.attr("href", 'data:text/plain;charset=utf-8,' + encodeURIComponent(JSON.stringify(terminal.values)));
            }

            function onImport() {
                var file = _import.prop("files")[0];

                var reader = new FileReader();
                reader.onload = function(ev) {
                    var json = JSON.parse(reader.result);
                    for (var i = 0; i < json.length; i++) {
                        var decoded = _decoderForAtom(json[i][1]);
                        var x = [json[i][0], decoded]
                        addState(state, x);
                        if (terminal.values.length >= 50) {
                            terminal.values.shift();
                        }
                        terminal.values.push(x);
                    }
                }
                reader.readAsText(file);
            }

            var download = $("<a>", {
                text: "Download",
                href: "",
                download: "state.json",
                style: "color: black; text-decoration: none;"
            }).click(onDownload)

            var _import = $("<input>", {
                type: "file"
            }).on("change", onImport);

            div.append($("<button>").append(download));
            div.append(_import);

            $("#time_travel").append(div);
        } else {
            terminal.show();
            self.text("Time Travel");
            $("#time_travel").remove();
        }
        inTerminal = !inTerminal;
    })

    socket.on("connect", function() {
        socket.emit("new");
    })

    socket.on('reload', function(data) {
        log("=== reloaded ===");

        document.getElementById("code").innerHTML = "";
        document.getElementById("error").innerHTML = "";
        eval(data);
    });

    socket.on('comp_error', function(data) {
        document.getElementById("error").innerHTML = "<br>" + data + "<br>";
    });

    socket.on('style', function(data) {
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

    function appendElemToTerminal(elem) {
        $(".terminal-output").append($("<div>", {
            style: "width: 100%"
        }).append(elem));
    }

    socket.on("code", function(command) {
        isCode = false;
        terminal.set_prompt("> ");
        try {
            reply = function(d, t) {
                appendElemToTerminal(dumpObject(d));
                //terminal.echo(dumpObject(d) + " : " + t)
            };
            window.eval(command);
        } catch (e) {
            terminal.error(new String(e));
        }
        isCode = true;
    })

    socket.on("prefix", function(command) {
        terminal.set_prompt(command + " ");
    })

    return terminal;
})()

terminal.values = [];

function recordNewValue(val, next) {
    var name = calledBy.shift();

    if (terminal.values.length < 50) {
        terminal.values.push([name, val]);
    } else {
        terminal.values.shift();
        terminal.values.push([name, val]);
    }

    if (!inTerminal) {
        var cont = $("#state")
        addState(cont, [name, val]);
    }
    next();
}