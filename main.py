import sys
from hexBoy.hex.game.HexGame import Hex_Play
from hexBoy.AI.GetAgent import GetAgent, PrintAgentHelp


'''
[ ] Change print statements to the logging python library
'''

def main() -> None:
    """ Main Function to run the game"""

    agentA = GetAgent(1)
    agentB = GetAgent(1)
    showEndGame = False
    showDisplay = False
    numGames = 1
    showPrint = True
    mockLogger = False

    opts = [opt for opt in sys.argv[1:] if opt.startswith("-")]
    args = [arg for arg in sys.argv[1:] if not arg.startswith("-")]

    if (len(opts) == 1 and opts[0] == "--help"): 
        printHelp()
        return

    # TODO check if any of the arguments are garbage/unexpected
    # - Accidentally running the main.py with random strings should complain and not run the default options
    argNum = 0 # what opt the arg is for
    for i in range(len(opts)):

        # -b <agent>, put something for a player
        if (opts[i] == "-b"):
            if (args[argNum].isnumeric()):
                agentA = GetAgent(int(args[argNum]))
            else:
                agentA = None
                showDisplay = True
            argNum += 1

        # -r <agent>
        elif (opts[i] == "-r"):
            if (args[argNum].isnumeric()):
                agentB = GetAgent(int(args[argNum]))
            else:
                agentB = None
                showDisplay = True
            argNum += 1

        # -d, for a display (auto on for players)
        elif (opts[i] == "-d"):
            showDisplay = True

        # -e, keep board on after game
        elif (opts[i] == "-e"):
            showEndGame = True

        # -n, number of games
        elif (opts[i] == "-n"):
            if (args[argNum].isnumeric()):
                numGames = int(args[argNum])
            else:
                numGames = 1
            argNum += 1

        # -p, disable print
        elif (opts[i] == "-p"):
            showPrint = False

        # -mock, disable logger and use mock logger
        elif (opts[i] == "--mock"):
            mockLogger = True

    Hex_Play(
        agentA,
        agentB,
        showEndGame,
        showDisplay,
        numGames,
        showPrint,
        mockLogger
    )

def printHelp() -> None:
    """Help I forgot how to run the game"""

    print()
    print("Command Line Arguments")
    print("----------------------")
    print("\tCan be used in any order. Flags that are expecting an argument need its argument directly after the flag")
    print()
    print("Game Config")
    print("`-n <arg>`\tNumber of games \t(Default: 1)")
    print()
    print("Basic Config Flags")
    print("\tShow Display \t\t`-d` \t\t(Default: hide display)")
    print("\tShow Endgame \t\t`-e` \t\t(Default: Skip Endgame)")
    print("\tHide Prints \t\t`-p` \t\t(Default: Show print summaries)")
    print("\tMock Logger \t\t`-mock` \t(Default: Use logger)")
    print()
    print("Agent Select: Enter an int for a specific agent or a string for a player (Default: AgentA*)")
    print("\tEnter Blue agent: \t`-b <arg>`")
    print("\tEnter Red agent: \t`-r <arg>`") # TODO put this at the bottom before agent help()
    print()
    PrintAgentHelp()

#-------------------------------------------
#   start
#-------------------------------------------
if __name__ == "__main__":
    main()
