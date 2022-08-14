import pytest

from hexBoy.hex.HexBoard import Board

@pytest.fixture(autouse=True)
def before_and_after_test(tmpdir):
    """Reset the board and pathfinder before each test"""
    tmpdir.size = 11
    tmpdir.board = Board(tmpdir.size)

    # ^^^ before ^^^
    yield # run the rest
    # vvv After vvv

def test_BoardBounds(tmpdir):
    """Test Bounds Of the Board"""
    assert tmpdir.board.isSpaceWithinBounds((0,0))
    assert tmpdir.board.isSpaceWithinBounds((-1,0))
    assert tmpdir.board.isSpaceWithinBounds((0,11))
    assert tmpdir.board.isSpaceWithinBounds((5,5))
    assert not tmpdir.board.isSpaceWithinBounds((-1,-1))
    assert not tmpdir.board.isSpaceWithinBounds((tmpdir.size,tmpdir.size))

def test_ValidateAndMakeMove(tmpdir):
    """Validate a moves and make maves"""
    move = (0,0)
    assert tmpdir.board.validateMove(move)
    tmpdir.board.makeMove(move, 1)
    assert not tmpdir.board.validateMove(move)

    badMove = (-1, -1)
    assert not tmpdir.board.validateMove(badMove)

def test_AdjacentSpaces(tmpdir):
    """Check Adjacent Spaces the board, make sure they are on the board"""
    space = (1,1)
    actual = tmpdir.board.getAdjacentSpaces(space)
    expected = [(1,0), (1,2), (0,1), (2,1), (0,2), (2,0)]
    assert actual == expected

    space = (-1,0)
    actual = tmpdir.board.getAdjacentSpaces(space)
    expected = [(-1,1), (0,0), (0,-1)]
    assert actual == expected

def test_ResetBoard(tmpdir):
    """Reset the board to all empty"""
    move = (0,0)
    tmpdir.board.makeMove(move, 1)
    tmpdir.board.resetGame()
    assert tmpdir.board.validateMove(move)

def test_DistanceToCenter(tmpdir):
    """Check the distance to the center of the board"""
    move = (5,5)
    assert tmpdir.board.getDistanceToCenter(move) == 0

    move = (0,10)
    assert tmpdir.board.getDistanceToCenter(move) == 10

def test_validateEdges(tmpdir):
    """testing edges, Imma rage if this doesn't work. Jk I'm an idiot"""
    assert  not tmpdir.board.validateMove((4,11))

def test_GetPlayerEndZone(tmpdir):
    """Get the player end zones"""

    actualBlueEndZone = tmpdir.board.getPlayerEndZone(1)
    actualRedEndZone = tmpdir.board.getPlayerEndZone(2)

    expectedBlueEndZone = [
        (0, -1), (0, 11), 
        (1, -1), (1, 11), 
        (2, -1), (2, 11), 
        (3, -1), (3, 11), 
        (4, -1), (4, 11), 
        (5, -1), (5, 11), 
        (6, -1), (6, 11), 
        (7, -1), (7, 11), 
        (8, -1), (8, 11), 
        (9, -1), (9, 11), 
        (10, -1), (10, 11)
    ] 

    expectedRedEndZone = [
        (-1, 0), (11, 0), 
        (-1, 1), (11, 1), 
        (-1, 2), (11, 2), 
        (-1, 3), (11, 3), 
        (-1, 4), (11, 4), 
        (-1, 5), (11, 5), 
        (-1, 6), (11, 6), 
        (-1, 7), (11, 7), 
        (-1, 8), (11, 8), 
        (-1, 9), (11, 9), 
        (-1, 10), (11, 10)
    ]

    assert  set(actualBlueEndZone) == set(expectedBlueEndZone)
    assert  set(actualRedEndZone) == set(expectedRedEndZone)
