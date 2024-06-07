# coding=utf-8
"""
对每一个Layer,分析其Call()函数，
目标：
1)构建继承关系图
2)找到构造函数和call()函数
3)构造函数用于确定需要搜索的参数空间, call()函数用于确定需要搜索的输入空间
"""
      
      
import json
import ast
import pickle
from utils import getAllFilePathes, getFullPath, isKerasClsDefNode, extractImport, getFullName, splitName
import os


rootDir='../data/keras-3.1.0'
APIList=json.load(open('../data/APIList.json'))
NSRecord = json.load(open('../data/globalNameRecord.json'))
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
                self.keywords = node.keywords


def createNewCls(name,node,res,fileName):
    newCls={'astnode':node,'import':res}
    newCls['name'] = name.value.split('.')[-1]
    newCls['nameSpace'] = '.'.join(name.value.split('.')[:-1])
    newCls['fileName'] = fileName
    return newCls
    
def CreateNewKerasCls(stmt,res,fileName):
    #collect all alias 
    newList=[]
    for callstmt in stmt.decorator_list:
        if callstmt.func.id == 'keras_export':
            fullName = callstmt.args[0]
            if isinstance(fullName,ast.List):
                for n in fullName.elts:
                    newList.append(createNewCls(n,stmt,res,fileName))
            else:
                newList.append(createNewCls(fullName,stmt,res,fileName)) 
    return newList

def searchForFuncs(importedModules, funcNameList, node):
        funcDefs={funcName:None for funcName in funcNameList}
        nextClsList=[]
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name in funcDefs.keys():
                funcDefs[stmt.name]=stmt
        for key in funcDefs.keys():
            if funcDefs[key] is not None:
                sc = superchecker()
                sc.visit(funcDefs[key])
            if not funcDefs[key] or sc.foundSuper:
                for baseName in node.bases:
                    fullName = getFullName(baseName)
                    nameSpace,directName = splitName(importedModules, fullName)
                    newCls = {'name':directName,'nameSpace':nameSpace}
                    if nameSpace+'.'+directName in NSRecord.keys():
                        filePath = NSRecord[nameSpace+'.'+directName]
                    else:
                        filePath = getFullPath(newCls['nameSpace'],rootDir)
                    a=ast.parse(open(filePath,encoding='utf-8').read())
                    newCls['import']=extractImport(filePath,rootDir)
                    newCls['fileName']=filePath
                    for stmt in a.body:
                        if isinstance(stmt,ast.ClassDef) and stmt.name==directName:
                            newCls['astnode']=stmt
                            break
                    nextClsList.append(newCls)     
        return nextClsList,funcDefs

if __name__ == '__main__':   
    for i,APIName in enumerate(APIList):
        APIList[i] = ''.join(APIName.split(' ')[:-1])

    fileList = getAllFilePathes(rootDir)

    #get nameSpace,astnode,name,import of initial cls
    newList = []
    for fileName in fileList:
        a=ast.parse(open(fileName,encoding='utf-8').read())
        for stmt in a.body:
            if isKerasClsDefNode(stmt,APIList):
                res=extractImport(fileName,rootDir)
                newList += CreateNewKerasCls(stmt,res,fileName)

    currentRound=newList
    AllCls=[]
    while (len(currentRound) > 0):
        nextRound = []
        for c in currentRound:
            nr,APIMap=searchForFuncs(c['import'],['__init__','call'],c['astnode'])
            c['funcMap']=APIMap
            c['base']=nr
            nextRound += nr
        AllCls.append(currentRound)
        currentRound=nextRound
        # existedName=[]
        # for c in nextRound:
        #     if not (c['nameSpace'],c['name']) in existedName:
        #         existedName.append((c['nameSpace'],c['name']))
        #         currentRound.append(c)

    result = []
    for layer in AllCls:
        for c in layer:
            for key in c['funcMap'].keys():
                if not c['funcMap'][key]:
                    hasDef=False
                    for cl in c['base']:
                        if cl['funcMap'][key]:
                            c['funcMap'][key] = cl['funcMap'][key]
                            hasDef=True
                            break
                    if not hasDef and c['name'] in APIList:
                        #print(c)
                        exit()
            if c['name'] in APIList and layer == AllCls[0]:
                result.append(c)

    pickle.dump(result,open('../data/funcDef.pickle','wb'))
            

