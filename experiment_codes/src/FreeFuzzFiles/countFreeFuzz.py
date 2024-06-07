import os,json
import re
import difflib
def string_similar(s1,s2):
    return difflib.SequenceMatcher(None,s1,s2).quick_ratio()

rootDir = 'freefuzzResult'
buggyOps = []
for fault in os.listdir('../SimpleFaults'):
    buggyOps.append(fault)

allFail = [0]
crashedRec = [0]
bugRec = [0]
for fileName in os.listdir(rootDir):
    bugList = []
    msgList = []
    op = fileName.split('.')[-1]
    op = op.split('_')[0]
    if op not in buggyOps:
        continue
    res = json.load(open(os.path.join(rootDir,fileName)))
    for rec in res:
        if rec == None:
            crashedRec.append(crashedRec[-1])
            allFail.append(allFail[-1])
        else:
            allFail.append(allFail[-1]+1)
            if 'Received' in rec:
                msg = rec.split('Received')[0]
            elif '\n' in rec:
                if rec.startswith('Error:Exception encountered when calling'):
                    msg = rec.split('\n')[2]
                else:
                    msg = rec.split('\n')[0]
                if  '{{' in msg:
                    msg = rec.split('}}')[1]
                msg = msg.split(':')[0]
                if 'Arguments receive' in msg:
                    msg = rec.split('Arguments receive')[0]
            else:
                msg = rec.split('. ')[0]
                msg = re.sub(r'[\"\'].*[\"\']', 'v',msg)
            msg = re.sub(r'\d+', 'v',msg)
            new = True
            for history in msgList:
                if string_similar(history,msg) > 0.8:
                    new=False
                    break
            if new:
                msgList.append(msg)
                print(msg)
                crashedRec.append(crashedRec[-1])
            else:
                crashedRec.append(crashedRec[-1]+1)
        if rec  != None and 'Catch a bug' in rec:
            searchResult = re.search('Catch a bug (\d+)',rec)
            bugID = searchResult.group(1)
            bugID = int(bugID)
            if bugID not in bugList:
                bugList.append(bugID)
                bugRec.append(bugRec[-1]+1)
            else:
                bugRec.append(bugRec[-1])
        else:
            bugRec.append(bugRec[-1])
resDict={'bug':bugRec,'duplicated':crashedRec,'allFail':allFail}
json.dump(resDict,open('fuzzRes.json','w'),indent=4)
