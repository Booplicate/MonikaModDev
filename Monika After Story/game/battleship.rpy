
# init -50 python:
#     def __render(self, width, height, st, at):

#         # pull out the current button back and text and render them
#         render_text, render_back = self._button_states[self._state]

#         # what is the text's with and height
#         rt_w, rt_h = renpy.render(render_text, width, height, st, at).get_size()

#         # build our renderer
#         r = renpy.Render(self.width, self.height)

#         # place our textures
#         r.place(render_back, 0, 0)
#         r.place(render_text, int((self.width - rt_w) / 2), int((self.height - rt_h) / 2))

#         # return renderer
#         return r

#     MASButtonDisplayable.render = __render

init python in mas_battleship:
    from store import Image, Null, Transform, MASButtonDisplayable
    from collections import OrderedDict
    import random
    import pygame
    # a = mas_battleship.Battleship()
    # renpy.show("monika 3hub", at_list=[tcommon(220)]); ui.add(mas_battleship.Battleship()); ui.interact()
    # renpy.show("monika 1eua", at_list=[t31]); ui.add(mas_battleship.Battleship()); renpy.say(m, "<3")
    # a = mas_battleship.Battleship(); renpy.show("monika 1eua", at_list=[t31]); ui.add(a); renpy.say(m, "<3", False); ui.interact()

    class Battleship(renpy.Displayable):
        """
        """
        # Grid sprites
        MAIN_GRID = Image("/mod_assets/games/battleship/grid.png")
        TRACKING_GRID = Image("/mod_assets/games/battleship/grid.png")

        # Marks sprites
        HIT_MARK = Image("/mod_assets/games/battleship/hit_mark.png")
        MISS_MARK = Image("/mod_assets/games/battleship/miss_mark.png")

        # Ships sprites
        # TODO: sprites for broken/sunk ships?
        SHIP_5_SQUARES = Image("/mod_assets/games/battleship/ship_5_squares.png")
        SHIP_4_SQUARES = Image("/mod_assets/games/battleship/ship_4_squares.png")
        SHIP_3_SQUARES = Image("/mod_assets/games/battleship/ship_3_squares.png")
        SHIP_2_SQUARES = Image("/mod_assets/games/battleship/ship_2_squares.png")

        ALL_SHIPS = (5, 4, 3, 2)

        SHIP_SET_CLASSIC = (5, 4, 4, 3, 3, 3, 2, 2, 2, 2)

        # Map between ship types and sprites
        # TODO: support multiple sprites for one ship type?
        # SHIP_SPRITES_MAP = {2: SHIP_2_SQUARES, 3: SHIP_3_SQUARES, 4: SHIP_4_SQUARES, 5: SHIP_5_SQUARES}
        SHIP_SPRITES_MAP = OrderedDict(zip(ALL_SHIPS, (SHIP_5_SQUARES, SHIP_4_SQUARES, SHIP_3_SQUARES, SHIP_2_SQUARES)))
        # Map between ship orientations and angles
        ROTATION_ANGLES_MAP = {0: 0, 1: 90, 2: 180, 3: 270} #dict(zip(Ship.ALL_ORIENTATIONS, (0, 90, 180, 270)))

        # Hovering mask
        SQUARE_HOVER = Image("/mod_assets/games/battleship/square_hover.png")

        GRID_HEIGHT = 378
        GRID_WIDTH = GRID_HEIGHT
        GRID_SPACING = 5

        SQUARE_HEIGHT = 32
        SQUARE_WIDTH = SQUARE_HEIGHT

        OUTER_BORDER_HEIGHT = 20
        OUTER_BORDER_WIDTH = OUTER_BORDER_HEIGHT
        INNER_BORDER_HEIGHT = 2
        INNER_BORDER_WIDTH = INNER_BORDER_HEIGHT

        # Game phases
        PHASE_PREPARING = 0
        PHASE_GAME = 1

        def __init__(self):
            """
            """
            super(renpy.Displayable, self).__init__()

            self.mouse_x = 0
            self.mouse_y = 0
            self.width = renpy.config.screen_width
            self.height = renpy.config.screen_height

            self.phase = Battleship.PHASE_PREPARING
            self.hovered_square = None
            self.dragged_ship = None

            self.__ship_sprites_cache = dict()

            self.ship_buttons = list()
            self.__build_ship_buttons()

            self.player = Player("Player", Battleship.SHIP_SET_CLASSIC)
            self.monika = Player("Monika", Battleship.SHIP_SET_CLASSIC)

            # _orientation = random.randint(0, 3)
            # _length = random.randint(2, 5)
            # _coords = self.player.grid.find_place_for_ship(_length, _orientation)
            # _ship = self.player.grid.build_ship(_coords[0], _coords[1], _length, _orientation)
            # self.player.ships.append(_ship)

            # self.player.grid.build_ships(self.player.ship_set)
            # self.player.ships = self.player.grid.ship_map.values()
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
            base_start_x = self.width - Battleship.GRID_WIDTH - Battleship.GRID_SPACING
            base_start_y = (self.height - Battleship.GRID_HEIGHT) / 2

            for j, ship_length in enumerate(Battleship.SHIP_SPRITES_MAP.iterkeys()):
                ship = Ship.build_ship(0, 0, ship_length, Ship.ORIENTATION_UP)
                ship_sprite = self.__get_ship_sprite(ship)
                x = base_start_x + j * (Battleship.SQUARE_WIDTH + Battleship.GRID_SPACING)# TODO: Separate const for this
                y = base_start_y

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
                    Battleship.SQUARE_HEIGHT * ship_length + Battleship.INNER_BORDER_HEIGHT * (ship_length - 1),
                    return_value=ship
                )
                ship_button._button_down = pygame.MOUSEBUTTONDOWN
                self.ship_buttons.append(ship_button)

        def __grid_coords_to_screen_coords(self, x, y, grid_origin_x, grid_origin_y):
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
                grid_origin_x + self.OUTER_BORDER_WIDTH + x * (self.INNER_BORDER_WIDTH + self.SQUARE_WIDTH),
                grid_origin_y + self.OUTER_BORDER_HEIGHT + y * (self.INNER_BORDER_HEIGHT + self.SQUARE_HEIGHT)
            )

        def __screen_coords_to_grid_coords(self, x, y, grid_origin_x, grid_origin_y):
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
            if (
                x < grid_origin_x + self.OUTER_BORDER_WIDTH
                or x > grid_origin_x + self.GRID_WIDTH - self.OUTER_BORDER_WIDTH
                or y < grid_origin_y + self.OUTER_BORDER_HEIGHT
                or y > grid_origin_y + self.GRID_HEIGHT - self.OUTER_BORDER_HEIGHT
            ):
                return None

            return (
                int((x - grid_origin_x - self.OUTER_BORDER_WIDTH - (int(x - grid_origin_x - self.OUTER_BORDER_WIDTH) / self.SQUARE_WIDTH) * self.INNER_BORDER_WIDTH) / self.SQUARE_WIDTH),
                int((y - grid_origin_y - self.OUTER_BORDER_HEIGHT - (int(y - grid_origin_y - self.OUTER_BORDER_HEIGHT) / self.SQUARE_HEIGHT) * self.INNER_BORDER_HEIGHT) / self.SQUARE_HEIGHT)
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
            # If the user's changed resolution, update buttons pos accordingly
            if self.width != width or self.height != height:
                self.width = width
                self.height = height
                self.ship_buttons[:] = []
                self.__build_ship_buttons()

            # Get origins of our systems
            main_grid_origin_x = width - 2 * (Battleship.GRID_WIDTH + Battleship.GRID_SPACING)
            main_grid_origin_y = (height - Battleship.GRID_HEIGHT) / 2
            tracking_grid_origin_x = width - Battleship.GRID_WIDTH - Battleship.GRID_SPACING
            tracking_grid_origin_y = (height - Battleship.GRID_HEIGHT) / 2

            # Define our main render
            main_render = renpy.Render(width, height)

            # Render grids
            main_grid_render = renpy.render(Battleship.MAIN_GRID, width, height, st, at)
            main_render.blit(main_grid_render, (main_grid_origin_x, main_grid_origin_y))
            if self.phase == Battleship.PHASE_GAME:
                tracking_grid_render = renpy.render(Battleship.TRACKING_GRID, width, height, st, at)
                main_render.blit(tracking_grid_render, (tracking_grid_origin_x, tracking_grid_origin_y))

            # Render ships
            for ship_list in self.player.grid.ship_map.itervalues():
                for ship in ship_list:
                    x, y = self.__grid_coords_to_screen_coords(ship.bow_coords[0], ship.bow_coords[1], main_grid_origin_x, main_grid_origin_y)
                    ship_sprite = self.__get_ship_sprite(ship)
                    main_render.place(ship_sprite, x, y)

            if self.phase == Battleship.PHASE_GAME:
                for ship_list in self.monika.grid.ship_map.itervalues():
                    for ship in ship_list:
                        # Render only sunk ships, otherwise it'd be too easy to figure ships positions
                        if not ship.is_alive:
                            x, y = self.__grid_coords_to_screen_coords(ship.bow_coords[0], ship.bow_coords[1], tracking_grid_origin_x, tracking_grid_origin_y)
                            ship_sprite = self.__get_ship_sprite(ship)
                            main_render.place(ship_sprite, x, y)

            # Render hits
            hit_mark_render = renpy.render(Battleship.HIT_MARK, width, height, st, at)
            for coords in self.player.hits_coords:
                x, y = self.__grid_coords_to_screen_coords(coords[0], coords[1], tracking_grid_origin_x, tracking_grid_origin_y)
                main_render.blit(hit_mark_render, (x, y))

            for coords in self.monika.hits_coords:
                x, y = self.__grid_coords_to_screen_coords(coords[0], coords[1], main_grid_origin_x, main_grid_origin_y)
                main_render.blit(hit_mark_render, (x, y))

            # Render misses
            miss_mark_render = renpy.render(Battleship.MISS_MARK, width, height, st, at)
            for coords in self.player.misses_coords:
                x, y = self.__grid_coords_to_screen_coords(coords[0], coords[1], tracking_grid_origin_x, tracking_grid_origin_y)
                main_render.blit(miss_mark_render, (x, y))

            for coords in self.monika.misses_coords:
                x, y = self.__grid_coords_to_screen_coords(coords[0], coords[1], main_grid_origin_x, main_grid_origin_y)
                main_render.blit(miss_mark_render, (x, y))

            # Render hovering mask
            if (
                self.phase == Battleship.PHASE_GAME
                and self.hovered_square is not None
            ):
                x, y = self.__grid_coords_to_screen_coords(self.hovered_square[0], self.hovered_square[1], tracking_grid_origin_x, tracking_grid_origin_y)
                hover_mask_render = renpy.render(Battleship.SQUARE_HOVER, width, height, st, at)
                main_render.blit(hover_mask_render, (x, y))

            if self.phase == Battleship.PHASE_PREPARING:
                # Render ship buttons
                for ship_button in self.ship_buttons:
                    main_render.blit(
                        ship_button.render(width, height, st, at),
                        (ship_button.xpos, ship_button.ypos)
                    )

                # Render the ship that's currently dragged (if any)
                if self.dragged_ship is not None:
                    ship_sprite = self.__get_ship_sprite(self.dragged_ship)
                    main_render.place(ship_sprite, (self.mouse_x - self.SQUARE_WIDTH / 2), (self.mouse_y - self.SQUARE_HEIGHT / 2))

            return main_render

        def per_interact(self):
            """
            Request redraw on each interaction
            """
            renpy.redraw(self, 0)

        def __check_ship_buttons(self, ev, x, y, st):
            """
            Checks if the player pressed one of the ship building buttons
            """
            if self.phase == Battleship.PHASE_PREPARING:
                for ship_button in self.ship_buttons:
                    ship = ship_button.event(ev, x, y, st)
                    if ship is not None:
                        self.dragged_ship = ship.copy()
                        renpy.redraw(self, 0)
                        return

        def event(self, ev, x, y, st):
            """
            Event handler
            """
            # Update internal mouse coords
            self.mouse_x = x
            self.mouse_y = y

            # Predefine these here since we're using them in many places
            main_grid_origin_x = self.width - 2 * (Battleship.GRID_WIDTH + Battleship.GRID_SPACING)
            main_grid_origin_y = (self.height - Battleship.GRID_HEIGHT) / 2
            tracking_grid_origin_x = self.width - Battleship.GRID_WIDTH - Battleship.GRID_SPACING
            tracking_grid_origin_y = (self.height - Battleship.GRID_HEIGHT) / 2

            # Check if the player wants to build a ship
            self.__check_ship_buttons(ev, x, y, st)

            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                if self.phase == Battleship.PHASE_PREPARING:
                    if self.dragged_ship is not None:
                        if ev.mod in (pygame.KMOD_LSHIFT, pygame.KMOD_RSHIFT):
                            self.dragged_ship.orientation -= 90

                        else:
                            self.dragged_ship.orientation += 90

                        renpy.redraw(self, 0)

                    # TODO: rotate ships on the grid w/o clicking on them

            elif ev.type == pygame.MOUSEMOTION:
                if self.phase == Battleship.PHASE_GAME:
                    coords = self.__screen_coords_to_grid_coords(x, y, tracking_grid_origin_x, tracking_grid_origin_y)

                    # Ask to redraw if we either started hover or just stopped
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

            elif ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if self.phase == Battleship.PHASE_PREPARING:
                    coords = self.__screen_coords_to_grid_coords(x, y, main_grid_origin_x, main_grid_origin_y)

                    if coords is not None:
                        ship = self.player.grid.get_ship_at(coords[0], coords[1])
                        if ship is not None:
                            self.dragged_ship = ship
                            self.player.grid.remove_ship(ship)
                            self.player.grid.update()

            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if self.phase == Battleship.PHASE_PREPARING:
                    if self.dragged_ship is not None:
                        main_grid_origin_x = self.width - 2 * (Battleship.GRID_WIDTH + Battleship.GRID_SPACING)
                        main_grid_origin_y = (self.height - Battleship.GRID_HEIGHT) / 2
                        coords = self.__screen_coords_to_grid_coords(x, y, main_grid_origin_x, main_grid_origin_y)

                        if coords is not None:
                            self.dragged_ship.bow_coords = coords
                            self.player.grid.place_ship(self.dragged_ship)

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
        SQUARE_TYPE_SHIP_SPACING = 4# TODO: highlighting for this when in the prep phase

        def __init__(self):
            """
            Constructor
            """
            self.__height = Grid.HEIGHT
            self.__width = Grid.WIDTH
            self._grid = {(col, row): Grid.SQUARE_TYPE_EMPTY for row in range(self.__height) for col in range(self.__width)}
            self.ship_map = {coords: list() for coords in self._grid.iterkeys()}

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
            key = (x, y)
            if key not in self._grid:
                return None

            return self._grid[(x, y)]

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

        def _set_square_at(self, x, y, type):
            """
            Set a square to a new type
            This will do nothing if the given coords are outside of this grid

            IN:
                x - x coord
                y - y coord
                type - new type for the square
            """
            key = (x, y)
            if (
                key not in self._grid
                or type < Grid.SQUARE_TYPE_EMPTY
                or type > Grid.SQUARE_TYPE_SHIP_SPACING
            ):
                return

            self._grid[(x, y)] = type

        def get_ship_at(self, x, y):
            """
            Returns a ship at the given coordinates

            NOTE: If for some reason we have more than one ship at a the square,
                this will return the one that was added last

            IN:
                x - x coord
                y - y coord

            OUT:
                Ship object or None if nothing found
            """
            ship_list = self.ship_map.get((x, y), [])
            if ship_list:
                return ship_list[-1]

            return None

        def get_conflicts(self):
            """
            Returns a list of conflicts on this grid

            OUT:
                list with coordinates
            """
            conflict_coords = list()

            for x, y in self.ship_map.iterkeys():
                if self._get_square_at(x, y) == Grid.SQUARE_TYPE_SHIP_SPACING:
                    conflict_coords.append((x, y))

            return conflict_coords

        def is_valid_grid(self):
            """
            Validates ship placements on the grid

            OUT:
                boolean: True if all the ships have an appropriate placement, False otherwise
            """
            for x, y in self.ship_map.iterkeys():
                if self._get_square_at(x, y) == Grid.SQUARE_TYPE_SHIP_SPACING:
                    return False

            return True

        def update(self):
            """
            Goes through this grid and sets its squares again
            """
            self.clear(clear_map=False)

            for ship_list in self.ship_map.itervalues():
                for ship in ship_list:
                    self.place_ship(ship, add_to_map=False)

        def remove_ship(self, ship):
            """
            Removes a ship from this grid ship map

            IN:
                ship - ship to remove
            """
            for ship_list in self.ship_map.itervalues():
                if ship in ship_list:
                    ship_list.remove(ship)

        def is_valid_place_for_ship(self, x, y, ship):
            """
            Checks if a ship may be placed at the given coordinates

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
                columns = range(self.__width)
                rows = range(self.__height)

            elif ship_orientation == Ship.ORIENTATION_RIGHT:
                columns = range(self.__width)
                rows = range(self.__height, 0, -1)
                should_swap_coords = True

            elif ship_orientation == Ship.ORIENTATION_DOWN:
                columns = range(self.__width)
                rows = range(self.__height, 0, -1)

            else:
                columns = range(self.__width)
                rows = range(self.__height)
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

            for coords_tuple in ship.health.iterkeys():
                if coords_tuple == bow_coords:
                    square_type = Grid.SQUARE_TYPE_SHIP_BOW

                    if ship_orientation == Ship.ORIENTATION_UP:
                        _y = coords_tuple[1] - 1
                        for _x in range(coords_tuple[0] - 1, coords_tuple[0] + 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                        _y = coords_tuple[1]
                        for _x in range(coords_tuple[0] - 1, coords_tuple[0] + 2, 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                    elif ship_orientation == Ship.ORIENTATION_RIGHT:
                        _x = coords_tuple[0] + 1
                        for _y in range(coords_tuple[1] - 1, coords_tuple[1] + 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                        _x = coords_tuple[0]
                        for _y in range(coords_tuple[1] - 1, coords_tuple[1] + 2, 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                    elif ship_orientation == Ship.ORIENTATION_DOWN:
                        _y = coords_tuple[1] + 1
                        for _x in range(coords_tuple[0] - 1, coords_tuple[0] + 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                        _y = coords_tuple[1]
                        for _x in range(coords_tuple[0] - 1, coords_tuple[0] + 2, 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                    else:
                        _x = coords_tuple[0] - 1
                        for _y in range(coords_tuple[1] - 1, coords_tuple[1] + 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                        _x = coords_tuple[0]
                        for _y in range(coords_tuple[1] - 1, coords_tuple[1] + 2, 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                elif coords_tuple == stern_coords:
                    square_type = Grid.SQUARE_TYPE_SHIP_STERN

                    if ship_orientation == Ship.ORIENTATION_UP:
                        _y = coords_tuple[1] + 1
                        for _x in range(coords_tuple[0] - 1, coords_tuple[0] + 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                        _y = coords_tuple[1]
                        for _x in range(coords_tuple[0] - 1, coords_tuple[0] + 2, 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                    elif ship_orientation == Ship.ORIENTATION_RIGHT:
                        _x = coords_tuple[0] - 1
                        for _y in range(coords_tuple[1] - 1, coords_tuple[1] + 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                        _x = coords_tuple[0]
                        for _y in range(coords_tuple[1] - 1, coords_tuple[1] + 2, 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                    elif ship_orientation == Ship.ORIENTATION_DOWN:
                        _y = coords_tuple[1] - 1
                        for _x in range(coords_tuple[0] - 1, coords_tuple[0] + 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                        _y = coords_tuple[1]
                        for _x in range(coords_tuple[0] - 1, coords_tuple[0] + 2, 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                    else:
                        _x = coords_tuple[0] + 1
                        for _y in range(coords_tuple[1] - 1, coords_tuple[1] + 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                        _x = coords_tuple[0]
                        for _y in range(coords_tuple[1] - 1, coords_tuple[1] + 2, 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                else:
                    square_type = Grid.SQUARE_TYPE_SHIP_HULL

                    if ship_orientation in Ship.VERT_ORIENTATIONS:
                        _y = coords_tuple[1]
                        for _x in range(coords_tuple[0] - 1, coords_tuple[0] + 2, 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                    else:
                        _x = coords_tuple[0]
                        for _y in range(coords_tuple[1] - 1, coords_tuple[1] + 2, 2):
                            self._set_square_at(_x, _y, Grid.SQUARE_TYPE_SHIP_SPACING)

                self._set_square_at(coords_tuple[0], coords_tuple[1], square_type)

                if add_to_map:
                    # If the ship was placed incorrectly, then its coords may be out of this grid
                    if coords_tuple in self.ship_map:
                        self.ship_map[coords_tuple].append(ship)

        def place_ships(self, ships):
            """
            Places ships on this grid at random position

            NOTE: This does respect ship placement

            IN:
                ships - list of Ship objects
            """
            done = False
            while not done:
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
                    done = True

    class Ship(object):
        """
        TODO: make this a displayable
        """
        # Orientation consts
        # TODO: use the angles as values here
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
            self.__stern_coords = tuple()# This will be filled later
            self.__length = length
            self.__orientation = orientation

            self.health = OrderedDict()# This will be filled later
            self.is_alive = True
            self.__update_props()

        def __update_props(self):
            """
            Updates this ship prop
            """
            x, y = self.__bow_coords

            # Update/set stern coords
            if self.__orientation == Ship.ORIENTATION_UP:
                self.__stern_coords = (x, y + (self.__length - 1))

            elif self.__orientation == Ship.ORIENTATION_RIGHT:
                self.__stern_coords = (x - (self.__length - 1), y)

            elif self.__orientation == Ship.ORIENTATION_DOWN:
                self.__stern_coords = (x, y - (self.__length - 1))

            else:
                self.__stern_coords = (x + (self.__length - 1), y)

            # Update/set health
            _health = self.health.values() or [True for k in range(self.__length)]
            self.health.clear()

            for i in range(self.__length):
                if self.__orientation == Ship.ORIENTATION_UP:
                    self.health[(x, y + i)] = _health[i]

                elif self.__orientation == Ship.ORIENTATION_RIGHT:
                    self.health[(x - i, y)] = _health[i]

                elif self.__orientation == Ship.ORIENTATION_DOWN:
                    self.health[(x, y - i)] = _health[i]

                else:
                    self.health[(x + i, y)] = _health[i]

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
            self.__update_props()

        @property
        def stern_coords(self):
            """
            Prop getter for stern coords
            """
            return self.__stern_coords

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
            """
            self.__orientation = value

            if self.__orientation < Ship.ORIENTATION_UP:
                self.__orientation = Ship.ORIENTATION_LEFT

            elif self.__orientation > Ship.ORIENTATION_LEFT:
                self.__orientation = Ship.ORIENTATION_UP

            self.__update_props()

        def register_hit(self, x, y):
            """
            """
            key = (x, y)
            if key not in self.health:
                return

            self.health[key] = False
            self.is_alive = any(self.health.values())

        def copy(self):
            """
            Returns a copy of this ship

            OUT:
                new Ship objects with the same params as this one
            """
            ship = Ship(self.__bow_coords[0], self.__bow_coords[1], self.__length, self.__orientation)

            for key, value in zip(ship.health.keys(), self.health.values()):
                ship.health[key] = value

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
                ship_set - set to build ships by

            OUT:
                list of Ship objects
            """
            ships = list()
            for ship_length in ship_set:
                ships.append(cls.build_ship(0, 0, ship_length))

            return ships

    class Player(object):
        """
        """
        def __init__(self, id, ship_set):
            """
            """
            self.id = id
            self.ship_set = ship_set
            self.grid = Grid()
            self.ships = list()

            self.hits_coords = list()
            self.misses_coords = list()
