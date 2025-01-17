# I don't like the pygame startup message.
from os import environ
environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import pygame
import sys
import threading, concurrent

from dataclasses import dataclass
from pygame.locals import *
from typing import List

from hexBoy.AI.agentUtil.pathfinder.TrimPath import TrimEdgesFromPath
from hexBoy.AI.HexAgent import HexAgent
from hexBoy.hex.board.HexBoard import HexBoard
from hexBoy.hex.game.HexGameRules import HexGameRules
from hexBoy.hex.graphics.HexGraphics import HexGraphics
from hexBoy.hex.node.HexNode import Hex
from hexBoy.pathfinder.PathBoy import PathBoy

from hexBoy.db.HexDBConfig import EventType
from hexBoy.db.HexLogger import HexLogger, MockLogger

# Custom Events
BEFORE_TURN = pygame.USEREVENT + 1
PLAYER_TURN = pygame.USEREVENT + 2
AFTER_TURN = pygame.USEREVENT + 3

# Game options
@dataclass
class HexGameOptions:
    showDisplay: bool = False
    showPrint: bool = False
    showEndGame: bool = False # Sorta works but only with one game
    startingPlayer: int = 1
    alternateStartingPlayer: bool = True
    gameType: str = "" # Type of game to label it as in the logger.
    testMode: bool = False # Disable the logger if true.

