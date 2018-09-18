#!/usr/bin/python
# coding: utf-8

import curses, locale
import sys, traceback
from random import randint

class DEBUG_TOOL:
    @staticmethod
    def debug(pos, info):
        GameControl.draw_one_cell(pos, "{0:>3} ".format(str(info)))
        GameControl.win.timeout(10)
        GameControl.win.getch()

    @staticmethod
    def debug_to_file(info):
        info = str(info)
        fw = open("log", "ab")
        fw.write(info)
        fw.write("\n")
        fw.close()

    @staticmethod
    def debug_out_board(input_board, snake, food):
        board = input_board[:]
        fw = open("log", "ab")
        fw.write("=" * 3 * CONSTANT.CURSES_WIDTH + "\n")
        for i in range(len(board)):
            if i == food.sn:
                board[i] = "@"
            elif i == snake.body[0]:
                board[i] = "*"
            elif i in snake.body:
                board[i] = "#"
            info = "{0:>3}".format(str(board[i]))
            fw.write(info)
            if i and (i+1) % CONSTANT.CURSES_WIDTH == 0:
                fw.write("\n")
        fw.write("=" * 3 * CONSTANT.CURSES_WIDTH + "\n")
        fw.close()

class CONSTANT:
    from curses import KEY_RIGHT  # 261
    from curses import KEY_LEFT   # 260
    from curses import KEY_UP     # 259
    from curses import KEY_DOWN   # 258

    KEY_ESC = 27
    KEY_NONE = -1

    SPEED_SLOW = 100
    SPEED_NORM = 10
    SPEED_FAST = 1

    GAME_SPPED = SPEED_NORM

    CURSES_WIDTH  = 20
    CURSES_HEIGHT = 10
    CURSES_SIZE   = CURSES_WIDTH * CURSES_HEIGHT

    BOARD_WIDTH   = CURSES_WIDTH  - 2
    BOARD_HEIGHT  = CURSES_HEIGHT - 2
    BOARD_SIZE    = BOARD_WIDTH * BOARD_HEIGHT

    ICON_FOOD = "@"
    ICON_HEAD = "*"
    ICON_BODY = "#"
    ICON_NONE = " "

    MOVE_ACT = {
        KEY_DOWN:   CURSES_WIDTH,
        KEY_UP:    -CURSES_WIDTH,
        KEY_RIGHT:  1,
        KEY_LEFT:  -1,
    }

    KEY_ARROW = {
        KEY_DOWN:   "↓",
        KEY_UP:     "↑",
        KEY_RIGHT:  "→",
        KEY_LEFT:   "←",
    }

    KEY_LIST = [KEY_DOWN, KEY_UP, KEY_RIGHT, KEY_LEFT]

class Food(object):
    _instance = None

    def __new__(cls, *args, **kw):
        if not cls._instance:
            cls._instance = super(Food, cls).__new__(cls, *args, **kw)
            cls._instance.sn = None
            cls._instance.exist = False
        return cls._instance

    def __init__(self, snake):
        self.__new(snake)

    def __new(self, snake):
        if not self.__class__._instance.exist:
            sn = GameControl.rand_food()
            while sn in snake.body:
                sn = GameControl.rand_food()

            self.__class__._instance.sn = sn
            self.__class__._instance.snake = snake
            GameControl.draw_one_cell(self.__class__._instance.sn, CONSTANT.ICON_FOOD)
            self.__class__._instance.exist = True
        else:
            pass

    def __delete(self):
        self.__class__._instance.exist = False

    def renew(self):
        self.__delete()
        self.__new(self.__class__._instance.snake)

