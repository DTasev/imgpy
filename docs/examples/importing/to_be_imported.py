from __future__ import absolute_import, division, print_function

print("I was imported damnit")


def Some_import():
    import boop1


class SomeClass(object):
    def __init__(self):
        print("Class imported")
