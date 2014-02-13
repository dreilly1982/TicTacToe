__author__ = 'Don Reilly'
from Tkinter import Tk, Button
from tkFont import Font
from copy import deepcopy
from random import randint
import pickle

class Board:

    """
    This is the main board class, defines the object that maintains the
    state of the game at any particular moment
    """
    def __init__(self, other=None):
        """
        Declares the attributes and sets of the board. 'Other' checks
        to see if this is an initial declaration or a copy
        """
        self.player = 'X'
        self.opponent = 'O'
        self.empty = ' '
        self.size = 3
        self.fields = hashabledict()
        for y in range(self.size):
            for x in range(self.size):
                self.fields[x, y] = self.empty
        if other:
            # Provides mechanism for deep copy
            self.__dict__ = deepcopy(other.__dict__)

    def move(self, x, y):
        """
        This is the move method.  Copies the board, inputs the proper
        game piece and then switches players out.
        """
        board = Board(self)
        board.fields[x, y] = board.player
        (board.player, board.opponent) = (board.opponent, board.player)
        return board

    def tied(self):
        """
        Check to see if the end game state is tied.
        """
        for (x, y) in self.fields:
            if self.fields[x, y] == self.empty:
                return False
        return True

    def won(self):
        """
        Check to see if game has been won on the previous turn.
        First for loop check horizontal
        Second checks vertical
        Third checks top left to bottom right diagonal
        Last checks top right to bottom left diagonal
        """
        for y in range(self.size):
            winning = []
            for x in range(self.size):
                if self.fields[x, y] == self.opponent:
                    winning.append((x, y))
            if len(winning) == self.size:
                return winning
        for x in range(self.size):
            winning = []
            for y in range(self.size):
                if self.fields[x, y] == self.opponent:
                    winning.append((x, y))
            if len(winning) == self.size:
                return winning
        winning = []
        for y in range(self.size):
            x = y
            if self.fields[x, y] == self.opponent:
                winning.append((x, y))
        if len(winning) == self.size:
            return winning
        winning = []
        for y in range(self.size):
            x = self.size-1-y
            if self.fields[x, y] == self.opponent:
                winning.append((x, y))
        if len(winning) == self.size:
            return winning
        return None

    def best(self):
        """
        Entry into the minimax algorithm.  This sets the inital A B
        values and enters into the recursive minimax process.
        Sets player as True, as we are looking from the perspective
        of the current player.  (Human or Computer).  Alpha is set
        LOW because we want to find the HIGHEST value for this player.
        Beta is set HIGH because we need to find the LOWEST value for
        the current opponent.
        The minimax returns a nested tuple of (value, (x, y)) where
        X and Y are the coordinates of the move with the corresponding
        value.
        """
        alpha = -1
        beta = +1
        move = self.__negamax(alpha, beta, tt=DictTT())
        return move[1]


    def __negamax(self, alpha, beta, tt=None):
        """
        This is where the magic happens.  First check for leaf node
        (end-state).  If the game was won on the previous round by
        the opponent, assign a -1 (worst case), else if the game is won

        the previous round by the player then assign a +1 (best case).

        Then check for a Tie.  Assign a 0 for a tie (neutral state)

        Next the real fun begins.  Dive into the recursion switching sides
        and checking each and every move.  IF a branch of the tree ends in an
        end state do not continue down (the alpha beta pruning part,
        this saves a TON of time).
        """
        alpha_orig = alpha
        lookup = None if (tt is None) else tt.lookup(self)
        if lookup is not None:
            flag, best = lookup['flag'], lookup['best']
            if flag == 0:
                return best
            elif flag == -1:
                alpha = max(alpha, best[0])
            elif flag == +1:
                beta = min(beta, best[0])

            if alpha >= beta:
                return best

        if self.won():
            return (-2, None)
        if self.tied():
            return (0, None)
        if lookup is None:
            best = (-1, None)
        for x, y in self.fields:
            if self.fields[x, y] == self.empty:
                value = -self.move(x, y).__negamax(-beta, -alpha, tt)[0]
                if value > best[0]:
                    best = (value, (x, y))
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
        if tt is not None:
            tt.store(game=self,
                     best=best,
                     flag=1 if (best[0] <= alpha_orig)
                     else (-1 if (best[0] >= beta) else 0))

        return best

    def ttentry(self):
        return self.fields


class hashabledict(dict):
    def __hash__(self):
        return hash(tuple(sorted(self.items())))


class DictTT:

    def __init__(self):
        self.d = dict()

    def lookup(self, game):
        return self.d.get(game.ttentry(), None)

    def store(self, **data):
        entry = data.pop("game").ttentry()
        self.d[entry] = data


class GUI:
    """
    This is a GUI.  Nothing really special to see here
    """

    def __init__(self):
        """
        Initiation bits.  Make buttons, give them handlers.  You know,
        all the normal stuff.
        """
        self.computer_first = 0  # randint(0, 1)
        self.app = Tk()
        self.app.attributes("-toolwindow", 1)
        self.app.title('Tic Tac Toe')
        self.app.resizable(width=False, height=False)
        self.board = Board()
        self.font = Font(family="Helvetica", size=32)
        self.buttons = {}
        for x, y in self.board.fields:
            handler = lambda x=x, y=y: self.move(x, y)
            button = Button(self.app, command=handler, font=self.font,
                            width=2, height=1)
            button.grid(row=y, column=x)
            self.buttons[x, y] = button
        handler = lambda: self.reset()
        button = Button(self.app, text='reset', command=handler)
        button.grid(row=self.board.size + 1, column=0,
                    columnspan=self.board.size, stick='WE')
        self.update()
        if self.computer_first:
            self.move(randint(0, self.board.size - 1),
                      randint(0, self.board.size - 1))

    def update(self):
        """
        Updates the board.  Deactivates played fields.  Checks to see if the
        last turn won.  If it did, lock the whole board, make the winning
        combination red.
        """
        for (x, y) in self.board.fields:
            text = self.board.fields[x, y]
            self.buttons[x, y]['text'] = text
            self.buttons[x, y]['disabledforeground'] = 'black'
            if text == self.board.empty:
                self.buttons[x, y]['state'] = 'normal'
            else:
                self.buttons[x, y]['state'] = 'disabled'
        winning = self.board.won()
        if winning:
            for x, y in winning:
                self.buttons[x, y]['disabledforeground'] = 'red'
            for x, y in self.buttons:
                self.buttons[x, y]['state'] = 'disabled'
        for (x, y) in self.board.fields:
            self.buttons[x, y].update()

    def reset(self):
        """
        Self-explanatory.  This re-instantiates the board.
        Also throws a random binary to see if the computer drew the
        first move.
        """
        self.board = Board()
        self.update()
        self.computer_first = randint(0, 1)
        if self.computer_first:
            self.move(randint(0, self.board.size - 1),
                      randint(0, self.board.size - 1))

    def move(self, x, y):
        """
        The action.  This allows the player to make a move, then
        instructs the computer to make a counter mover.
        """
        if self.computer_first:
            self.app.config(cursor='watch')
            self.board = self.board.move(x, y)
            self.update()
            self.computer_first = 0
            self.app.config(cursor='')
        else:
            self.board = self.board.move(x, y)
            self.update()
            self.app.config(cursor='watch')
            move = self.board.best()
            if move:
                self.board = self.board.move(*move)
                self.update()
            self.app.config(cursor='')

    def mainloop(self):
        """
        All games have to have a loop.  This GUI framework knows
        that.
        """
        self.app.mainloop()

if __name__ == '__main__':
    GUI().mainloop()  # Calls the main loop and kicks off the whole shindig.
