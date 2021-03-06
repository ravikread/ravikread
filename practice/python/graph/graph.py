import copy
import re
import logging
import sys

logging_level = logging.INFO
#logging_level = logging.DEBUG

class linkCmp:
    def __init__(self, obj, *args):
        self.obj = obj

    def __lt__(self, other):
        return linkSortCmp1(self.obj, other.obj) < 0

    def __gt__(self, other):
        return linkSortCmp1(self.obj, other.obj) > 0

    def __eq__(self, other):
        return linkSortCmp1(self.obj, other.obj) == 0

    def __le__(self, other):
        return linkSortCmp1(self.obj, other.obj) <= 0

    def __ge__(self, other):
        return linkSortCmp1(self.obj, other.obj) >= 0

    def __ne__(self, other):
        return linkSortCmp1(self.obj, other.obj) != 0

def linkSortCmp(new, old):
    newNum = int(new[1:])
    oldNum = int(old[1:])
    return newNum - oldNum

def strToLinkList(string):
    token = []
    if isinstance(string, str):
        token = re.findall('[0-9]+', string)
    elif isinstance(string, tuple):
        token = re.findall('[0-9]+', string[0])
        token = token + re.findall('[0-9]+', string[1])
    else:
        token = string
    return token


def linkSortCmp1(new, old):
    n_link = strToLinkList(new)
    o_link = strToLinkList(old)

    if len(n_link) > len(o_link):
        return 1
    if len(o_link) > len(n_link):
        return -1

    min_len = min(len(n_link), len(o_link))
    for i in range(min_len):
        ret = int(n_link[i]) - int(o_link[i])
        if ret != 0:
           return ret 

    return 0