class Snake(object):
    def __init__(self, snake=None):
        if not snake:
            self.board = [0] * CONSTANT.CURSES_SIZE

            self.body = []
            self.body.append(2 * CONSTANT.CURSES_WIDTH + 6)
            self.body.append(self.body[0] - 1)
            self.body.append(self.body[1] - 1)

            self.__draw_self()
        else:
            self.board = snake.board[:]
            self.body  = snake.body[:]

    def __hit_wall(self, key):
        return GameControl.hit_wall(self.body[0], key)

    def __hit_body(self, key):
        head = self.body[0]
        head += CONSTANT.MOVE_ACT.get(key, 0)
        return head in self.body[:-1]

    def __draw_self(self):
        for i in range(0, len(self.body)):
            GameControl.draw_one_cell(self.body[i], CONSTANT.ICON_NONE)

        GameControl.draw_one_cell(self.body[0], CONSTANT.ICON_HEAD)

        for i in range(1, len(self.body)):
            GameControl.draw_one_cell(self.body[i], CONSTANT.ICON_BODY)

    def move(self, key, virtual_move=False):
        if self.__hit_wall(key) or self.__hit_body(key):
            return False

        food = Food(self)
        tail = self.body[-1]

        if not virtual_move:
            GameControl.draw_one_cell(self.body[-1], CONSTANT.ICON_NONE)

        for i in xrange(len(self.body)-1, 0, -1):
            self.body[i] = self.body[i-1]
        self.body[0] += CONSTANT.MOVE_ACT.get(key, 0)

        if not virtual_move:
            # self.board[tail] = 99
            if self.body[0] == food.sn:
                self.body.append(tail)
                food.renew()
            self.__draw_self()

        return True

class AI(object):
    def __init__(self, snake):
        self.snake = snake
        self.food = Food(snake)

    def __bfs(self, snake, target, refresh_board=True):
        snake.board = [0] * CONSTANT.CURSES_SIZE if refresh_board else snake.board
        visited = {}
        queue = []
        queue.append(target)
        has_way = False
        while queue:
            sn = queue.pop(0)
            if visited.get(sn): continue
            visited[sn] = 1
            for key in CONSTANT.KEY_LIST:
                nearby_sn = sn + CONSTANT.MOVE_ACT[key]
                if not GameControl.hit_wall(sn, key):
                    if nearby_sn == snake.body[0]:
                        has_way = True
                    if nearby_sn not in snake.body:
                        if not visited.get(nearby_sn):
                            snake.board[nearby_sn] = snake.board[sn] + 1 if refresh_board else snake.board[nearby_sn]
                            queue.append(nearby_sn)
        return has_way

    def __get_possible_keys(self, snake):
        possible_keys = []
        head = snake.body[0]
        for key in CONSTANT.KEY_LIST:
            nearby_sn = head + CONSTANT.MOVE_ACT[key]
            if not GameControl.hit_wall(head, key) and nearby_sn not in snake.body:
                possible_keys.append(key)
        return possible_keys

    def __choose_shortest_way(self, snake, target):
        min_distance = sys.maxsize
        shortest_key = None
        head = snake.body[0]
        self.__bfs(snake, target, refresh_board=True)
        for key in self.__get_possible_keys(snake):
            nearby_sn = head + CONSTANT.MOVE_ACT[key]
            if snake.board[nearby_sn] < min_distance:
                min_distance = snake.board[nearby_sn]
                shortest_key = key
        return shortest_key

    def __choose_longest_way(self, snake, target):
        max_distance = -1
        longest_key = None
        head = snake.body[0]
        self.__bfs(snake, target, refresh_board=True)
        for key in self.__get_possible_keys(snake):
            nearby_sn = head + CONSTANT.MOVE_ACT[key]
            if snake.board[nearby_sn] > max_distance:
                max_distance = snake.board[nearby_sn]
                longest_key = key
        return longest_key

    def __eat_food(self, snake):
        food = self.food.sn
        shortest_key = self.__choose_shortest_way(snake, food)
        return shortest_key

    def __follow_tail(self, snake):
        tail = snake.body[-1]
        longest_key = self.__choose_longest_way(snake, tail)
        return longest_key

    def __wander(self, snake):
        possible_keys = self.__get_possible_keys(snake)
        wander_key = possible_keys[0] if possible_keys else None
        return wander_key

    def __can_follow_tail(self, snake):
        tail = snake.body[-1]
        return self.__bfs(snake, tail, refresh_board=False)

    # TODO: seems bug here
    def __send_virtual_snake(self):
        virtual_snake = Snake(self.snake)
        while virtual_snake.body[0] != self.food.sn:
            if not self.__bfs(virtual_snake, self.food.sn, refresh_board=False):
                return False
            food = self.food.sn
            shortest_key = self.__choose_shortest_way(virtual_snake, food)
            virtual_snake.move(shortest_key, virtual_move=True)
        return self.__can_follow_tail(virtual_snake)

    def control(self):
        way_to_food = self.__bfs(self.snake, self.food.sn, refresh_board=True)
        way_to_tail = self.__can_follow_tail(self.snake)

        ctrl_key = None
        if way_to_food:
            virtual_snake_safe = self.__send_virtual_snake()

            if virtual_snake_safe:
                ctrl_key = self.__eat_food(self.snake)
            else:
                ctrl_key = self.__follow_tail(self.snake)

        elif way_to_tail:
            ctrl_key = self.__follow_tail(self.snake)

        else:
            ctrl_key = self.__wander(self.snake)

        return ctrl_key


