# columns_model.py
# Holds all the logic of the columns game.

COLORS = ['S', 'T', 'V', 'W', 'X', 'Y', 'Z']
BLANK = " "

NONE = 0
JEWEL = 1
FALLER = 2
LANDED = 3
MATCHING = 4

LEFT = -1
RIGHT = 1

FALLER_LENGTH = 3
BUFFER_SIZE = FALLER_LENGTH - 1
MATCHING_LENGTH = 3

DEBUG_MODE = False


class Faller:
    '''
    Manages faller data.
    '''

    def __init__(self, col: int, colors: [str], length: int):
        self._col = col
        self._rows = [row for row in range(length)]
        self._colors = colors

    def col(self) -> int:
        '''
        Returns the column number.
        '''
        return self._col

    def bottom(self) -> int:
        '''
        Returns the row of the bottom jewel.
        '''
        return max(self._rows)

    def rows(self) -> [int]:
        '''
        Returns a list of rows that the faller is in.
        '''
        return self._rows

    def get_color(self, row: int) -> str:
        '''
        Returns the color of the jewel in the given row.
        '''
        return self._colors[self._rows.index(row)]

    def move(self, direction: int) -> None:
        '''
        Moves the faller left or right based on the direction.
        '''
        self._col += direction

    def drop(self) -> None:
        '''
        Moves the faller down one.
        '''
        self._rows = [row + 1 for row in self._rows]

    def rotate(self) -> None:
        '''
        Rotates the colors of the faller. Moves the jewel color
        to the top and pushes the others down.
        '''
        self._colors = [self._colors[-1]] + self._colors[:-1]

    def contains_cell(self, row: int, col: int) -> bool:
        '''
        Checks if the cell is in the faller.
        '''
        return col == self._col and row in self._rows


class Field:
    '''
    Stores the data of the field.
    '''

    def __init__(self, rows: int, cols: int, buffer_size: int):
        self._rows = rows+buffer_size
        self._cols = cols
        self._buffer_size = buffer_size
        self._cells = [[BLANK for col in range(
            self._cols)] for row in range(self._rows)]
        self._matching = []

    def rows(self) -> int:
        '''
        Returns the number of rows in the field.
        '''
        return self._rows

    def cols(self) -> int:
        '''
        Returns the number of columns in the fields.
        '''
        return self._cols

    def buffer_size(self) -> int:
        '''
        Returns the size of the buffer.
        '''
        return self._buffer_size

    def matching(self) -> [(int, int)]:
        '''
        Returns the matching jewel positions.
        '''
        return self._matching

    def get_color(self, row: int, col: int) -> str:
        '''
        Gets a color from a row and column.
        '''
        return self._cells[row][col]

    def set_color(self, row: int, col: int, val: str) -> None:
        '''
        Sets a color for a row and column.
        '''
        self._cells[row][col] = val

    def clear_matching(self) -> None:
        '''
        Removes the matching blocks and then empties the list.
        '''
        for row, col in self._matching:
            self._cells[row][col] = BLANK
        self._matching = []

    def drop_field(self) -> None:
        '''
        Instantly drops all pieces in the field.
        '''
        for col in range(self._cols):
            dropped_column = self._get_dropped_column(col)
            for row in range(self._rows):
                self._cells[row][col] = dropped_column[row]

    def _get_dropped_column(self, col: int) -> [str]:
        '''
        Drops the jewels in a column and returns the dropped column.
        '''
        dropped_col = [self._cells[row][col] for row in range(
            self._rows) if self._cells[row][col] != BLANK]
        dropped_col = [BLANK]*(self._rows-len(dropped_col)) + dropped_col
        return dropped_col

    def locate_matching(self) -> None:
        '''
        Finds all matching jewels in all directions and then adds them to 
        the matching jewels list.
        '''
        for row in range(len(self._cells)):
            for col in range(len(self._cells[row])):
                if self._cells[row][col] != BLANK:
                    self._add_matching(row, col, 0, 1)
                    self._add_matching(row, col, 1, 0)
                    self._add_matching(row, col, 1, 1)
                    self._add_matching(row, col, 1, -1)

    def matching_contains_cell(self, row: int, col: int) -> bool:
        '''
        Checks if a cell is in the matching jewels.
        '''
        return (row, col) in self._matching

    def column_full(self, col: int) -> bool:
        '''
        Checks if a column is full.
        '''
        return all([self._cells[row][col] != BLANK for row in range(self._buffer_size, self._rows)])

    def empty_buffer(self) -> bool:
        '''
        Checks if the buffer is empty.
        '''
        for row in range(self._buffer_size):
            for col in range(self._cols):
                if self._cells[row][col] != BLANK:
                    return False
        return True

    def no_matching(self) -> bool:
        '''
        Checks if the matching jewels list is empty.
        '''
        return len(self._matching) == 0

    def empty_rows(self, col: int, rows: [int]) -> bool:
        '''
        Checks if a column is empty.
        '''
        return not col < 0 and not col > self._cols - 1 and all([self._cells[row][col] == BLANK for row in rows])

    def is_landed(self, row: int, col: int) -> bool:
        '''
        Checks if a cell has landed (on top of a jewel or the floor).
        '''
        return row == self._rows - 1 or self._cells[row + 1][col] != BLANK

    def freeze_faller(self, faller: Faller) -> None:
        '''
        Freezes a faller into place.
        '''
        for row in faller.rows():
            self._cells[row][faller.col()] = faller.get_color(row)

    def _add_matching(self, row: int, col: int, drow: int, dcol: int) -> None:
        '''
        Adds matching jewels in a particular vector to the matching jewels
        list.
        '''
        matching = []
        base_color = self._cells[row][col]
        while row >= BUFFER_SIZE and col >= 0 and row < self._rows and col < self._cols:
            if self._cells[row][col] == base_color:
                matching.append((row, col))
            else:
                break
            row += drow
            col += dcol
        if len(matching) >= MATCHING_LENGTH:
            for match in matching:
                if match not in self._matching:
                    self._matching.append(match)


