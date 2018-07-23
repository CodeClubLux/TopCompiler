function toString(s) {
    return s.toString()
}

function log(s){
    console.log(s.toString())
}

function string_toString(s) {return s}
function int_toString(s) { return s.toString() }
function float_toString(s) { return s.toString() }
function array_toString(s) { return s.toString() }

function float_toInt(s) { return s | 0 }
function int_toInt(s) { return s }

String.prototype.toInt = function () { return Number(this) | 0 }
String.prototype.toFloat = function () { return Number(this) }
String.prototype.op_eq = function(s) { return this == s }

function float_toFloat(s) { return s }
function int_toFloat(s) { return s }

function raise(str) {
    throw new Exception(str);
}
function isOdd(number) {
    return number % 2 != 0
}

function isEven(number) {
    return number % 2 == 0
}

function min(a,b) {
    return a < b ? a : b
}

function max(a,b) {
    return a > b ? a : b
}

function log_unop(v, next) {
    console.log(v);
    return next()
}

function len(x) {
    return x.length
}

function toFloat(x) {
    return x.toFloat()
}

function assign(obj, other) {
    if (obj instanceof Array) {
        var arr = [];
        for (var i = 0; i < other.length; i++) {
            var c = other[i];
            if (c) {
                arr.push(c);
            } else {
                arr.push(obj[i]);
            }
        }
        for (var i = other.length; i < obj.length; i++) {
            arr.push(obj[i]);
        }
        return arr;
    }
    else if (typeof obj == "object") {
        return Object.assign(new obj.constructor(), obj, other);
    } else {
        return other
    }
}

function toInt(x) {
    return x.toInt()
}

function toJS(arg) {
    if (arg instanceof Vector) {
        return arg.map(toJS).toArray()
    }

    if (arg instanceof Function) {
        return funcWrapper(arg);
    }

    if (typeof arg === "object") {
        var obj = {}
        for (var key in arg) {
            obj[key] = toJS(arg[key]);
        }
        return obj
    }

    return arg
}

function fromJS(arg) {
    if (arg instanceof Array) {
        return fromArray(arg.map(fromJS));
    }

    else if (arg instanceof Function) {
        return jsFuncWrapper(arg);
    } else if (typeof arg === "object") {
        var obj = {}
        for (var key in arg) {
            obj[key] = fromJS(arg[key]);
        }
        return obj
    }

    return arg
}

function funcWrapper(func) {
    return function () {
        var x = Array.prototype.slice.call(arguments);

        var args = [];
        for (var i = 0; i < x.length; i++) {
            args.push(fromJS(x[i]));
        }

        return toJS(func.apply(null, args))
    }
}

function jsFuncWrapper(func) {
    return function () {
        var x = Array.prototype.slice.call(arguments);

        var args = [];
        for (var i = 0; i < x.length; i++) {
            args.push(toJS(x[i]));
        }

        return fromJS(func.apply(null, args));
    }
}

function toAsync(func) {
    return function () {
        var x = Array.prototype.slice.call(arguments);

        var args = [];
        for (var i = 0; i < x.length-1; i++) {
            args.push(x[i]);
        }

        var next = x[x.length-1];

        return next(func.apply(null, args));
    }
}

var _empty_func = function() {}

function toSync(func) {
    return function () {
        var x = Array.prototype.slice.call(arguments);

        var args = [];
        for (var i = 0; i < x.length; i++) {
            args.push(x[i]);
        }

        args.push(_empty_func);

        return func.apply(null, args);
    }
}


function unary_read(next) {
    next(this.arg);
}

function op_set(val, next) {
    this.arg = val;
    for (var i = 0; i < this.events.length; i++ ) {
        this.events[i](val, _empty_func);
    }
    next()
}

function atom_watch(func, next) {
    this.events.push(func)
    next();
}

function atom_update(func, next) {
  this.op_set(func(this.arg), next);
}

