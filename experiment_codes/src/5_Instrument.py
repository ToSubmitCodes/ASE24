import dill as pickle
import ast
import os
import shutil

def constructASTNode(clsName,methodName,decorator,parentFunc):
    callNode1 = ast.Call(func=ast.Name(id='super',ctx=ast.Load),
                         args=[
                             ast.Name(id=clsName,ctx=ast.Load),ast.Name(id='self',ctx=ast.Load)],
                         keywords=[])
    keywords=[ast.keyword(arg=None, value=ast.Name(id=parentFunc.args.kwarg.arg, ctx=ast.Load))] if parentFunc.args.kwarg else []
    callNode2 = ast.Call(func=ast.Attribute(value=callNode1,attr=methodName, ctx=ast.Load),
                         args=[ast.Name(id=arg.arg, ctx=ast.Load) for arg in parentFunc.args.args[1:]],
                         keywords=keywords)
    RetStmt = ast.Return(value=callNode2)
    funcNode = ast.FunctionDef(name=methodName,
                               args=parentFunc.args, 
                               body=[RetStmt],
                               decorator_list=[decorator])
    return funcNode

def initCopy(root_Dir,Instrument_Dir):
    if os.path.exists(Instrument_Dir):
        shutil.rmtree(Instrument_Dir)
    shutil.copytree(root_Dir,Instrument_Dir)

def instruct(root_Dir,Instrument_Dir,funcList,funcDefs,injectedCls=None):
    for c in funcDefs:
        if injectedCls is not None and c['name'] not in injectedCls:
            #print(c['name'])
            continue
        file=c['fileName'].replace(root_Dir,Instrument_Dir)
        a=ast.parse(open(file).read())
        for instrumentedFunc,decorator in funcList:
            decoratorNode = ast.Name(id=decorator, ctx=ast.Load)
            newbody=[ast.parse(f'from InstruHelper import {decorator}')]
            for node in a.body:
                if isinstance(node,ast.ClassDef) and node.name == c['name']:
                    newNodeBody=[]
                    found = False
                    for stmt in node.body:
                        if isinstance(stmt, ast.FunctionDef) and stmt.name == instrumentedFunc:
                            found = True
                            stmt.decorator_list = [decoratorNode]+stmt.decorator_list
                        newNodeBody.append(stmt)
                    if not found:
                        newNodeBody.append(constructASTNode(node.name,instrumentedFunc,decoratorNode,c['funcMap'][instrumentedFunc]))
                    node.body=newNodeBody
                newbody.append(node)
            a.body=newbody
        ast.fix_missing_locations(a)
        os.remove(file)
        with open(file,'w') as f:
            f.write(ast.unparse(a))
  
def instruct_collect(funcList,funcDefs,root_Dir):
    Instrument_Dir = '../data/instruct_collect'
    InstrTool_Dir = 'collectFiles'
    initCopy(root_Dir,Instrument_Dir)
    instruct(root_Dir,Instrument_Dir,funcList,funcDefs)
    for fileName in os.listdir(InstrTool_Dir):
        shutil.copyfile(os.path.join(InstrTool_Dir,fileName),os.path.join(Instrument_Dir,fileName))  

def instruct_PACO(root_Dir):
    Instrument_Dir = '../data/instruct_PACO'
    initCopy(root_Dir,Instrument_Dir)
    InstrTool_Dir = 'PACOFiles'
    for fileName in os.listdir(InstrTool_Dir):
        shutil.copyfile(os.path.join(InstrTool_Dir,fileName),os.path.join(Instrument_Dir,fileName))  

def instruct_FreeFuzzCollect(root_Dir):
    Instrument_Dir = '../data/instruct_FFcollect'
    InstrTool_Dir = 'FFCollect'
    initCopy(root_Dir,Instrument_Dir)
    for fileName in os.listdir(InstrTool_Dir):
        if os.path.isdir(os.path.join(InstrTool_Dir,fileName)):
            shutil.copytree(os.path.join(InstrTool_Dir,fileName),os.path.join(Instrument_Dir,fileName),dirs_exist_ok=True)  
        else:
            shutil.copyfile(os.path.join(InstrTool_Dir,fileName),os.path.join(Instrument_Dir,fileName))  
    shutil.copyfile(os.path.join(InstrTool_Dir,'keras/__init__.py'),os.path.join(Instrument_Dir,'keras/__init__.py'))     


def instruct_FF(funcList,funcDefs,root_Dir):
    Instrument_Dir = '../data/instruct_FreeFuzz'
    InstrTool_Dir = 'FreeFuzzFiles'
    initCopy(root_Dir,Instrument_Dir)
    instruct(root_Dir,Instrument_Dir,funcList,funcDefs)
    for fileName in os.listdir(InstrTool_Dir):
        if os.path.isdir(os.path.join(InstrTool_Dir,fileName)):
            shutil.copytree(os.path.join(InstrTool_Dir,fileName),os.path.join(Instrument_Dir,fileName),dirs_exist_ok=True)  
        else:
            shutil.copyfile(os.path.join(InstrTool_Dir,fileName),os.path.join(Instrument_Dir,fileName))  
    shutil.copyfile(os.path.join(InstrTool_Dir,'keras/__init__.py'),os.path.join(Instrument_Dir,'keras/__init__.py'))     
if __name__ == '__main__':
    
    #configs
    
    funcList=[('__init__','logInit'), ('call','logCall')]
    funcDefs = pickle.load(open('../data/funcDef.pickle','rb'))
    root_Dir='../data/keras-3.1.0'
    
    instruct_collect(funcList,funcDefs,root_Dir)
    instruct_PACO(root_Dir)
    instruct_FreeFuzzCollect(root_Dir)
    instruct_FF(funcList,funcDefs,root_Dir)


    
