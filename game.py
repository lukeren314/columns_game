# game.py
# The pygame implementation of the Columns game.
import random
import math
import pygame
import columns_model

ROWS = 13
COLUMNS = 6
DEFAULT_SIZE = (720, 720)
MARGIN_SIZE = 0.05
DEFAULT_SPEED = 15
ACCELERATION_SPEED = 0.2

FONT_SIZE = 0.025
FONT_COLOR = pygame.Color(0, 0, 0)

BORDER_SIZE = 0.0025
BORDER_COLOR = pygame.Color(0, 0, 0)
EMPTY_COLOR = pygame.Color(84, 84, 84)
MATCHING_COLOR = pygame.Color(168, 168, 168)
BACKGROUND_COLOR = pygame.Color(255, 255, 255)
COLORS = {"A": pygame.Color(255, 0, 0),
          "B": pygame.Color(255, 153, 0),
          "C": pygame.Color(255, 255, 0),
          "D": pygame.Color(0, 255, 0),
          "E": pygame.Color(0, 0, 255),
          "F": pygame.Color(75, 0, 130),
          "G": pygame.Color(238, 130, 238)}


class ColumnsGame:
    '''
    Controls the view and input of the game.
    '''

    def __init__(self):
        self._started = False
        self._running = True

        self._frame = 0
        self._score = 0
        self._high_score = 0
        self._next_colors = []

    def run(self) -> None:
        '''
        Runs the program.
        '''
        self._setup()
        try:
            while self._running:
                self._update()
        finally:
            self._clean_up()

    def _setup(self) -> None:
        '''
        Sets up the game state and necessary pygame features.
        '''
        self._initialize_state()

        pygame.init()
        pygame.display.set_caption("COLUMNS!")
        self._set_surface(DEFAULT_SIZE)
        self._clock = pygame.time.Clock()

    def _initialize_state(self) -> None:
        '''
        Creates the game state and initializes the field.
        '''
        self._state = columns_model.GameState()
        self._state.initialize_field(ROWS, COLUMNS)

    def _set_surface(self, size: (int, int)) -> None:
        '''
        Resets the screen surface and font size.
        '''
        pygame.display.set_mode(size, pygame.RESIZABLE)
        self._font = pygame.font.Font(
            pygame.font.get_default_font(), int(size[1]*FONT_SIZE))

    def _update(self) -> None:
        '''
        Updates the game by waiting time, handling events, and
        redrawing the screen.
        '''
        self._clock.tick(30)
        self._handle_events()
        self._redraw()

    def _clean_up(self) -> None:
        '''
        Cleans everything up.
        '''
        pygame.quit()

    def _create_faller(self) -> None:
        '''
        Creates a faller if there is a column empty, or ends the game.
        '''
        empty_cols = self._state.get_empty_cols()
        if len(empty_cols) == 0:
            self._lose_game()
        else:
            self._state.initialize_faller(
                random.choice(empty_cols), self._next_colors)
            self._queue_next_faller()

    def _queue_next_faller(self) -> None:
        '''
        Sets up the colors for the next faller.
        '''
        self._next_colors = [random.choice(
            list(COLORS.keys())) for color in range(columns_model.FALLER_LENGTH)]

    def _handle_events(self) -> None:
        '''
        Handles the different events and updates the state.
        '''
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._close_game()
            elif event.type == pygame.VIDEORESIZE:
                self._set_surface(event.size)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT and self._started:
                    self._state.move_faller(columns_model.LEFT)
                elif event.key == pygame.K_RIGHT and self._started:
                    self._state.move_faller(columns_model.RIGHT)
                elif event.key == pygame.K_SPACE:
                    if not self._started:
                        self._new_game()
                    else:
                        self._state.rotate_faller()
                elif event.key == pygame.K_DOWN and self._started:
                    self._update_state()
                elif event.key == pygame.K_r and self._started:
                    self._new_game()
        if self._started:
            self._frame += 1
            if self._frame >= max(2, DEFAULT_SPEED/math.log(self._score*ACCELERATION_SPEED + 3)):
                self._update_state()
                self._frame = 0
        if self._state.game_over():
            self._lose_game()

    def _update_state(self) -> None:
        '''
        Updates the state and score, creates a faller if there is none.
        '''
        self._state.update()
        self._score += len(self._state.matching())
        if self._state.no_faller() and len(self._state.matching()) == 0:
            self._create_faller()

    def _new_game(self) -> None:
        '''
        Starts a new game by resetting the parameters.
        '''
        self._initialize_state()
        self._queue_next_faller()
        self._frame = 0
        self._score = 0
        self._started = True

    def _redraw(self) -> None:
        '''
        Redraws the surface, including the field and menu.
        '''
        surface = pygame.display.get_surface()
        surface.fill(BACKGROUND_COLOR)
        self._draw_field()
        self._draw_menu()
        pygame.display.update()

    def _draw_field(self) -> None:
        '''
        Draws every cell in the field.
        '''
        for row in range(columns_model.BUFFER_SIZE, self._state.rows()):
            for col in range(self._state.cols()):
                self._draw_cell(row, col)

    def _draw_cell(self, row: int, col: int) -> None:
        '''
        Draws a cell based on its type.
        '''
        cell_type = self._state.get_type(row, col)
        rect = self._get_cell_rect(row-columns_model.BUFFER_SIZE, col)
        if cell_type == columns_model.NONE:
            self._draw_bordered_rect(rect, EMPTY_COLOR)
        elif cell_type == columns_model.JEWEL:
            self._draw_bordered_rect(rect, self._get_color(row, col))
        elif cell_type == columns_model.FALLER:
            self._draw_rect(rect, EMPTY_COLOR)
            self._draw_ellipse(rect, self._get_color(row, col))
        elif cell_type == columns_model.LANDED:
            self._draw_rect(rect, self._get_color(row, col))
        elif cell_type == columns_model.MATCHING:
            self._draw_rect(rect, MATCHING_COLOR)

    def _get_color(self, row: int, col: int) -> None:
        return COLORS[self._state.get(row, col)]

    def _get_cell_rect(self, row: int, col: int) -> None:
        topleft_x, topleft_y = (MARGIN_SIZE, MARGIN_SIZE)
        cell_width, cell_height = self._get_cell_size()
        return self._scale_rectangle(topleft_x+cell_width*col, topleft_y+cell_height*row, cell_width, cell_height)

    def _get_cell_size(self) -> (float, float):
        field_width, field_height = 0.5-MARGIN_SIZE*2, 1-MARGIN_SIZE*2
        return (field_width/COLUMNS, field_height/ROWS)

    def _scale_rectangle(self, x: float, y: float, width: float, height: float) -> pygame.Rect:
        surface = pygame.display.get_surface()
        surface_width, surface_height = surface.get_size()
        return pygame.Rect(int(x*surface_width), int(y*surface_height), int(width*surface_width), int(height*surface_height))

    def _scale_position(self, x: float, y: float) -> (int, int):
        surface = pygame.display.get_surface()
        return (int(x*surface.get_width()), int(y*surface.get_height()))

    def _draw_bordered_rect(self, rect: pygame.Rect, color: pygame.Color) -> None:
        self._draw_rect(rect, color)
        surface = pygame.display.get_surface()
        pygame.draw.rect(surface, BORDER_COLOR, rect,
                         int(BORDER_SIZE*surface.get_width()))

    def _draw_rect(self, rect: pygame.Rect, color: pygame.Color) -> None:
        surface = pygame.display.get_surface()
        pygame.draw.rect(surface, color, rect)

    def _draw_ellipse(self, rect: pygame.Rect, color: pygame.Color) -> None:
        surface = pygame.display.get_surface()
        pygame.draw.ellipse(surface, color, rect)

    def _draw_menu(self) -> None:
        self._draw_text("COLUMNS!", self._scale_position(
            0.5+MARGIN_SIZE, MARGIN_SIZE))
        self._draw_text(f"SCORE: {self._score}", self._scale_position(
            0.5+MARGIN_SIZE, MARGIN_SIZE * 2))
        self._draw_text(f"HIGH SCORE: {self._high_score}", self._scale_position(
            0.5+MARGIN_SIZE, MARGIN_SIZE * 3))

        self._draw_text(
            "NEXT FALLER:", self._scale_position(0.5+MARGIN_SIZE, MARGIN_SIZE*4))
        cell_width, cell_height = self._get_cell_size()
        for i in range(len(self._next_colors)):
            self._draw_ellipse(self._scale_rectangle(
                0.5+MARGIN_SIZE, MARGIN_SIZE*5+cell_width*i, cell_width, cell_height), COLORS[self._next_colors[i]])

        self._draw_text(f"< and > to move", self._scale_position(
            0.5+MARGIN_SIZE, MARGIN_SIZE * 10))
        self._draw_text(f"Spacebar to rotate", self._scale_position(
            0.5+MARGIN_SIZE, MARGIN_SIZE * 11))
        self._draw_text(f"Down to speed up", self._scale_position(
            0.5+MARGIN_SIZE, MARGIN_SIZE * 12))
        self._draw_text(f"R to restart", self._scale_position(
            0.5+MARGIN_SIZE, MARGIN_SIZE * 13))

        if not self._started and not self._state.game_over():
            self._draw_text("Press spacebar to start",
                            self._scale_position(0.5+MARGIN_SIZE, MARGIN_SIZE * 15))
        elif self._state.game_over():
            self._draw_text(
                "GAME OVER", self._scale_position(0.5+MARGIN_SIZE, MARGIN_SIZE * 15))
            self._draw_text("Press spacebar to start again",
                            self._scale_position(0.5+MARGIN_SIZE, MARGIN_SIZE * 16))

    def _draw_text(self, text: str, position: (int, int)) -> None:
        surface = pygame.display.get_surface()
        text = self._font.render(text, True, FONT_COLOR)
        surface.blit(text, text.get_rect().move(position[0], position[1]))

    def _lose_game(self) -> None:
        self._started = False
        self._high_score = max(self._high_score, self._score)

    def _close_game(self) -> None:
        self._running = False


if __name__ == "__main__":
    ColumnsGame().run()
