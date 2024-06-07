import requests
from bs4 import BeautifulSoup
from bs4.element import Tag,NavigableString
import json

def getInputOutput():
    pass


urlPrefix='https://keras.io'
rootRoutine='/api'
outFile='../data/APIList.json'
r = requests.get(urlPrefix+rootRoutine)
soup = BeautifulSoup(r.text, 'html.parser')
flag=False
allLayers = []
for i in soup.find(id='layers-api').parent.children:
    if isinstance(i,Tag) and 'id' in i.attrs.keys() and i['id'] == 'callbacks-api':
            flag=False
    if flag and isinstance(i,Tag):
        for li in i.find_all('a'):
            name=li.text
            if name.endswith('layers'):
                newRoutine=li['href']
                newPage = requests.get(urlPrefix+newRoutine)
                newSoup = BeautifulSoup(newPage.text,'html.parser')
                for a in newSoup.find_all('li'):
                    aName = a.text
                    if aName.endswith('layer'):
                        allLayers.append(aName)
    if isinstance(i,Tag) and 'id' in i.attrs.keys() and i['id'] == 'layers-api':
            flag=True
json.dump(allLayers,open(outFile,'w'),indent=9)   
    