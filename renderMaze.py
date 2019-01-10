import tkinter as tk
import tkinter.filedialog as tkf
import Search, Robot

import os, sys, tempfile


class Dialog(tk.Toplevel):
    """Sourced from http://effbot.org/tkinterbook/tkinter-dialog-windows.htm"""

    def __init__(self, parent, title=None):
        tk.Toplevel.__init__(self, parent)
        self.transient(parent)
        if title:
            self.title(title)
        self.parent = parent
        self.result = None
        body = tk.Frame(self)
        self.initial_focus = self.body(body)
        body.pack(padx=5, pady=5)
        self.buttonbox()
        self.grab_set()
        if not self.initial_focus:
            self.initial_focus = self
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.geometry("+%d+%d" % (parent.winfo_rootx() + 50,
                                  parent.winfo_rooty() + 50))
        self.initial_focus.focus_set()
        self.wait_window(self)

    #
    # construction hooks
    def body(self, master):
        # create dialog body.  return widget that should have
        # initial focus.  this method should be overridden
        pass

    def buttonbox(self):
        # add standard button box. override if you don't want the
        # standard buttons
        box = tk.Frame(self)
        w = tk.Button(box, text="OK", width=10, command=self.ok, default=tk.ACTIVE)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        w = tk.Button(box, text="Cancel", width=10, command=self.cancel)
        w.pack(side=tk.LEFT, padx=5, pady=5)
        self.bind("<Return>", self.ok)
        self.bind("<Escape>", self.cancel)
        box.pack()

    #
    # standard button semantics
    def ok(self, event=None):
        if not self.validate():
            self.initial_focus.focus_set()  # put focus back
            return
        self.withdraw()
        self.update_idletasks()
        self.apply()
        self.cancel()

    def cancel(self, event=None):
        # put focus back to the parent window
        self.parent.focus_set()
        self.destroy()

    #
    # command hooks
    def validate(self):
        return 1  # override

    def apply(self):

        pass  # override


class GenerateDialog(Dialog):
    def body(self, master):
        self.rows = tk.IntVar(value=20)
        self.cols = tk.IntVar(value=20)
        self.objects = tk.IntVar(value=0)
        self.density = tk.DoubleVar(value=.2)
        tk.Label(master, text="Rows: ").grid(row=0, column=0)
        tk.Entry(master, textvariable=self.rows).grid(row=0, column=1)
        tk.Label(master, text="Cols: ").grid(row=1, column=0)
        tk.Entry(master, textvariable=self.cols).grid(row=1, column=1)
        tk.Label(master, text="Objects: ").grid(row=2, column=0)
        tk.Entry(master, textvariable=self.objects).grid(row=2, column=1)
        tk.Scale(master, label="Density: ", from_=0, to=1, resolution=.05, tick=.25, length=300, variable=self.density,
                 orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=2)

    def validate(self):
        flag = True
        if not (100 > self.rows.get() > 0):
            flag = False
            self.rows.set(20)
        if not (100 > self.cols.get() > 0):
            flag = False
            self.rows.set(20)
        if not (0 <= self.density.get() <= 1):
            flag = False
            self.density.set(.2)
        if not (0 <= self.objects.get() <= 30):
            flag = False
            self.objects.set(0)
        return flag

    def apply(self):
        cols = self.cols.get()
        rows = self.rows.get()
        density = self.density.get()
        objects = self.objects.get()
        self.result = {"cols": cols, "rows": rows, "density": density, "items": objects}


