
def extractPart(seedpool,keyParams,passby=False):
    keyArgList = []
    exists={i:[] for i in keyParams}
    for seeds in seedpool:
        if passby:
            oneArg=tuple((i,str(seeds[i])) for i in keyParams)
            if oneArg not in keyArgList:
                keyArgList.append(oneArg)
        else:
            new=False
            for i in keyParams:
                if str(seeds[i]) not in exists[i]:
                    exists[i].append( str(seeds[i]) )
                    new=True
            if new:
                oneArg=tuple( (i,str(seeds[i])) for i in keyParams)
                if oneArg not in keyArgList:
                    keyArgList.append(oneArg)
    return keyArgList

def comb(kp,fp,length):
    newTC = [None for _ in range(length)]
    for arg in kp+fp:
        newTC[arg[0]] = eval(arg[1])
    return tuple(newTC)

def buildArgValueList(argInfoList,keyparams):
    valueList=[]
    for paramIndex in keyparams:
        for v in argInfoList[paramIndex]['valueSpace']:
            valueList.append((paramIndex,v))
    return valueList
        
          
if __name__ == '__main__':
    import dill,json,os
    from executionUtils import executeTupleWithBackends,BACKENDS
    
    for backend in BACKENDS:       
        paramInfo = dill.load(open('../paramInfo.pickle','rb'))
        seedpool = dill.load(open('../seedpool.pickle','rb'))
        allRes = {}
        allCores = {}
        keyArgs = {}
        failed = 0
        success = 0
        clsCnt = 0
        for clsName in seedpool.keys():
            #print(f'{backend},{clsCnt}/{len(clsList)},{clsName}')
            clsCnt += 1
            #initialize
            keyParams = paramInfo['keyParams'][clsName]
            freeParams = paramInfo['freeParams'][clsName]                
            argInfoList = paramInfo['ParamList'][clsName]
            #all passed test cases
            allseeds = seedpool[clsName]
            allRes[clsName] = {}
            for tc in allseeds:
                res,Res = executeTupleWithBackends(clsName,tc,[backend])
                if res != 'Crash':
                    allRes[clsName][tc] = (Res,res)
                else:
                    allseeds.remove(tc)
            #all test case result
            
            allCores[clsName] = []
            #print("Key")
            KeyArgList = extractPart(allseeds,keyParams,True)
            #print('Free')
            freeArgList = extractPart(allseeds,freeParams)
            allv = buildArgValueList(argInfoList,freeParams+keyParams)
            CrashTimeTable = {v:0 for v in allv}
            ShowTimeTable = {v:0 for v in allv}
            changeTimeTable= {v:0 for v in allv}
            newShapeTimeTable = {v:0 for v in allv}
            AR,IC,PS={k:{} for k in KeyArgList},{k:[] for k in KeyArgList},{k:[] for k in KeyArgList}
            
            
            SpaceVolumn = 1
            for argIndex in freeParams+keyParams:
                SpaceVolumn *= len(argInfoList[argIndex]['valueSpace'])
            maxIter = min(SpaceVolumn,1000)
            #print(f'{SpaceVolumn}, maxInter:{maxIter}')
            #start testing
            retried = False
            while(len(allRes[clsName]) < maxIter):
                startNum = len(allRes[clsName])
                foundNewSR = False
                #print(f'currentTSsize:{len(allRes[clsName])}')
                #Module1. Seed Pool Extention
                KeyArgList = extractPart(allseeds,keyParams,True)
                freeArgList = extractPart(allseeds,freeParams)
                #print(len(KeyArgList))
                #print(len(freeArgList))
                allv = buildArgValueList(argInfoList,freeParams+keyParams)
                CrashTimeTable = {v:CrashTimeTable[v] for v in allv}
                ShowTimeTable = {v:ShowTimeTable[v] for v in allv}
                changeTimeTable= {v:changeTimeTable[v] for v in allv}
                newShapeTimeTable = {v:newShapeTimeTable[v] for v in allv}
                newAR,newIC,newPS = {},{},{}
                for seed in allseeds:
                    kp = extractPart([seed],keyParams,True)[0]
                    if kp in newPS.keys():
                        newPS[kp].append(seed)
                    else:
                        newPS[kp] = [seed]
                for k in KeyArgList:
                    newAR[k],newIC[k] = {},[]
                    for ok in AR.keys():
                        diffList = [a1 for a1 in ok if a1 not in k]
                        if len(diffList) == 0:
                            newAR[k],newIC[k] = AR[ok],IC[ok]
                            break
                AR,IC,PS = newAR,newIC,newPS
                #allseeds=[]    
                #generate new seedpool: key x free   
                foundNewKV = False
                keyIndex = None
                for k in KeyArgList:
                    ar = {}
                    newTCSet = [comb(k,fp,len(argInfoList)) for fp in freeArgList]  
                    #newTCSet = [i for i in newTCSet if i not in allRes[clsName].keys()]
                    nt = []
                    for tc in newTCSet:
                        Invalid = False
                        for invCore in IC[k]:
                            exist=True
                            for arg in invCore:
                                if tc[arg[0]] != arg[1]:
                                    exist = False
                                    break
                            if exist:
                                Invalid = True
                                break
                        if not Invalid:
                            nt.append(tc)
                    newTCSet = nt
                    ##print(f'firstRoundSize:{len(newTCSet)}')
                    crashed=[]
                    passed=[]
                    for tc in newTCSet:
                        if tc in allRes[clsName].keys() and allRes[clsName][tc][0] != 'Crash':
                            continue
                        res,Res = executeTupleWithBackends(clsName,tc,[backend])
                        if res == 'Crash':
                            crashed.append((tc,Res,res))
                        else:
                            passed.append((tc,Res,res))
                    for rec in crashed+passed:
                        ar[rec[0]] = (rec[1],rec[2])
                        allRes[clsName][rec[0]] = (rec[1],rec[2])

                    for rec in passed:
                        allseeds.append(rec[0])
                    #analyze crash core
                    while len(crashed) > 0:
                        tc = crashed.pop(0)
                        candidates = [(i,tc[0][i]) for i in freeParams]
                        core = [(i,tc[0][i]) for i in freeParams]
                        closestTC = None
                        maxSim = -1
                        for tc2 in passed:
                            sim = 0
                            for arg in candidates:
                                if tc2[0][arg[0]] == arg[1]:
                                    sim += 1
                                    if arg in core:
                                        core.remove(arg) 
                            if sim > maxSim:
                                maxSim = sim
                                closestTC = tc2[0]
                        if closestTC is None and len(passed)>0:
                            closestTC = passed[0]
                        if len(passed) == 0:
                            finalCore = candidates
                        else:
                            finalCore = []
                            pairExamples = {}
                            for arg in core:
                                newTestCase = list(tc[0])
                                newTestCase[arg[0]] = closestTC[arg[0]]
                                newTestCase = tuple(newTestCase)
                                Invalid = False
                                for invCore in IC[k]:
                                    exist=True
                                    for Narg in invCore:
                                        if newTestCase[Narg[0]] != Narg[1]:
                                            exist = False
                                            break
                                    if exist:
                                        Invalid = True
                                        break
                                if not Invalid: 
                                    if newTestCase in ar.keys():
                                        Res,res = ar[newTestCase]
                                    else:
                                        res,Res = executeTupleWithBackends(clsName,newTestCase,[backend])
                                        allRes[clsName][newTestCase] = (Res,res)
                                        if res=='Crash':
                                            if Res[backend][3] != tc[1][backend][3]:
                                                crashed.append((newTestCase,Res,res))
                                        else:
                                            allseeds.append(newTestCase)
                                            passed.append((newTestCase,Res,res))
                                        
                                    if res != 'Crash':
                                        finalCore.append(arg)
                                        pairExamples[arg] = (newTestCase,Res,res)
                        if len(finalCore) == 0 or len(passed) == 0:
                                failed += 1
                                for arg in candidates:
                                    ShowTimeTable[arg] += 1
                                    CrashTimeTable[arg] += 1
                        else:
                                success += 1
                                newCore = IC[k]+[finalCore]
                                IC[k] = newCore
                                allCores[clsName].append((tc[1], k, finalCore,pairExamples))
                    
                    for tc in passed:
                        if tc[0] not in PS[k]:
                            PS[k].append(tc[0])
                        for tc2 in passed:
                            if tc == tc2:
                                continue
                            diffNum=0
                            diffShape=False
                            diffindex = None
                            for i,arg in enumerate(tc[0]):
                                if arg != tc2[0][i]:
                                    changeTimeTable[(i,arg)] += 1
                                    diffNum += 1
                                    diffindex = i
                                    if tc[1] != tc2[1]:
                                        newShapeTimeTable[(i,arg)] += 1
                                        diffShape =True
                            if diffShape and (diffNum == 1):
                                foundNewKV = True
                                keyIndex = diffindex
                    AR[k].update(ar)
                    
                
                for k in KeyArgList:
                    allRes[clsName].update(AR[k])
                
                if foundNewKV:
                    #print(keyIndex,argInfoList[keyIndex]['name'])
                    keyParams.append(keyIndex)
                    freeParams.remove(keyIndex)
                    continue

                if len(allRes[clsName]) >= maxIter:
                    break
                    
                ##print(f'baseSize: {len(allRes[clsName])}')
                #mutate
                for ki,k in enumerate(KeyArgList):
                    seeds = PS[k]
                    scoreDict = {}
                    for seed in seeds:
                        risk = 1
                        for i,arg in enumerate(seed):
                            if (i,arg) in allv:
                                risk *= (CrashTimeTable[(i,arg)]+1.)/(ShowTimeTable[(i,arg)]+1.)
                        scoreDict[seed] = risk
                    seeds = sorted(scoreDict.items(),key=lambda k:k[1],reverse=True)
                    values = {}
                    for v in allv:
                        if v[0] not in freeParams:
                            continue
                        values[v] = (newShapeTimeTable[v]+1.)/(changeTimeTable[v]+1.) + (CrashTimeTable[v]+1.)/(ShowTimeTable[v]+1.)
                    values = sorted(values.items(), key=lambda k:k[1])
                    newTestCase = None
                    while (len(values) > 0 ):
                        v,_ = values.pop()
                        found = False
                        newTestCase = None
                        candidatesSeeds = seeds.copy()
                        while (True):
                            targetSeed = None
                            for i,seed, in enumerate(candidatesSeeds):
                                if seed[0][v[0]] != v[1]:
                                    targetSeed,_ = candidatesSeeds.pop(i)
                                    break
                            if targetSeed is None:
                                break
                            else:
                                newTestCase = list(targetSeed)
                                newTestCase[v[0]] = v[1]
                                newTestCase = tuple(newTestCase)
                                Invalid = False
                                for core in IC[k]:
                                    exist=True
                                    for arg in core:
                                        if newTestCase[arg[0]] != arg[1]:
                                            exist=False
                                            break
                                    if exist:
                                        Invalid = True                            
                                if newTestCase not in allRes[clsName].keys() and not Invalid:
                                    found = True
                                    break
                                newTestCase = None
                        if found:
                            break
                    if newTestCase is None:
                        continue
                    
                    #execute
                    res,Res = executeTupleWithBackends(clsName,newTestCase,[backend])
                    AR[k][newTestCase] = (Res,res)
                    allRes[clsName][newTestCase] = (Res,res)
                    ##print(f'newLength:{len(allRes[clsName])}')
                    
                    #analyze
                    if res == 'Crash':
                      crashed = [(newTestCase,Res,res)]
                      while len(crashed) > 0:
                        newTestCase,Res,res = crashed.pop(0)
                        ORES = Res
                        ##print("Result:Crash")
                        #input()
                        localCore=True
                        for tc2 in PS[k]:
                            if tc2[v[0]] == v[1]:
                                localCore = False
                        if localCore:
                            newCore = IC[k]+[[v]]
                            IC[k] = newCore
                            allCores[clsName].append((Res, k, [v],targetSeed))
                        else:     
                            candidates = [(i,newTestCase[i]) for i in freeParams]
                            core = [(i,newTestCase[i]) for i in freeParams]
                            closestTC = None
                            maxSim = -1
                            for tc2 in allseeds:
                                if tc2[v[0]] != v[1]:
                                    continue
                                sim = 0
                                for arg in candidates:
                                    if tc2[v[0]] == v[1]:
                                        sim += 1
                                        if arg in core:
                                            core.remove(arg) 
                                    if sim > maxSim:
                                        maxSim = sim
                                        closestTC = tc2[0]
                            if closestTC is None and len(passed)>0:
                                closestTC = passed[0]
                            if len(passed) == 0:
                                finalCore = candidates
                            else:
                                finalCore = []
                                pairExamples = {}
                                for arg in core:
                                    ntc = list(newTestCase)
                                    ntc[arg[0]] = closestTC[arg[0]]
                                    ntc = tuple(ntc)
                                    Invalid = False
                                    for invCore in IC[k]:
                                        exist=True
                                        for Narg in invCore:
                                            if ntc[Narg[0]] != Narg[1]:
                                                exist = False
                                                break
                                        if exist:
                                            Invalid = True
                                            break
                                    if not Invalid:
                                        if ntc in allRes[clsName].keys():
                                            Res,res = allRes[clsName][newTestCase]
                                        else:
                                            res,Res = executeTupleWithBackends(clsName,ntc,[backend])
                                            allRes[clsName][ntc] = (Res,res)
                                            if res=='Crash':
                                                if Res[backend][3] != ORES[backend][3]:
                                                    crashed.append((ntc,Res,res))
                                            else:
                                                PS[k].append(ntc)
                                                allseeds.append(ntc)
                                        if res != 'Crash':
                                            finalCore.append(arg)
                                            pairExamples[arg] = (ntc,Res,res)
                            if len(finalCore) == 0 or len(passed) == 0:
                                    failed += 1
                                    for arg in candidates:
                                        ShowTimeTable[arg] += 1
                                        CrashTimeTable[arg] += 1
                            else:
                                    success += 1
                                    for k in KeyArgList:
                                        newCore = IC[k]+[finalCore]
                                        IC[k] = newCore
                                    if len(passed) > 0:
                                        allCores[clsName].append((ORES, None, finalCore,pairExamples))

                    else:
                        PS[k].append(newTestCase)
                        allseeds.append(newTestCase)
                        seed = None
                        originalRes,_ = allRes[clsName][targetSeed]
                        if originalRes == Res:
                            ##print("Mutation Result: Nochange")
                            #input()
                            changeTimeTable[v] += 1
                        else:
                            ##print(f'newKeyVar:{v[0]}')
                            #input()
                            #print(v[0],argInfoList[v[0]]['name'])
                            keyParams.append(v[0])
                            freeParams.remove(v[0])
                            foundNewSR = True
                            break
                
                if not foundNewSR and not retried:
                    #print("RETRY")
                    cons = []
                    retried = True
                    for index in keyParams:
                        if argInfoList[index]['name'] == 'call_inputs':
                            inputsIndex=index
                        for t in argInfoList[index]['type']:
                            if 'int' in str(t) or 'float' in str(t) or 'Tensor' in str(t):
                                cons.append(index)
                                #print(argInfoList[index]['name'])
                                break
                    for index in cons:
                        keyParams.remove(index)
                        freeParams.append(index)
                    if len(keyParams)==0:
                        keyParams.append(inputsIndex)
                        freeParams.remove(inputsIndex)

                elif (len(allRes[clsName]) >= maxIter) or (len(allRes[clsName]) == startNum):
                    #print(len(allRes[clsName]),'no new tc')
                    break
            keyArgs[clsName] = keyParams
        if not os.path.exists('../RQ3Res'):
            os.mkdir('../RQ3Res')
        dill.dump(allRes,open(f'../RQ3Res/res_{backend}.pickle','wb'))
        dill.dump({'fail':failed,'success':success},open(f'../RQ3Res/count_{backend}.pickle','wb'))
        dill.dump(allCores,open(f'../RQ3Res/cores_{backend}.pickle','wb'))
        dill.dump(keyArgs,open(f'../RQ3Res/keys_{backend}.pickle','wb'))
                    
                
                    
                            
                            
                    
                                                        
                                
                    
                
                            
                    
            
            
            
                