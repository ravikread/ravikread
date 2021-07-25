import copy
import re
import logging
import sys

logging_level = logging.DEBUG

class Graph:
    def __init__(self, outFileName = None, linkOutFileName = None, link3OutFileName = None):
        self.adj = {}
        self.path = []
        self.outFileName = outFileName
        self.outFile = None
        self.srcNode = None
        self.dstNode = None
        self.diversedPath = None
        self.linkInPath = None
        self.linkOutFile = None
        self.link3OutFile = None
        self.linkList = []
        logging.basicConfig(stream=sys.stderr, level=logging_level)

        if outFileName is not None:
            self.outFile = open(outFileName, 'w')

        if linkOutFileName is not None:
            self.linkOutFile = open(linkOutFile, 'w')

        if link3OutFileName is not None:
            self.link3OutFile = open(link3OutFile, 'w')


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


    def addLink(self, srcNode, dstNode, link):
        if link is not self.linkList:
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

    def printAllPath(self):
        uniqList = []
        self.unifyPath()

        i = 0
        for s_path in self.path:
            self.printOnePath(self.srcNode, self.dstNode, i, s_path)
            i = i + 1

        logging.debug("total path: %s unique path: %s ", len(self.path), len(uniqList))

        '''uniqList = []

        self.path.sort(key = len)
        i = 0
        for s_path in self.path:
            s_path.reverse()
            tmpList = copy.deepcopy(s_path)
            tmpList.sort()
            if tmpList in uniqList:
                print("duplicate ", s_path)
                continue

            uniqList.append(tmpList)
            self.printOnePath(self.srcNode, self.dstNode, i, s_path)
            i = i + 1

        print("total path: ", len(self.path), "unique path: ", len(uniqList))'''

    def printOnePath(self, srcNode, dstNode, seqNo, path):
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

        if self.outFile is not None:
            self.outFile.write(line + "\n")
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
            self.printOnePath(self.srcNode, self.dstNode, i, s_path)
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
                nodePairs.append((nodeList[i], nodeList[j]))
        return nodePairs

    def findAllPathBtAllNodes(self):
        nodePair = self.getNodeList()
        print(nodePair)
        for pair in nodePair:
            logging.debug("find path for %s", pair)
            self.findAllPath(pair[0], pair[1])
        

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
    g = Graph(outFileName = "outfile.csv")
    #g = Graph(outFileName = None)
    g.buildGraphFromFile("network")
    #g.findAllPath("N1", "N2")
    g.findAllPathBtAllNodes()

if __name__ == '__main__':
    #testGraph()
    print("Test result from file")
    testGraph1()
