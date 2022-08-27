from re import L
from typing import List
from hexBoy.models.SortedDict import SortedDict
from hexBoy.hex.HexNode import HexNode
from hexBoy.hex.HexBoard import Board
from hexBoy.AI.agentUtil.agentSmart.GetConnections import GetConnections
from hexBoy.AI.agentUtil.agentSmart.GetStrongMoves import GetStrongMoves
from hexBoy.pathfinder.PathBoy import PathBoy

'''----------------------------------
Smart Chain
----------------------------------'''
# Assuming that the hexes are all in one chain due to the agent's game plan. 
# - Can defs do dynamic programming and update one move at a time to save time

class SmartChain():
    """A chain that links hexes that have a connection on a board"""
    board: Board
    player: int = None

    pathfinder: PathBoy
    linkedDict: SortedDict = None
    connections: List[tuple] = None
    startPos: tuple = None
    endPos: tuple = None
    startDist: int = None
    endDist: int = None
    length: int = None

    playerStart: tuple = None
    playerEnd: tuple = None

    def __init__(self, _player: int, _board: Board):
        self.board = _board
        self.player = _player

        # TODO I do this stuff too often
        if (self.player == 1):
            # blue
            self.playerStart = self.board.blueStartSpace
            self.playerEnd = self.board.blueEndSpace
            self.checkIfBarrier = HexNode.checkIfBlueBarrierForAI
        else:
            # red
            self.playerStart = self.board.redStartSpace
            self.playerEnd = self.board.redEndSpace
            self.checkIfBarrier = HexNode.checkIfRedBarrierForAI

        self.connections = []
        self.linkedDict = SortedDict()
        self.length = 0

        self.pathfinder = PathBoy(
            self.board,
            self.board.getAdjacentSpaces,
            self.checkIfBarrier
        )

        # update chain based on board
        self.updateChain()

    def getDistToEndZone(self, X) -> int:
        """"Get distance to closest player endZone (i think this exists somewhere)"""

        if (self.player == 1):
            # blue, compare y
            val = X[1]
        else:
            # red, compare x
            val = X[0]

        # assume board size 11
        if (val <= 5):
            return val + 1
        else:
            return 11 - val

    '''---
    Public
    ---'''
    def updateChain(self) -> None:
        """Look at the board and get the chain"""

        playerMoves = self.board.getPlayerMoves(self.player)
        nMoves = len(playerMoves)
        self.connections = []
        # No moves
        if (nMoves == 0):
            return
        
        (weakConnections, strongConnections) = GetConnections(self.board, self.player)
        allConnections = [*weakConnections, *strongConnections]
        bestPath = self.pathfinder.findPath(self.playerStart, self.playerEnd)

        lastNode = None
        lenBestPath = len(bestPath)
        length = 0
        iMove = 0 # capture move index
        i = 0
        for X in bestPath:
            # Player Move
            if (X in playerMoves):
                iMove += 1
                length += 1
                if (iMove == 1): 
                    # first move
                    self.startPos = X
                    self.startDist = i
                    lastNode = X
                
                if (iMove == nMoves):
                    # last move
                    self.endPos = X
                    self.endDist = lenBestPath - i - 1
                    self.linkedDict[lastNode] = X

                if (iMove != 1 and iMove != nMoves):
                    # middle move
                    self.linkedDict[lastNode] = X
                    lastNode = X

            # Weak Connection
            elif (X in weakConnections):
                length += 1
                self.connections.append(X)

            elif (X in strongConnections):
                length += 1
                self.connections.append(X)

                adjacentHexes = self.board.getAdjacentSpaces(X)
                for aX in adjacentHexes:
                    if aX in strongConnections:
                        self.connections.append(aX)

            i += 1

        # finish up
        self.length = length


    def getStartPotentialMoves(self) -> list:
        """Get Potential moves for the start pos (not validated)"""
        (x,y) = self.startPos
        strongMoves = GetStrongMoves(self.board, self.player)

        pMoves = []
        pStrongMoves = []
        if (self.player == 1):
            # blue
            pMoves = self.board.getAdjacentSpaces(self.startPos)
            pStrongMoves = [
                (x-1, y-1),
                (x+2, y-1),
                (x+1, y-2)
            ]
        
        else:
            # red
            pMoves = self.board.getAdjacentSpaces(self.startPos)
            pStrongMoves = [   
                (x-1, y-1),
                (x-1, y+2),
                (x-2, y+1)
            ]

        potentialMoves = []
        for m in pMoves:
            if (self.board.validateMove(m) and m not in self.connections):
                potentialMoves.append(m)

        for m in pStrongMoves:
            if (m in strongMoves and m not in self.connections):
                potentialMoves.append(m)
                
        return potentialMoves

    def getEndPotentialMoves(self) -> list:
        """Get Potential moves for the end pos"""
        (x,y) = self.endPos
        strongMoves = GetStrongMoves(self.board, self.player)


        pMoves = []
        if (self.player == 1):
            # blue
            pMoves = self.board.getAdjacentSpaces(self.endPos)
            pStrongMoves = [   
                (x-2, y+1),
                (x+1, y+1),
                (x-1, y+2),
            ]
        
        else:
            # red
            pMoves = self.board.getAdjacentSpaces(self.endPos)
            pStrongMoves = [   
                (x+1, y-2),
                (x+1, y+1),
                (x+2, y-1),
            ]

        potentialMoves = []
        for m in pMoves:
            if (self.board.validateMove(m) and m not in self.connections):
                potentialMoves.append(m)

        for m in pStrongMoves:
            if (m in strongMoves and m not in self.connections):
                potentialMoves.append(m)
                
        return potentialMoves

    def getPotentialMoves(self) -> list:
        """Get Moves that will extend the chain to the end"""

        # For now just going to return the three strong moves closer to the closest edge and the two short moves. (for both start and end)

        startMoves = []
        endMoves = []
        if (self.startPos and self.startDist > 1):
            startMoves = self.getStartPotentialMoves()

        if (self.endPos and self.endDist > 1):
            endMoves = self.getEndPotentialMoves()

        return [*startMoves, *endMoves]