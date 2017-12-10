import pickle
import os
import pprint

def save(parser, port=False):
    #return

    f = open("lib/parser.p", "wb")

    print("port is", port)
    if port != False:
        parser.rootAst = 0
        parser.currentNode = 0
        parser.compiled = []
        parser.Stringable = 0
        parser.atomTyp = 0
        parser._tokens = 0
        parser.tokens = 0
        parser.order = 0

    for package in parser.structs:
        for s in parser.structs[package]:
            parser.structs[package][s].node = 0
    """"
    sizes = {}
    for k, v in parser.__dict__.items():
        print(k)
        print(v)
        l = len(pickle.dumps(v))
        if l > 50:
            sizes[k] = l

    s = reversed(sorted([b for (a,b) in sizes.items()]))
    pprint.pprint(sizes)
    pprint.pprint(list(s))
    print("sizes")
    """


    pickle.dump(parser, f)

def load():
    #return False

    try:
        f = open("lib/parser.p", "rb")
        if os.stat("lib/parser.p").st_size == 0:
            return False

        res = pickle.load(f)
        return res
    except FileNotFoundError:
        return False