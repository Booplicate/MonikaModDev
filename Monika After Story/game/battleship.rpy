init 999 python:
    mas_enable_quit()
    while mas_inEVL("mas_battleship_game_start"):
        mas_rmEVL("mas_battleship_game_start")
    if persistent.current_monikatopic != "mas_battleship_game_start":
        queueEvent("mas_battleship_game_start")

screen mas_battleship_ui(game):
    layer "minigames"

    vbox:
        xanchor 1.0
        xpos 1.0
        xoffset -mas_battleship.Battleship.GRID_SPACING
        yalign 0.0
        yoffset mas_battleship.Battleship.GRID_SPACING
        xmaximum 2*mas_battleship.Battleship.GRID_WIDTH + mas_battleship.Battleship.GRID_SPACING
        ymaximum config.screen_height
        xfill False
        yfill False
        spacing mas_battleship.Battleship.GRID_SPACING

        #         vbox:
        #             text "Score: 700-700"
        #             text "Grade: 10000"
        #             text "Best Grade: 100000"

        vbox:
            spacing mas_battleship.Battleship.GRID_SPACING

            frame:
                xanchor 0.0
                xpos 0.0
                xminimum 200

                vbox:
                    python:
                        if game.is_player_turn():
                            turn = store.player
                        else:
                            turn = "Monika"

                        target = game.get_hovering_square()

                    text "Turn: [turn]"
                    text "Target: [target]"

            frame:
                xanchor 1.0
                xpos 1.0

                hbox:
                    spacing 0

                    textbutton "Start":
                        action Function(game.set_phase_action)
                        sensitive game.is_in_preparation() and game.can_start_action()

                    textbutton "Reposition":
                        action Function(game.build_and_place_player_ships)
                        sensitive game.is_in_preparation()

                    textbutton "Shutdown":
                        action [
                            Function(game.mark_player_gaveup),
                            Function(game.set_phase_done),
                        ]
                        sensitive not game.is_done()

        add game:
            xanchor 1.0
            xpos 1.0

        if not game.is_in_preparation():
            frame:
                background None
                padding (0, 0, 0, 0)
                # HACK: without ymaximum this frame keeps expanding, even though it knows its children size and had yfill False
                # probably a bug in renpy
                ymaximum 0
                yfill False
                xanchor 0.0
                xpos 0.0

                frame:
                    xanchor 0.0
                    xpos 0.0
                    xminimum 132

                    vbox:
                        python:
                            ph = game.get_player_hits_count()
                            pm = game.get_player_misses_count()
                        text "Hits: [ph]"
                        text "Misses: [pm]"

                frame:
                    xanchor 0.0
                    xpos 0.0
                    xoffset mas_battleship.Battleship.GRID_WIDTH + mas_battleship.Battleship.GRID_SPACING
                    xminimum 132

                    vbox:
                        python:
                            mh = game.get_monika_hits_count()
                            mm = game.get_monika_misses_count()
                        text "Hits: [mh]"
                        text "Misses: [mm]"


label mas_battleship_game_start:
    window hide
    $ HKBHideButtons()
    $ disable_esc()

    $ mas_battleship.game = mas_battleship.Battleship()
    # $ renpy.start_predict(mas_battleship.game)
    $ mas_battleship.game.build_and_place_player_ships()
    $ mas_battleship.game.choose_first_player()

    if mas_battleship.game.is_player_turn():
        m 3eua "Your turn first."
    else:
        m 3hub "First turn is mine."

    show monika 1eua at t31
    show screen mas_battleship_ui(mas_battleship.game)

    # FALL THROUGH

label mas_battleship_game_loop:
    while not mas_battleship.game.is_done():
        if not mas_battleship.game.is_player_turn() and mas_battleship.game.is_in_action():
            $ mas_battleship.game.handle_monika_turn()
        $ ui.interact(type="minigame")

    pause 1.0
    # FALL THROUGH

label mas_battleship_game_end:
    if mas_battleship.game.is_player_winner():
        m 1hub "Congrats! ^^"

    elif mas_battleship.game.is_monika_winner():
        m 1euu "Better luck next time :P"

    elif mas_battleship.game.did_player_giveup():
        m 1eua "Aww, I really wanted to finish this one."

    else:
        m 1eua "[player], you shouldn't be able to see this. Is it a bug?"

    hide screen mas_battleship_ui
    # $ renpy.stop_predict(mas_battleship.game)
    show monika at t11

    $ mas_battleship.game = None

    $ enable_esc()
    $ HKBShowButtons()
    window auto

    return


