function op_add(x,y) {return x.op_add(y)}
function op_sub(x,y) {return x.op_sub(y)}
function op_mul(x,y) {return x.op_mul(y)}
function op_div(x,y) {return x.op_div(y)}
function op_mod(x,y) {return x.op_mod(y)}
function op_eq(x,y) {return x.op_eq(y)}
function op_pow(x,y) {return Math.pow(x,y)}
function op_lt(x,y) {return x.op_lt(y)}
function op_gt(x,y) {return x.op_gt(y)}
function op_or(x,y) {return x || y}
function op_not(x) {return !x}
function op_and(x,y) { return x && y }
function op_ne(x,y) { return x.op_ne(y) }

function unary_add(x) {return x}
function unary_sub(x) {return -x}

Number.prototype.op_add = function (other) { return this + other }
Number.prototype.op_div = function (other) { return this / other }
Number.prototype.op_sub = function (other) { return this - other }
Number.prototype.op_mul = function (other) { return this * other }
Number.prototype.op_eq = function (other) { return this == other }
Number.prototype.op_mod = function (other) { return this % other }
Number.prototype.op_lt = function (other) { return this < other }
Number.prototype.op_gt = function (other) { return this > other }
Number.prototype.op_ne = function (other) { return this != other }

Number.prototype.toFloat = function () { return this }
Number.prototype.toInt = function () { return this | 0 }

String.prototype.op_eq = function (other) { return this == other }
String.prototype.op_ne = function (other) { return this != other }
String.prototype.op_add = function (other) { return this + other }
String.prototype.op_lt = function (other) { return this < other }
String.prototype.op_gt = function (other) { return this > other }
String.prototype.get = function(index) { return this[index]; }