class MazeApp(tk.Frame):
    COLOURS = {0: "white", 1: "gray", 2: "green", 3: "blue", 4: "white", 5: "white", -1: "magenta", -2: "yellow",
               -3: "red"}
    ENEMY_COLS = {"predefined-known": "lightGreen", "predefined-unknown": "lightblue", "random": "orange",
                  "aggressive": "red"}

    def __init__(self, master, game, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.gameState = game
        self.collisions = tk.IntVar(self, value=0)
        self.attacks = tk.IntVar(self, value=0)
        self.steps = tk.IntVar(self, value=0)
        self.objectsRet = tk.IntVar(self, value=0)
        self.objectsTot = tk.IntVar(self, value=game.game.numberOfObjs())
        self.timer = None
        self.width = 800
        self.height = 800
        self.unsaved = False
        lPanel = tk.Frame(self)
        self.canvas = tk.Canvas(lPanel, width=800, height=800, bg="white")
        self.canvas.pack(anchor=tk.CENTER)
        lPanel.pack(side=tk.LEFT)
        rPanel = tk.Frame(self)
        tk.Label(rPanel, text="Steps:", font='-weight bold -size 12').pack(side=tk.TOP)
        tk.Label(rPanel, textvariable=self.steps, font='-weight bold -size 12').pack(side=tk.TOP)
        tk.Label(rPanel, text="Collisions:", font='-weight bold -size 12').pack(side=tk.TOP)
        tk.Label(rPanel, textvariable=self.collisions, font='-weight bold -size 12', fg='red').pack(side=tk.TOP)
        tk.Label(rPanel, text="Enemy Attacks:", font='-weight bold -size 12').pack(side=tk.TOP)
        tk.Label(rPanel, textvariable=self.attacks, font='-weight bold -size 12', fg='red').pack(side=tk.TOP)
        tk.Label(rPanel, text="Retrieved:", font='-weight bold -size 12').pack(side=tk.TOP)
        rtGrp = tk.Frame(rPanel)
        tk.Label(rtGrp, textvariable=self.objectsRet, font='-weight bold -size 12', fg='red').pack(side=tk.LEFT, padx=2)
        tk.Label(rtGrp, text="out of", font='-weight bold -size 12').pack(side=tk.LEFT, padx=2)
        tk.Label(rtGrp, textvariable=self.objectsTot, font='-weight bold -size 12').pack(side=tk.LEFT, padx=2)
        rtGrp.pack(side=tk.TOP)
        tk.Label(rPanel, text="").pack(side=tk.TOP)

        tk.Button(rPanel, text="Step", command=self.step).pack(side=tk.TOP)
        tk.Button(rPanel, text="Start", command=self.start).pack(side=tk.TOP)
        tk.Button(rPanel, text="Pause", command=self.pause).pack(side=tk.TOP)
        tk.Button(rPanel, text="Restart", command=self.restart).pack(side=tk.TOP)
        tk.Button(rPanel, text="Render", command=self.full_render).pack(side=tk.TOP)
        tk.Button(rPanel, text="ConsolePrint", command=self)
        tk.Label(rPanel, text="").pack(side=tk.TOP)

        self.gamemodeVar = tk.IntVar(value=self.gameState.gameArgs['gameType'])
        self.gamemodeVar.trace_variable('w', self.changeGamemode)
        tk.Label(rPanel, text="Game mode:").pack(side=tk.TOP)
        tk.OptionMenu(rPanel, self.gamemodeVar, 1, 2, 3).pack(side=tk.TOP)
        tk.Label(rPanel, text="").pack(side=tk.TOP)

        tk.Button(rPanel, text="Load Board", command=self.load).pack(side=tk.TOP)
        tk.Button(rPanel, text="Save Board", command=self.save).pack(side=tk.TOP)
        tk.Button(rPanel, text="Generate Board", command=self.gen).pack(side=tk.TOP)
        tk.Label(rPanel, text="").pack(side=tk.TOP)

        self.rate = tk.IntVar(self, 1000)
        tk.Label(rPanel, text="Update Speed").pack(side=tk.TOP)
        tk.Scale(rPanel, from_=1, to=1000, resolution=10, tick=100, length=300, variable=self.rate,
                 orient=tk.HORIZONTAL).pack(side=tk.TOP)
        rPanel.pack(side=tk.RIGHT)
        self.pack()
        self.full_render()
        self.canvas.bind("<Button-1>", self.lClick)
        self.canvas.bind("<Button-3>", self.rClick)

    def lClick(self, event):
        if self.timer:
            return
        self.unsaved = True
        (rowSize, colSize) = self.getGridSize()
        row = event.y // rowSize
        col = event.x // colSize
        print(row, col)
        p = self.gameState.game.board.scanSpace(row, col)
        print(p)
        if p == 1:
            self.gameState.game.board.updateSpace(row, col, 0)
        if p == 0:
            self.gameState.game.board.updateSpace(row, col, 1)

        self.full_render()

    def rClick(self, event):
        if self.timer:
            return
        self.unsaved = True
        (rowSize, colSize) = self.getGridSize()
        row = event.y // rowSize
        col = event.x // colSize
        popup = tk.Menu(ROOT, tearoff=0)
        popup.add_command(label="Empty", command=lambda: self.changeSquare(0, row, col))
        popup.add_command(label="Wall", command=lambda: self.changeSquare(1, row, col))
        popup.add_command(label="Goal", command=lambda: self.changeSquare(2, row, col))
        popup.add_command(label="Start", command=lambda: self.changeSquare(3, row, col))
        popup.add_command(label="Object", command=lambda: self.changeSquare(4, row, col))
        try:
            popup.tk_popup(event.x_root, event.y_root)
        finally:
            popup.grab_release()

    def changeSquare(self, target, row, col):
        # So many special cases...
        old = self.gameState.game.board.scanSpace(row, col)
        if old == 3 or old == 5:
            return  # Must always have a start square so no overwriting, and overwriting enemies is not supported
        if old == 2:
            if self.gameState.game.getGoal() == [row, col]:
                for i in range(self.gameState.game.rows):
                    for j in range(self.gameState.game.cols):
                        if not (i == row and j == col):
                            if self.gameState.game.board.scanSpace(i, j) == 2:
                                self.gameState.game.board.goal = [i, j]
            if self.gameState.game.getGoal() == [row, col]:
                # No alternative found, so don't allow replacing final goal
                return
        if old == 4:
            # Update the game data for the new number of objects
            self.gameState.game.totalItems = self.gameState.game.totalItems - 1
            self.gameState.game.board.totalItems = self.gameState.game.board.totalItems - 1
        if target == 2:
            self.gameState.game.board.goal = [row, col]  # Use newest goal as target
        if target == 3:
            oldStart = self.gameState.game.getStart()
            self.gameState.game.board.updateSpace(oldStart[0], oldStart[1], 0)  # Revert old start to empty
            self.gameState.game.board.start = [row, col]  # Replace start with new start
            if self.gameState.game.getCurrentLocation() == oldStart:  # If robot is sitting at start
                self.gameState.game.currentCol = col  # Move robot to new start
                self.gameState.game.currentRow = row
                self.gameState.moveList = [(row, col, "")]
        if target == 4:
            # Update the game data for the new number of objects
            self.gameState.game.totalItems = self.gameState.game.totalItems + 1
            self.gameState.game.board.totalItems = self.gameState.game.board.totalItems + 1

        self.gameState.game.board.updateSpace(row, col, target)
        self.full_render()

    def changeGamemode(self, *args):
        var = self.gamemodeVar.get()
        self.gameState.gameArgs['gameType'] = var
        self.restart()

    def getRate(self):
        r = self.rate.get()
        if r < 1:
            r = 0
        return r

    def load(self):
        self.pause()
        newFile = tkf.askopenfilename(parent=self, initialdir=os.path.join(PATH, 'exampleMazes'),
                                      title="Select Maze",
                                      filetypes=(("Maze Files", "*.maze"), ("Maze Files", "*.txt")))
        self.gameState.gameArgs = {'gameType': self.gameState.gameArgs['gameType'], 'file': newFile}
        self.reset()

    def save(self):
        self.pause()
        saveFile = tkf.asksaveasfilename(parent=self, initialdir=os.path.join(PATH, 'exampleMazes'),
                                         title="Save Maze",
                                         filetypes=(("Maze Files", "*.maze"), ("Maze Files", "*.txt")),
                                         defaultextension=".maze")
        self.gameState.game.board.writeBoard(saveFile)

    def gen(self):
        self.pause()
        dialogBox = GenerateDialog(self)
        result = self.gameState.gameArgs
        if dialogBox.result:
            result = dialogBox.result
            result['gameType'] = self.gameState.gameArgs['gameType']
            result['file'] = ""
            result['eTups'] = list()
        self.gameState.gameArgs = result
        self.reset()

    def start(self):
        self.gameState.done = False
        self.timer = self.after(self.getRate(), self.on_time)

    def pause(self):
        if self.timer:
            self.after_cancel(self.timer)
        self.timer = None

    def restart(self):
        self.pause()
        if self.unsaved:
            self.gameState.restart()
        else:
            self.gameState.reset()
        self.canvas.delete("all")
        self.full_render()

    def reset(self):
        self.pause()
        self.gameState.reset()
        self.canvas.delete("all")
        self.full_render()

    def on_time(self):
        self.step()
        if not self.gameState.done:
            self.timer = self.after(self.getRate(), self.on_time)

    def step(self):
        if self.unsaved:
            self.unsaved = False
            self.gameState.tempSave()
        self.gameState.nextAction()
        self.partial_render()

    def getGridSize(self):
        col = self.width // self.gameState.game.board.col
        row = self.height // self.gameState.game.board.row
        return (row, col)

    def full_render(self):
        # Update counters
        self.collisions.set(self.gameState.game.collisions)
        self.steps.set(self.gameState.game.movesMade)
        self.objectsTot.set(self.gameState.game.numberOfObjs())
        self.objectsRet.set(self.gameState.game.itemsRetrieved)
        # Redraw maze grid
        (row, col) = self.getGridSize()
        colx = 0

        # render board colours
        for i in self.gameState.game.board.room:
            colx = colx + col
            rowx = 0
            for j in i:
                rowx += row
                self.canvas.create_rectangle(rowx, colx, rowx - row, colx - col, fill=self.COLOURS[j.scanSpace()])
                if j.scanSpace() == 4:
                    self.canvas.create_rectangle(rowx - row / 4, colx - col / 4, rowx - 3 * row / 4, colx - 3 * col /
                                                 4, fill=self.COLOURS[-2], tag="object")
                if j.scanSpace() == 5:
                    f = False
                    for en in self.gameState.game.enemyList:

                        if en.currRow==(colx//col)-1 and en.currCol==(rowx//row)-1:
                            f = True
                            self.canvas.create_oval(rowx, colx, rowx - row, colx - col,
                                                    fill=self.ENEMY_COLS[en.tactic],
                                                    tag="enemy")
                    if not f:
                        self.canvas.create_oval(rowx, colx, rowx - row, colx - col,
                                                fill=self.COLOURS[-3],
                                                tag="enemy")

        # Render path taken
        lastR, lastC, discard = self.gameState.moveList[0]
        lastX = lastC * col + col // 2
        lastY = lastR * row + row // 2
        for i in self.gameState.moveList:
            nextX = i[1] * col + col // 2
            nextY = i[0] * row + row // 2
            if (nextX, nextY) == (lastX, lastY):
                # Collided with wall or wait
                if i[2] == "EAST":
                    self.canvas.create_line(lastX, lastY, nextX + (col // 2), nextY, tag="trail")
                elif i[2] == "WEST":
                    self.canvas.create_line(lastX, lastY, nextX - (col // 2), nextY, tag="trail")
                elif i[2] == "SOUTH":
                    self.canvas.create_line(lastX, lastY, nextX, nextY + (col // 2), tag="trail")
                elif i[2] == "NORTH":
                    self.canvas.create_line(lastX, lastY, nextX, nextY - (col // 2), tag="trail")
            else:
                self.canvas.create_line(lastX, lastY, nextX, nextY, tag="trail")
            lastX = nextX
            lastY = nextY
        # Render robot
        rCol = self.gameState.game.currentCol * col
        rRow = self.gameState.game.currentRow * row
        self.canvas.create_oval(rCol, rRow, rCol + col, rRow + row, fill=self.COLOURS[-1], tag="robot")
        if self.gameState.game.robotCarrying():
            self.canvas.create_rectangle(rCol + col / 4, rRow + row / 4, rCol + 3 * col / 4, rRow + 3 * row / 4,
                                         fill=self.COLOURS[-2], tag="robot")

    def partial_render(self):
        # Update counters
        self.collisions.set(self.gameState.game.collisions)
        self.steps.set(self.gameState.game.movesMade)
        self.attacks.set(self.gameState.game.enemyCollisions)
        self.objectsTot.set(self.gameState.game.numberOfObjs())
        self.objectsRet.set(self.gameState.game.itemsRetrieved)
        (row, col) = self.getGridSize()

        if len(self.gameState.moveList) >= 2:
            (X, Y, discard) = self.gameState.moveList[-2]
        else:
            (X, Y) = self.gameState.game.getStart()

        i = self.gameState.moveList[-1]
        lastX = Y * col + col // 2
        lastY = X * row + row // 2
        nextX = i[1] * col + col // 2
        nextY = i[0] * row + row // 2
        if (nextX, nextY) == (lastX, lastY):
            # Collided with wall or wait
            if i[2] == "EAST":
                self.canvas.create_line(lastX, lastY, nextX + (col // 2), nextY, tag="trail")
            elif i[2] == "WEST":
                self.canvas.create_line(lastX, lastY, nextX - (col // 2), nextY, tag="trail")
            elif i[2] == "SOUTH":
                self.canvas.create_line(lastX, lastY, nextX, nextY + (col // 2), tag="trail")
            elif i[2] == "NORTH":
                self.canvas.create_line(lastX, lastY, nextX, nextY - (col // 2), tag="trail")
        else:
            self.canvas.create_line(lastX, lastY, nextX, nextY, tag="trail")

        self.canvas.delete("robot")
        rCol = self.gameState.game.currentCol * col
        rRow = self.gameState.game.currentRow * row
        self.canvas.create_oval(rCol, rRow, rCol + col, rRow + row, fill=self.COLOURS[-1], tag="robot")
        if self.gameState.game.robotCarrying():
            self.canvas.create_rectangle(rCol + col / 4, rRow + row / 4, rCol + 3 * col / 4, rRow + 3 * row / 4,
                                         fill=self.COLOURS[-2], tag="robot")

        self.canvas.delete("enemy")
        self.canvas.delete("object")
        colx = 0
        for i in self.gameState.game.board.room:
            colx = colx + col
            rowx = 0
            for j in i:
                rowx += row
                if j.scanSpace() == 4:
                    self.canvas.create_rectangle(rowx - row / 4, colx - col / 4, rowx - 3 * row / 4, colx - 3 * col /
                                                 4, fill=self.COLOURS[-2], tag="object")
                if j.scanSpace() == 5:
                    f = False
                    for en in self.gameState.game.enemyList:

                        if en.currRow == (colx // col) - 1 and en.currCol == (rowx // row) - 1:
                            f = True
                            self.canvas.create_oval(rowx, colx, rowx - row, colx - col,
                                                    fill=self.ENEMY_COLS[en.tactic],
                                                    tag="enemy")
                    if not f:
                        self.canvas.create_oval(rowx, colx, rowx - row, colx - col,
                                                fill=self.COLOURS[-3],
                                                tag="enemy")


class GameState:
    def __init__(self, type, maze, robot):
        self.robotProto = robot
        self.done = False
        self.moveList = []
        self.gameArgs = {"gameType": type, "file": maze}
        self.reset()

    def reset(self):
        self.game = Search.Game(**self.gameArgs)
        self.robot = self.robotProto()
        self.moveList = []
        self.done = False
        self.moveList.append((self.game.currentRow, self.game.currentCol, ""))
        print("Starting in Space: " + str([self.game.currentRow, self.game.currentCol]))

    def restart(self):
        self.tempSave()
        self.reset()

    def tempSave(self):
        temp = os.path.join(tempfile.gettempdir(), 'cs255_cw2temp.maze')
        if os.path.exists(temp):
            os.remove(temp)
        self.game.board.writeBoard(temp)
        self.gameArgs = {'gameType': self.gameArgs.get('gameType'), 'file': temp}

    def nextAction(self):
        print(self.game.gameType)

        nextMove = self.robot.nextMove(self.game, self.game.gameType)

        if self.game.gameType == 1 or self.game.gameType == 2:
            if nextMove == "STOP":
                self.checkGoal()
                self.done = True
            else:
                self.game.moveRobot(nextMove, verbose=True)
                self.moveList.append((self.game.currentRow, self.game.currentCol, nextMove))
        if self.game.gameType == 3:

            if nextMove == "STOP":
                self.checkGoal()
                self.done = True
            else:
                print("Moving robot")
                self.game.moveRobot(nextMove, verbose=True)
                print("Moving Enemy")
                self.game.moveEnemyRobots(verbose=True)
                self.moveList.append((self.game.currentRow, self.game.currentCol, nextMove))

    def checkGoal(self):
        if self.game.gameType == 1:
            if self.game.atGoal():
                print(str(self.robot.name) + " has successfully navigated the terrain!")
                print("Moves made: " + str(self.game.movesMade))
                print("Collisions: " + str(self.game.collisions))
                return True
            else:
                print(str(self.robot.name) + " did not reach the goal.")
                print("Moves made: " + str(self.game.movesMade))
                print("Collisions: " + str(self.game.collisions))
                return False
        if self.game.gameType == 2:
            if self.game.atGoal():
                print(str(self.robot.name) + " has successfully navigated the terrain!")
                print("Moves made: " + str(self.game.movesMade))
                print("Collisions: " + str(self.game.collisions))
                print("Retrieved " + str(self.game.itemsRetrieved) + " out of " + str(self.game.totalItems))
                return True
            else:
                print(str(self.robot.name) + " did not reach the goal.")
                print("Moves made: " + str(self.game.movesMade))
                print("Collisions: " + str(self.game.collisions))
                print("Retrieved " + str(self.game.itemsRetrieved) + " out of " + str(self.game.totalItems))
                return False
        if self.game.gameType == 3:
            if self.game.atGoal():
                print(str(self.robot.name) + " has successfully navigated the terrain!")
                print("Moves made: " + str(self.game.movesMade))
                print("Collisions: " + str(self.game.collisions))
                print("Enemy Collisions: " + str(self.game.enemyCollisions))
                print("Retrieved " + str(self.game.itemsRetrieved) + " out of " + str(self.game.totalItems))
                return True
            else:
                print(str(self.robot.name) + " did not reach the goal.")
                print("Moves made: " + str(self.game.movesMade))
                print("Collisions: " + str(self.game.collisions))
                print("Enemy Collisions: " + str(self.game.enemyCollisions))
                print("Retrieved " + str(self.game.itemsRetrieved) + " out of " + str(self.game.totalItems))
                return False


PATH = ''
if getattr(sys, 'frozen', False):
    PATH = os.path.dirname(sys.executable)
elif __file__:
    PATH = os.path.dirname(__file__)

if __name__ == '__main__':
    ROOT = tk.Tk()
    [gT, mazeFile] = [3, "exampleMazes/GameType3/50Squares-PDFK.txt"]
    gameState = GameState(gT, mazeFile, Robot.Robot)
    render = MazeApp(ROOT, gameState)
    ROOT.mainloop()
