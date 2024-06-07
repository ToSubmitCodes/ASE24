from utils import NTensor
def extractPart(seedpool,keyParams,argInfoList,passby=False):
    keyArgList = []
    exists={i:[] for i in keyParams}
    for seeds in seedpool:
        if passby:
            oneArg=tuple((i,seeds[i]) for i in keyParams)
            if oneArg not in keyArgList:
                keyArgList.append(oneArg)
        else:
            new=False
            for i in keyParams:
                index  = (seeds[i])
                if index not in exists[i]:
                    exists[i].append( index )
                    new=True
            if new:
                oneArg=tuple((i,seeds[i]) for i in keyParams)
                if oneArg not in keyArgList:
                    keyArgList.append(oneArg)
    return keyArgList

def comb(kp,fp,length,argInfoList):
    newTC = [None for _ in range(length)]
    for arg in kp+fp:
        newTC[arg[0]] = arg[1]
    return tuple(newTC)

def buildArgValueList(argInfoList,keyparams):
    valueList=[]
    for paramIndex in keyparams:
        for v in argInfoList[paramIndex]['valueSpace']:
            valueList.append((paramIndex,v))
    return valueList
        
          
if __name__ == '__main__':
    import dill,json,os
    import time
    from executionUtils import executeTupleWithBackends,BACKENDS
    
    start_time=time.time()
    for backend in ['tensorflow']:#BACKENDS:       
        paramInfo = dill.load(open('../paramInfo.pickle','rb'))
        seedpool = dill.load(open('../seedpool.pickle','rb'))
        clsList = json.load(open('../injectedCls.json'))
        allRes = {}
        allCores = {}
        keyArgs = {}
        failed = 0
        success = 0
        clsCnt = 0
        for clsName in os.listdir('../SimpleFaults'):
            if not os.path.exists(f'../SimpleFaults/{clsName}'):
                continue
            #print(f'{backend},{clsCnt}/{len(os.listdir("../SimpleFaults"))},{clsName}')
            clsCnt += 1
            #initialize
            keyParams = paramInfo['keyParams'][clsName]
            freeParams = paramInfo['freeParams'][clsName]                
            argInfoList = paramInfo['ParamList'][clsName]
            #all passed test cases
            allseeds = seedpool[clsName]
            allRes[clsName] = {}
            for tc in allseeds:
                res,Res = executeTupleWithBackends(clsName,tc,[backend],'RQ1')
                if res != 'Crash':
                    allRes[clsName][tc] = (Res,res)
                else:
                    allseeds.remove(tc)
            #all test case result
            
            allCores[clsName] = []
            #print("Key")
            KeyArgList = extractPart(allseeds,keyParams,argInfoList,True)
            #print('Free')
            freeArgList = extractPart(allseeds,freeParams,argInfoList)
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
                KeyArgList = extractPart(allseeds,keyParams,argInfoList,True)
                freeArgList = extractPart(allseeds,freeParams,argInfoList)
                #print(len(KeyArgList))
                #print(len(freeArgList))
                allv = buildArgValueList(argInfoList,freeParams+keyParams)
                CrashTimeTable = {v:CrashTimeTable[v] for v in allv}
                ShowTimeTable = {v:ShowTimeTable[v] for v in allv}
                changeTimeTable= {v:changeTimeTable[v] for v in allv}
                newShapeTimeTable = {v:newShapeTimeTable[v] for v in allv}
                newAR,newIC,newPS = {},{},{}
                for seed in allseeds:
                    kp = extractPart([seed],keyParams,argInfoList,True)[0]
                    if kp in newPS.keys():
                        newCore = newPS[kp]+[seed]
                        newPS[kp] = newCore
                    else:
                        newPS[kp] = [seed]
                # for ok in IC.keys():
                #     #printV = []
                #     for argp in ok:
                #             #printV.append((argp[0],argp[1]))
                #     #print(#printV)
                #     #print("Core:")
                #     for cb in IC[ok]:
                #         #printV = []
                #         for argp in cb:
                #             #printV.append((argp[0],dill.loads(argp[1]).s if isinstance(dill.loads(argp[1]),NTensor) else dill.loads(argp[1]) ))
                #         #print(#printV)
                #     #print('\n')
                for k in KeyArgList:
                    newAR[k],newIC[k] = {},[]
                    for ok in IC.keys():
                        diffList = [a1 for a1 in ok if a1 not in k]
                        if len(diffList) == 0:
                            newAR[k],newIC[k] = AR[ok],IC[ok]
                            break
                AR,IC,PS = newAR,newIC,newPS
                #allseeds=[]    
                #generate new seedpool: key x free   
                if len(allRes[clsName]) >= maxIter:
                    #print('reach limits')
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
                    res,Res = executeTupleWithBackends(clsName,newTestCase,[backend],'RQ1')
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
                            newCore = IC[k] + [[v]]
                            IC[k] = newCore
                            # #print("ADD Local:",v[0],dill.loads(v[1]).s if isinstance(dill.loads(v[1]),NTensor) else dill.loads(v[1]))
                            
                            # #printV = []
                            # for argp in targetSeed:
                            #         #printV.append((argp[0],dill.loads(argp[1]).s if isinstance(dill.loads(argp[1]),NTensor) else dill.loads(argp[1]) ))
                            # #print(#printV)
                            # #print('\n')
                            # #printV = []
                            # for argp in newTestCase:
                            #         #printV.append((argp[0],dill.loads(argp[1]).s if isinstance(dill.loads(argp[1]),NTensor) else dill.loads(argp[1]) ))
                            # #print(#printV)
                            # #print('\n')
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
                            if closestTC is None and len(PS[k])>0:
                                closestTC = PS[k][0]
                            if len(PS[k]) == 0:
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
                                            res,Res = executeTupleWithBackends(clsName,ntc,[backend],'RQ1')
                                            if res=='Crash':
                                                if Res[backend][3] != ORES[backend][3]:
                                                    crashed.append((ntc,Res,res))
                                        if res != 'Crash':
                                            finalCore.append(arg)
                                            pairExamples[arg] = (ntc,Res,res)
                            if len(finalCore) <= 1 or len(PS[k]) == 0:
                                    failed += 1
                                    for arg in candidates:
                                        ShowTimeTable[arg] += 1
                                        CrashTimeTable[arg] += 1
                            else:
                                    success += 1
                                    # #print("ADD free:",ORES)
                                    # #printV = []
                                    # for argp in finalCore:
                                    #         #printV.append((argp[0],dill.loads(argp[1]).s if isinstance(dill.loads(argp[1]),NTensor) else dill.loads(argp[1]) ))
                                    # #print(#printV)
                                    # #print('\n')
                                    for k in KeyArgList:
                                        newCore = IC[k]+[finalCore]
                                        IC[k] = newCore
                                    allCores[clsName].append((ORES, None, finalCore,pairExamples))

                    else:
                        newCore = PS[k] + [newTestCase]
                        PS[k] = newCore
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
                
                # #print('check IC after step2:')
                # for k in IC.keys():
                #     #printV = []
                #     for argp in k:
                #             #printV.append((argp[0],argp[1]))
                #     #print(#printV)
                #     #print("Core:",len(IC[k]))
                #     #printV = []
                #     for argp in IC[k]:
                #             #printV.append((argp[0],dill.loads(argp[1]).s if isinstance(dill.loads(argp[1]),NTensor) else dill.loads(argp[1]) ))
                #     #print(#printV)
                #     #print('\n')
                
                # if not foundNewSR and not retried:
                #     #print("RETRY")
                #     cons = []
                #     retried = True
                #     for index in keyParams:
                #         if argInfoList[index]['name'] == 'call_inputs':
                #             inputsIndex=index
                #         for t in argInfoList[index]['type']:
                #             if 'int' in str(t) or 'float' in str(t) or 'Tensor' in str(t):
                #                 cons.append(index)
                #                 #print(argInfoList[index]['name'])
                #                 break
                #     for index in cons:
                #         keyParams.remove(index)
                #         freeParams.append(index)
                #     if len(keyParams)==0:
                #         keyParams.append(inputsIndex)
                #         freeParams.remove(inputsIndex)

                if (len(allRes[clsName]) >= maxIter) or (len(allRes[clsName]) == startNum):
                    #print(len(allRes[clsName]),'no new tc')
                    break
            keyArgs[clsName] = keyParams
        if not os.path.exists('../RQ2Res'):
            os.mkdir('../RQ2Res')
        dill.dump(allRes,open(f'../RQ2Res/res_{backend}_mFIC.pickle','wb'))
        dill.dump(allCores,open(f'../RQ2Res/cores_{backend}_mFIC.pickle','wb'))
    endtime = time.time()
    #print(f"Execution Time:{endtime-start_time}")               
                    
                
                    
                            
                            
                    
                                                        
                                
                    
                
                            
                    
            
            
            
                