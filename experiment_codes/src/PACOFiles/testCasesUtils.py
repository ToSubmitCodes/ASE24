import dill, importlib
from Eutils import NLayer,NList,NDict,NTensor,NDtype
from keras.backend.common.keras_tensor import KerasTensor
import numpy as np
from keras.dtype_policies.dtype_policy import FloatDTypePolicy
import json
import traceback
import re

paramInfoFile = '../paramInfo.pickle'
paramInfo = dill.load(open(paramInfoFile,'rb'))

dictFile = '../funcDef.pickle'
def getNameSpace():
    a = dill.load(open(dictFile,'rb'))
    NSMap = {}
    for clsInfo in a:
        filePath = clsInfo['fileName']
        eles = filePath.split('/')
        head = -1
        for i,e in enumerate(eles):
            if e=='keras':
                head = i
        if head == -1:
            #print(f"Error: {filePath}")
            exit()
        fullName = '.'.join(eles[head:])
        fullName = fullName[:-3] if fullName.endswith('.py') else fullName
        NSMap[clsInfo['name']] = fullName
    return NSMap

NSMap = getNameSpace()

def getValue(v):
    if isinstance(v,NDtype):
        return FloatDTypePolicy('float32')
    if isinstance(v,NLayer):
        return None
    elif isinstance(v,NList):
        rv = []
        for e in v.l:
            rv.append(getValue(e))
        return rv
    elif isinstance(v,NDict):
        rv = {}
        for k in v.d.keys():
            rv[k] = getValue(v.d[k])
        return rv
    elif isinstance(v,NTensor):
        if None in v.s:
            return KerasTensor(shape=list(v.s))
        else:
            return np.random.rand(*list(v.s))
    else:
        return v

def extractErrmag(msg):
    pattern = re.compile('File \"(.*)\"(.*)\n(.*)\n')
    results = re.findall(pattern,msg)
    return '\n'.join(results[-1])

def extractDcit(rawArgDict):
    resArgDict={'init':{},'call':{}}
    for k,v in rawArgDict:
        funcName,argName = k.split('_',1)
        assert funcName in resArgDict.keys(), f'funcName not exists: {funcName}'
        assert not argName in resArgDict[funcName].keys(), f'duplicated argName:{argName}'
        resArgDict[funcName][argName] = getValue(dill.loads(v))
    return resArgDict

def execute(clsName,rawArgDict):
    Module = NSMap[clsName]
    m = importlib.import_module(Module)
    cls = getattr(m,clsName)
    argDict = extractDcit(rawArgDict)
    Res = [None,None,None,None,None]
    try:
        layer = cls(**argDict['init'])
        Res[0] = 'Success'
    except Exception as e:
        msg = traceback.format_exc()
        msg = extractErrmag(msg)
        return [msg,None,None,msg,(repr(e),str(e))]
    try:
        y = layer(**argDict['call'])
        if isinstance(y,tuple):
            y = y[0]
        ##print(type(y))
        Res[1] = list(y.shape)
    except Exception as e:
        msg = traceback.format_exc()
        msg = extractErrmag(msg)
        Res[1] = msg
        Res[3] = msg
        Res[4] = (repr(e),str(e))
    try:
        if 'inputs' in argDict['call'].keys():
            x = argDict['call']['inputs']
        else:
            x = argDict['call']['sequences']
        if isinstance(x,list):
            s = layer.compute_output_shape([i.shape for i in x])
        else:
            s = layer.compute_output_shape(x.shape)
        Res[2] = list(s)
    except Exception as e:
        msg = traceback.format_exc()
        msg = extractErrmag(msg)
        Res[2] = msg
        Res[3] = msg
        Res[4] = (repr(e),str(e))
    return Res


def getPartialDict(clsName,argDict,argIndexList):
    partialArgDict = []
    allargs = {}
    flagDict={}
    for index in argIndexList:
        allargs[paramInfo[clsName][index]['name']] = paramInfo[clsName][index]['default']
        flagDict[paramInfo[clsName][index]['name']] = False
    for args in argDict:
            if args[0] in allargs.keys():
                partialArgDict.append(args)
                flagDict[args[0]]=True
    for k in flagDict.keys():
        if not flagDict[k]:
            partialArgDict.append((k,allargs[k]))
    return tuple(partialArgDict)


def getPartial(clsName,argIndexList):
    argIDList=[]
    for index in argIndexList:
        for v in paramInfo[clsName][index]['valueSpace']:
            argIDList.append((paramInfo[clsName][index]['name'],v))
    return tuple(argIDList)

