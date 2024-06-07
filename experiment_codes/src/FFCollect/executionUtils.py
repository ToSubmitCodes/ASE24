import dill,os
from pathlib import Path

WORKER_NUM = 1
BACKENDS = ['tensorflow','torch','jax']
paramInfo = dill.load(open('../paramInfo.pickle','rb'))

class CrashHandler:
    def __init__(self,clsName):
        self.CrashCore = []
        self.showTimeCrash = {} 
        self.successCnt = 0
        self.failCnt = 0
        self.clsName = clsName
        self.allRes = {}
    def crashHandle(self,ConsPart,d1,discList):
        if not ConsPart in self.showTimeCrash.keys():
            self.showTimeCrash[ConsPart] = {}
        newCore = self.findInfCore(d1,discList,[ConsPart])
        if len(newCore) == 1:
            self.failCnt += 1
            for v in d1:
                self.showTimeCrashDict[ConsPart][v] += 1
        else:
            self.successCnt += 1
            self.CrashCore.append(newCore) 
    
    def findInfCore(self,d1,dset,initCore=[]):
        candidates = list(d1)
        MaxSim=-1
        closestDis=None
        for d2,_,r2 in dset:
            if r2=='Crash':
                continue 
            sim=0
            for v in d2:
                if v in candidates:
                    candidates.remove(v)
                if v in d1:
                    sim += 1
            if sim > MaxSim:
                MaxSim = sim
                closestDis=d2
        if closestDis is None:
            return initCore
        core = initCore
        for v in candidates:
            newTestCase = [v2 if v2[0] != v[0] else v for v2 in newTestCase]
            Res,res = self.execute(newTestCase)
            if not res == 'Crash':
                core.append(v)
        return core

    def execute(self,d):
        d = self.reorder(d)
        if not d in self.allRes.keys():
            res,Res = executewithBackends(self.clsName,d,BACKENDS)
            self.allRes[d] = (Res,res)
            return (Res,res)
        else:
            return self.allRes[d]


def execBatch(clsName, seedSet):
    ResDict={}
    while len(seedSet)>0 :
        #search for a free worker
        for id in range(WORKER_NUM):
            lockFile = f'../workSpace/{id}/running'
            if not os.path.exists(lockFile):
                argDict = seedSet.pop()
                dill.dump(argDict,open(lockFile,'wb'))
                assignTask(clsName,argDict,BACKENDS,id)
                if len(seedSet) == 0:
                    break
        for id in range(WORKER_NUM):
            lockFile = f'../workSpace/{id}/running'
            if os.path.exists(lockFile):
                argDict = dill.load(open(lockFile,'rb'))
                res,Res = collectRes(BACKENDS,id)
                ResDict[argDict] = (Res,res)
                while True:
                    try:
                        os.remove(lockFile)
                        break
                    except Exception as e:
                        print(e)
    return ResDict



def analyzeResults(resSet):
    #Check1. Invalid
    for k in resSet.keys():
        if resSet[k][3] is not None:
            return 'Crash'
    #Check2. Shape Consistant
    for k in resSet.keys():
        if resSet[k][1] != resSet[k][2]:
            return 'Crash'
    #Check3. Res Consisitant
    if len(resSet) == 1:
        return 'Pass'
    else:
        keyList = list(resSet.keys())
        for i,k in enumerate(keyList[:-1]):
            if resSet[k][1] != resSet[keyList[i+1]][1]:
                return "DifferentRes"
    return 'Pass'

def assignTask(clsName,argDict,backends,id=0):
    for backend in backends:
        inputFile = f'../workSpace/{id}/inputs/{backend}'
        dill.dump((clsName,argDict),open(inputFile,'wb'))
        inputFlag = Path(f'../workSpace/{id}/flags/start_{backend}')
        inputFlag.touch()

def collectRes(backends,id=0):
    ResSet={}
    for backend in backends:
        outputFlag = f'../workSpace/{id}/flags/done_{backend}'
        while(True):
            if os.path.exists(outputFlag):
                outputFile = f'../workSpace/{id}/outputs/{backend}'
                ResSet[backend] = dill.load(open(outputFile,'rb'))
                os.remove(outputFile)
                while True:
                    try:
                        os.remove(outputFlag)
                        break
                    except Exception as e:
                        print(str(e))
                        pass
                break
    res = analyzeResults(ResSet)
    return res,ResSet

def executewithBackends(clsName,argDict,backends,id=0):
    #execute TestCases
    assignTask(clsName,argDict,backends,id)
    #collect Result
    res,ResSet = collectRes(backends,id)
    return res,ResSet

def executeTupleWithBackends(clsName,argTuple,backends=BACKENDS,id=0):
    #execute TestCases
    argList = paramInfo['ParamList'][clsName]
    argDict = [(argList[i]['name'],arg) for i,arg in enumerate(argTuple)]
    assignTask(clsName,argDict,backends,id)
    #collect Result
    res,ResSet = collectRes(backends,id)
    return res,ResSet

def execTupleBatch(clsName, seedSet):
    passed = []
    crashed = []
    argList = paramInfo['ParamList'][clsName]
    while len(seedSet)>0 :
        #search for a free worker
        for id in range(WORKER_NUM):
            lockFile = f'../workSpace/{id}/running'
            if not os.path.exists(lockFile):
                argTuple = seedSet.pop()
                argDict = [(argList[i]['name'],arg) for i,arg in enumerate(argTuple)]
                dill.dump(argTuple,open(lockFile,'wb'))
                assignTask(clsName,argDict,BACKENDS,id)
                if len(seedSet) == 0:
                    break
        for id in range(WORKER_NUM):
            lockFile = f'../workSpace/{id}/running'
            if os.path.exists(lockFile):
                argDict = dill.load(open(lockFile,'rb'))
                res,Res = collectRes(BACKENDS,id)
                if res=='Crash':
                    crashed.append((argDict,Res,res))
                else:
                    passed.append((argDict,Res,res))
                while True:
                    try:
                        os.remove(lockFile)
                        break
                    except Exception as e:
                        print(e)
    return crashed,passed