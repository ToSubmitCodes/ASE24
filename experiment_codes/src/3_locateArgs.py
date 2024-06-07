import pickle
import ast,dill

class superchecker(ast.NodeVisitor):
    def __init__(self):
        self.foundSuper = False
        self.args=None
        self.keywords=None
    def visit_Call(self, node):
        if isinstance(node.func,ast.Attribute) and isinstance(node.func.value, ast.Call) and "__init__" in node.func.attr:
            callee = node.func.value
            if isinstance(callee.func,ast.Name) and 'super' in callee.func.id:
                self.foundSuper = True
                self.args = node.args
                self.keywords = []
                for kw in node.keywords:
                    self.keywords.append(kw.arg)

            
def getValue(node,globalDict):
    if isinstance(node,ast.Constant):
        v = node.value
    elif isinstance(node, ast.Tuple):
        v = [getValue(i,globalDict) for i in node.elts] 
        v = tuple(v)
    elif isinstance(node, ast.UnaryOp):
        if isinstance(node.op,ast.USub):
            v = -getValue(node.operand,globalDict)
        else:
            raise NotImplementedError
    elif isinstance(node, ast.Name):
        exist=False
        for gv in globalDict:
            if node.id == gv['alias']:
                v = gv['value']
                exist=True
                break
        if not exist:
            raise NotImplementedError
    else:
        #print(type(node),ast.dump(node))
        raise NotImplementedError
    return v

def extractArgList(k,node,globalDict,base):
    sc = superchecker()
    sc.visit(node)    
    newFunc=[]
    for arg in node.args.args:
        if not arg.arg == 'self':
            newArg={'name':arg.arg}
            newFunc.append(newArg)
    startIndex = len(newFunc) - len(node.args.defaults)
    for i in range(startIndex):
        newFunc[i]['valueSpace'] = []
        newFunc[i]['type'] = []
    for i,dft in enumerate(node.args.defaults):
        v = getValue(dft,globalDict)
        ty = type(v)
        v = dill.dumps(v)
        newFunc[i+startIndex]['default'] = v
        newFunc[i+startIndex]['type'] = [str(ty)]
        newFunc[i+startIndex]['valueSpace'] = [v]
    kwList = []
    for i,kwa in enumerate(node.args.kwonlyargs):
        kwList.append({'name':kwa.arg})
    startIndex = len(kwList) - len(node.args.kw_defaults)    
    for i,dfkw in enumerate(node.args.kw_defaults):
        v = getValue(dfkw,globalDict)
        ty = type(v)
        v = dill.dumps(v)
        kwList[i+startIndex]['default'] = v
        kwList[i+startIndex]['type'] = [str(ty)]
        kwList[i+startIndex]['valueSpace'] = [v]
    newFunc += kwList
    if sc.foundSuper:
        parentc = base[0]
        parentFunc = extractArgList(k,parentc['funcMap'][k],parentc['import'],parentc['base'])
        for i in sc.args:
            parentFunc.pop(0)
        for kw in parentFunc:
            if kw['name'] not in sc.keywords:
                exist=False
                for arg in newFunc:
                    if arg['name'] == kw['name']:
                        exist = True
                        break
                if not exist:
                    newFunc.append(kw)
    return newFunc

#data structure:nameSpace,astnode,name,import,funcMap
clsList=pickle.load(open('../data/funcDef.pickle','rb'))

for c in clsList:
    c['funcArgList']={}
    for k in c['funcMap'].keys():
       c['funcArgList'][k] = extractArgList(k,c['funcMap'][k],c['import'],c['base'])
       
pickle.dump(clsList,open('../data/funcDefwithArgList.pickle','wb'))