class GameControl:
    win = None

    @staticmethod
    def init_trap_int():
        import signal
        def handler(signum, frame):
            GameControl.close_screen()
            print "programe stoped for SIGINT received"
            sys.exit()
        signal.signal(signal.SIGINT, handler)

    @staticmethod
    def init_screen():
        locale.setlocale(locale.LC_ALL, "");

        curses.initscr()
        curses.noecho()
        curses.curs_set(0)

        GameControl.win = curses.newwin(CONSTANT.CURSES_HEIGHT, CONSTANT.CURSES_WIDTH, 0, 0)
        GameControl.win.keypad(1)
        GameControl.win.border(0)
        GameControl.win.nodelay(1)

        GameControl.win.timeout(10)
        GameControl.win.getch()

    @staticmethod
    def close_screen():
        curses.endwin()

    @staticmethod
    def draw_one_cell(sn, ch):
        GameControl.win.addstr(sn / CONSTANT.CURSES_WIDTH, sn % CONSTANT.CURSES_WIDTH + 1, ch)

    @staticmethod
    def rand_food():
        row  = randint(1, CONSTANT.CURSES_HEIGHT - 2)
        line = randint(0, CONSTANT.CURSES_WIDTH - 3)
        sn = row * CONSTANT.CURSES_WIDTH + line
        return sn

    @staticmethod
    def hit_wall(sn, key):
        if   key == CONSTANT.KEY_LEFT:
            return False if sn % CONSTANT.CURSES_WIDTH > 0 else True
        elif key == CONSTANT.KEY_RIGHT:
            return False if sn % CONSTANT.CURSES_WIDTH < (CONSTANT.CURSES_WIDTH - 3) else True
        elif key == CONSTANT.KEY_UP:
            return False if sn / CONSTANT.CURSES_WIDTH > 1 else True
        elif key == CONSTANT.KEY_DOWN:
            return False if (sn / CONSTANT.CURSES_WIDTH) < (CONSTANT.CURSES_HEIGHT - 2) else True
        return True

    @staticmethod
    def is_direction_key(key):
        direction_list = [CONSTANT.KEY_ESC, CONSTANT.KEY_LEFT, CONSTANT.KEY_UP, CONSTANT.KEY_RIGHT, CONSTANT.KEY_DOWN]
        return key in direction_list

    @staticmethod
    def play_game():
        win = GameControl.win

        cur_key = CONSTANT.KEY_RIGHT

        snake = Snake()
        food = Food(snake)
        ai = AI(snake)

        while cur_key != CONSTANT.KEY_ESC:
            win.timeout(CONSTANT.GAME_SPPED)

            got_key = win.getch()
            if got_key == CONSTANT.KEY_ESC:
                DEBUG_TOOL.debug_out_board(ai.snake.board, ai.snake, food)
            cur_key = ctrl_key = got_key if GameControl.is_direction_key(got_key) else cur_key
            cur_key = ctrl_key = ai.control()
            snake.move(ctrl_key)

def main():
    try:
        GameControl.init_trap_int()
        GameControl.init_screen()
        GameControl.play_game()
        GameControl.close_screen()

    except Exception as e:
        GameControl.close_screen()
        err_info = traceback.format_exc()
        print err_info

    finally:
        pass

if __name__ == "__main__":
    main()





