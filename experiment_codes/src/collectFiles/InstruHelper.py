from functools import wraps
import json
import os
import dill
from keras.layers.layer import Layer
from tensorflow.python.framework.ops import SymbolicTensor
from keras.utils.tracking import TrackedList
from keras.dtype_policies.dtype_policy import DTypePolicy  
import shutil
from Eutils import NLayer, NList, NTensor, NDict, NDtype, NVar
import numpy as np

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




def RecordTestCase(func,args,kwargs):
    clsName,funcName = func.__qualname__.split('.')
    paramDict = dill.load(open(os.path.join(argDictDir,clsName),'rb'))
    paramList = paramDict[funcName]
    Rec=[]
    for i,arg in enumerate(args[1:]):
        newVar = {'argName':paramList[i]['name']}
        v,t = getAbsType(arg)
        v = dill.dumps(v)
        paramList[i]['valueSpace'].append(v)
        paramList[i]['type'].append(t)
        newVar['value'] = v
        newVar['type'] = t
        Rec.append(newVar)
    for k in kwargs.keys():
        newVar = {'argName':str(k)}
        v,t = getAbsType(kwargs[k])
        v = dill.dumps(v)
        newVar['value'] = v
        newVar['type'] = t
        Rec.append(newVar)
        if not k=='name':
            found = False
            for arg in paramList:
                if arg['name'] == k:
                    found=True
                    arg['valueSpace'].append(v)
                    arg['type'].append(t)

    paramDict[funcName]=paramList
    dill.dump(paramDict,open(os.path.join(argDictDir,clsName),'wb'))
    return Rec

def RecordTestCase2(func,args,kwargs):
    clsName,funcName = func.__qualname__.split('.')
    paramDict = dill.load(open(os.path.join(argDictDir,clsName),'rb'))
    paramList = paramDict[funcName]
    Rec=[]
    for i,arg in enumerate(args[1:]):
        newVar = {'argName':paramList[i]['name']}
        v,t = getAbsType(arg)
        v = dill.dumps(v)
        paramList[i]['valueSpace'].append(v)
        paramList[i]['type'].append(t)
        newVar['value'] = v
        newVar['type'] = t
        Rec.append(newVar)
    for k in kwargs.keys():
        newVar = {'argName':k}
        v,t = getAbsType(kwargs[k])
        v = dill.dumps(v)
        newVar['value'] = v
        newVar['type'] = t
        Rec.append(newVar)
        found = False
        for arg in paramList:
            if arg['name'] == k:
                found=True
                arg['valueSpace'].append(v)
                arg['type'].append(t)

    paramDict[funcName]=paramList
    dill.dump(paramDict,open(os.path.join(argDictDir,clsName),'wb'))
    return Rec

def checkDillable(obj):
    try:
        dill.dump(obj,open('../temp.pickle','wb'))
        dill.load(open('../temp.pickle','rb'))
    except:
        recFile = '../undillableType.json'
        undillableType=json.load(open(recFile,'r')) if os.path.exists(recFile) else []
        undillableType.append(str(type(obj['value'])))
        json.dump(undillableType,open(recFile,'w'),indent=9)

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
        allArgs.append(('init_'+arg['argName'],arg['value']))
    for arg in callArgs:
        allArgs.append(('call_'+arg['argName'],arg['value']))
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
    
def logCall(func):
        @wraps(func)
        def with_logging(*args, **kwargs):
            try:
                v = func(*args,**kwargs)
            except:
                return func(*args, **kwargs) 
            initArgs = getattr(args[0],'initArgList')
            callArgs = RecordTestCase2(func,args,kwargs)
            allArgs = comb(initArgs,callArgs)
            clsName,_ = func.__qualname__.split('.')
            recPath = '../rawTC.pickle' 
            recs = dill.load(open(recPath,'rb')) if os.path.exists(recPath) else {}
            if clsName in recs.keys():
                recs[clsName].append(allArgs)
            else:
                recs[clsName]=[allArgs]
            dill.dump(recs,open(recPath,'wb'))
            return v
         
        return with_logging