class Graph:
    def __init__(self, outFileName = None, currPathName = None, linkOutFileName = None, link3OutFileName = None):
        self.adj = {}
        self.path = []
        self.outFileName = outFileName
        self.outFileNameV2 = "pathList_v2.csv"
        self.linkOutFileName = linkOutFileName
        self.summarizedFileName = "merge_path_xcno.csv"
        self.summarizedFileNameV2 = "merge_path_xcno_v2.csv"
        self.outFile = None
        self.srcNode = None
        self.dstNode = None
        self.diversedPath = None
        self.linkInPath = {}
        self.linkOutFile = None
        self.currPathFile = None
        self.link3OutFile = None
        self.linkList = []
        self.linkTableHdrWrite = False
        logging.basicConfig(stream=sys.stderr, level=logging_level)

        if outFileName is not None:
            self.outFile = open(outFileName, 'w')

        if currPathName is not None:
            self.currPathFile = open(currPathName, 'w')

        if linkOutFileName is not None:
            self.linkOutFile = open(linkOutFileName, 'w')

        if link3OutFileName is not None:
            self.link3OutFile = open(link3OutFileName, 'w')


    def __del__(self):
        if self.outFile is not None:
            self.outFile.close()

    def parseNode(self, line):
        #tuple of 3 token srcNdoe, dstNode, link is expected. validation node done, tail is ignored if partial
        token = line.split(",")
        j = 0
        for i in range(len(token)/3):
            self.addLink(token[j].strip(), token[j + 1].strip(), token[j + 2].strip())
            j = j + 3


    def buildGraphFromFile(self, path):
        with open(path) as inFile:
            for line in inFile:
                self.parseNode(line.strip("\n"))

        self.linkList.sort(key=linkCmp)
        print("........ linkList", self.linkList)


    def addLink(self, srcNode, dstNode, link):
        if link not in self.linkList:
            self.linkList.append(link)

        if srcNode in self.adj:
            self.adj[srcNode][dstNode] = link
        else:
            self.adj[srcNode] = {}
            self.adj[srcNode][dstNode] = link

        if dstNode in self.adj:
            self.adj[dstNode][srcNode] = link
        else:
            self.adj[dstNode] = {}
            self.adj[dstNode][srcNode] = link
 
    def findPath(self, srcNode, dstNode, visitedNode):
        retList = []
        if srcNode in visitedNode:
            return None

        if srcNode == dstNode:
            self.path.append([])
            return [len(self.path) - 1]

        for tmpNode in self.adj[srcNode]:
            visitedNode.append(srcNode)
            ret = self.findPath(tmpNode, dstNode, visitedNode)
            visitedNode.pop()
            if ret is not None:
                retList = retList + ret
                for i in ret:
                    self.path[i].append(self.adj[srcNode][tmpNode])

        return retList

    def findAllPath(self, srcNode, dstNode):
        logging.debug("nodes: %s", self.adj)
        visitedNode = []
        self.path = []
        self.srcNode = srcNode
        self.dstNode = dstNode
        self.findPath(srcNode, dstNode, visitedNode)
        self.printAllPath()

    def buildLinkAndPathTable(self):
        self.linkInPath = {}

        t_link = len(self.linkList)

        #with Single link 
        for i in range(t_link):
            link = self.linkList[i:i+1]
            key = str(link)
            self.linkInPath[key] = []
            self.linkInPath[key].append(link)

        #with two link
        for i in range(t_link - 1):
            for j in range(i + 1, t_link):
                link = self.linkList[i:i+1] + self.linkList[j:j+1]
                #link = copy.deepcopy(link)
                link.sort(key=linkCmp)
                key = str(link)
                self.linkInPath[key] = []
                self.linkInPath[key].append(link)

        #set link path status to 0 by default
        for key in self.linkInPath.keys():
            self.linkInPath[key] = self.linkInPath[key] + [1] * len(self.path)

        logging.debug("Path Table %s, %s", len(self.linkInPath.keys()), self.linkInPath.keys())

        for i in range(len(self.path)):
            path = self.path[i]
            for key in self.linkInPath.keys():
                for link in self.linkInPath[key][0]:
                    if link in path:
                        self.linkInPath[key][i+1] = 0
                        break

    def writeToFile(self, fileHandle, rStr):
        if fileHandle is not None:
            fileHandle.write(rStr)

    def printLinkTableHdr(self):
        if self.linkTableHdrWrite is False:
            keys = self.linkInPath.keys()
            keys.sort(key=linkCmp)
            for i in range(len(self.linkList)):
                line = ""
                doWrite = False
                j = 0
                for key in keys:
                    if i < len(self.linkInPath[key][0]):
                        line = line + self.linkInPath[key][0][i] + ","
                        doWrite = True
                    else:
                        line = line + ","
                    j = j + 1

                if doWrite == False:
                    line = ""
                line = line + "\n"
                self.writeToFile(self.linkOutFile, line)
                self.writeToFile(self.link3OutFile, line)

                if doWrite == False:
                    break

        self.linkTableHdrWrite = True

    def printLinkTableData(self):
        keys = self.linkInPath.keys()
        keys.sort(key=linkCmp)
        for i in range(len(self.path)):
            line = ""
            for key in keys:
                line = line + str(self.linkInPath[key][1 + i]) + ","

            line = line + "\n"
            self.writeToFile(self.linkOutFile, line)
            if i <= 2:
                self.writeToFile(self.link3OutFile, line)




    def printLinkTable(self):
        if self.linkOutFile is None and self.link3OutFile is None:
            return

        self.printLinkTableHdr()
        self.printLinkTableData()
        


    def printAllPath(self):
        uniqList = []

        #uniqfy path
        self.unifyPath()

        # build link and path table
        self.buildLinkAndPathTable()
        self.printLinkTable()
        
        i = 0
        for s_path in self.path:
            self.printOnePath(self.srcNode, self.dstNode, i, s_path, self.outFile)
            i = i + 1

        logging.debug("total path: %s unique path: %s ", len(self.path), len(uniqList))

    def printOnePath(self, srcNode, dstNode, seqNo, path, fileHandle):
        line = ""
        if seqNo == 0:
            line = srcNode + "," + dstNode + "," + "W"
        if seqNo == 1:
            line = srcNode + "," + dstNode + "," + "P"
        if seqNo > 1:
            if self.diversedPath == True:
                line = srcNode + "," + dstNode + "," + "R" + str(seqNo - 1)
            else:
                line = srcNode + "," + dstNode + "," + "NR" + str(seqNo - 1)

        for link in path:
            line = line + "," + link

        if fileHandle is not None:
            fileHandle.write(line + "\n")
        else:
            print(line)

    def unifyPath(self):
        uniqList = []
        priorityPathList = []

        # sort path based on link
        self.path.sort(key = len)
        
        # remove duplicate paths
        i = 0
        for s_path in self.path:
            s_path.reverse()
            tmpList = copy.deepcopy(s_path)
            tmpList.sort()
            if tmpList in uniqList:
                logging.debug("duplicate %s", s_path)
                continue

            uniqList.append(tmpList)
            priorityPathList.append(s_path)
            i = i + 1
    
        self.path = priorityPathList
        usedPath = []
        priorityPathList = []
        #First three path are with unique link
        i = 0
        j = 0
        for s_path in self.path:
            ret = self.isDiversedPath(s_path, priorityPathList)
            if ret == True:
                priorityPathList.append(s_path)
                usedPath.append(j)
                i = i + 1

            if (i == 3):
                break

            j = j + 1

        # check if first three path are diversed
        if i is not 3:
            self.diversedPath = False
        else:
            self.diversedPath = True

        #append remaining path
        for i in range(len(self.path)):
            if i in usedPath:
                continue

            priorityPathList.append(self.path[i])


        self.path = priorityPathList
 
    def isDiversedPath(self, n_path, pathList):
        for tmpPath in pathList:
            for link in n_path:
                if link in tmpPath:
                    return False

        return True

    def printAllPathToFile(self):
        uniqList = []
        self.unifyPath()

        i = 0
        for s_path in self.path:
            self.printOnePath(self.srcNode, self.dstNode, i, s_path, self.outFile)
            i = i + 1

        logging.debug("total path: %s unique path: %s ", len(self.path), len(uniqList))

    def getNodeList(self, nodeName):
        nodeList = []
        nodePairs = []
        with open(nodeName) as inFile:
            for line in inFile:
                nodeList = nodeList + re.split('\n,', line)
        
        totalNode = len(nodeList)
        for i in range(0, totalNode):
            for j in range(i + 1, totalNode):
                nodePairs.append((nodeList[i], nodeList[j]))

        return nodePairs

    def getNodeList(self):
        # should be called after buildgraph is done
        nodeList = []
        nodePairs = []
        
        for node in self.adj.keys():
            nodeList.append(node)
        
        totalNode = len(nodeList)
        for i in range(0, totalNode):
            for j in range(i + 1, totalNode):
                i_num = re.findall('[0-9]+', nodeList[i])
                j_num = re.findall('[0-9]+', nodeList[j])
                if int(i_num[0]) > int(j_num[0]):
                    nodePairs.append((nodeList[j], nodeList[i]))
                else:
                    nodePairs.append((nodeList[i], nodeList[j]))

        nodePairs.sort(key=linkCmp)
        return nodePairs

    def removeLinkPrefix(self, srcFile, dstFile):
        outFileSrc = file(srcFile, "r")
        outFileDst = file(dstFile, "w")

        lines = outFileSrc.readlines()

        for line in lines:
            outFileDst.write(line.replace("L", ""))

        outFileSrc.close()
        outFileDst.close()
 
    def mergeFile(self, srcFileWHdr, srcFile, dstFile):
        srcFileWHdr = file(srcFileWHdr, "r")
        srcFile = file(srcFile, "r")
        dstFile = file(dstFile, "w")
        sep = ","

        # both file should have same number of lines except hdr part
        linesW = srcFileWHdr.readlines()
        lines = srcFile.readlines()

        max_column = 0
        for line in lines:
            if max_column < line.count(','):
                max_column = line.count(',')
        i = 0
        max_column = max_column + 1 
        for i in range(len(linesW)):
            sLine = linesW[i]
            dstLine = "," * max_column + sep + sLine
            #end of header
            if sLine == "\n":
                dstFile.write("\n")
                print("..... got hdr break")
                break
            dstFile.write(dstLine)
        i = i + 1


        if len(lines) != len(linesW) - i:
            print("....... : ", len(lines), len(linesW), i)
            #raise("Files are not same length")
        #merge files line by line
        for j in range(len(lines)):
            dstLine = lines[j][:-1] + "," * (max_column - lines[j].count(','))  + sep + linesW[i]
            dstFile.write(dstLine)
            i = i + 1
            
        srcFile.close()
        dstFile.close()
        srcFileWHdr.close()
 
    def finalizeOutPut(self):
        #close file and create V2 file
        if self.outFile is not None:
            self.outFile.close()

        if self.linkOutFile is not None:
            self.linkOutFile.close()

        self.removeLinkPrefix(self.outFileName, self.outFileNameV2)
        self.mergeFile(self.linkOutFileName, self.outFileName, self.summarizedFileName)
        self.mergeFile(self.linkOutFileName, self.outFileNameV2, self.summarizedFileNameV2)
       

    def findAllPathBtAllNodes(self):
        nodePair = self.getNodeList()
        logging.info("search path: %s", nodePair)
        logging.info("linkLsit: %s", self.linkList)
        for pair in nodePair:
            logging.debug("find path for %s", pair)
            self.findAllPath(pair[0], pair[1])
        self.finalizeOutPut()

def testGraph():
    g = Graph()
    g.addLink("N1", "N2", "L1")
    g.addLink("N2", "N3", "L2")
    g.addLink("N3", "N4", "L3")
    g.addLink("N4", "N1", "L4")
    g.addLink("N1", "N5", "L5")
    g.addLink("N2", "N5", "L6")
    g.addLink("N3", "N5", "L7")
    g.addLink("N4", "N5", "L8")

    g.findAllPath("N1", "N2")

def testGraph1():
    g = Graph(outFileName = "pathList_v1.csv", currPathName = "currPath.csv", linkOutFileName = "xcno.csv")
    #g = Graph(outFileName = None)
    g.buildGraphFromFile("network")
    #g.findAllPath("N1", "N2")
    g.findAllPathBtAllNodes()

if __name__ == '__main__':
    #testGraph()
    print("Test result from file")
    testGraph1()
