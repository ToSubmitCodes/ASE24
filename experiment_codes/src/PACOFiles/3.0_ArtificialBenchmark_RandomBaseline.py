from Eutils import NLayer,NList,NDict,NTensor,NDtype
from keras.dtype_policies.dtype_policy import FloatDTypePolicy
import random,dill
import numpy as np
def randShape():
    length = random.randint(1,5)
    shape = [random.randint(1,5) for i in range(length)]
    return shape

def getMutateValue(v):
    if isinstance(v,NDtype):
        return FloatDTypePolicy('float32')
    elif isinstance(v,NLayer):
        return None
    elif isinstance(v,NList):
        rv = []
        for e in v.l:
            rv.append(getMutateValue(e))
        return rv
    elif isinstance(v,NDict):
        rv = {}             
        for k in v.d.keys():
            rv[k] = getValue(v.d[k])
        return rv
    elif isinstance(v,NTensor):
        shape = randShape()
        return np.random.rand(*shape)
    elif 'int' in str(type(v)):
        return random.randint(1,100)
    elif 'float' in str(type(v)):
        return random.random()
    else:
        return v

if __name__ == '__main__':
    import dill
    from executionUtils import executeTupleWithBackends,execTupleBatch
    import random     
    import time, os
    start_time = time.time()
    paramInfo = dill.load(open('../paramInfo.pickle','rb'))
    seedpool = dill.load(open('../seedpool.pickle','rb'))
    allRes = {}
    BKS = ['tensorflow']#,'torch','jax']
    cnt = 0
    for clsName in os.listdir('../SimpleFaults'): #seedpool.keys(): 
        #print(clsName)
        #print(cnt,'//',len(os.listdir('../FinalSimpleFaults')))
        allRes[clsName] = {}
        allseeds = seedpool[clsName]
        keyParams = paramInfo['keyParams'][clsName]
        freeParams = paramInfo['freeParams'][clsName]
        argInfoList = paramInfo['ParamList'][clsName]
        SpaceVolumn = 1
        allv = 0
        for argIndex in freeParams+keyParams:
            SpaceVolumn *= len(argInfoList[argIndex]['valueSpace'])
            allv += len(argInfoList[argIndex]['valueSpace'])
        maxIter = min(SpaceVolumn,1000)
        #print(maxIter)
        for seed in allseeds:
            res,Res=executeTupleWithBackends(clsName,seed,BKS,'RQ1')
            allRes[clsName][seed] = (Res,res)
        while (len(allRes[clsName]) < maxIter):
            #print(len(allRes[clsName]))
            testCaseToexecute = None
            for tryTime in range(10000):
                s = random.choice(allseeds)
                p = random.choice(range(allv))
                tp = None
                for i,arg in enumerate(argInfoList):
                    l = len(arg['valueSpace'])
                    if l<=p:
                        p -= l
                    else:
                        v=arg['valueSpace'][p]
                        tp = i
                newS = list(s)
                newS[tp] = dill.dumps(getMutateValue(dill.loads(v)))
                newS=tuple(newS)
                if newS not in allRes[clsName].keys():
                    testCaseToexecute = newS
                    break
            if testCaseToexecute is None:
                break
            else:
                res,Res=executeTupleWithBackends(clsName,testCaseToexecute,BKS,'RQ1')
                allRes[clsName][testCaseToexecute] = (Res,res)
                if res != 'Crash':
                    allseeds.append(testCaseToexecute)
    if not os.path.exists('../RQ1Res'):
        os.mkdir('../RQ1Res')
    dill.dump(allRes,open('../RQ1Res/randRes.pickle','wb'))
    endtime = time.time()
    #print(endtime-start_time)
                