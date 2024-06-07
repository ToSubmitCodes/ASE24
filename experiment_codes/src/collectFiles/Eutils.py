class NLayer():
    def __init__(self,t):
        self.t = t
    def __eq__(self, others):
        return isinstance(others,NLayer) and hash(self) == hash(others)
    def __hash__(self):
        return hash(self.t)

class NotAParam():
    def __init__(self):
        pass

class NVar():
    def __init__(self,t):
        self.t = t
    def __eq__(self, others):
        return isinstance(others,NVar) and hash(self) == hash(others)

class NList():
    def __init__(self,l,t):
        self.t = t
        self.l = l
    def __eq__(self,others):
        return isinstance(others,NList) and hash(self) == hash(others)
    def __hash__(self):
        return(hash(tuple(self.l)))
class NDict():
    def __init__(self,d,t):
        self.t = t
        self.d = d
    def __eq__(self,others):
        return isinstance(others,NDict) and hash(self) == hash(others)
    def __hash__(self):
        return hash(tuple(self.d.values()))
class NTensor():
    def __init__(self,s,t):
        self.t = t
        self.s = s
    def __eq__(self,others):
        return isinstance(others,NTensor) and hash(self) == hash(others)
    def __hash__(self):
        return hash(self.s)    

class NDtype():
    def __init__(self,dt,t):
        self.dt=t
        self.t = t
    def __eq__(self,others):
        return isinstance(others,NDtype) and hash(self) == hash(others)
    def __hash__(self):
        return hash(self.dt)