'''----------------------------------
Main hex game class
----------------------------------'''
@dataclass
class HexGame:
    """ # Hex
    The game class to manage agents and games.

    - Played on an 11 x 11 hexagon grid. With blue on the top and bottom and read on the left and right.
    - Each player takes turns placing a piece on the board. 
    - The goal is to connect your sides of the board.
    - The first player to connect their sides wins.
227
    Public:

    > Thank you Hex for changing my life
    """

    _gameBoard: HexBoard  # Board, Hex Board Object 
    _options: HexGameOptions

    _currentPlayer: int  
    _gameInProgress: bool  
    _forceQuit: bool

    _winPath: List[Hex]  # the winning path

    _graphics: HexGraphics  # Render the game board
    _bluePathFinder: PathBoy  # Pathfinder, Algorithms to find paths
    _redPathfinder: PathBoy

    _blueAgent: HexAgent  # AIs for player, None = human
    _redAgent: HexAgent
    _currentGameNumber: int
    _blueWins: int
    _redWins: int

    _blueName: str 
    _redName: str

    _nextMove: tuple

    _xLogger: HexLogger

    def __init__(
        self,
        agent1: HexAgent = None,
        agent2: HexAgent =None,
        options: HexGameOptions = HexGameOptions()
    ):
        """
        Initialize the HexGame

        Args:
            agent1: (HexAgent) "Blue Agent"
            agent2: HexAgent "Red Agent"
            options: HexGameOptions "Game Options"
        """
        pygame.init() # Needs to be first

        self._gameBoard = HexBoard()
        self._options = options
        self._currentPlayer = self._options.startingPlayer

        self._gameInProgress = True  # game loop check
        self._forceQuit = False

        self._currentGameNumber = 1
        self._winPath = None
        self._blueWins = 0
        self._redWins = 0

        if self._options.showDisplay:
            self._graphics = HexGraphics()

        self._bluePathFinder = PathBoy(
            self._gameBoard,
            HexGameRules.getCheckIfBarrierFunc(1,useEmpty=False),
            HexGameRules.getHeuristicFunc(1)
        )
        self._redPathFinder = PathBoy(
            self._gameBoard,
            HexGameRules.getCheckIfBarrierFunc(2,useEmpty=False),
            HexGameRules.getHeuristicFunc(2)
        )

        self._blueAgent = None
        self._redAgent = None
        self._blueName = ""
        self._redName = ""

        # Set AIs if provided
        if agent1 != None:
            self._blueAgent = agent1
            self._blueName = self._blueAgent.getName()
            self._blueAgent.setGameBoardAndPlayer(self._gameBoard, 1)

        if agent2 != None:
            self._redAgent = agent2
            self._redName = self._redAgent.getName()
            self._redAgent.setGameBoardAndPlayer(self._gameBoard, 2)

        # Logger
        if (self._options.testMode):
            self._xLogger = MockLogger()
        else:
            self._xLogger = HexLogger()

        
        self._eventToHandler = {
            QUIT: self._terminateGame,
            MOUSEBUTTONDOWN: self._handleMouseClick,
            BEFORE_TURN: self._handleAgentTurn,
            PLAYER_TURN: self._handleNextMove,
            AFTER_TURN: self._endTurn
        }   

    '''---
    Game Loops
    ---'''

    def _gameEventLoop(self) -> None:
        """Main event Game Loop (Game in progress)"""

        def noop():
            pass

        for event in pygame.event.get():

            handler = self._eventToHandler.get(event.type, noop)
            handler()

    def _endGameEventLoop(self) -> None:
        """Event loop after a game has been completed"""

        # loop through events.
        for event in pygame.event.get():

            # quit
            if event.type == QUIT:
                self._terminateGame()

    '''---
    Event Triggers
    ---'''
    def _eventStartTurn(self):
        """Trigger Game Event Start Turn"""
        pygame.event.post(pygame.event.Event(BEFORE_TURN))

    def _eventDoPlayerMove(self):
        """Trigger Game Event Player Turn"""
        pygame.event.post(pygame.event.Event(PLAYER_TURN))

    def _eventAfterTurn(self):
        """Trigger Game Event End Turn"""
        pygame.event.post(pygame.event.Event(AFTER_TURN))

    '''---
    Event Handlers
    ---'''
    def _handleMouseClick(self) -> None:
        """Handle a click on the Game Board
        
        Args:
            mousePos: Hex "Mouse position on the game board"
        """

        mousePos = pygame.mouse.get_pos()

        if self._options.showDisplay:
            move = self._graphics.findHexagonCoordsForMousePos(mousePos)
            if self._validatePlayer() and self._gameBoard.validateMove(move):
                self._nextMove = move
                self._eventDoPlayerMove()

    def _handleAgentTurn(self) -> None:
        """Handle getting a move from an agent if needed"""

        if self._currentPlayer == 1 and self._blueAgent != None:
            self._nextMove = self._blueAgent.getAgentMove()
            self._eventDoPlayerMove()

        if self._currentPlayer == 2 and self._redAgent != None:
            self._nextMove = self._redAgent.getAgentMove()
            self._eventDoPlayerMove()

    def _handleNextMove(self, player: int = None, move: Hex = None) -> None:
        """Handle the next move
        - optional parameters for tests to manually pass in the player and move for the test
        """
        player = player if (player != None) else self._currentPlayer
        move = move if ( move != None) else self._nextMove

        if self._gameBoard.validateMove(move):
            self._gameBoard.makeMove(player, move)
            self._updateAgentBoards()
            self._xLogger.logEvent(EventType.MOVE, (player, move))
            self._eventAfterTurn()

    '''---
    Game Management
    ---'''
    def _endTurn(self) -> None:
        """Check the board for a winner or switch turns
        - check if the current player won
        - switch turns
        """

        if self._currentPlayer == 1:
            # blue just went, Look for a completed blue path
            winPath = self._bluePathFinder.findPath(
                HexGameRules.blue.start,
                HexGameRules.blue.end,
            )

        else:
            # red just went, Look for a completed red path
            winPath = self._redPathFinder.findPath(
                HexGameRules.red.start,
                HexGameRules.red.end,
            )

        # Is the game over?
        if len(winPath) != 0:
            self._winPath = TrimEdgesFromPath(winPath)
            self._gameInProgress = False

            if self._blueAgent != None:
                self._blueAgent.scoreGame()
            if self._redAgent != None:
                self._redAgent.scoreGame()

        else:  # switch turns
            self._switchTurns()
            self._eventStartTurn()

    '''---
    Game Management
    ---'''
    def _validatePlayer(self) -> bool:
        """Validate if the current player is a human"""

        if self._currentPlayer == 1:
            return self._blueAgent == None
        else:
            return self._redAgent == None

    def _preGameSetup(self) -> None: 
        """Setup board and graphics, trigger start turn event
        - Reset game board
        - Setup graphics window 
        - start game for both agents
        """

        self._gameBoard.resetGameBoard()

        if self._options.showDisplay:
            self._graphics.setupWindow(self._gameBoard)

        if self._blueAgent != None:
            self._blueAgent.startGame()
        if self._redAgent != None:
            self._redAgent.startGame()

        self._winPath = None
        self._eventStartTurn()

        self._xLogger.logEvent(EventType.START_GAME, (self._blueName, self._redName, self._currentPlayer, self._options.gameType))

    def _updateGameWindow(self) -> None:
        """Update Graphics screen"""

        if self._options.showDisplay:
            self._graphics.updateWindow(self._gameBoard, self._winPath)

    def _updateAgentBoards(self) -> None:
        """Update Agents Boards because it changed"""

        if self._blueAgent != None:
            self._blueAgent.updateBoard()
        if self._redAgent != None:
            self._redAgent.updateBoard()

    def _terminateGame(self) -> None:
        """Force Quit game"""

        self._gameInProgress = False
        self._forceQuit = True

    def _playGame(self) -> None:
        """Play a game
        - setup game
        - game loop
        - post game loop
        """

        # Pre Game
        self._preGameSetup()

        # Game
        while self._gameInProgress:
            self._updateGameWindow()
            self._gameEventLoop()

        # Post Game
        self._updateGameWindow()
        if self._currentPlayer == 1:
            self._blueWins += 1
        else:
            self._redWins += 1

        self._gameInProgress = True
        while self._gameInProgress and self._options.showDisplay and self._options.showEndGame:
            self._endGameEventLoop()
            self._updateGameWindow()

    def _switchTurns(self) -> None:
        """Switch between blue and red turns"""

        if self._currentPlayer == 1:
            self._currentPlayer = 2
        else:
            self._currentPlayer = 1

    '''---
    Printing
    ---'''
    def _printGameSummary(self) -> None:
        """Print the current game number and current win summary
        - Overwrites the current line with each entry
        
        Output:
            "Game #, Blue wins: #, Red wins: #"       
        """

        if not self._options.showPrint:
            return

        # Note: _currentGameNumber is always one game ahead of the games completed. Showing that the game that is currently being played is the current game. 
        sys.stdout.write(
            "\rGame #%d, Blue%s wins: %d, Red%s wins: %d"
            % (
                self._currentGameNumber,
                self._blueName,
                self._blueWins,
                self._redName,
                self._redWins,
            )
        )
        sys.stdout.flush()

    def _printPostGameSummary(self) -> None:
        """Print the Post game summary of win percents

        Output:
            "Blue Win:  %"
            "Red Win:  %"
        """

        self._currentGameNumber -= 1  # _currentGameNumber is always one game ahead of completed games
        if not self._options.showPrint:
            return

        numGames = self._currentGameNumber
        if numGames == 0: # Always check if divide by zero
            numGames = 1
        blueWinPercent = self._blueWins / numGames
        redWinPercent = self._redWins / numGames
        self._printGameSummary()
        print()
        print("Blue%s Win:  %0.2f" % (self._blueName, blueWinPercent))
        print("Red%s Win:  %0.2f" % (self._redName, redWinPercent))

    '''---
    Threads
    ---'''
    def _gameThread(self, event, numGames: int) -> None:
        
        self._printGameSummary()

        for i in range(numGames):
            if not self._forceQuit:
                if (self._options.alternateStartingPlayer):
                    self._currentPlayer = (i % 2) + 1  # alternate starting 
                self._playGame()
                self._currentGameNumber += 1
                self._printGameSummary()

        # Post summary
        self._printPostGameSummary()

    '''---
    public
    ---'''
    def main(self, numGames=1) -> bool:
        """Play a number of hex games"""
        
        event = threading.Event() # Event to signal the end of the game
        # TODO probs rename this to something more descriptive

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Start threads
            executor.submit(self._xLogger.loggerThread, event)

            # Start Game
            self._gameThread(event, numGames)
            event.set()

        return True # return true to show that the game finished

'''----------------------------------
Main
----------------------------------'''
def Hex_Play(
    agentA=None,
    agentB=None,
    showEndGame=False,
    showDisplay=True,
    numGames=None,
    showPrint=True,
    mockLogger=False
):
    """Main HexGame Function to play games given config
    
    Args
        agentA: HexAgent "Blue Agent"
        agentB: HexAgent "Red Agent"
        showEndGame: bool "Pause at the end game screen. Only works with one game"
        showDisplay: bool "Show the game screen. On if playing with a human"
        numGames: int "Number of games to play"
        showPrint: bool "Print the game summary to the console"
    """

    options = HexGameOptions(
        showDisplay=showDisplay,
        showPrint=showPrint,
        showEndGame=showEndGame,
        testMode=mockLogger
    )

    game: HexGame = HexGame(
        agent1=agentA,
        agent2=agentB,
        options=options
    )

    game.main(numGames)
