from typing import Callable, Dict, List, Tuple

from hexBoy.hex.board.HexBoard import Board, HexBoard
from hexBoy.hex.game.HexGameRules import HexGameRules, HexPlayerInfo
from hexBoy.pathfinder.PathBoy import PathBoy
from hexBoy.hex.node.HexNode import Hex, HexNode
from hexBoy.models.SortedDict import SortedDict

class NumPathFinder(PathBoy):

    # TODO remove from pathboy. A* ruins the num path algorithm
    _playerInfo: HexPlayerInfo

    def __init__(
        self,
        board: Board,
        player: int
    ):
        PathBoy.__init__(self, 
            board,
            checkIfBarrier=HexGameRules.getCheckIfBarrierFunc(player),
            heuristicFunc=HexGameRules.getHeuristicFunc(player)
        )

        self._playerInfo = HexGameRules.getPlayerInfo(player)

    def initEmptyBoard(self) -> None:

        board = self._board

        # Init all the nodes with their costs and family
        nodes: Dict[Hex, HexNode] = board.getNodeDict()
        adjacentSpaces: List[Hex] = None
        nextNode: Hex = None

        # sort by heur. go row by row 
        def sortFunc(item: Tuple[HexNode, HexNode]) -> int:
            return self._heuristicFunc(item[1], None)

        openNodes: SortedDict = SortedDict(getSortValue=sortFunc, reverse=True)
        closedNodes: SortedDict = SortedDict()

        currentNode: HexNode = self._playerInfo.start
        openNodes[currentNode] = nodes[currentNode]

        def _scoreNode(X: HexNode) -> None:
            """Score PCD and set initial family"""
            if (X.getHexType().xType == 1):
                h = self._heuristicFunc(X, None)
                X.setPath(11 - h)
                X.setDist(h - 1)
                X.setHeur(h - 1)

                # Set dads/sons 
                for aX in board.getAdjacentSpaces(X): # Sometimes using board sometimes self._board
                    adjX = nodes[aX]
                    # Playable Board
                    if (adjX.getHexType().xType == 1): 
                        if (self._heuristicFunc(adjX, None) < self._heuristicFunc(X, None)):
                            X.addSon(adjX)

                        elif (self._heuristicFunc(adjX, None) > self._heuristicFunc(X, None)):
                            X.addDad(adjX)
                    
                    # Player Edge
                    elif (adjX.getHexType().player == self._playerInfo.player 
                        and(X[0] == adjX[0] or X[1] == adjX[1])
                    ): # Player edge Hex in same row or col
                        if (self._heuristicFunc(adjX, None) < self._heuristicFunc(X, None)):
                            X.setSon(adjX) # only have one son to the edge
                            adjX.setDad(X)

                        elif (self._heuristicFunc(adjX, None) > self._heuristicFunc(X, None)):
                            X.setDad(adjX) # only have one dad from the edge
                            adjX.setSon(X)

            if (len(X.getDads()) == 0):
                # Edges with no dads have 1 path
                X.setPathsToNode(1)

            else:
                num = 0
                for dad in X.getDads():
                    num += dad.getPathsToNode()
                X.setPathsToNode(num)
            

        while (len(openNodes) != 0):
            currentNode = openNodes.pop()
            closedNodes[currentNode] = None
            _scoreNode(currentNode)
            
            adjacentSpaces = self._board.getAdjacentSpaces(currentNode)            
            for nextPos in adjacentSpaces:
                nextNode = nodes[nextPos]

                if not self._checkIfBarrier(nextNode) and not closedNodes.hasKey(nextPos) and not openNodes.hasKey(nextPos):
                    nodes[nextNode] = nextNode
                    openNodes[nextNode] = nextNode


        # Go backward
        openNodes = SortedDict(getSortValue=sortFunc)
        closedNodes = SortedDict()

        currentNode = self._playerInfo.end
        openNodes[currentNode] = nodes[currentNode]

        def _setPathsFrom(X: HexNode) -> None:
            # TODO
            if (len(X.getSons()) == 0):
                # Edges with no dads have 1 path
                X.setPathsFromNode(1)

            else:
                num = 0
                for son in X.getSons():
                    num += son.getPathsFromNode()
                X.setPathsFromNode(num)

        while (len(openNodes) != 0):
            currentNode = openNodes.pop()
            closedNodes[currentNode] = None
            _setPathsFrom(currentNode)

            adjacentSpaces = self._board.getAdjacentSpaces(currentNode)            
            for nextPos in adjacentSpaces:
                nextNode = nodes[nextPos]

                if not self._checkIfBarrier(nextNode) and not closedNodes.hasKey(nextPos) and not openNodes.hasKey(nextPos):
                    openNodes[nextNode] = nextNode
        

    def updateMove(self, player: int, move: Hex) -> None:
        """Update board with the new move"""


        nodes = self._board.getNodeDict()
        X: HexNode = nodes[move]

        if (player != self._playerInfo.player):
            for s in X.getSons():
                s.delDad(X)

            for d in X.getDads():
                d.delSon(X)


        def _sortFunc(item: Tuple[HexNode, int]) -> int:
            return item[1]

        # Helper functions

        def _updateSon(X: HexNode) -> None:
            """Update node's dads, path, and paths to node"""

            if (X.getHexType().xType == 2): # Edge
                return

            dads: List[HexNode] = X.getDads()

            if (len(dads) == 0): 
                # Get new dads
                bestDadPC = -1
                adjHexes = self._board.getAdjacentSpaces(X)
                for aX in adjHexes:
                    adjX = nodes[aX]

                    if (not self._checkIfBarrier(adjX)): # and (adjX.getPC() < bestDadPC or bestDadPC == -1)):
                        bestDadPC = adjX.getPC()

                for aX in adjHexes:
                    adjX = nodes[aX]
                    if (adjX.getPC()== bestDadPC):
                        X.addDad(adjX) #TODO I'm pretty sure I have to add a son to aX
                        dads.append(adjX)

            # Get best dad
            bestPC = -1
            for d in dads:
                if (d.getPC() < bestPC or bestPC == -1):
                    bestPC = d.getPC()

            # Get pathsTo from dads
            badDads = []
            pathsToNode = 0
            for d in dads:
                if (d.getPC() == bestPC):
                    pathsToNode += d.getPathsToNode()
                else:
                    badDads.append(d)

            # remove dads with worst path+cost
            for bd in badDads:
                X.delDad(bd)

            # Update node and nodes
            X.setPathsToNode(pathsToNode)
            X.setPath(X.getDad().getPC())
            nodes[X] = X

        def _updateDad(X: HexNode) -> None:
            """Update node's sons, dist and paths from node"""

            if (X.getHexType().xType == 2): # Edge
                return

            sons: List[HexNode] = X.getSons()

            if (len(sons) == 0): 
                # Get new sons
                bestSonCD = -1
                for aX in self._board.getAdjacentSpaces(X):
                    adjX = nodes[aX]
                    if (self._checkIfBarrier(aX) and (adjX.getCD() < bestSonCD or bestSonCD == -1)):
                        bestSonCD = adjX.getCD()

                for aX in self._board.getAdjacentSpaces(X):
                    adjX = nodes[aX]
                    if (adjX.getCD()== bestSonCD):
                        X.addSon(adjX) #TODO I'm pretty sure I have to add a son to aX
            
            # Get best son
            bestCD = -1
            for s in sons:
                if (s.getCD() < bestCD or bestCD == -1):
                    bestCD = s.getCD()
            
            # Get pathsFrom from sons
            badSons = []
            pathsFromNode = 0
            for s in sons:
                if (s.getCD() == bestCD):
                    pathsFromNode += s.getPathsFromNode()
                else:
                    badSons.append(s)

            # remove sons with worst cost+dist
            for bs in badSons:
                X.delSon(bs)

            # Update node and nodes
            X.setPathsFromNode(pathsFromNode)
            X.setDist(X.getSon().getCD())
            nodes[X] = X

        # Update sons first
        openNodes = SortedDict(getSortValue=_sortFunc)
        closedNodes = SortedDict()

        for son in X.getSons():
            openNodes[son] = 1

        while (len(openNodes) != 0):
            currentNode, depth = openNodes.popItem()
            closedNodes[currentNode] = None
            _updateSon(currentNode)

            for son in currentNode.getSons():
                if (not openNodes.hasKey(son) and not closedNodes.hasKey(son)):
                    openNodes[son] = depth + 1

        # Then update dads
        openNodes = SortedDict(getSortValue=_sortFunc)
        closedNodes = SortedDict()

        for dad in X.getDads():
            openNodes[dad] = 1

        while (len(openNodes) != 0):
            currentNode, depth = openNodes.popItem()
            closedNodes[currentNode] = None

            _updateDad(currentNode)

            for dad in currentNode.getDads():
                if (not openNodes.hasKey(dad) and not closedNodes.hasKey(dad)):
                    openNodes[dad] = depth + 1





            

    def getNumPaths(self) -> int:
        """Get the total number of paths that have the best cost"""
        bestBest: int = -1
        numPaths: int = 0

        nodes: Dict[Hex, HexNode] = self._board.getNodeDict()
        openNodes = SortedDict()
        closedNodes = SortedDict()

        currentNode = self._playerInfo.end
        openNodes[currentNode] = nodes[currentNode]

        while (len(openNodes) != 0):
            currentNode: HexNode = openNodes.pop()
            closedNodes[currentNode] = None

            if (currentNode.getDad().getBest() < bestBest or bestBest == -1):
                bestBest = currentNode.getDad().getBest()

            adjacentSpaces = self._board.getAdjacentSpaces(currentNode)            
            for nextPos in adjacentSpaces:
                nextNode = nodes[nextPos]

                if (not self._checkIfBarrier(nextNode) and not closedNodes.hasKey(nextPos) and not openNodes.hasKey(nextPos)
                    and nextNode.getHexType().xType == 2
                ):
                    openNodes[nextNode] = nextNode

        print()
        for X in closedNodes.getKeys():
            dad: HexNode = X.getDad()
            print(dad, dad.getBest(), dad.getPathsToNode())
            if (dad.getBest() == bestBest):
                numPaths += dad.getPathsToNode()

        return numPaths

    def getNumPathsToHex(self, X: Hex) -> int:
        """Get the number of paths to a given hex"""

        node: HexNode = self._board.getNodeDict()[X]
        return node.getPathsToNode()

    def getNumPathsFromHex(self, X: Hex) -> int:
        """Get the number of paths from a given Hex"""

        node: HexNode = self._board.getNodeDict()[X]
        return node.getPathsFromNode()

