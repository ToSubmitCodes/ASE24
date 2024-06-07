
import os,dill
from pathlib import Path
from multiprocessing import Process 
from executionUtils import WORKER_NUM,BACKENDS

def executeWithBackend(backend,id):
    os.environ['KERAS_BACKEND'] = backend
    from testCasesUtils import execute
    stopflag = f'../workSpace/{id}/flags/stopFlag'
    inputFlag = f'../workSpace/{id}/flags/start_{backend}'
    outputFlag = Path(f'../workSpace/{id}/flags/done_{backend}')
    inputFile = f'../workSpace/{id}/inputs/{backend}'
    outputFile = f'../workSpace/{id}/outputs/{backend}'
    for fileName in [stopflag,inputFlag,inputFile,outputFile,outputFlag,f'../workSpace/{id}/running']:
        if os.path.exists(fileName):
            os.remove(fileName)
    while(True):
        if os.path.exists(stopflag):
            break
        if os.path.exists(inputFlag):
            clsName,argDict = dill.load(open(inputFile,'rb'))
            os.remove(inputFile)
            while (True):
                try:
                    os.remove(inputFlag)
                    break
                except Exception as e:
                    #print(str(e))
                    pass
            res = execute(clsName,argDict)
            dill.dump(res,open(outputFile,'wb'))
            outputFlag.touch()
    return 

if __name__ == '__main__':
    
    
    processes =[]
    for backend in BACKENDS:
        for workerId in range(WORKER_NUM):
            p = Process(target=executeWithBackend,args=(backend,workerId,))
            p.start()
            processes.append(p)







