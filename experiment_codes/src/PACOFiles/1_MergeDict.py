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

if __name__ == '__main__':
    import dill
    collectedSeeds = dill.load(open('../rawTC.pickle','rb'))
    initTestCases = {}
    allResult = {}
    ParamInfoDict = {'ParamList':{},'keyParams':{},'freeParams':{}}
    for clsName in collectedSeeds.keys():
        if 'EinsumDense' in clsName:
            continue
        #print(clsName)
        
        #initailize ParamTable
        argDict = dill.load(open(f'../argDir/{clsName}','rb'))
        for key in ParamInfoDict.keys():
            ParamInfoDict[key][clsName] = []
        InitArgList(ParamInfoDict,clsName,argDict['__init__'],'init')
        InitArgList(ParamInfoDict,clsName,argDict['call'],'call')
        
    dill.dump(ParamInfoDict,open('../paramInfo.pickle','wb'))