init -30 python in mas_battleship:
    import math as meth

    # @renpy.atl_warper
    def _water_transform_warper(t):
        """
        Custom warper for time interpolation
        Based on: https://easings.net/#easeInOutBack
        Graph: https://www.desmos.com/calculator/wwt6eqizfb
        """
        c1 = -3.8
        c2 = c1 * 1.525

        if t < 0.5:
            return (meth.pow(2*t, 2) * ((c2 + 1)*2*t - c2)) / 2.0

        else:
            return (meth.pow(2*t - 2, 2) * ((c2 + 1)*(t*2 - 2) + c2) + 2) / 2.0

init -20:
    transform mas_battleship_water_transform(width, height):
        animation

        subpixel True
        anchor (0.0, 0.0)

        block:
            crop (0, 0, width//2, height//2)
            linear 30.0 crop (width//8, height//16, width//2, height//2)
            warp mas_battleship._water_transform_warper 70.0 crop (width//2, height//2, width//2, height//2)
            repeat

init -10 python in mas_battleship:
    import random
    import pygame
    import math as meth
    import itertools

    from collections import OrderedDict, Counter
    from renpy import store
    from store import (
        Image,
        Transform,
    )

    # The game object, will be set on game start
    game = None

    # class ExpressionManager(object):
    #     class Pose(object):
    #         """
    #         Monika's poses constants
    #         TODO: turn this into enum
    #         """
    #         RESTING = "1"
    #         CROSSED = "2"
    #         RESTING_POINT_RIGHT = "3"
    #         POINT_RIGHT = "4"
    #         # LEAN = "5"
    #         DOWN_POINRT_RIGHT = "7"

    #         @classmethod
    #         def switch_pose(cls, pose):
    #             """
    #             Switches from resting to crossed or vice versa

    #             IN:
    #                 pose - Pose constant, the pose to switch from
    #             """
    #             if pose == cls.RESTING:
    #                 return cls.CROSSED

    #             if pose == cls.CROSSED:
    #                 return cls.RESTING

    #             # Should never happen
    #             return pose

    #         @classmethod
    #         def transition_to_pointing(cls, pose, want_change_pose=False):
    #             """
    #             Finds an appropriate expr with pointing hand using the current pose

    #             IN:
    #                 pose - Pose constant, current pose
    #                 want_change_pose - bool, do we want to change from resting to crossed
    #                     or vice versa
    #             """
    #             if want_change_pose:
    #                 return cls.DOWN_POINRT_RIGHT

    #             if pose == cls.RESTING:
    #                 return cls.RESTING_POINT_RIGHT

    #             if pose == cls.CROSSED:
    #                 return cls.POINT_RIGHT

    #             # Should never happen
    #             return pose

    #         @classmethod
    #         def transition_from_pointing(cls, pose):
    #             """
    #             """
    #             if pose == cls.RESTING_POINT_RIGHT:
    #                 return cls.RESTING

    #             if pose == cls.POINT_RIGHT:
    #                 return cls.CROSSED

    #     class ExprSet(object):
    #         """
    #         Sets of expressions we're going to use for battleship dialogues
    #         """
    #         # NOTE: codes are pose-agnostic

    #         SURPRISED = "wud"
    #         PIKACHU_SURPRISED = "wuo"
    #         SMILE_EYES_NORMAL = "eua"
    #         SMILE_EYES_LEFT = "lua"
    #         SMILE_EYES_HAPPY = "hua"
    #         SMILE_EYES_SMUG = "tua"
    #         SMILE_EYES_SMUG_LEFT = "mua"
    #         SMUG_EYES_NORMAL = "euu"
    #         SMUG_EYES_SMUG = "tuu"
    #         SMUG_EYES_LEFT = "luu"
    #         SMUG_EYES_SMUG_LEFT = "muu"
    #         # POUT_EYES_LEFT = "lsp"
    #         TALK_EYES_NORMAL = "eub"
    #         TALK_EYES_SMUG = "tub"
    #         TALK_EYES_LEFT = "lub"
    #         TALK_EYES_HAPPY = "hub"
    #         TALK_EYES_SMUG_LEFT = "mub"
    #         THINKING_EYES_LEFT = "ltc"

    #     def __init__(self):
    #         self._pose = Pose.RESTING
    #         self._next_pose = Pose.CROSSED
    #         self._turns_without_pose_change = 0
    #         self._should_switch_pose = False

    #     def check_want_change_pose(self):
    #         if self._pose in (Pose.RESTING, Pose.CROSSED) and self._turns_without_pose_change > 2:
    #             self._next_pose = Pose.switch_pose(self._pose)
    #             self._should_switch_pose = True




    class Battleship(renpy.display.core.Displayable):
        """
        Event handler, render, and main logic for the game
        """
        ### Size and coords constants
        GRID_HEIGHT = 378
        GRID_WIDTH = GRID_HEIGHT
        GRID_SPACING = 5

        # PLAYER_FIELD_SIZE = 338

        CELL_HEIGHT = 32
        CELL_WIDTH = CELL_HEIGHT

        OUTER_FRAME_THICKNESS = 20
        INNER_GRID_THICKNESS = 2

        MAIN_GRID_ORIGIN_X = 0 # config.screen_width - 2 * (GRID_WIDTH + GRID_SPACING)
        MAIN_GRID_ORIGIN_Y = 0 # (config.screen_height - GRID_HEIGHT) // 2
        TRACKING_GRID_ORIGIN_X = GRID_WIDTH + GRID_SPACING # config.screen_width - GRID_WIDTH - GRID_SPACING
        TRACKING_GRID_ORIGIN_Y = MAIN_GRID_ORIGIN_Y # (config.screen_height - GRID_HEIGHT) // 2

        ### Grid sprites
        GRID_BACKGROUND = Image("/mod_assets/games/battleship/grid/background.png")
        GRID_FRAME = Image("/mod_assets/games/battleship/grid/frame.png")
        GRID = Image("/mod_assets/games/battleship/grid/grid.png")

        # HACK: The animated sprite is blinking at the edges, probably due to incorrect blitting and pixel smudging
        # I come up with a hack: we render this layer 2px bigger and overlap its edges with the grid frame
        HACK_WATER_LAYER_OFFSET = 2

        WATER_LAYER = store.Transform(
            store.mas_battleship_water_transform(
                child=Image("/mod_assets/games/battleship/water_loop.png"),
                width=1024,
                height=1024,
            ),
            # TODO: replace with xysize in r8
            size=(GRID_HEIGHT - OUTER_FRAME_THICKNESS*2 + HACK_WATER_LAYER_OFFSET*2, GRID_WIDTH - OUTER_FRAME_THICKNESS*2 + HACK_WATER_LAYER_OFFSET*2),
        )

        ### Indicators
        CELL_HOVER = Image("/mod_assets/games/battleship/indicators/hover.png")
        CELL_CONFLICT = Image("/mod_assets/games/battleship/indicators/conflict.png")
        CELL_HIT = Image("/mod_assets/games/battleship/indicators/hit.png")
        CELL_MISS = Image("/mod_assets/games/battleship/indicators/miss.png")

        ### Ships sprites
        SHIP_5_SQUARES = Image("/mod_assets/games/battleship/ships/carrier.png")
        SHIP_4_SQUARES = Image("/mod_assets/games/battleship/ships/battleship.png")
        SHIP_3_SQUARES = Image("/mod_assets/games/battleship/ships/submarine.png")
        SHIP_2_SQUARES = Image("/mod_assets/games/battleship/ships/destroyer.png")

        # Used for sunk ships
        GREYOUT_MATRICX = store.im.matrix.desaturate() * store.im.matrix.brightness(-0.25)

        ALL_SHIP_SPRITES = (SHIP_5_SQUARES, SHIP_4_SQUARES, SHIP_3_SQUARES, SHIP_2_SQUARES)

        ALL_SHIPS_TYPES = (5, 4, 3, 2)

        SHIP_SET_CLASSIC = (5, 4, 4, 3, 3, 3, 2, 2, 2, 2)

        # Map between ship types and sprites
        # TODO: support multiple sprites for one ship type?
        SHIP_SPRITES_MAP = OrderedDict(zip(ALL_SHIPS_TYPES, ALL_SHIP_SPRITES))

        class GamePhase(object):
            """
            Types of Game phases
            TODO: turn this into enum
            """
            PREPARATION = 0
            ACTION = 1
            DONE = 2

        class WinState(object):
            """
            Types of win conditions
            TODO: turn this into enum
            """
            UNKNOWN = 0
            PLAYER_WON = 1
            MONIKA_WON = 2
            PLAYER_GAVEUP = 3

        def __init__(self):
            """
            """
            super(Battleship, self).__init__()

            self._last_mouse_x = 0
            self._last_mouse_y = 0

            self._is_sensitive = True

            self._turn = 0
            self._is_player_turn = False
            self._phase = self.GamePhase.PREPARATION
            self._win_state = self.WinState.UNKNOWN

            self._hovered_cell = None
            self._dragged_ship = None
            self._grid_conflicts = []

            self._ship_sprites_cache = {}

            self._player = Player(self.SHIP_SET_CLASSIC)
            self._monika = AIPlayer(self.SHIP_SET_CLASSIC, RandomStrategy(self))

            # FIXME: this is temp
            self._monika.grid.place_ships(Ship.build_ships(self._monika.ship_set))

        def choose_first_player(self):
            """
            Decides who will shoot in the first turn, sets the flag
            """
            self._is_player_turn = random.random() < 0.5

        def _switch_turn(self):
            """
            Switches turn between Monika and player
            """
            self._is_player_turn = not self._is_player_turn

        def is_player_turn(self):
            return self._is_player_turn


        def mark_player_won(self):
            self._win_state = self.WinState.PLAYER_WON

        def mark_monika_won(self):
            self._win_state = self.WinState.MONIKA_WON

        def mark_player_gaveup(self):
            self._win_state = self.WinState.PLAYER_GAVEUP

        def is_player_winner(self):
            return self._win_state == self.WinState.PLAYER_WON

        def is_monika_winner(self):
            return self._win_state == self.WinState.MONIKA_WON

        def did_player_giveup(self):
            return self._win_state == self.WinState.PLAYER_GAVEUP


        def get_player_hits_count(self):
            return self._player.total_hits()

        def get_player_misses_count(self):
            return self._player.total_misses()

        def get_monika_hits_count(self):
            return self._monika.total_hits()

        def get_monika_misses_count(self):
            return self._monika.total_misses()


        def can_start_action(self):
            """
            Checks if all players' ships are placed and valid

            OUT:
                bool
            """
            for player in (self._player, self._monika):
                if player.grid.has_conflicts():
                    return False

                set_ships = Counter(player.ship_set)
                grid_ships = Counter(ship.length for ship in player.grid.iter_ships())

                if set_ships != grid_ships:
                    return False

            return True

        def is_in_preparation(self):
            """
            Returns True if the players are positioning their ships

            OUT:
                bool
            """
            return self._phase == self.GamePhase.PREPARATION

        def is_in_action(self):
            """
            Returns True if the game is in active phase

            OUT:
                bool
            """
            return self._phase == self.GamePhase.ACTION

        def is_done(self):
            """
            Returns True if at least one player has lost all of their ships

            OUT:
                bool
            """
            return self._phase == self.GamePhase.DONE

        def set_phase_action(self):
            """
            Changes the game phase to action

            NOTE: returning a non-None value is important, this way we end the interaction
            from the screen action

            OUT:
                bool
            """
            if self.is_in_action() or not self.can_start_action():
                return False

            self._phase = self.GamePhase.ACTION
            return True

        def set_phase_done(self):
            """
            Changes the game phase to done

            NOTE: returning a non-None value is important, this way we end the interaction
            from the screen action

            OUT:
                bool
            """
            self._phase = self.GamePhase.DONE
            self._is_sensitive = False
            return True


        @staticmethod
        def _update_screens():
            """
            Request renpy to update all screens
            """
            renpy.restart_interaction()

        def get_hovering_square(self):
            """
            Returns a human-readable name of the cell
            that the player is hovering mouse above

            OUT:
                str like "A1" or "J10"
            """
            if not self._hovered_cell:
                return "n/a"

            UNICOED_CODE_POINT_OFFSET = 65
            AXIS_OFFSET = 1
            x, y = self._hovered_cell

            return "{}{}".format(
                chr(x + UNICOED_CODE_POINT_OFFSET),
                y + AXIS_OFFSET,
            )


        @staticmethod
        def _get_monika_expr():
            """
            Returns current Monika's expression

            OUT:
                str | None
                    str will be of format like "1eua", "idle", etc
            """
            # NOTE: There's no renpy.get_attributes() in r6.12, so I will make one myself
            # TODO: Don't forget to remove in r8
            layer = renpy.exports.default_layer(None, "monika")

            if not renpy.showing("monika", layer):
                return None

            ctx = renpy.game.context()
            if not ctx:
                return None

            attrs = ctx.images.get_attributes(layer, "monika")
            if not attrs:
                return None

            return attrs[0]

        def invoke_say(self, what, expr=None, restore_expr=True):
            """
            Invokes renpy say from a new context allowing Monika speak mid game

            IN:
                what - str, what Monika will say
                expr - str | None, the expression to show if any
                restore_expr - bool, if an expr was given and this parameter is True,
                    then after the dialogue the expression will return to the previous one
            """
            previous_is_sensitive = self._is_sensitive
            self._is_sensitive = False

            prev_expr = None
            if expr:
                prev_expr = self._get_monika_expr()
                renpy.show("monika {}".format(expr))

            renpy.invoke_in_new_context(renpy.say, store.m, what, interact=True)

            if expr and prev_expr and restore_expr:
                renpy.show("monika {}".format(prev_expr))

            self._is_sensitive = previous_is_sensitive


        def build_and_place_player_ships(self):
            """
            Builds and places ships for the player on the grid

            NOTE: returning a non-None value is important, this way we end the interaction
            from the screen action
            """
            if not self.is_in_preparation():
                return False

            self._player.grid.clear()
            self._player.grid.place_ships(Ship.build_ships(self._player.ship_set))
            self._grid_conflicts[:] = self._player.grid.get_conflicts()

            return True

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
            key = (ship.length, ship.orientation, ship.is_alive())

            if key not in self._ship_sprites_cache:
                # NOTE: Sprites are headed up, but in our system 0 degrees is right, NOT up
                # so we need to adjust the angle to avoid rotation
                angle = ship.orientation - Ship.Orientation.UP
                sprite = self.SHIP_SPRITES_MAP[ship.length]
                if not ship.is_alive():
                    # TODO: use matrices in r8
                    sprite = store.im.MatrixColor(sprite, self.GREYOUT_MATRICX)

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
            main_render = renpy.Render(2*self.GRID_WIDTH + self.GRID_SPACING, self.GRID_HEIGHT)

            # # # Render grids
            # Predefine renders
            grid_background_render = renpy.render(self.GRID_BACKGROUND, width, height, st, at)
            grid_frame_render = renpy.render(self.GRID_FRAME, width, height, st, at)
            grid_render = renpy.render(self.GRID, width, height, st, at)
            water_layer_render = renpy.render(self.WATER_LAYER, width, height, st, at)
            # Now blit 'em
            main_render.subpixel_blit(grid_background_render, (self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y))
            main_render.subpixel_blit(
                water_layer_render,
                (
                    self.MAIN_GRID_ORIGIN_X + self.OUTER_FRAME_THICKNESS - self.HACK_WATER_LAYER_OFFSET,
                    self.MAIN_GRID_ORIGIN_Y + self.OUTER_FRAME_THICKNESS  - self.HACK_WATER_LAYER_OFFSET,
                ),
            )
            main_render.subpixel_blit(grid_frame_render, (self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y))
            main_render.subpixel_blit(grid_render, (self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y))

            # Render Monika's grid only during the game phase
            if self.is_in_action() or self.is_done():
                main_render.subpixel_blit(grid_background_render, (self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y))
                main_render.subpixel_blit(
                    water_layer_render,
                    (
                        self.TRACKING_GRID_ORIGIN_X + self.OUTER_FRAME_THICKNESS - self.HACK_WATER_LAYER_OFFSET,
                        self.TRACKING_GRID_ORIGIN_Y + self.OUTER_FRAME_THICKNESS - self.HACK_WATER_LAYER_OFFSET,
                    ),
                )
                main_render.subpixel_blit(grid_frame_render, (self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y))
                main_render.subpixel_blit(grid_render, (self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y))

            # Render conflicts
            if self.is_in_preparation():
                if self._grid_conflicts:
                    error_mask_render = renpy.render(self.CELL_CONFLICT, width, height, st, at)
                    for coords in self._grid_conflicts:
                        x, y = self._grid_coords_to_screen_coords(coords[0], coords[1], self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y)
                        main_render.subpixel_blit(error_mask_render, (x, y))

            # Render player's ships
            for ship in self._player.grid.iter_ships():
                ship_sprite = self._get_ship_sprite(ship)
                x, y = self._grid_coords_to_screen_coords(ship.bow_coords[0], ship.bow_coords[1], self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y)
                main_render.place(ship_sprite, x, y)

            # # # Render things that only relevant during the game
            if not self.is_in_preparation():
                # Render Monika's ships
                for ship in self._monika.grid.iter_ships():
                    if not ship.is_alive():
                        ship_sprite = self._get_ship_sprite(ship)
                        x, y = self._grid_coords_to_screen_coords(ship.bow_coords[0], ship.bow_coords[1], self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y)
                        main_render.place(ship_sprite, x, y)

                # Render hits
                hit_mark_render = renpy.render(self.CELL_HIT, width, height, st, at)
                for coords in self._player.iter_hits():
                    x, y = self._grid_coords_to_screen_coords(coords[0], coords[1], self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y)
                    main_render.subpixel_blit(hit_mark_render, (x, y))

                for coords in self._monika.iter_hits():
                    x, y = self._grid_coords_to_screen_coords(coords[0], coords[1], self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y)
                    main_render.subpixel_blit(hit_mark_render, (x, y))

                # Render misses
                miss_mark_render = renpy.render(self.CELL_MISS, width, height, st, at)
                for coords in self._player.iter_misses():
                    x, y = self._grid_coords_to_screen_coords(coords[0], coords[1], self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y)
                    main_render.subpixel_blit(miss_mark_render, (x, y))

                for coords in self._monika.iter_misses():
                    x, y = self._grid_coords_to_screen_coords(coords[0], coords[1], self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y)
                    main_render.subpixel_blit(miss_mark_render, (x, y))

                if not self.is_done():
                    # Render hovering mask
                    if self._hovered_cell is not None:
                        hover_mask_render = renpy.render(self.CELL_HOVER, width, height, st, at)
                        x, y = self._grid_coords_to_screen_coords(self._hovered_cell[0], self._hovered_cell[1], self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y)
                        main_render.subpixel_blit(hover_mask_render, (x, y))

            # # # Render things that only relevant during ship building
            elif self.is_in_preparation():
                # Render hovering mask
                if self._hovered_cell is not None:
                    hover_mask_render = renpy.render(self.CELL_HOVER, width, height, st, at)
                    x, y = self._grid_coords_to_screen_coords(self._hovered_cell[0], self._hovered_cell[1], self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y)
                    main_render.subpixel_blit(hover_mask_render, (x, y))

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

        def _redraw_now(self):
            """
            Requests redraw ASAP
            """
            renpy.redraw(self, 0)

        def _handle_preparation_events(self, ev, x, y, st):
            # # # The player pressed the rotation key
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_r:
                # If the player's dragging a ship, rotate it
                if self._dragged_ship is not None:
                    if ev.mod in (pygame.KMOD_LSHIFT, pygame.KMOD_RSHIFT):
                        self._dragged_ship.orientation -= 90
                    else:
                        self._dragged_ship.orientation += 90

                    self._grid_conflicts[:] = self._player.grid.get_conflicts()

                    self._redraw_now()
                    return True

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

                    self._redraw_now()
                    return True

            # # # The player moves the mouse, we may need to update the screen
            elif ev.type == pygame.MOUSEMOTION:
                # Continue to update the screen while the player's dragging a ship
                if self._dragged_ship is not None:
                    self._redraw_now()

                coords = self._screen_coords_to_grid_coords(x, y, self.MAIN_GRID_ORIGIN_X, self.MAIN_GRID_ORIGIN_Y)
                if coords != self._hovered_cell:
                    self._hovered_cell = coords
                    self._redraw_now()
                    self._update_screens()
                    # NOTE: usually we want to pass mousemoution events to other dispalyable
                    # but since we have to update screens here, this causes lag,
                    # so we ignore the mousemoution if we used it for hover/unhover
                    raise renpy.IgnoreEvent()

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

                self._redraw_now()
                return True

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

                # NOTE: If the ship is out of grid, we will return it where it was when player started dragging it
                self._player.grid.place_ship(self._dragged_ship)
                # Check for invalid placement
                self._grid_conflicts[:] = self._player.grid.get_conflicts()
                self._dragged_ship = None

                self._redraw_now()
                return True

        def _handle_action_events(self, ev, x, y, st):
            # # # The player moves the mouse, we may need to update the screen for hover events
            if ev.type == pygame.MOUSEMOTION:
                coords = self._screen_coords_to_grid_coords(x, y, self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y)
                if coords != self._hovered_cell:
                    self._hovered_cell = coords
                    self._redraw_now()
                    self._update_screens()
                    # NOTE: usually we want to pass mousemoution events to other dispalyable
                    # but since we have to update screens here, this causes lag,
                    # so we ignore the mousemoution if we used it for hover/unhover
                    raise renpy.IgnoreEvent()

            # # # The player releases the mouse button potentially shooting
            elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
                if not self.is_player_turn():
                    return

                coords = self._screen_coords_to_grid_coords(x, y, self.TRACKING_GRID_ORIGIN_X, self.TRACKING_GRID_ORIGIN_Y)
                if coords is None:
                    return

                if self._player.has_shot_at(coords):
                    # Already shot there
                    return

                ship = self._monika.grid.get_ship_at(coords[0], coords[1])
                if ship is None:
                    self._player.register_miss(coords)

                else:
                    self._player.register_hit(coords)
                    ship.take_hit()
                    if not ship.is_alive():
                        if self._monika.has_lost_all_ships():
                            self.set_phase_done()
                            self.mark_player_won()

                self._switch_turn()
                self._redraw_now()
                return True

        def handle_monika_turn(self):
            if self.is_player_turn():
                return

            coords = self._monika.pick_cell_for_attack()
            if coords is None:
                return

            if self._monika.has_shot_at(coords):
                # This should never happen!
                self._switch_turn()
                return

            quip = self._monika.pick_turn_start_quip(self)
            if quip is not None:
                self.invoke_say(quip[1], quip[0])
            else:
                renpy.pause(0.3)

            ship = self._player.grid.get_ship_at(coords[0], coords[1])
            if ship is None:
                self._monika.register_miss(coords)

            else:
                self._monika.register_hit(coords)
                ship.take_hit()
                if not ship.is_alive():
                    if self._player.has_lost_all_ships():
                        self.set_phase_done()
                        self.mark_monika_won()

            self._switch_turn()

        def event(self, ev, x, y, st):
            """
            Event handler
            """
            # Update internal mouse coords
            self._last_mouse_x = x
            self._last_mouse_y = y

            # When disabled we only process mouse motions
            if not self._is_sensitive and ev.type != pygame.MOUSEMOTION:
                return None

            if self.is_in_preparation():
                return self._handle_preparation_events(ev, x, y, st)

            elif self.is_in_action():
                return self._handle_action_events(ev, x, y, st)

            # TODO: use ignroeevent and only return True when the game is over, this'd allow to remove the loop from the label?
            # but this could cause problems with rollback
            return

        def visit(self):
            return [
                self.GRID_BACKGROUND,
                self.GRID_FRAME,
                self.GRID,
                self.WATER_LAYER,
                self.CELL_HOVER,
                self.CELL_CONFLICT,
                self.CELL_HIT,
                self.CELL_MISS,
                self.SHIP_5_SQUARES,
                self.SHIP_4_SQUARES,
                self.SHIP_3_SQUARES,
                self.SHIP_2_SQUARES,
            ]


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

            OUT:
                iterator over the list of ships
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

        def has_conflicts(self):
            """
            Returns True if there's ships on the grid that were placed incorrectly

            OUT:
                bool
            """
            for coords, cell_state in self._cell_states.iteritems():
                if cell_state == self.CellState.CONFLICT:
                    return True
            return False

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

        def __repr__(self):
            return "<{0}: (at: {1}, size: {2}, hp: {3})>".format(
                type(self).__name__,
                self.bow_coords,
                self.length,
                self._health,
            )

        def is_alive(self):
            return self._health > 0

        def take_hit(self):
            if self.is_alive():
                self._health -= 1

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
            offset = int(meth.hypot(self.bow_coords[0]-self.drag_coords[0], self.bow_coords[1]-self.drag_coords[1]))
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
        Meat battleship player
        """
        def __init__(self, ship_set):
            """
            Constructor
            """
            self.ship_set = ship_set
            self.grid = Grid()

            # Sets of tuples with coordinates
            self._hits = set()
            self._misses = set()

        def __repr__(self):
            return "<{0}: (ships: {1}, hits: {2}, misses: {3})>".format(
                type(self).__name__,
                list(self.grid.iter_ships()),
                sorted(self._hits),
                sorted(self._misses),
            )

        def get_total_alive_ships(self):
            """
            Returns a number of ships that are "alive"

            OUT:
                int
            """
            counter = 0
            for ship in self.grid.iter_ships():
                if ship.is_alive():
                    counter += 1

            return counter

        def has_lost_all_ships(self):
            """
            Checks whether or not the player has lost all their ships

            OUT:
                bool
            """
            for ship in self.grid.iter_ships():
                if ship.is_alive():
                    return False

            return True

        def register_hit(self, coords):
            """
            Adds a successful hit for this player

            IN:
                coords - a tuple of x and y coordinates
            """
            self._hits.add(coords)

        def register_miss(self, coords):
            """
            Adds a "successful" miss for this player

            IN:
                coords - a tuple of x and y coordinates
            """
            self._misses.add(coords)

        def has_shot_at(self, coords):
            """
            Returns True if this player has shot at the given coordinates

            IN:
                coords - a tuple of x and y coordinates

            OUT:
                bool
            """
            return coords in self._misses or coords in self._hits

        def total_hits(self):
            return len(self._hits)

        def total_misses(self):
            return len(self._misses)

        def iter_hits(self):
            """
            Returns iterator over this player hits

            OUT:
                iterator over the set of hits
            """
            return iter(self._hits)

        def iter_misses(self):
            """
            Returns iterator over this player misses

            OUT:
                iterator over the set of misses
            """
            return iter(self._misses)

    class _Quip(object):
        """
        A set of possible expressions and dialogue lines to pick from

        This automatically adds {w=}{nw} to the lines, so player don't have to click for each quip
        """
        def __init__(self, exprs, lines):
            """
            Creates a new quip

            IN:
                exprs - an iterable of expressions (str) that can be used with this quip
                    NOTE: can be passed as a single str if there's just one option
                lines - an iterable of str that can be displayed in dialogue
                    NOTE: can be passed as a single str if there's just one option
            """
            if isinstance(exprs, str):
                exprs = (exprs,)

            if isinstance(lines, str):
                lines = (lines,)

            if not exprs:
                raise ValueError("must provide at least one expression")
            if not lines:
                raise ValueError("must provide at least one line")

            self.exprs = exprs
            self.lines = lines

        def pick(self):
            """
            Picks an expr and a line from this quip

            OUT:
                tuple of exprs (str) and dlg (str)
            """
            if len(self.exprs) == 1:
                expr = self.exprs[0]
            else:
                expr = random.choice(self.exprs)

            if len(self.lines) == 1:
                line = self.lines[0]
            else:
                line = random.choice(self.lines)

            line += "{w=1.0}{nw}"

            return (expr, line)

    class _QuipSet(object):
        def __init__(self, *quips):
            """
            Creates a new quip set

            IN:
                quips - _Quip objects
            """
            if not quips:
                raise ValueError("must provide at least one quip")

            self.quips = quips

        def pick(self):
            """
            Picks a quip from this set

            OUT:
                tuple of exprs (str) and dlg (str)
            """
            if len(self.quips) == 1:
                quip = self.quips[0]
            else:
                quip = random.choice(self.quips)

            return quip.pick()

    class AIPlayer(Player):
        """
        Steal and circuits battleship player
        """

        _LINES_TURN_START_COMMON_0 = (
            _("Where are your ships I wonder.{w=0.1}.{w=0.1}.{w=0.1}"),
            _("Where could your ships be.{w=0.1}.{w=0.1}.{w=0.1}"),
            _("Where are your ships.{w=0.1}.{w=0.1}.{w=0.1}"),
            _("I wonder where your ships are.{w=0.1}.{w=0.1}.{w=0.1}"),
        )
        # Monika has many ships, player has more than 1 ship
        TURN_START_TEASE = _QuipSet(
            _Quip(
                exprs=("1mta", "2mta", "1mtu", "2mtu"),
                lines=_LINES_TURN_START_COMMON_0,
            ),
        )
        # Monika has a few ships, player has more than 1
        TURN_START_NORM = _QuipSet(
            _Quip(
                exprs=("1lta", "2lta"),
                lines=_LINES_TURN_START_COMMON_0,
            ),
            _Quip(
                exprs=("1lua", "2lua", "1luu", "2luu"),
                lines=(
                    "Let's see.{w=0.1}.{w=0.1}.{w=0.1}",
                    "Hmmm.{w=0.1}.{w=0.1}.{w=0.1}",
                ),
            ),
        )
        # Monika has 1-2 ships, player has more than 1
        TURN_START_WORRY = _QuipSet(
            _Quip(
                exprs=("2ltsdra", "2ltsdla"),
                lines=(
                    _LINES_TURN_START_COMMON_0
                    + (
                        "[player], I'm your girlfriend after all...{w=0.3}you could go a little bit easier on me~",
                        "Hmmm.{w=0.1}.{w=0.1}.{w=0.1}",
                    )
                ),
            ),
            _Quip(
                exprs=("2etsdra", "2eksdlu", "2ltsdra", "2ltsdla"),
                lines="[player], I'm your girlfriend after all...{w=0.3}you could go a little bit easier on me~",
            ),
        )
        # Monika has some ships, player has just one
        TURN_START_GREAT = _QuipSet(
            _Quip(
                exprs=("1mta", "2mta", "1mtu", "2mtu"),
                lines=(
                    _("Where is your last ships I wonder.{w=0.1}.{w=0.1}.{w=0.1}"),
                    _("Where could your last ship be.{w=0.1}.{w=0.1}.{w=0.1}"),
                    _("Where's your last ship.{w=0.1}.{w=0.1}.{w=0.1}"),
                    _("I wonder where is your last ship is.{w=0.1}.{w=0.1}.{w=0.1}"),
                ),
            ),
        )

        LOST_SHIP_NORM = _QuipSet(
            _Quip(
                exprs=("2etp", "2rtp"),
                lines=(
                    "Aww...",
                    "That's unfortunate...",
                    "Unlucky...",
                ),
            ),
        )

        SUNK_SHIP_NORM = _QuipSet(
            _Quip(
                exprs=("1efu", "21efu", "1tfu", "2tfu", "1huu", "2huu"),
                lines=(
                    "Ehehe~",
                    "There we go~",
                    "What was that?~",
                    "Ooops~",
                ),
            ),
        )

        def __init__(self, ship_set, strategy):
            """
            Constructor for AI player
            """
            super(AIPlayer, self).__init__(ship_set)
            self.strategy = strategy

        def pick_cell_for_attack(self):
            """
            AI plays turn

            OUT:
                tuple of coordinates
            """
            return self.strategy.pick_cell_for_attack()

        def pick_turn_start_quip(self, game):
            """
            Returns a quip for Monika's turn start

            IN:
                game - the game object

            OUT:
                a tuple of the expression and line or None
            """
            if random.random() > 0.1:
                return None

            player_ships_count = game._player.get_total_alive_ships()
            monika_ships_count = game._monika.get_total_alive_ships()
            ship_diff = player_ships_count - monika_ships_count

            if ship_diff >= 2 and monika_ships_count <= 2:
                return self.TURN_START_WORRY.pick()

            if player_ships_count == 1 and monika_ships_count > 1:
                return self.TURN_START_GREAT.pick()

            if ship_diff <= -2 and monika_ships_count >= 3:
                return self.TURN_START_WORRY.pick()

            return self.TURN_START_NORM.pick()


    ### abc.ABC sucks in py2, so just imagine it's here
    ### TODO: in r8 use abc or better Protocol for the interface

    class RandomStrategy(object):
        """
        AI will pick random cells to shoot at
        """
        def __init__(self, game, available_cells=None):
            self.game = game
            if available_cells is None:
                self.available_cells = set(
                    (col, row)
                    for row in range(Grid.HEIGHT)
                    for col in range(Grid.WIDTH)
                )
            else:
                self.available_cells = available_cells

        def pick_cell_for_attack(self):
            cell = random.choice(tuple(self.available_cells))
            self.available_cells.remove(cell)
            return cell