function newAtom(arg) {
    return {
        unary_read: unary_read,
        op_set: op_set,
        arg: arg,
        watch: atom_watch,
        events: [],
        toString: function(){return ""},
        update: atom_update,
        op_eq: function(other) { return this === other; }
    }
}

function newLens(reader, setter, string, maybe) {
    return {
        query: function(item) {
            if (maybe) {
                try {
                    return Some(reader(item));
                } catch (Exception) {
                    return None;
                }
            }
            return reader(item);
        },
        set: function(old, item) {
            try {
                return setter(old, item);
            } catch (Exception) {
                return old;
            }
        },
        toString: function() {
            return string;
        },
        op_eq: function(other) {
            return other.toString() === string;
        }
    }
}

function defer(func) {
    return function (x) {
        return function (callback) { func(x, callback) }
    }
}

function Maybe(x) {
    this[0] = x;
}

function Some(x) {
    var s = new Maybe(0);
    s[1] = x;
    return s
}

var None = new Maybe(1);

function Maybe_withDefault(self,def){
    if (self[0] === 0) {
        return self[1];
    } else {
        return def;
    }
}

function Maybe_toString(self) {
    if (self[0] == 0) {
        return "Some("+self[1].toString()+")";
    } else {
        return "None"
    }
}

function Maybe_map(self,func){
    if (self[0] == 0) {
        return Some(func(self[1]));
    } else {
        return None;
    }
}

Maybe.prototype.withDefault = function(def){
    return Maybe_withDefault(this,def);
}

Maybe.prototype.map = function(func){
    return Maybe_map(this,func);
}

Maybe.prototype.toString = function() {
    return Maybe_toString(this);
}

function sleep(time, callback) {
    setTimeout(callback, time);
}

function Result(x) {
    this[0] = x;
}

function Ok(x) {
    var s = new Result(0);
    s[1] = x;
    return s;
}

function Error(x) {
    var s = new Result(1);
    s[1] = x;
    return s;
}

function Result_toString(self) {
    if (self[0] == 0) {
        return "Ok(" + self[1].toString() + ")"
    } else {
        return "Error(" + self[1].toString() + ")"
    }
}

function Result_map(self, f) {
    if (self[0] == 0) {
        return Ok(f(self[1]));
    } else {
        return self;
    }
}

function Result_mapError(self, f) {
    if (self[0] == 0) {
        return self;
    } else {
        return Error(f(self[1]));
    }
}

function Result_withDefault(self, x) {
    if (self[0] == 0) {
        return self[1];
    } else {
        return x;
    }
}

function Result_toMaybe(self) {
    if (self[0] == 0) {
        return Some(self[1]);
    } else {
        return None;
    }
}

Result.prototype.toMaybe = function() {
    return Result_toMaybe(this);
}

Result.prototype.map = function(f) {
    return Result_map(this,f);
}

Result.prototype.mapError = function(f) {
    return Result_mapError(this,f);
}

Result.prototype.withDefault = function(x) {
    return Result_withDefault(this,x);
}

Result.prototype.toString = function(){
    return Result_toString(this);
}


function parallel(funcs, next) {
    var count = 0;

    var length = funcs.length;
    var array = funcs;

    for (var i = 0; i < funcs.length; i++) {
        var f = (function (i) {
            return function (res) {
                count++;
                array = array.set(i, res);

                if (count == funcs.length) {
                    next(array);
                }
            }
        })(i)

        funcs.get(i)(f);

    }
}

function serial(funcs, next) {
    var i = 0;
    var length = funcs.length;
    var array = EmptyVector;

    function loop() {
        if (i == funcs.length) {
            next(array);
        } else {
            funcs.get(i)(function (val) {
                array = array.append(val);
                i += 1
                loop()
            })

        }
    }
    loop()
}

function core_assign(construct, obj) {
    var changed = false;
    for (var name in obj) {
        if (construct[name] !== obj[name]) {
            changed = true;
        }
    }
    if (!changed) { return construct }
    return Object.assign(new construct.constructor(), construct, obj);
}