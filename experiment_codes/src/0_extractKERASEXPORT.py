import ast,json
from utils import getAllFilePathes

if __name__ == '__main__':
    rootDir='../data/keras-3.1.0'
    fileList = getAllFilePathes(rootDir)
    globalNameRecord = {}
    for fileName in fileList:
        a=ast.parse(open(fileName,encoding='utf-8').read())
        for stmt in a.body:
            if not (isinstance(stmt,ast.ClassDef) and len(stmt.decorator_list) > 0):
                continue
            for callstmt in stmt.decorator_list:
                if callstmt.func.id == 'keras_export':
                    for arg in callstmt.args:
                        if isinstance(arg,ast.Constant):
                            fullName = arg.value
                            assert '.' in fullName,f'{stmt.name} has an decorator {fullName} in file {fileName}'
                            globalNameRecord[fullName] = fileName
                        elif isinstance(arg,ast.List):
                            for e in arg.elts:
                                fullName = e.value
                                assert '.' in fullName,f'{stmt.name} has an decorator {fullName} in file {fileName}'
                                globalNameRecord[fullName] = fileName
    json.dump(globalNameRecord,open('../data/globalNameRecord.json','w'),indent=4)
                                