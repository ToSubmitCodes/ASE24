from functools import wraps
import json
import os
import dill
from keras.layers.layer import Layer
from tensorflow.python.framework.ops import SymbolicTensor
from keras.utils.tracking import TrackedList
from keras.dtype_policies.dtype_policy import DTypePolicy  
import shutil
from utils import NLayer, NList, NTensor, NDict, NDtype, NVar
import numpy as np

class MyException(BaseException):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


argDictDir = '../argDir'

def getAbsType(arg):
    ty = str(type(arg))
    if isinstance(arg,(list,tuple,np.ndarray)):
        vl =  []
        tl = ty+' of ['
        if isinstance(arg,np.ndarray) and len(arg.shape) == 0:
            return NList([arg.item()],ty+' of [ int ]'),ty+' of [ int ]'
        for e in arg:
            v,t = getAbsType(e)
            vl.append(v)
            tl += t+','
        tl += ']'
        return NList(vl,ty),tl
    elif 'Tensor' in ty or 'Variable' in ty:
        return NTensor(arg.shape,ty),ty
    elif isinstance(arg,Layer):
        return NLayer(ty),ty
    elif isinstance(arg,dict):
        vl =  {}
        tl = ty+' of ['
        for k in arg.keys():
            vk,tk = getAbsType(k)
            ve,te = getAbsType(arg[k])
            vl[vk] = ve
            tl += f'{tk}:{te},'
        tl += ']'
        return NDict(vl,tl),tl
    elif isinstance(arg,DTypePolicy):
        return NDtype(arg.name,ty),ty
    else:
        return arg,ty


ParamInfoDict = dill.load(open('../paramInfo.pickle','rb'))

def RecordTestCase(func,args,kwargs):
    clsName,_ = func.__qualname__.split('.')
    paramList = ParamInfoDict['ParamList'][clsName]
    Rec=[]
    for i,arg in enumerate(args[1:]):
        newVar = {'argName':paramList[i]['name']}
        v,t = getAbsType(arg)
        v = dill.dumps(v)
        newVar['value'] = v
        newVar['type'] = t
        Rec.append(newVar)
    for k in kwargs.keys():
        newVar = {'argName':'init_'+str(k)}
        v,t = getAbsType(kwargs[k])
        v = dill.dumps(v)
        newVar['value'] = v
        newVar['type'] = t
        Rec.append(newVar)
    return Rec

def RecordTestCase2(func,args,kwargs):
    clsName,funcName = func.__qualname__.split('.')
    paramList = ParamInfoDict['ParamList'][clsName]
    Rec=[]
    for i in range(len(paramList)):
        if paramList[i]['name'].startswith('call_'):
            startindex = i
            break
    for i,arg in enumerate(args[1:]):
        newVar = {'argName':paramList[startindex+i]['name']}
        v,t = getAbsType(arg)
        v = dill.dumps(v)
        newVar['value'] = v
        newVar['type'] = t
        Rec.append(newVar)
    for k in kwargs.keys():
        newVar = {'argName':'call_'+k}
        v,t = getAbsType(kwargs[k])
        v = dill.dumps(v)
        newVar['value'] = v
        newVar['type'] = t
        Rec.append(newVar)
    return Rec

def checkDillable(obj):
    try:
        dill.dump(obj,open('../temp.pickle','wb'))
        dill.load(open('../temp.pickle','rb'))
    except:
        recFile = '../undillableType.json'
        undillableType=json.load(open(recFile,'r')) if os.path.exists(recFile) else []
        undillableType.append(str(type(obj['value'])))

def checkDillableAll(args,kwargs):
    for arg in args[1:]:
        newVar = {}
        v,t = getAbsType(arg)
        if 'initializer' in t or 'DType' in t:
            continue
        newVar['value'] = v
        newVar['type'] = t
        checkDillable(newVar)
    for k in kwargs.keys():
        newVar = {'argName':str(k)}
        v,t = getAbsType(kwargs[k])
        newVar['value'] = v
        newVar['type'] = t
        checkDillable(newVar)

def comb(initArgs,callArgs):
    allArgs=[]
    for arg in initArgs:
        if arg['argName'] == 'name':
            continue
        allArgs.append((arg['argName'],arg['value']))
    for arg in callArgs:
        allArgs.append((arg['argName'],arg['value']))
    return tuple(allArgs)

def logInit(func):
        @wraps(func)
        def with_logging(*args, **kwargs):
            try:
                v = func(*args,**kwargs)    
            except:
                return func(*args, **kwargs)          
            setattr(args[0],'initArgList',RecordTestCase(func,args,kwargs))
            return v
        return with_logging

def ListTC2tupleTC(listTC,argInfoList):
    newTC = []
    for arg in argInfoList:
        found = False
        v = None
        for a in listTC:
            if a[0] == arg['name']:
                v = dill.loads(a[1])
                found = True
                break
        if not found:
            v = dill.loads(arg['default'])
        newTC.append(v)
    return tuple(newTC)

injectedBugs={}
for fileName in os.listdir('../SimpleFaults'):
    injectedBugs[fileName]=dill.load(open(f'../SimpleFaults/{fileName}','rb'))
    
def checkfault(clsName,args):
    newTestCase = ListTC2tupleTC(args,ParamInfoDict['ParamList'][clsName])
    if clsName in injectedBugs.keys():
        (comb1,err1),(comb2,err2) = injectedBugs[clsName][2]
        (comb3,err3),(comb4,err4) = injectedBugs[clsName][3]
        if newTestCase[comb1[0][0]] == dill.loads(comb1[0][1]) and newTestCase[comb1[1][0]] == dill.loads(comb1[1][1]):
            raise Exception(f'Catch a bug {err1}')
        if newTestCase[comb2[0][0]] == dill.loads(comb2[0][1]) and newTestCase[comb2[1][0]] == dill.loads(comb2[1][1]):
            return err2
        if newTestCase[comb3[0][0]] == dill.loads(comb3[0][1]) and newTestCase[comb3[1][0]] == dill.loads(comb3[1][1]) and newTestCase[comb3[2][0]] == dill.loads(comb3[2][1]):
            raise Exception(f'Catch a bug {err3}')
        if newTestCase[comb4[0][0]] == dill.loads(comb4[0][1]) and newTestCase[comb4[1][0]] == dill.loads(comb4[1][1]) and newTestCase[comb4[2][0]] == dill.loads(comb4[2][1]):
            return err4
    else:
        return None
            
def logCall(func):
        @wraps(func)
        def with_logging(*args, **kwargs):
            initArgs = getattr(args[0],'initArgList')
            callArgs = RecordTestCase2(func,args,kwargs)
            allArgs = comb(initArgs,callArgs)
            clsName,_ = func.__qualname__.split('.')
            res = checkfault(clsName,allArgs)
            if res is not None:
                try:
                    v = func(*args,**kwargs)
                    s = list(v.shape)
                    ns=s+[res]
                    return np.ones(ns)
                except:
                    return func(*args,**kwargs)
            else:
                return func(*args,**kwargs)
        return with_logging