"""
    '''---
    Best paths
    ---'''
    def old_numBestPaths(self, nodes, startPos, endPos, checkIfBarrier):
        nodes = self._board.getNodeDict(),
        spaces = HexNode.SpaceTypes
        numPaths = SortedDict()

        winPath = self._AStar(startPos, endPos)
        bestCost = self.scorePath(winPath)

        openNodes = SortedDict(getSortValue=self.getSortValue)
        closedNodes = SortedDict()
        endNodes = SortedDict()  # nodes to add up to get the number of paths

        # add starting position to pop off
        currentPos = startPos # maybe rename Pos to Hex
        currentNode = nodes[currentPos]
        currentNode.setExtraPathsToNode(0.25)
        openNodes[currentPos] = currentNode

        adjacentSpaces = None
        nextNode = None
        closedNode = None

        # helper functions
        def setNodeInOpenNodes(pos):
            nextNode.scoreHeuristic(currentPos, currentNode.getPC(), endPos)
            nonlocal numPaths

            # check if this pos is on the winning edge and moving from a non edge
            # to an end edge
            if (
                (nextNode.type == spaces.BLUE_EDGE or nextNode.type == spaces.RED_EDGE)
                and (
                    currentNode.type != spaces.BLUE_EDGE
                    or currentNode.type != spaces.RED_EDGE
                )
                and nextNode.getPC() == bestCost
            ):
                # node is an edge and has the best cost -> is a winning path
                # add paths to the total paths
                if currentNode.extraPathsToThisNode != 0:
                    numPaths[currentPos] = currentNode.extraPathsToThisNode

            # moving from start edge to playable board
            elif (
                nextNode.type != spaces.BLUE_EDGE or nextNode.type != spaces.RED_EDGE
            ) and (
                currentNode.type == spaces.BLUE_EDGE
                or currentNode.type == spaces.RED_EDGE
            ):
                nextNode.setExtraPathsToNode(1)

            else:
                nextNode.setExtraPathsToNode(currentNode.extraPathsToThisNode)

            nodes[pos] = nextNode
            openNodes[pos] = nextNode

        def updateNodeInOpenNodes(pos):
            nonlocal numPaths

            # check if it is a # check if it is a what?
            if (
                (nextNode.type == spaces.BLUE_EDGE or nextNode.type == spaces.RED_EDGE)
                and (
                    currentNode.type != spaces.BLUE_EDGE
                    or currentNode.type != spaces.RED_EDGE
                )
                and nextNode.getPC() == bestCost
            ):
                if currentNode.extraPathsToThisNode != 0:
                    numPaths[currentPos] = currentNode.extraPathsToThisNode

            # moving from start edge to playable board
            elif (
                nextNode.type != spaces.BLUE_EDGE or nextNode.type != spaces.RED_EDGE
            ) and (
                currentNode.type == spaces.BLUE_EDGE
                or currentNode.type == spaces.RED_EDGE
            ):
                nextNode.setExtraPathsToNode(1)

            else:
                openNodes[pos].addExtraPathsToNode(currentNode.extraPathsToThisNode)

        # gotta loop through everything
        while len(openNodes) > 0:
            currentNode = openNodes.popKey()
            closedNodes[currentNode] = None

            adjacentSpaces = self.getAdjacentSpaces(currentNode)
            for nextPos in adjacentSpaces:
                nextNode = nodes[nextPos]

                if not checkIfBarrier(nextNode) and not closedNodes.hasKey(nextPos):
                    if (currentNode.getPC() + nextNode.cost) > bestCost:
                        # Too expensive
                        pass

                    elif nextPos == endPos:
                        # Path Found
                        pass

                    elif openNodes.hasKey(nextPos):
                        # In open nodes. check cost compared to this path
                        if nextNode.getPC() > currentNode.getPC() + nextNode.cost:
                            # new path better. Overwrite and set path
                            setNodeInOpenNodes(nextPos)

                        elif nextNode.getPC() == currentNode.getPC() + nextNode.cost:
                            # same path same cost. add paths to node
                            updateNodeInOpenNodes(nextPos)

                    else:
                        # not in open nodes
                        setNodeInOpenNodes(nextPos)

        # return paths
        total = 0
        ez = [] #  remove if not used
        while len(numPaths) > 0:
            num = numPaths.pop()
            ez.append(num)
            total += num
        return total
        
"""