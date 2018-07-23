function core_json_int(obj) {
    var n = Number(obj);
    if (isNaN(n)) {
        return Error(toString(obj)+" is not a number");
    } else {
        return Ok(n | 0);
    }
}

function core_json_float(obj) {
    var n = Number(obj);
    if (isNaN(n)) {
        return Error(toString(obj)+" is not a number");
    } else {
        return Ok(n);
    }
}

function core_json_bool(obj) {
    if (typeof obj == "boolean") {
        return Ok(obj);
    } else {
        return Error(toString(obj)+" is not a boolean")
    }
}

function core_json_string(obj) {
    if (typeof obj == "string") {
        return Ok(obj);
    } else {
        return Error(toString(obj) + " is not a boolean")
    }
}

function core_json_struct(constr, array) {
    return function core_json_struct(realObj) {
        if (typeof realObj !== "object") {
            return Error(toString(realObj)+ " cannot be converted to a struct")
        }
        var len = array.length;
        var obj = new constr();
        for (var i = 0; i < len; i++) {
            var arr = array[i];
            var newValue = arr[1](realObj[arr[0]]);
            if (newValue[0] == 1) {
                return Error("Field "+arr[0]+" of struct : "+newValue[1]);
            } else {
                obj[arr[0]] = newValue[1];
            }
        }
        console.log("Converted to struct");
        console.log(obj);
        return Ok(obj);
    }
}

function core_json_interface(array) {
    return function core_json_interface(realObj) {
        if (typeof realObj !== "object") {
            return Error(toString(realObj)+ " cannot be converted to an interface")
        }

        var obj = {};
        var len = array.length;
        for (var i = 0; i < len; i++) {
            var arr = array[i];
            var newValue = arr[1](realObj[arr[0]]);
            if (newValue[0] == 1) {
                return Error("Field "+arr[0]+" of interface : "+newValue[1]);
            } else {
                obj[arr[0]] = newValue[1];
            }
        }
        return Ok(obj);
    }
}

function core_json_enum(typ, array) {
    return function core_json_enum(realObj) {
        if (typeof realObj !== "object" && !Array.isArray(realObj)) {
            return Error(toString(realObj)+ " cannot be converted to a enum")
        }
        var iter = realObj[0]
        var _enum = new typ(iter);
        for (var i = 1; i < array[iter].length+1; i++) {
            var newValue = array[iter][i - 1](realObj[i]);
            if (newValue[0] == 0) {
                _enum[i] = newValue[1];
            } else {
                return Error("Field "+iter+" of enum : "+newValue[1]);
            }
        }
        return Ok(_enum);
    }
}

//root, len, depth, start

function core_json_vector(decoder) {
    return function core_json_vector(realObj) {
        if (realObj.root && realObj.length && realObj.depth && realObj.start) {
            var vector = new Vector(realObj.root, realObj.length, realObj.depth, realObj.start);
            return vector;
        } else if (!Array.isArray(realObj)) {
            return Error(toString(realObj)+ " cannot be converted to a vector")
        }

        var newArray = EmptyVector;

        for (var i = 0; i < realObj.length; i++) {
            var newValue = decoder(realObj[i]);
            if (newValue[0] == 0) {
                newArray = newArray.append_m(newValue[1]);
            } else {
                return Error("Index "+i+" in array : "+newValue[1]);
            }
        }
        return Ok(newArray);
    }
}

function core_json_tuple(decoder) {
    return function core_json_tuple(arr) {
        if (!Array.isArray(arr)) {
            return Error(toString(arr)+ " cannot be converted to a tuple")
        }

        var a = [];
        for (var i = 0; i < arr.length; i++) {
            var newValue = decoder[i](arr[i]);
            if (newValue[0] == 0) {
                a.push(newValue[1]);
            } else {
                return Error("Index "+i+" of tuple : "+newValue[1]);
            }
        }
        return Ok(a);
    }
}

function parseJson(decoder, str) {
    try {
        var obj = JSON.parse(str);
    } catch(e) {
        return Error(toString(e));
    }
    return decoder(obj);
}

function jsonStringify(i) {
    return JSON.stringify(i);
}