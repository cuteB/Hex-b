import random

from hexBoy.pathfinder.PathBoy import PathBoy
from hexBoy.HexBoard import Board
from hexBoy.AI.HexAgent import HexAgent
from hexBoy.HexNode import HexNode
from hexBoy.AI.agentUtil.BoardEval import BoardStates
from hexBoy.AI.agentUtil.MoveEval import evaluateMove

'''
-----------------------------------------------
Reinforcement Learning Agent
-----------------------------------------------
'''
class AgentAStar(HexAgent):

  def __init__(self):
    HexAgent.__init__(self)
    self.name = "Agent_A*"


  '''
  -----------------------------------------------
  Agent Functions (Overides)
  -----------------------------------------------
  '''
  def getAgentMove(self):
    gameBoard = self.gameBoard

    # get value to use for sorting
    def getSortValue(cell):
      node = gameBoard.getNodeDict()[cell]
      return HexNode.getCellValueForNextMove(node)

    # Find best path to win
    potentialMoves = self.pathfinder.findPath(
      gameBoard.getNodeDict(),
      self.startPos,
      self.endPos,
      self.checkIfBarrier,
      HexNode.getCellValueForNextMove
    )

    # make a move on the best path
    random.shuffle(potentialMoves)
    for move in potentialMoves:
      if (gameBoard.validateMove(move)):
        return move

    return self.randomMove(gameBoard)

  def setGameBoardAndPlayer(self, gameBoard, player):
    HexAgent.setGameBoardAndPlayer(self, gameBoard, player)

    # AStar Pathfinder
    self.pathfinder = PathBoy(
      self.getAdjacentSpaces,
      1 #AStar
    )