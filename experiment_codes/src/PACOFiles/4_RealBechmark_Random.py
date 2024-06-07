
def extractPart(seedpool,keyParams):
    keyArgList = []
    for seeds in seedpool:
            oneArg=tuple((i,seeds[i]) for i in keyParams)
            if not oneArg in keyArgList:
                keyArgList.append(oneArg)
    return keyArgList

if __name__ == '__main__':
    import dill,os
    from executionUtils import executeTupleWithBackends,execTupleBatch
    import random     
    paramInfo = dill.load(open('../paramInfo.pickle','rb'))
    seedpool = dill.load(open('../seedpool.pickle','rb'))
    allRes = {}
    for clsName in seedpool.keys(): 
        #print(clsName)
        allRes[clsName] = {}
        allseeds = seedpool[clsName]
        keyParams = paramInfo['keyParams'][clsName]
        freeParams = paramInfo['freeParams'][clsName]
        argInfoList = paramInfo['ParamList'][clsName]
        SpaceVolumn = 1
        for argIndex in freeParams+keyParams:
            SpaceVolumn *= len(argInfoList[argIndex]['valueSpace'])
        maxIter = min(SpaceVolumn,1000)
        for seed in allseeds:
            res,Res=executeTupleWithBackends(clsName,seed)
            allRes[clsName][seed] = (Res,res)
        while (len(allRes[clsName]) < maxIter):
            #print(len(allRes[clsName]))
            testCaseToexecute = None
            for tryTime in range(10000):
                s = random.choice(allseeds)
                p = random.choice(freeParams+keyParams)
                v = random.choice(argInfoList[p]['valueSpace'])
                newS = list(s)
                newS[p] = v
                newS=tuple(newS)
                if newS not in allRes[clsName].keys():
                    testCaseToexecute = newS
                    break
            if testCaseToexecute is None:
                break
            else:
                res,Res=executeTupleWithBackends(clsName,testCaseToexecute)
                allRes[clsName][testCaseToexecute] = (Res,res)
                if res != 'Crash':
                    allseeds.append(testCaseToexecute)
    if not os.path.exists('../RQ3Res'):
            os.mkdir('../RQ3Res')
    dill.dump(allRes,open('../RQ3Res/randRes.pickle','wb'))                