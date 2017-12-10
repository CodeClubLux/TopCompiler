from .Parser import *
from .Types import *
import AST as Tree
from .ExprParser import *
from .Error import *

tmp = T("K", Interface(False,{}), "Dict")
key_interface = Interface(False,{
    "op_gt": FuncPointer([tmp], Bool()),
    "op_lt": FuncPointer([tmp], Bool()),
    "op_eq": FuncPointer([tmp], Bool())
}, {}, "Comparable")

K = T("K", key_interface,"Dict")
V = T("V", Interface(False,{}), "Dict")

def dictTyp(K,V):
    generic = coll.OrderedDict([
        ("Dict.K", K),
        ("Dict.V", V),
    ])

    d = Interface(False,{
        "get": FuncPointer([K], V),
        "toString": FuncPointer([], String(0))
    },generic,"Dict")

    d.types["set"] = FuncPointer([K,V], d)

    return d

topDict = dictTyp(K,V)

K_ = T("K", key_interface,"dict")
V_ = T("V", Interface(False,{}),"dict")

dictFunc = FuncPointer([Array(False, Tuple([K_,V_]))], dictTyp(K_,V_), generic=coll.OrderedDict([
    ("K", K_),
    ("V", V_),
]))
