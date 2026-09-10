
class A:
    def clown():
        print("clown A")

class B:
    def clown():
        print("clown B")


class C(A, B):
    pass


C.clown()