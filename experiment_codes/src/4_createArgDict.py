import dill as pickle
import os 
import shutil

if __name__ == '__main__':
    inFile='../data/funcDefwithArgList.pickle'
    outDir='../data/argDir'

    if os.path.exists(outDir):
        shutil.rmtree(outDir)
    os.mkdir(outDir)
    arglist = pickle.load(open(inFile,'rb'))
    argDict = {}
    for c in arglist:
        outFile = outDir+'/'+ c['name']
        pickle.dump(c['funcArgList'],open(outFile,'wb'))