class GameState:
    '''
    Stores the game state of the game.
    '''

    def __init__(self):
        self._faller = None
        self._field = None
        self._game_over = False

    def initialize_field(self, rows: int, cols: int) -> None:
        '''
        Initializes the field attribute given a number of rows and columns.
        '''
        self._field = Field(rows, cols, BUFFER_SIZE)

    def initialize_contents(self, contents: [[str]]) -> None:
        '''
        Initializes the contents of the field givena set of nested list
        of colors.
        '''
        for row in range(len(contents)):
            for col in range(len(contents[row])):
                self._field.set_color(row+BUFFER_SIZE, col, contents[row][col])
        self._update_matching()

    def rows(self) -> int:
        '''
        Returns the number of rows in the field.
        '''
        return self._field.rows()

    def cols(self) -> int:
        '''
        Returns the number of columns in the field.
        '''
        return self._field.cols()

    def buffer_size(self) -> int:
        '''
        Returns the size of the buffer in the field.
        '''
        return self._field.buffer_size()

    def matching(self) -> int:
        return self._field.matching()

    def no_faller(self) -> bool:
        return self._faller == None

    def get_type(self, row: int, col: int) -> int:
        '''
        Gets the type of cell from the field or faller.
        '''
        if self._faller and self._faller.contains_cell(row, col):
            if self._check_faller_landed():
                return LANDED
            else:
                return FALLER
        elif self._field.matching_contains_cell(row, col):
            return MATCHING
        elif self._field.get_color(row, col) == BLANK:
            return NONE
        else:
            return JEWEL

    def get(self, row: int, col: int) -> str:
        '''
        Gets the color of cell from the field or faller.
        '''
        if self._faller and self._faller.contains_cell(row, col):
            return self._faller.get_color(row)
        return self._field.get_color(row, col)

    def update(self) -> None:
        '''
        Updates the game state.
        '''

        if self._faller:
            if self._check_faller_landed():
                self._field.freeze_faller(self._faller)
                self._faller = None
            else:
                self._faller.drop()
        self._update_matching()
        if self._field.no_matching() and not self._field.empty_buffer():
            self._lose_game()

    def initialize_faller(self, col: int, colors: [str]) -> None:
        '''
        Creates a faller and assigns it, ends the game if not possible.
        '''
        if self._faller == None and self._field.no_matching():
            if self._field.column_full(col):
                self._lose_game()
            else:
                self._faller = Faller(
                    col, colors, FALLER_LENGTH)

    def rotate_faller(self) -> None:
        '''
        Rotates the faller if it exists.
        '''
        if self._faller != None and not self._game_over:
            self._faller.rotate()

    def move_faller(self, direction: int) -> None:
        '''
        Moves the faller left or right based on a direction.
        '''
        if self._faller and not self._game_over and self._field.empty_rows(self._faller.col()+direction, self._faller.rows()):
            self._faller.move(direction)

    def get_empty_cols(self) -> [int]:
        '''
        Gets the empty columns in the field.
        '''
        return [col for col in range(self._field.cols()) if not self._field.column_full(col)]

    def game_over(self) -> bool:
        '''
        Returns the game over state.
        '''
        return self._game_over

    def _check_faller_landed(self) -> bool:
        '''
        Checks if the faller has landed.
        '''
        return self._field.is_landed(self._faller.bottom(), self._faller.col())

    def _update_matching(self) -> None:
        '''
        Updates the matching jewels list. If buffer isn't empty after the 
        update, end the game.
        '''
        self._field.clear_matching()
        self._field.drop_field()
        self._field.locate_matching()

    def _lose_game(self) -> None:
        '''
        If the game is lost, end the game.
        '''
        self._game_over = True
