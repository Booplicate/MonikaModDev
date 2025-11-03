
init python in mas_battleship:
    import random
    import pygame
    import math as meth
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
        # Sprites for animated water
        WATER_LAYER_0 = renpy.display.image.ImageReference(("water_d",))
        WATER_LAYER_1 = renpy.display.image.ImageReference(("water_t",))

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
        SQUARE_HOVER = Image("/mod_assets/games/battleship/square_hover.png")
        # Error mask
        SQUARE_ERROR = Image("/mod_assets/games/battleship/square_error.png")

        # Size + coords constants
        GRID_HEIGHT = 378
        GRID_WIDTH = GRID_HEIGHT
        GRID_SPACING = 5

        SQUARE_HEIGHT = 32
        SQUARE_WIDTH = SQUARE_HEIGHT

        OUTER_FRAME_THICKNESS = 20
        INNER_GRID_THICKNESS = 2

        MAIN_GRID_ORIGIN_X = config.screen_width - 2 * (GRID_WIDTH + GRID_SPACING)
        MAIN_GRID_ORIGIN_Y = (config.screen_height - GRID_HEIGHT) / 2
        TRACKING_GRID_ORIGIN_X = config.screen_width - GRID_WIDTH - GRID_SPACING
        TRACKING_GRID_ORIGIN_Y = (config.screen_height - GRID_HEIGHT) / 2

        # Game phases
        PHASE_PREPARING = 0
        PHASE_GAME = 1

        def __init__(self):
            """
            """
            super(Battleship, self).__init__()

            self.mouse_x = 0
            self.mouse_y = 0

            self.phase = Battleship.PHASE_PREPARING
            self.hovered_square = None
            self.dragged_ship = None
            self.grid_conflicts = list()

            self.__ship_sprites_cache = dict()

            self.ship_buttons = list()
            self.__build_ship_buttons()

            self.player = Player("Player", Battleship.SHIP_SET_CLASSIC)
            self.monika = Player("Monika", Battleship.SHIP_SET_CLASSIC)

            # _orientation = random.randint(0, 3)
            # _length = random.randint(2, 5)
            # _coords = self.player.grid.find_place_for_ship(_length, _orientation)
            # _ship = self.player.grid.build_ship(_coords[0], _coords[1], _length, _orientation)

            # self.player.grid.build_ships(self.player.ship_set)
            # self.player.misses_coords.append((0, 0))
            # self.player.misses_coords.append((0, 9))
            # self.player.misses_coords.append((9, 0))
            # self.player.misses_coords.append((9, 9))
            # self.monika.misses_coords.append((7, 7))
            # _coords = self.player.ships[0].health.keys()[1]
            # self.monika.hits_coords.append(_coords)

        def __build_ship_buttons(self):
            """
            Creates MASButtonDisplayable object and fill the list of buttons
            """
            text_disp = Null()
            for j, ship_length in enumerate(Battleship.SHIP_SPRITES_MAP.iterkeys()):
                ship = Ship.build_ship(0, 0, ship_length, Ship.ORIENTATION_UP)
                ship_sprite = self.__get_ship_sprite(ship)
                x = Battleship.TRACKING_GRID_ORIGIN_X + j * (Battleship.SQUARE_WIDTH + Battleship.GRID_SPACING)# TODO: Separate const for this
                y = Battleship.TRACKING_GRID_ORIGIN_Y

                ship_button = MASButtonDisplayable(
                    text_disp,
                    text_disp,
                    text_disp,
                    ship_sprite,
                    ship_sprite,
                    ship_sprite,# TODO: greyed out sprite for this, maybe via an im?
                    x,
                    y,
                    Battleship.SQUARE_WIDTH,
                    Battleship.SQUARE_HEIGHT * ship_length + Battleship.INNER_GRID_THICKNESS * (ship_length - 1),
                    return_value=ship
                )
                ship_button._button_down = pygame.MOUSEBUTTONDOWN
                # NOTE: since for some reason MASButtonDisplayable never fully inits as a disp,
                # we have to manually do it here
                super(renpy.Displayable, ship_button).__init__()
                self.ship_buttons.append(ship_button)

        @classmethod
        def __grid_coords_to_screen_coords(cls, x, y, grid_origin_x, grid_origin_y):
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
                grid_origin_x + cls.OUTER_FRAME_THICKNESS + x * (cls.INNER_GRID_THICKNESS + cls.SQUARE_WIDTH),
                grid_origin_y + cls.OUTER_FRAME_THICKNESS + y * (cls.INNER_GRID_THICKNESS + cls.SQUARE_HEIGHT)
            )

        @classmethod
        def __screen_coords_to_grid_coords(cls, x, y, grid_origin_x, grid_origin_y):
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
                int((x - grid_origin_x - cls.OUTER_FRAME_THICKNESS - (int(x - grid_origin_x - cls.OUTER_FRAME_THICKNESS) / cls.SQUARE_WIDTH) * cls.INNER_GRID_THICKNESS) / cls.SQUARE_WIDTH),
                int((y - grid_origin_y - cls.OUTER_FRAME_THICKNESS - (int(y - grid_origin_y - cls.OUTER_FRAME_THICKNESS) / cls.SQUARE_HEIGHT) * cls.INNER_GRID_THICKNESS) / cls.SQUARE_HEIGHT)
            )

        def __get_ship_sprite(self, ship):
            """
            Returns a sprite for a ship using cache system (generates if needed, retrives if already generated)

            IN:
                ship - ship to get sprite for

            OUT:
                sprite (a Transform obj)
            """
            _angle = ship.orientation
            _sprite = Battleship.SHIP_SPRITES_MAP[ship.length]
            _key = (ship.length, ship.orientation)

            if _key not in self.__ship_sprites_cache:
                self.__ship_sprites_cache[_key] = Transform(
                    child=_sprite,
                    xanchor=0.5,
                    yanchor=16,
                    offset=(16, 16),
                    transform_anchor=True,
                    rotate_pad=False,
                    subpixel=True,
                    rotate=_angle
                )

            return self.__ship_sprites_cache[_key]

        def render(self, width, height, st, at):
            """
            Render method for this disp
            """
            # Define our main render
            main_render = renpy.Render(width, height)

            # # # Render grids
            # Predefine renders
            grid_base_render = renpy.render(Battleship.GRID_BASE, width, height, st, at)
            grid_render = renpy.render(Battleship.GRID, width, height, st, at)
            # TODO: separate water sprites for each grid so we get unique water movement
            water_layer_0_render = renpy.render(Battleship.WATER_LAYER_0, width, height, st, at)
            water_layer_1_render = renpy.render(Battleship.WATER_LAYER_1, width, height, st, at)
            # Now blit 'em
            main_render.blit(grid_base_render, (Battleship.MAIN_GRID_ORIGIN_X, Battleship.MAIN_GRID_ORIGIN_Y))
            main_render.blit(water_layer_0_render, (Battleship.MAIN_GRID_ORIGIN_X + Battleship.OUTER_FRAME_THICKNESS, Battleship.MAIN_GRID_ORIGIN_Y + Battleship.OUTER_FRAME_THICKNESS))
            main_render.blit(water_layer_1_render, (Battleship.MAIN_GRID_ORIGIN_X + Battleship.OUTER_FRAME_THICKNESS, Battleship.MAIN_GRID_ORIGIN_Y + Battleship.OUTER_FRAME_THICKNESS))
            main_render.blit(grid_render, (Battleship.MAIN_GRID_ORIGIN_X, Battleship.MAIN_GRID_ORIGIN_Y))
            # Render Monika's grid only during the game phase
            if self.phase == Battleship.PHASE_GAME:
                # tracking_grid_render = renpy.render(Battleship.TRACKING_GRID, width, height, st, at)
                # main_render.blit(tracking_grid_render, (Battleship.TRACKING_GRID_ORIGIN_X, Battleship.TRACKING_GRID_ORIGIN_Y))
                main_render.blit(grid_base_render, (Battleship.TRACKING_GRID_ORIGIN_X, Battleship.TRACKING_GRID_ORIGIN_Y))
                main_render.blit(water_layer_0_render, (Battleship.TRACKING_GRID_ORIGIN_X + Battleship.OUTER_FRAME_THICKNESS, Battleship.TRACKING_GRID_ORIGIN_Y + Battleship.OUTER_FRAME_THICKNESS))
                main_render.blit(water_layer_1_render, (Battleship.TRACKING_GRID_ORIGIN_X + Battleship.OUTER_FRAME_THICKNESS, Battleship.TRACKING_GRID_ORIGIN_Y + Battleship.OUTER_FRAME_THICKNESS))
                main_render.blit(grid_render, (Battleship.TRACKING_GRID_ORIGIN_X, Battleship.TRACKING_GRID_ORIGIN_Y))

            # Render conflicts
            if self.phase == Battleship.PHASE_PREPARING:
                if self.grid_conflicts:
                    error_mask_render = renpy.render(Battleship.SQUARE_ERROR, width, height, st, at)
                    for coords in self.grid_conflicts:
                        x, y = Battleship.__grid_coords_to_screen_coords(coords[0], coords[1], Battleship.MAIN_GRID_ORIGIN_X, Battleship.MAIN_GRID_ORIGIN_Y)
                        main_render.blit(error_mask_render, (x, y))

            # Render player's ships
            for ship in self.player.grid.ship_list:
                ship_sprite = self.__get_ship_sprite(ship)
                x, y = Battleship.__grid_coords_to_screen_coords(ship.bow_coords[0], ship.bow_coords[1], Battleship.MAIN_GRID_ORIGIN_X, Battleship.MAIN_GRID_ORIGIN_Y)
                main_render.place(ship_sprite, x, y)

            # # # Render things that only relevant during the game
            if self.phase == Battleship.PHASE_GAME:
                # Render Monika's ships
                for ship in self.monika.grid.ship_list:
                    if not ship.is_alive:
                        ship_sprite = self.__get_ship_sprite(ship)
                        x, y = Battleship.__grid_coords_to_screen_coords(ship.bow_coords[0], ship.bow_coords[1], Battleship.TRACKING_GRID_ORIGIN_X, Battleship.TRACKING_GRID_ORIGIN_Y)
                        main_render.place(ship_sprite, x, y)

                # Render hits
                hit_mark_render = renpy.render(Battleship.HIT_MARK, width, height, st, at)
                for coords in self.player.hits_coords:
                    x, y = Battleship.__grid_coords_to_screen_coords(coords[0], coords[1], Battleship.TRACKING_GRID_ORIGIN_X, Battleship.TRACKING_GRID_ORIGIN_Y)
                    main_render.blit(hit_mark_render, (x, y))

                for coords in self.monika.hits_coords:
                    x, y = Battleship.__grid_coords_to_screen_coords(coords[0], coords[1], Battleship.MAIN_GRID_ORIGIN_X, Battleship.MAIN_GRID_ORIGIN_Y)
                    main_render.blit(hit_mark_render, (x, y))

                # Render misses
                miss_mark_render = renpy.render(Battleship.MISS_MARK, width, height, st, at)
                for coords in self.player.misses_coords:
                    x, y = Battleship.__grid_coords_to_screen_coords(coords[0], coords[1], Battleship.TRACKING_GRID_ORIGIN_X, Battleship.TRACKING_GRID_ORIGIN_Y)
                    main_render.blit(miss_mark_render, (x, y))

                for coords in self.monika.misses_coords:
                    x, y = Battleship.__grid_coords_to_screen_coords(coords[0], coords[1], Battleship.MAIN_GRID_ORIGIN_X, Battleship.MAIN_GRID_ORIGIN_Y)
                    main_render.blit(miss_mark_render, (x, y))

                # Render hovering mask
                if self.hovered_square is not None:
                    hover_mask_render = renpy.render(Battleship.SQUARE_HOVER, width, height, st, at)
                    x, y = Battleship.__grid_coords_to_screen_coords(self.hovered_square[0], self.hovered_square[1], Battleship.TRACKING_GRID_ORIGIN_X, Battleship.TRACKING_GRID_ORIGIN_Y)
                    main_render.blit(hover_mask_render, (x, y))

            # # # Render things that only relevant during ship building
            elif self.phase == Battleship.PHASE_PREPARING:
                # Render ship buttons
                for ship_button in self.ship_buttons:
                    sb_render = renpy.render(ship_button, width, height, st, at)
                    main_render.blit(sb_render, (ship_button.xpos, ship_button.ypos))

                # Render the ship that's currently dragged (if any)
                if self.dragged_ship is not None:
                    ship_sprite = self.__get_ship_sprite(self.dragged_ship)
                    if self.dragged_ship.orientation in Ship.VERT_ORIENTATIONS:
                        x_offset = 0
                        y_offset = self.dragged_ship.get_drag_point() * self.SQUARE_HEIGHT

                    else:
                        x_offset = self.dragged_ship.get_drag_point() * self.SQUARE_WIDTH
                        y_offset = 0

                    main_render.place(
                        ship_sprite,
                        (self.mouse_x - self.SQUARE_WIDTH / 2 + x_offset),
                        (self.mouse_y - self.SQUARE_HEIGHT / 2 + y_offset)
                    )

            return main_render

        def per_interact(self):
            """
            Request redraw on each interaction
            """
            return

        def __check_buttons_events(self, ev, x, y, st):
            """
            Checks if the player pressed one of the ship building buttons
            """
            if self.phase == Battleship.PHASE_PREPARING:
                for ship_button in self.ship_buttons:
                    ship = ship_button.event(ev, x, y, st)
                    if ship is not None:
                        drag_point = (y - Battleship.TRACKING_GRID_ORIGIN_Y) / (Battleship.SQUARE_HEIGHT + Battleship.INNER_GRID_THICKNESS)
                        self.dragged_ship = ship.copy()
                        self.dragged_ship.set_drag_point((0, drag_point))
                        return True
            return False

        def event(self, ev, x, y, st):
            """
            Event handler
            """
            # Update internal mouse coords
            self.mouse_x = x
            self.mouse_y = y

            # Check if the player wants to build a ship
            if self.__check_buttons_events(ev, x, y, st):
                # We handle buttons' events in the method above
                renpy.redraw(self, 0)

            # # # The player pressed the rotation key
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                if self.phase == Battleship.PHASE_PREPARING:
                    # If the player's dragging a ship, rotate it
                    if self.dragged_ship is not None:
                        if ev.mod in (pygame.KMOD_LSHIFT, pygame.KMOD_RSHIFT):
                            self.dragged_ship.orientation -= 90

                        else:
                            self.dragged_ship.orientation += 90

                        self.grid_conflicts[:] = self.player.grid.get_conflicts()
                        renpy.redraw(self, 0)

                    # If the player's pressed the keybinding for rotating while hovering over a ship, rotate it
                    else:
                        coords = Battleship.__screen_coords_to_grid_coords(x, y, Battleship.MAIN_GRID_ORIGIN_X, Battleship.MAIN_GRID_ORIGIN_Y)

                        if coords is not None:
                            ship = self.player.grid.get_ship_at(coords[0], coords[1])

                            if ship is not None:
                                if ev.mod in (pygame.KMOD_LSHIFT, pygame.KMOD_RSHIFT):
                                    angle = -90

                                else:
                                    angle = 90

                                self.player.grid.remove_ship(ship)
                                ship.rotate(angle, coords[0], coords[1])
                                self.player.grid.place_ship(ship)
                                self.grid_conflicts[:] = self.player.grid.get_conflicts()

                                renpy.redraw(self, 0)

            # # # The player moves the mouse, we may need to update the screen
            elif ev.type == pygame.MOUSEMOTION:
                if self.phase == Battleship.PHASE_GAME:
                    coords = Battleship.__screen_coords_to_grid_coords(x, y, Battleship.TRACKING_GRID_ORIGIN_X, Battleship.TRACKING_GRID_ORIGIN_Y)

                    # Ask to redraw if we either just started hover or stopped
                    if (
                        coords is not None
                        or self.hovered_square is not None
                    ):
                        self.hovered_square = coords
                        renpy.redraw(self, 0)

                # Continue to update the screen while the player's dragging a ship
                elif (
                    self.phase == Battleship.PHASE_PREPARING
                    and self.dragged_ship is not None
                ):
                    renpy.redraw(self, 0)

            # # # The player clicks on a ship and starts dragging it
            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.phase == Battleship.PHASE_PREPARING:
                    coords = Battleship.__screen_coords_to_grid_coords(x, y, Battleship.MAIN_GRID_ORIGIN_X, Battleship.MAIN_GRID_ORIGIN_Y)

                    if coords is not None:
                        ship = self.player.grid.get_ship_at(coords[0], coords[1])

                        if ship is not None:
                            self.player.grid.remove_ship(ship)
                            self.grid_conflicts[:] = self.player.grid.get_conflicts()
                            ship.set_drag_point(coords)
                            self.dragged_ship = ship

                            renpy.redraw(self, 0)

            # # # The player releases the mouse button and places the ship on the grid
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if self.phase == Battleship.PHASE_PREPARING:
                    if self.dragged_ship is not None:
                        coords = Battleship.__screen_coords_to_grid_coords(x, y, Battleship.MAIN_GRID_ORIGIN_X, Battleship.MAIN_GRID_ORIGIN_Y)

                        if coords is not None:
                            # Let's get dragging offsets
                            if self.dragged_ship.orientation in Ship.VERT_ORIENTATIONS:
                                x_offset = 0
                                y_offset = self.dragged_ship.get_drag_point()

                            else:
                                x_offset = self.dragged_ship.get_drag_point()
                                y_offset = 0

                            # Repack the tuple appying the offsets
                            coords = (coords[0] + x_offset, coords[1] + y_offset)
                            # Set new coords for the ship
                            self.dragged_ship.bow_coords = coords
                            # Reset drag point
                            self.dragged_ship.set_drag_point(coords)
                            # Finally place it
                            self.player.grid.place_ship(self.dragged_ship)
                            # Check for invalid placement
                            self.grid_conflicts[:] = self.player.grid.get_conflicts()

                        # Set to None anyway if the player just wanted to remove the ship
                        self.dragged_ship = None
                        renpy.redraw(self, 0)

            # raise renpy.IgnoreEvent()
            return

    class Grid(object):
        """
        """
        HEIGHT = 10
        WIDTH = HEIGHT

        SQUARE_TYPE_EMPTY = 0
        SQUARE_TYPE_SHIP_BOW = 1
        SQUARE_TYPE_SHIP_HULL = 2
        SQUARE_TYPE_SHIP_STERN = 3
        SQUARE_TYPE_SHIP_SPACING = 4
        SQUARE_TYPE_CONFLICT = 5

        ALL_SQUARE_TYPES = (
            SQUARE_TYPE_EMPTY,
            SQUARE_TYPE_SHIP_BOW,
            SQUARE_TYPE_SHIP_HULL,
            SQUARE_TYPE_SHIP_STERN,
            SQUARE_TYPE_SHIP_SPACING,
            SQUARE_TYPE_CONFLICT
        )

        def __init__(self):
            """
            Constructor
            """
            self._grid = {(col, row): Grid.SQUARE_TYPE_EMPTY for row in range(Grid.HEIGHT) for col in range(Grid.WIDTH)}
            self.ship_map = {coords: list() for coords in self._grid.iterkeys()}
            self.ship_list = list()

        def clear(self, clear_grid=True, clear_map=True):
            """
            Clears this grid
            """
            if clear_grid:
                for coords in self._grid:
                    self._grid[coords] = Grid.SQUARE_TYPE_EMPTY

            if clear_map:
                for ship_list in self.ship_map.itervalues():
                    ship_list[:] = []

                # If we clear the map, we must clear the main list too
                self.ship_list[:] = []

        def _get_square_at(self, x, y):
            """
            Returns the type of a square

            IN:
                x - x coord
                y - y coord

            OUT:
                int as one of types,
                or None if the given coordinates are out of this grid
            """
            return self._grid.get((x, y), None)

        def is_empty_at(self, x, y):
            """
            Checks if the square at the given coordinates is empty
            (has no ship nor is spacing for a ship)

            IN:
                x - x coord
                y - y coord

            OUT:
                boolean: True if free, False otherwise
            """
            return self._get_square_at(x, y) == Grid.SQUARE_TYPE_EMPTY

        def is_empty_or_spacing_at(self, x, y):
            """
            Checks if the square at the given coordinates has no ship

            IN:
                x - x coord
                y - y coord

            OUT:
                boolean: True if free, False otherwise
            """
            _type = self._get_square_at(x, y)
            return _type == Grid.SQUARE_TYPE_EMPTY or _type == Grid.SQUARE_TYPE_SHIP_SPACING

        def _set_square_at(self, x, y, value):
            """
            Set a square to a new type
            This will do nothing if the given coords are outside of this grid

            IN:
                x - x coord
                y - y coord
                value - new type for the square
            """
            _key = (x, y)
            if (
                _key not in self._grid
                or value not in Grid.ALL_SQUARE_TYPES
            ):
                return

            self._grid[_key] = value

        def get_ship_at(self, x, y):
            """
            Returns a ship at the given coordinates

            NOTE: If for some reason we have more than one ship at the square,
                this will return the one that was added last

            IN:
                x - x coord
                y - y coord

            OUT:
                Ship object or None if nothing found
            """
            ships = self.ship_map.get((x, y), None)
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
                for coords, square_type in self._grid.iteritems()
                if square_type == Grid.SQUARE_TYPE_CONFLICT
            ]

        def update(self):
            """
            Goes through this grid and sets its squares again
            """
            self.clear(clear_map=False)

            for ship in self.ship_list:
                self.place_ship(ship, add_to_map=False)

        def remove_ship(self, ship):
            """
            Removes a ship from this grid

            IN:
                ship - ship to remove
            """
            for ship_list in self.ship_map.itervalues():
                if ship in ship_list:
                    ship_list.remove(ship)

            if ship in self.ship_list:
                self.ship_list.remove(ship)

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

            if ship_orientation == Ship.ORIENTATION_UP:
                x_coords = (x,) * ship_length
                y_coords = range(y, y + ship_length)

            elif ship_orientation == Ship.ORIENTATION_RIGHT:
                x_coords = range(x, x - ship_length, -1)
                y_coords = (y,) * ship_length

            elif ship_orientation == Ship.ORIENTATION_DOWN:
                x_coords = (x,) * ship_length
                y_coords = range(y, y - ship_length, -1)

            else:
                x_coords = range(x, x + ship_length)
                y_coords = (y,) * ship_length

            for _x, _y in zip(x_coords, y_coords):
                if not self.is_empty_at(_x, _y):
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
            available_positions = list()

            should_swap_coords = False
            if ship_orientation == Ship.ORIENTATION_UP:
                columns = range(Grid.WIDTH)
                rows = range(Grid.HEIGHT)

            elif ship_orientation == Ship.ORIENTATION_RIGHT:
                columns = range(Grid.WIDTH)
                rows = range(Grid.HEIGHT, 0, -1)
                should_swap_coords = True

            elif ship_orientation == Ship.ORIENTATION_DOWN:
                columns = range(Grid.WIDTH)
                rows = range(Grid.HEIGHT, 0, -1)

            else:
                columns = range(Grid.WIDTH)
                rows = range(Grid.HEIGHT)
                should_swap_coords = True

            for col in columns:
                # List of tuples with coords
                line = list()
                for row in rows:
                    if should_swap_coords:
                        x = row
                        y = col

                    else:
                        x = col
                        y = row

                    # If this square is free, add it to the line
                    if self.is_empty_at(x, y):
                        line.append((x, y))

                    # Otherwise we got all free squares we could
                    else:
                        # See if we can fit our ship in this line
                        if len(line) >= ship_length:
                            available_positions.append(line)
                        # Reset the list before continuing iterating
                        line = list()

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
            sets the appropriate type for the squares under the ship and adds
            the ship to the ship map

            NOTE: this makes no checks whether or not we can place the ship on the given pos

            IN:
                ship - ship to place
                add_to_map - whether we add this ship to the ship map or we do not
                    (Default: True)
            """
            ship_orientation = ship.orientation
            bow_coords = ship.bow_coords
            stern_coords = ship.stern_coords
            bad_placement = ship.has_bad_placement()

            for coords_tuple in ship.health.iterkeys():
                if coords_tuple == bow_coords:
                    square_type = Grid.SQUARE_TYPE_SHIP_BOW

                    if ship_orientation == Ship.ORIENTATION_UP:
                        y = coords_tuple[1] - 1
                        for x in range(coords_tuple[0] - 1, coords_tuple[0] + 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                        y = coords_tuple[1]
                        for x in range(coords_tuple[0] - 1, coords_tuple[0] + 2, 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                    elif ship_orientation == Ship.ORIENTATION_RIGHT:
                        x = coords_tuple[0] + 1
                        for y in range(coords_tuple[1] - 1, coords_tuple[1] + 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                        x = coords_tuple[0]
                        for y in range(coords_tuple[1] - 1, coords_tuple[1] + 2, 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                    elif ship_orientation == Ship.ORIENTATION_DOWN:
                        y = coords_tuple[1] + 1
                        for x in range(coords_tuple[0] - 1, coords_tuple[0] + 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                        y = coords_tuple[1]
                        for x in range(coords_tuple[0] - 1, coords_tuple[0] + 2, 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                    else:
                        x = coords_tuple[0] - 1
                        for y in range(coords_tuple[1] - 1, coords_tuple[1] + 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                        x = coords_tuple[0]
                        for y in range(coords_tuple[1] - 1, coords_tuple[1] + 2, 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                elif coords_tuple == stern_coords:
                    square_type = Grid.SQUARE_TYPE_SHIP_STERN

                    if ship_orientation == Ship.ORIENTATION_UP:
                        y = coords_tuple[1] + 1
                        for x in range(coords_tuple[0] - 1, coords_tuple[0] + 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                        y = coords_tuple[1]
                        for x in range(coords_tuple[0] - 1, coords_tuple[0] + 2, 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                    elif ship_orientation == Ship.ORIENTATION_RIGHT:
                        x = coords_tuple[0] - 1
                        for y in range(coords_tuple[1] - 1, coords_tuple[1] + 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                        x = coords_tuple[0]
                        for y in range(coords_tuple[1] - 1, coords_tuple[1] + 2, 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                    elif ship_orientation == Ship.ORIENTATION_DOWN:
                        y = coords_tuple[1] - 1
                        for x in range(coords_tuple[0] - 1, coords_tuple[0] + 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                        y = coords_tuple[1]
                        for x in range(coords_tuple[0] - 1, coords_tuple[0] + 2, 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                    else:
                        x = coords_tuple[0] + 1
                        for y in range(coords_tuple[1] - 1, coords_tuple[1] + 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                        x = coords_tuple[0]
                        for y in range(coords_tuple[1] - 1, coords_tuple[1] + 2, 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                else:
                    square_type = Grid.SQUARE_TYPE_SHIP_HULL

                    if ship_orientation in Ship.VERT_ORIENTATIONS:
                        y = coords_tuple[1]
                        for x in range(coords_tuple[0] - 1, coords_tuple[0] + 2, 2):
                            if self.is_empty_or_spacing_at(x, y):
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_SHIP_SPACING)

                            else:
                                self._set_square_at(x, y, Grid.SQUARE_TYPE_CONFLICT)

                    else:
                        x = coords_tuple[0]
                        for y in range(coords_tuple[1] - 1, coords_tuple[1] + 2, 2):
                            if self.is_empty_or_spacing_at(x, y):
                                _type = Grid.SQUARE_TYPE_SHIP_SPACING
                            else:
                                _type = Grid.SQUARE_TYPE_CONFLICT

                            self._set_square_at(x, y, _type)

                if bad_placement or not self.is_empty_at(coords_tuple[0], coords_tuple[1]):
                    square_type = Grid.SQUARE_TYPE_CONFLICT

                self._set_square_at(coords_tuple[0], coords_tuple[1], square_type)

                if add_to_map:
                    # If the ship was placed incorrectly, then its coords may be out of this grid
                    if coords_tuple in self.ship_map:
                        self.ship_map[coords_tuple].append(ship)

            if add_to_map:
                # Also add to the main list
                self.ship_list.append(ship)

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
                        if ship.orientation in Ship.VERT_ORIENTATIONS:
                            rest_orientations = Ship.HORIZ_ORIENTATIONS

                        else:
                            rest_orientations = Ship.VERT_ORIENTATIONS

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
        # Orientation consts
        ORIENTATION_UP = 0
        ORIENTATION_RIGHT = 90
        ORIENTATION_DOWN = 180
        ORIENTATION_LEFT = 270

        ALL_ORIENTATIONS = (ORIENTATION_UP, ORIENTATION_RIGHT, ORIENTATION_DOWN, ORIENTATION_LEFT)
        VERT_ORIENTATIONS = (ORIENTATION_UP, ORIENTATION_DOWN)
        HORIZ_ORIENTATIONS = (ORIENTATION_RIGHT, ORIENTATION_LEFT)

        def __init__(self, x, y, length, orientation):
            """
            """
            self.__bow_coords = (x, y)
            self.__stern_coords = None
            self.__length = length
            self.__orientation = orientation

            self.health = OrderedDict()
            self.is_alive = True
            self.__drag_point = 0
            # Now fill these
            self.__update_stern_coords()
            self.__update_health()

        @staticmethod
        def __apply_roto_matrix(x, y, cos, sin, origin_x, origin_y, is_positive):
            """
            Rotates a point, using rotation matrix

            IN:
                x - x coordinate
                y - y coordinate
                cos - rotation angle cosine
                sin - rotation angle sine
                is_positive - whether or not the rotation angle is positive
            """
            factor = 1 if is_positive else -1
            new_x = origin_x + (x - origin_x) * cos - factor * (y - origin_y) * sin
            new_y = origin_y + (y - origin_y) * cos + factor * (x - origin_x) * sin

            return new_x, new_y

        def __rotate(self, angle, origin_x, origin_y):
            """
            Rotates this ship
            NOTE: this doesn't update the orientation and drag_point props, assuming these'll be set afterwards
            
            IN:
                angle - angle to rotate by
                    NOTE: in degrees
                    NOTE: assumes it was sanitized to be between 0-270
                origin_x - origin x to rotate around
                origin_y - origin y to rotate around
            """
            # Get the rotation direction
            is_positive = angle >= 0
            angle = meth.radians(angle)
            # Get cos and sin
            cos = int(round(meth.cos(angle), 5))
            sin = int(round(meth.sin(angle), 5))
            # Rotate
            old_health = self.health.copy()
            self.health.clear()
            for old_coords, value in old_health.iteritems():
                new_coords = self.__apply_roto_matrix(
                    x=old_coords[0],
                    y=old_coords[1],
                    cos=cos,
                    sin=sin,
                    origin_x=origin_x,
                    origin_y=origin_y,
                    is_positive=is_positive
                )
                self.health[new_coords] = value

            chunks_coords = self.health.keys()
            self.__bow_coords = chunks_coords[0]
            self.__stern_coords = chunks_coords[-1]

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

            self.__rotate(angle, origin_x, origin_y)
            self.__orientation += angle
            self.__orientation %= 360
            self.__update_drag_point()

        def __update_bow_coords(self):
            """
            Updates (forcefully) this ship's bow coords using current stern coords, orientation, and length
            """
            x, y = self.__stern_coords
            _len = self.__length - 1

            if self.__orientation == Ship.ORIENTATION_UP:
                self.__bow_coords = (x, y - _len)

            elif self.__orientation == Ship.ORIENTATION_RIGHT:
                self.__bow_coords = (x + _len, y)

            elif self.__orientation == Ship.ORIENTATION_DOWN:
                self.__bow_coords = (x, y + _len)

            else:
                self.__bow_coords = (x - _len, y)

        def __update_stern_coords(self):
            """
            Updates (forcefully) this ship's stern coords using current bow coords, orientation, and length
            """
            x, y = self.__bow_coords
            _len = self.__length - 1

            if self.__orientation == Ship.ORIENTATION_UP:
                self.__stern_coords = (x, y + _len)

            elif self.__orientation == Ship.ORIENTATION_RIGHT:
                self.__stern_coords = (x - _len, y)

            elif self.__orientation == Ship.ORIENTATION_DOWN:
                self.__stern_coords = (x, y - _len)

            else:
                self.__stern_coords = (x + _len, y)

        def __update_health(self):
            """
            Updates this ship's health using current bow coords, orientation, and length
            NOTE: changes coordinates, keeps the values
            """
            x, y = self.__bow_coords

            if self.health:
                old_health_values = self.health.values()
                self.health.clear()

            else:
                old_health_values = [True for k in range(self.__length)]

            for i in range(self.__length):
                if self.__orientation == Ship.ORIENTATION_UP:
                    self.health[(x, y + i)] = old_health_values[i]

                elif self.__orientation == Ship.ORIENTATION_RIGHT:
                    self.health[(x - i, y)] = old_health_values[i]

                elif self.__orientation == Ship.ORIENTATION_DOWN:
                    self.health[(x, y - i)] = old_health_values[i]

                else:
                    self.health[(x + i, y)] = old_health_values[i]

        def __update_drag_point(self):
            """
            Updates drag_point using current orientation
            """
            if (
                (
                    self.__drag_point > 0
                    and self.__orientation in (Ship.ORIENTATION_LEFT, Ship.ORIENTATION_UP)
                )
                or (
                    self.__drag_point < 0
                    and self.__orientation in (Ship.ORIENTATION_RIGHT, Ship.ORIENTATION_DOWN)
                )
            ):
                self.__drag_point = -self.__drag_point

        @property
        def bow_coords(self):
            """
            Prop getter for bow coords
            """
            return self.__bow_coords

        @bow_coords.setter
        def bow_coords(self, value):
            """
            Prop setter for bow coords
            """
            self.__bow_coords = value
            self.__update_stern_coords()
            self.__update_health()

        @property
        def stern_coords(self):
            """
            Prop getter for stern coords
            """
            return self.__stern_coords

        @stern_coords.setter
        def stern_coords(self, value):
            """
            Prop setter for stern coords
            """
            self.__stern_coords = value
            self.__update_bow_coords()
            self.__update_health()

        @property
        def length(self):
            """
            Prop getter for length
            """
            return self.__length

        @property
        def orientation(self):
            """
            Prop getter for orientation
            """
            return self.__orientation

        @orientation.setter
        def orientation(self, value):
            """
            Prop setter for orientation
            NOTE: this assumes that we rotate the ship around its bow
            NOTE: allowed angles are 0, 90, 180, and 270
            """
            # I actually love that modulo works like this in python
            value %= 360

            if (
                value == self.__orientation
                or value % 90 != 0
            ):
                return

            self.__rotate(
                (value - self.__orientation),
                self.__bow_coords[0],
                self.__bow_coords[1]
            )
            self.__orientation = value
            self.__update_drag_point()

        def get_drag_point(self):
            """
            Getter for drag_point
            """
            return self.__drag_point

        def set_drag_point(self, value):
            """
            Setter for drag_point

            IN:
                value - tuple with x, y coords of a pointon the grid
            """
            # Sanity check, drag point MUST be inside this ship
            if value not in self.health:
                return

            id = self.health.keys().index(value)
            # Check if we need to invert it
            if self.orientation in (Ship.ORIENTATION_LEFT, Ship.ORIENTATION_UP):
                id = -id

            self.__drag_point = id

        def register_hit(self, x, y):
            """
            """
            _key = (x, y)
            if _key not in self.health:
                return

            self.health[_key] = False
            self.is_alive = any(self.health.values())

        def has_bad_placement(self):
            """
            Checks whether or not this ship was placed incorrectly
            NOTE: this just checks this ship's coords, this DOES NOT check for conflicts with other ships

            OUT:
                boolean: True if incorrectly, False if everything is fine
            """
            for x, y in self.health.iterkeys():
                if not (0 <= x <= 9 and 0 <= y <= 9):
                    return True
            return False

        def copy(self):
            """
            Returns a copy of this ship

            OUT:
                new Ship objects with the same params as this one
            """
            ship = Ship(self.__bow_coords[0], self.__bow_coords[1], self.__length, self.__orientation)

            for _key, value in zip(ship.health.keys(), self.health.values()):
                ship.health[_key] = value

            ship.is_alive = self.is_alive
            ship.__drag_point = self.__drag_point

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
                orientation = random.choice(cls.ALL_ORIENTATIONS)

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

            self.hits_coords = list()
            self.misses_coords = list()

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
