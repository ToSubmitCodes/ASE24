# coding=utf-8
import os
import ast

def importHelper(names, prefix=''):
    importedModules=[]
    for name in names:
        oneImport={}
        if len(prefix) > 0:
            oneImport['nameSpace'] = prefix+'.'+name.name
        else:
            oneImport['nameSpace'] = name.name
        if name.asname:
            oneImport['alias'] = name.asname
        else:
            oneImport['alias'] = name.name
        importedModules.append(oneImport)
    return importedModules

def extractImport(fileName,rootDir):
    importredModules=[]
    node = ast.parse(open(fileName,encoding='utf-8').read())
    for stmt in node.body:
        if isinstance(stmt,ast.Import):
            importredModules+=importHelper(stmt.names)
        elif isinstance(stmt,ast.ImportFrom):
            importredModules+=importHelper(stmt.names,prefix=stmt.module)
        elif isinstance(stmt,ast.ClassDef):
            oneImport={}
            oneImport['alias']=stmt.name
            oneImport['nameSpace']=fullName2NameSpace(fileName, rootDir)+'.'+stmt.name
            importredModules.append(oneImport)
        elif isinstance(stmt,ast.Assign):
            oneImport={}
            oneImport['alias']=stmt.targets[0].id
            oneImport['nameSpace']=fullName2NameSpace(fileName, rootDir)+'.'+stmt.targets[0].id
            oneImport['value']=stmt.value.value
            importredModules.append(oneImport)
    return importredModules

"""
输入:文件系统中的一个目录
输出:迭代输出目录中所有的文件
"""
def getAllFilePathes(dir):
    dirList=[dir]
    fileList=[]
    while len(dirList) > 0:
        curDir=dirList.pop()
        for filename in os.listdir(curDir):
            fullPath=curDir+'/'+filename
            if os.path.isdir(fullPath):
                dirList.append(fullPath)
            elif fullPath.endswith('.py') and not 'test' in fullPath and not '_v1' in fullPath and not 'example' in fullPath:
                fileList.append(fullPath)
    return fileList

def getFullPath(nameSpace,root):
    return root+'/'+nameSpace.replace('.','/')+'.py'

def fullName2NameSpace(fullName,root):
    return fullName.replace(root,'').replace('.py','').replace('/','.')

def getFullName(name):
    if isinstance(name,ast.Name):
        return name.id
    elif isinstance(name, ast.Attribute):
        return getFullName(name.value)+'.'+name.attr
    else:
        raise NotImplementedError()

def splitName(importedModules, name):
        fullName=''
        #replaceTheAlias
        for imp in importedModules:
            if imp['alias']+'.' in name:
                fullName=name.replace(imp['alias'],imp['nameSpace'])
                break
            elif imp['alias'] == name:
                fullName=name.replace(imp['alias'],imp['nameSpace'])
                break
        assert '.' in fullName
        directName=fullName.split('.')[-1]
        nameSpace='.'.join(fullName.split('.')[:-1])
        return nameSpace,directName

def isKerasClsDefNode(node, APIList):
    if not (isinstance(node,ast.ClassDef) and node.name in APIList and len(node.decorator_list) > 0):
        return False
    for callstmt in node.decorator_list:
        argsContainLayers=False
        for arg in callstmt.args:
            if isinstance(arg,ast.Constant) and 'layers' in arg.value and not '_legacy' in arg.value:
                argsContainLayers = True
            if isinstance(arg,ast.List):
                for e in arg.elts:
                    if isinstance(e, ast.Constant) and 'layers' in e.value and not '_legacy' in e.value:
                        argsContainLayers = True
        if callstmt.func.id == 'keras_export' and argsContainLayers:
            return True
    return False



