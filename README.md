# cs255_MazeRender
A graphical environment for testing maze finding robots in the 2018/19 Warwick CS255 coursework

## Installation:
Like the coursework, this tool requires Python 3.
Add renderMaze.py to your dev environment alongside the other provided files, and run it instead of running runMaze.py. 

## Usage
Start the visual environment using `python3 renderMaze.py`.

You can then load, generate and save mazes using the onscreen tools. You can trigger one call to the loaded robot's `nextMove()` using the *Step* function, or you can cause it to be called itteratively by using the *Start*. While the robot is running, the *Pause* button will cause the robot to halt progress, whereupon it can be restarted or stepped as above. Restart will cause the robot to be reinitialised, along with the maze. This means that the robot will have no remnents of previous route calculations when restarted.

The board can be edited using the mouse. A left click will toggle between walls and empty tiles. Right click will bring up a menu where the desired tile can be selected. The program will attempt to ensure that there is always exactly one starting tile, and that there is at least one finish tile. It will not attempt to check that a route exists from one to the other. 
A new random maze can be generated from the *Generate Board* tool. This will allow you to enter the size of the desired board (between 1 and 99 on each axis) and the desired wall density. By selecting a density of 0, an empty board can be generated.
A generated or changed board can be saved to a file using the *Save Board* tool and reloaded using *Load Board*.

The *Update Speed* slider allows you to set how often the robot's nextMove function is called.

## Usage notes
Please note: although effort has been taken to ensure that the output from this program is as faithful to the original files as possible there is a chance that small incompatabilities may exist. Please also check your program using only the provided files to ensure maximal correctness.

Also, the graphical interface will hang if your robot's `nextMove` function takes a long time to return. Please be aware that it may become unresponsive if your program enters an infinite loop. None of the provided functions are able to interupt your robots calculations and in this case the whole application would need to be terminated.
