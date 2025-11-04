init 999 python:
    mas_enable_quit()

init python in mas_battleship:
    import random
    import pygame
    import math as meth
    import itertools
    from store import Image, Null, Transform, MASButtonDisplayable
    from collections import OrderedDict
    from renpy import config

    # a = mas_battleship.Battleship()
    # renpy.show("monika 3hub", at_list=[tcommon(220)]); ui.add(mas_battleship.Battleship()); ui.interact()
    # renpy.show("monika 1eua", at_list=[t31]); ui.add(mas_battleship.Battleship()); renpy.say(m, "<3")
    # a = mas_battleship.Battleship(); renpy.show("monika 1eua", at_list=[t31]); ui.add(a); renpy.say(m, "<3", False); ui.interact()

    class Battleship(renpy.display.core.Displayable):
        """
        """
        # Grid sprites
        # MAIN_GRID = Image("/mod_assets/games/battleship/grid.png")
        # TRACKING_GRID = Image("/mod_assets/games/battleship/grid.png")
        GRID_BASE = Image("/mod_assets/games/battleship/grid_base.png")
        GRID = Image("/mod_assets/games/battleship/grid.png")

        # Marks sprites
        HIT_MARK = Image("/mod_assets/games/battleship/hit_mark.png")
        MISS_MARK = Image("/mod_assets/games/battleship/miss_mark.png")

        # Ships sprites
        # TODO: sprites for broken/sunk ships?
        SHIP_5_SQUARES = Image("/mod_assets/games/battleship/ship_5_squares.png")
        SHIP_4_SQUARES = Image("/mod_assets/games/battleship/ship_4_squares.png")
        SHIP_3_SQUARES = Image("/mod_assets/games/battleship/ship_3_squares.png")
        SHIP_2_SQUARES = Image("/mod_assets/games/battleship/ship_2_squares.png")

        ALL_SHIP_SPRITES = (SHIP_5_SQUARES, SHIP_4_SQUARES, SHIP_3_SQUARES, SHIP_2_SQUARES)

        ALL_SHIPS_TYPES = (5, 4, 3, 2)

        SHIP_SET_CLASSIC = (5, 4, 4, 3, 3, 3, 2, 2, 2, 2)

        # Map between ship types and sprites
        # TODO: support multiple sprites for one ship type?
        SHIP_SPRITES_MAP = OrderedDict(zip(ALL_SHIPS_TYPES, ALL_SHIP_SPRITES))

        # Hovering mask
        CELL_HOVER = Image("/mod_assets/games/battleship/square_hover.png")
        # Error mask
        CELL_ERROR = Image("/mod_assets/games/battleship/square_error.png")

        # Size + coords constants
        GRID_HEIGHT = 378
        GRID_WIDTH = GRID_HEIGHT
        GRID_SPACING = 5

        CELL_HEIGHT = 32
        CELL_WIDTH = CELL_HEIGHT

        OUTER_FRAME_THICKNESS = 20
        INNER_GRID_THICKNESS = 2

        MAIN_GRID_ORIGIN_X = config.screen_width - 2 * (GRID_WIDTH + GRID_SPACING)
        MAIN_GRID_ORIGIN_Y = (config.screen_height - GRID_HEIGHT) // 2
        TRACKING_GRID_ORIGIN_X = config.screen_width - GRID_WIDTH - GRID_SPACING
        TRACKING_GRID_ORIGIN_Y = (config.screen_height - GRID_HEIGHT) // 2

        class GamePhase(object):
            """
            Types of Game phases consts
            TODO: turn this into enum
            """
            PREPARING = 0
            PLAYING = 1

        def __init__(self):
            """
            """
            super(Battleship, self).__init__()

            self._last_mouse_x = 0
            self._last_mouse_y = 0

            self._phase = self.GamePhase.PREPARING
            self._hovered_cell = None
            self._dragged_ship = None
            self._grid_conflicts = []

            self._ship_sprites_cache = {}

            self._ship_buttons = []
            self._build_ship_buttons()

            self._player = Player("Player", self.SHIP_SET_CLASSIC)
            self._monika = Player("Monika", self.SHIP_SET_CLASSIC)

            # _orientation = random.randint(0, 3)
            # _length = random.randint(2, 5)
            # _coords = self._player.grid.find_place_for_ship(_length, _orientation)
            # _ship = self._player.grid.build_ship(_coords[0], _coords[1], _length, _orientation)

            # self._player.grid.build_ships(self._player.ship_set)
            # self._player.misses_coords.append((0, 0))
            # self._player.misses_coords.append((0, 9))
            # self._player.misses_coords.append((9, 0))
            # self._player.misses_coords.append((9, 9))
            # self._monika.misses_coords.append((7, 7))
            # _coords = self._player.ships[0].health.keys()[1]
            # self._monika.hits_coords.append(_coords)

        def _build_ship_buttons(self):
            """
            Creates MASButtonDisplayable object and fill the list of buttons
            """
            text_disp = Null()
            for j, ship_length in enumerate(self.SHIP_SPRITES_MAP.iterkeys()):
                ship = Ship.build_ship(0, 0, ship_length, Ship.Orientation.UP)
                ship_sprite = self._get_ship_sprite(ship)
                x = self.TRACKING_GRID_ORIGIN_X + j * (self.CELL_WIDTH + self.GRID_SPACING)# TODO: Separate const for this
                y = self.TRACKING_GRID_ORIGIN_Y

                ship_button = MASButtonDisplayable(
                    text_disp,
                    text_disp,
                    text_disp,
                    ship_sprite,
                    ship_sprite,
                    ship_sprite,# TODO: greyed out sprite for this, maybe via an im?
                    x,
                    y,
                    self.CELL_WIDTH,
                    self.CELL_HEIGHT * ship_length + self.INNER_GRID_THICKNESS * (ship_length - 1),
                    return_value=ship,
                )
                ship_button._button_down = pygame.MOUSEBUTTONDOWN
                self._ship_buttons.append(ship_button)

        @classmethod
        def _grid_coords_to_screen_coords(cls, x, y, grid_origin_x, grid_origin_y):
            """
            Converts grid coordinates into screen coordinates

            IN:
                x - row of the grid
                y - column of the grid
                grid_origin_x - screen x coord of the grid origin
                grid_origin_y - screen y coord of the grid origin

            OUT:
                tuple with coords
            """
            return (
                grid_origin_x + cls.OUTER_FRAME_THICKNESS + x * (cls.INNER_GRID_THICKNESS + cls.CELL_WIDTH),
                grid_origin_y + cls.OUTER_FRAME_THICKNESS + y * (cls.INNER_GRID_THICKNESS + cls.CELL_HEIGHT),
            )

        @classmethod
        def _screen_coords_to_grid_coords(cls, x, y, grid_origin_x, grid_origin_y):
            """
            Converts screen coordinates into grid coordinates

            IN:
                x - x coord
                y - y coord
                grid_origin_x - screen x coord of the grid origin
                grid_origin_y - screen y coord of the grid origin

            OUT:
                tuple with coords,
                or None if the given coords are outside the grid
            """
            # First check if we're within this grid
            if not (
                grid_origin_x + cls.OUTER_FRAME_THICKNESS <= x <= grid_origin_x + cls.GRID_WIDTH - cls.OUTER_FRAME_THICKNESS
                and grid_origin_y + cls.OUTER_FRAME_THICKNESS <= y <= grid_origin_y + cls.GRID_HEIGHT - cls.OUTER_FRAME_THICKNESS
            ):
                return None

            return (
                int((x - grid_origin_x - cls.OUTER_FRAME_THICKNESS - (int(x - grid_origin_x - cls.OUTER_FRAME_THICKNESS) / cls.CELL_WIDTH) * cls.INNER_GRID_THICKNESS) / cls.CELL_WIDTH),
                int((y - grid_origin_y - cls.OUTER_FRAME_THICKNESS - (int(y - grid_origin_y - cls.OUTER_FRAME_THICKNESS) / cls.CELL_HEIGHT) * cls.INNER_GRID_THICKNESS) / cls.CELL_HEIGHT),
            )

        def _get_ship_sprite(self, ship):
            """
            Returns a sprite for a ship using cache system (generates if needed, retrives if already generated)

            IN:
                ship - ship to get sprite for

            OUT:
                sprite (a Transform obj)
            """
            # NOTE: Sprites are headed up, but in our system 0 degrees is right, NOT up
            # so we need to adjust the angle to avoid rotation
            angle = ship.orientation - Ship.Orientation.UP
            sprite = self.SHIP_SPRITES_MAP[ship.length]
            key = (ship.length, ship.orientation)

            if key not in self._ship_sprites_cache:
                self._ship_sprites_cache[key] = Transform(
                    child=sprite,
                    xanchor=0.5,
                    yanchor=16,
                    offset=(16, 16),
                    transform_anchor=True,
                    rotate_pad=False,
                    subpixel=True,
                    rotate=angle,
                )

            return self._ship_sprites_cache[key]

        def render(self, width, height, st, at):
            """
            Render method for this disp
            """
            # Define our main render
            main_render = renpy.Render(width, height)

            # # # Render grids
            # Predefine renders
            grid_base_render = renpy.render(self.GRID_BASE, width, height, st, at)
            grid_render = renpy.render(self.GRID, width, height, st, at)
            # Now blit 'em
            main_render.blit(grid_base_render, (self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y))
            main_render.blit(grid_render, (self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y))
            # Render Monika's grid only during the game phase
            if self._phase == self.GamePhase.PLAYING:
                # tracking_grid_render = renpy.render(self.TRACKING_GRID, width, height, st, at)
                # main_render.blit(tracking_grid_render, (self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y))
                main_render.blit(grid_base_render, (self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y))
                main_render.blit(grid_render, (self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y))

            # Render conflicts
            if self._phase == self.GamePhase.PREPARING:
                if self._grid_conflicts:
                    error_mask_render = renpy.render(self.CELL_ERROR, width, height, st, at)
                    for coords in self._grid_conflicts:
                        x, y = self._grid_coords_to_screen_coords(coords[0], coords[1], self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y)
                        main_render.blit(error_mask_render, (x, y))

            # Render player's ships
            for ship in self._player.grid.iter_ships():
                ship_sprite = self._get_ship_sprite(ship)
                x, y = self._grid_coords_to_screen_coords(ship.bow_coords[0], ship.bow_coords[1], self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y)
                main_render.place(ship_sprite, x, y)

            # # # Render things that only relevant during the game
            if self._phase == self.GamePhase.PLAYING:
                # Render Monika's ships
                for ship in self._monika.grid.iter_ships():
                    if not ship.is_alive:
                        ship_sprite = self._get_ship_sprite(ship)
                        x, y = self._grid_coords_to_screen_coords(ship.bow_coords[0], ship.bow_coords[1], self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y)
                        main_render.place(ship_sprite, x, y)

                # Render hits
                hit_mark_render = renpy.render(self.HIT_MARK, width, height, st, at)
                for coords in self._player.hits_coords:
                    x, y = self._grid_coords_to_screen_coords(coords[0], coords[1], self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y)
                    main_render.blit(hit_mark_render, (x, y))

                for coords in self._monika.hits_coords:
                    x, y = self._grid_coords_to_screen_coords(coords[0], coords[1], self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y)
                    main_render.blit(hit_mark_render, (x, y))

                # Render misses
                miss_mark_render = renpy.render(self.MISS_MARK, width, height, st, at)
                for coords in self._player.misses_coords:
                    x, y = self._grid_coords_to_screen_coords(coords[0], coords[1], self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y)
                    main_render.blit(miss_mark_render, (x, y))

                for coords in self._monika.misses_coords:
                    x, y = self._grid_coords_to_screen_coords(coords[0], coords[1], self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y)
                    main_render.blit(miss_mark_render, (x, y))

                # Render hovering mask
                if self._hovered_cell is not None:
                    hover_mask_render = renpy.render(self.CELL_HOVER, width, height, st, at)
                    x, y = self._grid_coords_to_screen_coords(self._hovered_cell[0], self._hovered_cell[1], self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y)
                    main_render.blit(hover_mask_render, (x, y))

            # # # Render things that only relevant during ship building
            elif self._phase == self.GamePhase.PREPARING:
                # Render ship buttons
                for ship_button in self._ship_buttons:
                    sb_render = renpy.render(ship_button, width, height, st, at)
                    main_render.blit(sb_render, (ship_button.xpos, ship_button.ypos))

                # Render the ship that's currently dragged (if any)
                if self._dragged_ship is not None:
                    ship_sprite = self._get_ship_sprite(self._dragged_ship)
                    if Ship.Orientation.is_vertical(self._dragged_ship.orientation):
                        x_offset = 0
                        y_offset = self._dragged_ship.get_drag_offset_from_bow() * self.CELL_HEIGHT

                    else:
                        x_offset = self._dragged_ship.get_drag_offset_from_bow() * self.CELL_WIDTH
                        y_offset = 0

                    main_render.place(
                        ship_sprite,
                        (self._last_mouse_x - self.CELL_WIDTH / 2 + x_offset),
                        (self._last_mouse_y - self.CELL_HEIGHT / 2 + y_offset)
                    )

            return main_render

        # def per_interact(self):
        #     """
        #     Request redraw on each interaction
        #     """
        #     return

        def _handle_ship_buttons_events(self, ev, x, y, st):
            """
            Checks if the player pressed one of the ship building buttons
            """
            for ship_button in self._ship_buttons:
                ship = ship_button.event(ev, x, y, st)
                if ship is not None:
                    drag_point = (y - self.TRACKING_GRID_ORIGIN_Y) / (self.CELL_HEIGHT + self.INNER_GRID_THICKNESS)
                    self._dragged_ship = ship.copy()
                    self._dragged_ship.drag_coords = (0, drag_point)
                    return True
            return False

        def _handle_preparing_events(self, ev, x, y, st):
            # # # Check if the player wants to build a ship
            if self._handle_ship_buttons_events(ev, x, y, st):
                # We handle buttons' events in the method above
                renpy.redraw(self, 0)

            # # # The player pressed the rotation key
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                # If the player's dragging a ship, rotate it
                if self._dragged_ship is not None:
                    if ev.mod in (pygame.KMOD_LSHIFT, pygame.KMOD_RSHIFT):
                        self._dragged_ship.orientation -= 90
                    else:
                        self._dragged_ship.orientation += 90

                    self._grid_conflicts[:] = self._player.grid.get_conflicts()
                    renpy.redraw(self, 0)

                # If the player's pressed the keybinding for rotating while hovering over a ship, rotate it
                else:
                    coords = self._screen_coords_to_grid_coords(x, y, self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y)
                    if coords is None:
                        return

                    ship = self._player.grid.get_ship_at(coords[0], coords[1])
                    if ship is None:
                        return

                    if ev.mod in (pygame.KMOD_LSHIFT, pygame.KMOD_RSHIFT):
                        angle = -90
                    else:
                        angle = 90

                    self._player.grid.remove_ship(ship)
                    ship.rotate(angle, coords[0], coords[1])
                    self._player.grid.place_ship(ship)
                    self._grid_conflicts[:] = self._player.grid.get_conflicts()

                    renpy.redraw(self, 0)

            # # # The player moves the mouse, we may need to update the screen
            elif ev.type == pygame.MOUSEMOTION:
                # Continue to update the screen while the player's dragging a ship
                if self._dragged_ship is not None:
                    renpy.redraw(self, 0)

            # # # The player clicks on a ship and starts dragging it
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                coords = self._screen_coords_to_grid_coords(x, y, self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y)
                if coords is None:
                    return

                ship = self._player.grid.get_ship_at(coords[0], coords[1])
                if ship is None:
                    return

                self._player.grid.remove_ship(ship)
                self._grid_conflicts[:] = self._player.grid.get_conflicts()
                ship.drag_coords = coords
                self._dragged_ship = ship

                renpy.redraw(self, 0)

            # # # The player releases the mouse button and places the ship on the grid
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if self._dragged_ship is None:
                    return

                coords = self._screen_coords_to_grid_coords(x, y, self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y)
                if coords is not None:
                    # Let's get dragging offsets
                    if Ship.Orientation.is_vertical(self._dragged_ship.orientation):
                        x_offset = 0
                        y_offset = self._dragged_ship.get_drag_offset_from_bow()

                    else:
                        x_offset = self._dragged_ship.get_drag_offset_from_bow()
                        y_offset = 0

                    # Repack the tuple appying the offsets
                    coords = (coords[0] + x_offset, coords[1] + y_offset)
                    # Set new coords for the ship
                    self._dragged_ship.bow_coords = coords
                    # Reset drag point
                    self._dragged_ship.drag_coords = coords
                    # Finally place it
                    self._player.grid.place_ship(self._dragged_ship)
                    # Check for invalid placement
                    self._grid_conflicts[:] = self._player.grid.get_conflicts()

                # NOTE: set to None anyway if the player just wanted to remove the ship
                self._dragged_ship = None
                renpy.redraw(self, 0)

        def _handle_playing_events(self, ev, x, y, st):
            # # # The player moves the mouse, we may need to update the screen
            if ev.type == pygame.MOUSEMOTION:
                coords = self._screen_coords_to_grid_coords(x, y, self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y)

                # Ask to redraw if we either just started hover or stopped
                if (
                    coords is not None
                    or self._hovered_cell is not None
                ):
                    self._hovered_cell = coords
                    renpy.redraw(self, 0)

        def event(self, ev, x, y, st):
            """
            Event handler
            """
            # Update internal mouse coords
            self._last_mouse_x = x
            self._last_mouse_y = y

            if self._phase == self.GamePhase.PREPARING:
                self._handle_preparing_events(ev, x, y, st)

            elif self._phase == self.GamePhase.PLAYING:
                self._handle_playing_events(ev, x, y, st)

            # raise renpy.IgnoreEvent()
            return

    class Grid(object):
        """
        Represents a field/screen for battleship placement
        """
        HEIGHT = 10
        WIDTH = HEIGHT

        class CellState(object):
            """
            Types of grid cell consts
            TODO: turn this into enum
            """
            EMPTY = 0
            SHIP = 1
            SPACING = 2
            CONFLICT = 3

            @classmethod
            def get_all(cls):
                return (cls.EMPTY, cls.SHIP, cls.SPACING, cls.CONFLICT)

        def __init__(self):
            """
            Constructor
            """
            # Coordinates: cell state
            self._cell_states = {
                (col, row): self.CellState.EMPTY
                for row in range(self.HEIGHT)
                for col in range(self.WIDTH)
            }
            # Coordinates: ships
            self._ships_grid = {coords: [] for coords in self._cell_states.iterkeys()}
            # All ships on the grid
            self._ships = []

        @property
        def total_ships(self):
            return len(self._ships)

        def iter_ships(self):
            """
            Returns an iterator over the ships on this grid
            """
            return iter(self._ships)

        def clear(self, clear_grid=True, clear_map=True):
            """
            Clears this grid
            """
            if clear_grid:
                for coords in self._cell_states:
                    self._cell_states[coords] = self.CellState.EMPTY

            if clear_map:
                for ships in self._ships_grid.itervalues():
                    ships[:] = []

                # If we clear the map, we must clear the main list too
                self._ships[:] = []

        def _is_within(self, x, y):
            """
            Returns whether or not the coordinates are within the grid

            IN:
                x - x coord
                y - y coord

            OUT:
                bool
            """
            return (0 <= x < self.WIDTH) and (0 <= y < self.HEIGHT)

        def _get_cell_at(self, x, y):
            """
            Returns the state of a cell

            IN:
                x - x coord
                y - y coord

            OUT:
                int as one of states,
                or None if the given coordinates are out of this grid
            """
            return self._cell_states.get((x, y), None)

        def _is_empty_at(self, x, y):
            """
            Checks if the cell at the given coordinates is empty
            (has no ship nor is spacing for a ship)

            IN:
                x - x coord
                y - y coord

            OUT:
                boolean: True if free, False otherwise
            """
            return self._get_cell_at(x, y) == self.CellState.EMPTY

        def _is_empty_or_spacing_at(self, x, y):
            """
            Checks if the cell at the given coordinates has no ship

            IN:
                x - x coord
                y - y coord

            OUT:
                boolean: True if free, False otherwise
            """
            state = self._get_cell_at(x, y)
            return state == self.CellState.EMPTY or state == self.CellState.SPACING

        def _set_cell_at(self, x, y, value):
            """
            Set a cell to a new state
            This will do nothing if the given coords are outside of this grid

            IN:
                x - x coord
                y - y coord
                value - new state for the cell
            """
            coords = (x, y)
            if (
                coords not in self._cell_states
                or value not in self.CellState.get_all()
            ):
                return

            self._cell_states[coords] = value

        def get_ship_at(self, x, y):
            """
            Returns a ship at the given coordinates

            NOTE: If for some reason we have more than one ship in the cell,
                this will return the one that was added last

            IN:
                x - x coord
                y - y coord

            OUT:
                Ship object or None if nothing found
            """
            ships = self._ships_grid.get((x, y), None)
            if ships:
                return ships[-1]

            return None

        def get_conflicts(self):
            """
            Returns a list of coordinates of ships that were placed incorrectly

            OUT:
                list with coordinates
            """
            return [
                coords
                for coords, cell_state in self._cell_states.iteritems()
                if cell_state == self.CellState.CONFLICT
            ]

        def update(self):
            """
            Goes through this grid and sets its cells again
            """
            self.clear(clear_map=False)

            for ship in self._ships:
                self.place_ship(ship, add_to_map=False)

        def remove_ship(self, ship):
            """
            Removes a ship from this grid

            IN:
                ship - ship to remove
            """
            for ships in self._ships_grid.itervalues():
                if ship in ships:
                    ships.remove(ship)

            if ship in self._ships:
                self._ships.remove(ship)

            self.update()

        def is_valid_place_for_ship(self, x, y, ship):
            """
            Checks if a ship can be placed at coordinates

            IN:
                x - x coord for the ship bow
                y - y coord for the ship bow
                ship - ship

            OUT:
                boolean: True if the place if valid, False otherwise
            """
            ship_length = ship.length
            ship_orientation = ship.orientation

            if ship_orientation == Ship.Orientation.UP:
                x_coords = itertools.repeat(x, ship_length)
                y_coords = range(y, y + ship_length)

            elif ship_orientation == Ship.Orientation.RIGHT:
                x_coords = range(x, x - ship_length, -1)
                y_coords = itertools.repeat(y, ship_length)

            elif ship_orientation == Ship.Orientation.DOWN:
                x_coords = itertools.repeat(x, ship_length)
                y_coords = range(y, y - ship_length, -1)

            else:
                x_coords = range(x, x + ship_length)
                y_coords = itertools.repeat(y, ship_length)

            for _x, _y in zip(x_coords, y_coords):
                if not self._is_empty_at(_x, _y):
                    return False

            return True

        def find_place_for_ship(self, ship):
            """
            Tries to find a place for a ship

            IN:
                ship - ship

            OUT:
                tuple with the coordinates for the bow of this ship,
                or None if no free place found
            """
            ship_length = ship.length
            ship_orientation = ship.orientation
            # List with all free lines where we could place this ship on
            available_positions = []

            should_swap_coords = False
            if ship_orientation == Ship.Orientation.UP:
                columns = range(self.WIDTH)
                rows = range(self.HEIGHT)

            elif ship_orientation == Ship.Orientation.RIGHT:
                columns = range(self.WIDTH)
                rows = range(self.HEIGHT, 0, -1)
                should_swap_coords = True

            elif ship_orientation == Ship.Orientation.DOWN:
                columns = range(self.WIDTH)
                rows = range(self.HEIGHT, 0, -1)

            else:
                columns = range(self.WIDTH)
                rows = range(self.HEIGHT)
                should_swap_coords = True

            for col in columns:
                # List of tuples with coords
                line = []
                for row in rows:
                    if should_swap_coords:
                        x = row
                        y = col

                    else:
                        x = col
                        y = row

                    # If this square is free, add it to the line
                    if self._is_empty_at(x, y):
                        line.append((x, y))

                    # Otherwise we got all free squares we could
                    else:
                        # See if we can fit our ship in this line
                        if len(line) >= ship_length:
                            available_positions.append(line)
                        # Reset the list before continuing iterating
                        line = []

                # Reached the end of this col, append this line if it fits
                if len(line) >= ship_length:
                    available_positions.append(line)

            # Return None if we couldn't find a place for this ship
            if not available_positions:
                return None

            # Now choose the one that we'll use
            line = random.choice(available_positions)
            coords = line[random.randint(0, len(line) - ship_length)]

            return coords

        def place_ship(self, ship, add_to_map=True):
            """
            Places a ship at the coordinates of its bow,
            sets the appropriate state for the cells under the ship and adds
            the ship to the ship map

            NOTE: this makes no checks whether or not we can place the ship on the given pos

            IN:
                ship - ship to place
                add_to_map - whether we add this ship to the ship map or we do not
                    (Default: True)
            """
            ship_cells, spacing_cells = ship.get_cells()

            is_ship_within_grid = True
            for cell in ship_cells:
                # We have to iterate twice, if at least one cell is out of bounds,
                # we want to mark all of them as conflict, so the player knows something is wrong
                if not self._is_within(cell[0], cell[1]):
                    is_ship_within_grid = False
                    break

            for cell in ship_cells:
                if is_ship_within_grid and self._is_empty_at(cell[0], cell[1]):
                    cell_state = self.CellState.SHIP
                else:
                    cell_state = self.CellState.CONFLICT

                self._set_cell_at(cell[0], cell[1], cell_state)

                if add_to_map:
                    # If the ship was placed incorrectly, then its coords may be out of this grid
                    if cell in self._ships_grid:
                        self._ships_grid[cell].append(ship)

            for cell in spacing_cells:
                if self._is_empty_or_spacing_at(cell[0], cell[1]):
                    cell_state = self.CellState.SPACING

                else:
                    cell_state = self.CellState.CONFLICT

                self._set_cell_at(cell[0], cell[1], cell_state)

            if add_to_map:
                # Also add to the main list
                self._ships.append(ship)

        def place_ships(self, ships):
            """
            Places ships on this grid at random position

            NOTE: This does respect ship placement

            IN:
                ships - list of Ship objects
            """
            while True:
                for ship in ships:
                    coords = self.find_place_for_ship(ship)

                    # If we got appropriate coords, place the ship
                    if coords is not None:
                        ship.bow_coords = coords
                        self.place_ship(ship)

                    # Otherwise try another orientation
                    else:
                        if Ship.Orientation.is_vertical(ship.orientation):
                            rest_orientations = (Ship.Orientation.RIGHT, Ship.Orientation.LEFT)

                        else:
                            rest_orientations = (Ship.Orientation.UP, Ship.Orientation.DOWN)

                        ship.orientation = random.choice(rest_orientations)
                        coords = self.find_place_for_ship(ship)

                        # Try with the new coords
                        if coords is not None:
                            ship.bow_coords = coords
                            self.place_ship(ship)

                        # Otherwise start from the beginning
                        else:
                            self.clear()
                            break

                # If we haven't interrupted the inner loop, then we're done
                else:
                    return

    class Ship(object):
        """
        TODO: make this a displayable
        """
        class Orientation(object):
            """
            Orientation consts
            TODO: turn this into enum
            """
            UP = 270# 0
            RIGHT = 0# 90
            DOWN = 90# 180
            LEFT = 180# 270

            @classmethod
            def get_all(cls):
                return (cls.UP, cls.RIGHT, cls.DOWN, cls.LEFT)

            @classmethod
            def is_vertical(cls, value):
                return value in (cls.UP, cls.DOWN)

            @classmethod
            def is_horizontal(cls, value):
                return value in (cls.RIGHT, cls.LEFT)

        def __init__(self, x, y, length, orientation):
            """
            """
            self.bow_coords = (x, y)
            self._length = length
            self._orientation = orientation

            self._health = length
            self.drag_coords = self.bow_coords

        @property
        def is_alive(self):
            return self._health > 0

        @staticmethod
        def _apply_rotation_matrix(x, y, cos, sin, origin_x, origin_y, is_positive):
            """
            Rotates a point, using rotation matrix

            IN:
                x - x coordinate
                y - y coordinate
                cos - rotation angle cosine
                sin - rotation angle sine
                origin_x - x coordinate of the point to rotate around
                origin_y - y coordinate of the point to rotate around
                is_positive - whether or not the rotation angle is positive
            """
            factor = 1 if is_positive else -1
            new_x = origin_x + (x - origin_x) * cos - factor * (y - origin_y) * sin
            new_y = origin_y + (y - origin_y) * cos + factor * (x - origin_x) * sin

            return (new_x, new_y)

        @classmethod
        def _rotate_point(cls, x, y, angle, origin_x, origin_y):
            """
            Rotates a point, using rotation matrix

            IN:
                x - x coordinate
                y - y coordinate
                angle - rotation angle
                origin_x - x coordinate of the point to rotate around
                origin_y - y coordinate of the point to rotate around
            """
            # Get the rotation direction
            is_positive = angle >= 0
            angle = meth.radians(angle)
            # Get cos and sin, we're using 90 degrees rotation and thus can safely floor them
            cos = int(meth.cos(angle))
            sin = int(meth.sin(angle))
            # Rotate
            return cls._apply_rotation_matrix(
                x=x,
                y=y,
                cos=cos,
                sin=sin,
                origin_x=origin_x,
                origin_y=origin_y,
                is_positive=is_positive,
            )

        def _rotate(self, angle, origin_x, origin_y):
            """
            Rotates this ship's bow around the given origin
            NOTE: this doesn't update the orientation and drag_point props, assuming these'll be set afterwards

            IN:
                angle - angle to rotate by
                    NOTE: in degrees
                    NOTE: assumes it was sanitized to be between 0-270
                origin_x - origin x to rotate around
                origin_y - origin y to rotate around
            """
            if self.bow_coords == (origin_x, origin_y):
                # Don't rotate around itself
                return

            self.bow_coords = self._rotate_point(
                x=self.bow_coords[0],
                y=self.bow_coords[1],
                angle=angle,
                origin_x=origin_x,
                origin_y=origin_y,
            )

        def rotate(self, angle, origin_x, origin_y):
            """
            Public method for rotating this ship

            IN:
                angle - angle to rotate by
                    NOTE: in degrees
                origin_x - origin x to rotate around
                origin_y - origin y to rotate around
            """
            angle %= 360
            # Sanity check
            if angle == 0 or angle % 90 != 0:
                return

            self._rotate(angle, origin_x, origin_y)
            self._orientation += angle
            self._orientation %= 360

        @property
        def length(self):
            """
            Prop getter for length
            """
            return self._length

        @property
        def orientation(self):
            """
            Prop getter for orientation
            """
            return self._orientation

        @orientation.setter
        def orientation(self, value):
            """
            Prop setter for orientation
            NOTE: this assumes that we rotate the ship around its bow
            NOTE: allowed angles are 0, 90, 180, and 270
            """
            value %= 360

            if (
                value == self._orientation
                or value % 90 != 0
            ):
                return

            self._orientation = value

        def get_drag_offset_from_bow(self):
            """
            Returns offset from where the player drags the ship to its bow
            TODO: Consider caching this value
            """
            offset =  int(meth.sqrt(
                meth.pow(self.bow_coords[0]-self.drag_coords[0], 2)
                + meth.pow(self.bow_coords[1]-self.drag_coords[1], 2)
            ))
            # Check if we need to invert it
            if self.orientation in (self.Orientation.LEFT, self.Orientation.UP):
                offset *= -1
            return offset

        def get_cells(self):
            """
            Returns cells occupied by this ship

            OUT:
                tuple of 2 lists: first list is the ship cells, second list os the spacing cells
            """
            base_x = self.bow_coords[0]
            base_y = self.bow_coords[1]
            length = self._length

            ship = []
            spacing = []

            if self._orientation == self.Orientation.UP:
                ship_xs = itertools.repeat(base_x, length)
                ship_ys = range(base_y, base_y+length)
                ship.extend(zip(ship_xs, ship_ys))

                for y in (base_y - 1, base_y + length):
                    for x in range(base_x - 1, base_x + 2):
                        spacing.append((x, y))

                for i in range(length):
                    y = base_y + i
                    spacing.append((base_x - 1, y))
                    spacing.append((base_x + 1, y))

            elif self._orientation == self.Orientation.RIGHT:
                ship_xs = range(base_x, base_x-length, -1)
                ship_ys = itertools.repeat(base_y, length)
                ship.extend(zip(ship_xs, ship_ys))

                for x in (base_x - length, base_x + 1):
                    for y in range(base_y - 1, base_y + 2):
                        spacing.append((x, y))

                for i in range(length):
                    x = base_x - i
                    spacing.append((x, base_y - 1))
                    spacing.append((x, base_y + 1))

            elif self._orientation == self.Orientation.DOWN:
                ship_xs = itertools.repeat(base_x, length)
                ship_ys = range(base_y, base_y-length, -1)
                ship.extend(zip(ship_xs, ship_ys))

                for y in (base_y + 1, base_y - length):
                    for x in range(base_x - 1, base_x + 2):
                        spacing.append((x, y))

                for i in range(length):
                    y = base_y - i
                    spacing.append((base_x - 1, y))
                    spacing.append((base_x + 1, y))

            else:
                ship_xs = range(base_x, base_x+length)
                ship_ys = itertools.repeat(base_y, length)
                ship.extend(zip(ship_xs, ship_ys))

                for x in (base_x - 1, base_x + length):
                    for y in range(base_y - 1, base_y + 2):
                        spacing.append((x, y))

                for i in range(length):
                    x = base_x + i
                    spacing.append((x, base_y - 1))
                    spacing.append((x, base_y + 1))

            return (ship, spacing)

        def copy(self):
            """
            Returns a copy of this ship

            OUT:
                new Ship objects with the same params as this one
            """
            ship = Ship(self.bow_coords[0], self.bow_coords[1], self._length, self._orientation)

            ship._health = self._health
            ship.drag_coords = self.drag_coords

            return ship

        @classmethod
        def build_ship(cls, x, y, length, orientation=None):
            """
            Builds a ship

            IN:
                x - x coord for the ship bow
                y - y coord for the ship bow
                length - ship length
                orientation - ship orientation, if None, it will be chosen at random
                    (Default: None)

            OUT:
                Ship object
            """
            if orientation is None:
                orientation = random.choice(cls.Orientation.get_all())

            return cls(x, y, length, orientation)

        @classmethod
        def build_ships(cls, ship_set):
            """
            Builds multiple ships using the given set

            IN:
                ship_set - list of ship types

            OUT:
                list of Ship objects
            """
            return [cls.build_ship(0, 0, ship_type) for ship_type in ship_set]

    class Player(object):
        """
        """
        def __init__(self, id, ship_set):
            """
            Constructor
            """
            self.id = id
            self.ship_set = ship_set
            self.grid = Grid()

            self.hits_coords = []
            self.misses_coords = []

    class AIPlayer(Player):
        """
        """
        def __init__(self, id, ship_set):
            """
            Constructor for AI player
            """
            super(AIPlayer, self).__init__(id, ship_set)
            # Add params as needed

        def play_turn(self):
            """
            AI plays turn
            """
            return
