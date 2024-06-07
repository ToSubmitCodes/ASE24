def InitArgList(ParamInfoDict, clsName, argList, funcName):
    NewArgList = []
    cnt = 0
    for i,argInfo in enumerate(argList):    
        if argInfo['name'] == 'name':
            continue
        a={}
        a['name'] = f'{funcName}_{argInfo["name"]}'
        a['valueSpace'] = []
        a['type'] = argInfo['type']
        if 'default' in argInfo.keys():
            a['default'] = argInfo['default']
        NewArgList.append(a)
        isCons = False
        for t in argInfo['type']:
            if 'int' in str(t) or 'float' in str(t) or 'Tensor' in str(t):
                ParamInfoDict['keyParams'][clsName].append(len(ParamInfoDict['ParamList'][clsName])+cnt)
                isCons = True
                break
        if not isCons:
            ParamInfoDict['freeParams'][clsName].append(len(ParamInfoDict['ParamList'][clsName])+cnt)
        cnt += 1
    ParamInfoDict['ParamList'][clsName] += NewArgList

def extractValue(ParamInfoDict,clsName,testcase):
    testCaseDict = {argName:v for argName,v in testcase}
    for i,argInfo in enumerate(ParamInfoDict['ParamList'][clsName]):
        if argInfo['name'] in testCaseDict.keys():
            newV = testCaseDict[argInfo['name']]
        else:
            assert 'default' in argInfo.keys(),f'{clsName} Arg without default {argInfo["name"]}'
            newV = argInfo['default']
        if newV not in argInfo['valueSpace']:
            ParamInfoDict['ParamList'][clsName][i]['valueSpace'].append(newV)
 
def ListTC2tupleTC(listTC,argInfoList):
    newTC = []
    for arg in argInfoList:
        found = False
        v = None
        for a in listTC:
            if a[0] == arg['name']:
                v = a[1]
                found = True
                break
        if not found:
            v = arg['default']
        newTC.append(v)
    return tuple(newTC)
     
if __name__ == '__main__':
    from executionUtils import executewithBackends,BACKENDS,executeTupleWithBackends
    import dill
    collectedSeeds = dill.load(open('../rawTC.pickle','rb'))
    initTestCases = {}
    allResult = {}
    ParamInfoDict = {'ParamList':{},'keyParams':{},'freeParams':{}}
    for clsName in collectedSeeds.keys():
        if 'EinsumDense' in clsName:
            continue
        
        #initailize ParamTable
        argDict = dill.load(open(f'../argDir/{clsName}','rb'))
        for key in ParamInfoDict.keys():
            ParamInfoDict[key][clsName] = []
        InitArgList(ParamInfoDict,clsName,argDict['__init__'],'init')
        InitArgList(ParamInfoDict,clsName,argDict['call'],'call')
        
        if 'EinsumDense' in clsName:
            continue
        #filter testCases
        allResult[clsName] = {}
        initTestCases[clsName] = []
        cnt = 0
        for rec in collectedSeeds[clsName]:
            cnt += 1
            #print(cnt,'/',len(collectedSeeds[clsName]))
            res,Res = executewithBackends(clsName,rec,BACKENDS)
            if res == 'Crash':
                pass
            else:
                extractValue(ParamInfoDict,clsName,rec)
                newTestCase = ListTC2tupleTC(rec,ParamInfoDict['ParamList'][clsName]) 
                initTestCases[clsName].append(newTestCase)    
                allResult[clsName][newTestCase]=(Res,res)
        missedV = []
        cnt = 0
        for i,arg in enumerate(argDict['__init__']):
            if arg['name'] == 'name':
                continue
            for v in arg['valueSpace']:
                if v not in ParamInfoDict['ParamList'][clsName][cnt]['valueSpace'] and (cnt,v) not in missedV:
                    missedV.append((cnt,v))
            cnt += 1
        for i,arg in enumerate(argDict['call']):
            if arg['name'] == 'name':
                continue
            for v in arg['valueSpace']:
                if v not in ParamInfoDict['ParamList'][clsName][cnt]['valueSpace']and (cnt,v) not in missedV:
                    missedV.append((cnt,v))
            cnt += 1
        for index,v in missedV:
            if v in ParamInfoDict['ParamList'][clsName][index]['valueSpace']:
                continue
            success=False
            for seed in initTestCases[clsName]:
                newTC=list(seed)
                newTC[index] = v
                newTC=tuple(newTC)
                res,Res = executeTupleWithBackends(clsName,newTC,BACKENDS)
                if isinstance(Res['tensorflow'][1],list) or isinstance(Res['torch'][1],list) or isinstance(Res['torch'][1],list):
                    initTestCases[clsName].append(newTC)
                    ParamInfoDict['ParamList'][clsName][index]['valueSpace'].append(v)
                    allResult[clsName][newTC] = (Res,res)
                    success = True
                    break

                
    dill.dump(ParamInfoDict,open('../paramInfo.pickle','wb'))
    dill.dump(initTestCases,open('../seedpool.pickle','wb'))
    dill.dump(allResult,open('../allRes.pickle','wb'))