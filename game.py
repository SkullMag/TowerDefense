from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.grid import Grid
from playsound import playsound
from threading import Thread
import pygame as pg
import math
import glob
import time
import sys
import os
import gc


fps = 60
app_running = True
cell_size = 100
tower_hp = 100
wave_count = 20
coins = 100
wave_speed = 800
start_timer_n = 10
start_timer_event_id = 30

game_map = list()
for i in open("map.map", "r", encoding="utf-8").readlines():
    a = []
    for j in i.strip("\n"):
        a.append(j)
    game_map.append(a)

pg.init()
width, height = cell_size * len(game_map[0]), cell_size * len(game_map)
screen = pg.display.set_mode((width, height))
clock = pg.time.Clock()

towers = pg.sprite.Group()
tiles = pg.sprite.Group()
enemies = pg.sprite.Group()

n_enemies = 0
screenshots_taken = 0


class Tile(pg.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()

        self.image = pg.image.load(img)
        self.image = pg.transform.scale(self.image, (cell_size, cell_size))
        self.rect = self.image.get_rect().move(cell_size * x, cell_size * y)

    def get_pos(self):
        return pg.math.Vector2(self.rect.center[0], self.rect.center[1])


class Enemy(pg.sprite.Sprite):
    def __init__(self, img, hp, x, y):
        super().__init__()

        self.image = pg.image.load("Sprites/skeleton.gif")
        self.image = pg.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect().move(cell_size * x + 25,
                                               cell_size * y + 25)
        self.hp = hp
        self.max_hp = hp
        self.current_direction = ""
        self.directions = None
        self.steps = 0

    def update(self):
        n = 5
        if self.current_direction == "r":
            self.rect.x += n
        elif self.current_direction == "l":
            self.rect.x -= n
        elif self.current_direction == "d":
            self.rect.y += n
        elif self.current_direction == "u":
            self.rect.y -= n
        self.steps += n
        if self.steps == n * 10:
            self.next_direction()
            self.steps = 0

    def next_direction(self):
        try:
            self.current_direction = next(self.directions)
        except StopIteration:
            global tower_hp

            tower_hp -= 10
            self.kill()
            del self

    def set_directions(self, directions):
        self.directions = (i for i in directions[:])

    def hit(self, damage: int):
        global coins

        if self.hp - damage <= 0:
            self.hp -= damage
            self.kill()
            coins += 10
            return True
        self.hp -= damage
        return False

    def get_pos(self):
        return pg.math.Vector2(self.rect.center[0], self.rect.center[1])


class Tower(pg.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()

        self.image = pg.image.load(img)
        self.image = pg.transform.scale(self.image, (cell_size, cell_size))
        self.rect = self.image.get_rect().move(100 * x, 100 * y)
        self.target = None
        self.x = x
        self.n = 0
        self.n_anim = 0

    def set_target(self, target: Enemy):
        self.target = target

    def hit_target(self):
        global coins

        if self.target not in enemies:
            self.target = None
            self.n = 0
        else:
            res = self.target.hit(50)

    def update_(self):
        if self.has_target():
            self.n += 1
            if self.n == 30:
                if self.get_pos().distance_to(self.target.get_pos()) < 200:
                    self.hit_target()
                    # self.rotate()
                else:
                    self.target = None
                self.n = 0
    
    def rotate(self):
        if self.n_anim < 240:
            self.n_anim += 1
        else:
            print(self.n_anim)
            direction = self.target.get_pos() - self.get_pos()
            radius, angle = direction.as_polar()

            self.image = pg.transform.rotate(self.orig_image, -angle)

            self.rect = self.image.get_rect(center=self.rect.center)
            self.n_anim = 0

    def has_target(self):
        return self.target is not None

    def get_pos(self):
        return pg.math.Vector2(self.rect.center[0], self.rect.center[1])


def load_map(path: str):
    global tiles
    tile_assets = {"#": "Sprites/grass_tile_1.png",
                   ".": "Sprites/sand_tile.png"}
    with open(path, "r", encoding="utf-8") as f:
        map_ = f.readlines()
        width = len(max(map_, key=len))
        height = len(map_)
        for y in range(height):
            for x in range(width):
                try:
                    tiles.add(Tile(tile_assets[map_[y][x]], x, y))
                except Exception:
                    pass


def text_objects(text, font, color):
    textSurface = font.render(text, True, pg.Color(color))
    return textSurface, textSurface.get_rect()


def message_display(text: str, x: int, y: int, size=50, color="black"):
    largeText = pg.font.Font('joystix.ttf', size)
    TextSurf, TextRect = text_objects(text, largeText, color)
    TextRect.center = (x, y)
    screen.blit(TextSurf, TextRect)


def find_path(start: tuple, end: tuple, map=game_map) -> list:
    matrix = list()
    for i in map:
        a = []
        for j in i:
            if j == "#":
                a.append(1)
            else:
                a.append(0)
        matrix.append(a)
    grid = Grid(matrix=matrix)

    start = grid.node(*start)
    end = grid.node(*end)

    finder = AStarFinder()
    path, _ = finder.find_path(start, end, grid)
    return path


def create_path_string(path: list) -> str:
    s = ""
    for i in range(len(path)):
        try:
            if path[i][0] < path[i + 1][0]:
                s += "rr"
            elif path[i][0] > path[i + 1][0]:
                s += "ll"
            elif path[i][1] < path[i + 1][1]:
                s += "dd"
            elif path[i][1] > path[i + 1][1]:
                s += "uu"
        except:
            pass
    return [i for i in s]


def check_for_killed():
    global wave_speed
    while [i for i in enemies] != []:
        time.sleep(1)
    wave_speed = int(wave_speed * .9)
    pg.time.set_timer(event_id, wave_speed)


def terminate():
    pg.quit()
    sys.exit()


def display_start_menu():
    start_button = pg.transform.scale(
        pg.image.load("Sprites/button.png"), (400, 100))
    credits_button = pg.transform.scale(
        pg.image.load("Sprites/button.png"), (400, 100))
    exit_button = pg.transform.scale(
        pg.image.load("Sprites/button.png"), (400, 100))
    screen.fill(pg.Color("orange"))
    screen.blit(credits_button, (width // 2 - 200, 300))
    screen.blit(start_button, (width // 2 - 200, 200))
    screen.blit(exit_button, (width // 2 - 200, 400))
    message_display("Start", width // 2, 245)
    message_display("Credits", width // 2, 345)
    message_display("Exit", width // 2, 445)
    message_display("Tower Defense", width // 2, 70)


def display_credits_tab():
    main_menu = pg.transform.scale(
        pg.image.load("Sprites/button.png"), (400, 100))
    screen.blit(main_menu, (width // 2 - 200, 525))
    message_display(
        "main purpose of this game is for you to have fun",
        width // 2, 230, 30)
    message_display(
        "in this game you have to defend the tower from skeletons", 
        width // 2, 300, 30)
    message_display(
        "you should enjoy playing and replaying it every time", 
        width // 2, 370, 30)
    message_display("this game was created by rybalko oleg",
                    width // 2, 440, 30)
    message_display("<main menu",  width // 2, 570, 40)


def create_waves() -> tuple:
    waves = []
    for j in range(20):
        a = []
        for i in range(10 + j):
            if i == 0:
                if j == 0:
                    a.append(Enemy(None, 100, 0, 3))
                else:
                    a.append(Enemy(None, waves[-1][-1].hp + 4, 0, 3))
            else:
                a.append(Enemy(None, a[i - 1].hp + 4, 0, 3))
        waves.append(a)
    waves = (i for i in waves)
    current_wave = next(waves)
    return waves, current_wave


def start_screen():
    display_start_menu()
    current_menu = "main"

    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                terminate()
            if event.type == pg.MOUSEBUTTONDOWN:
                if current_menu == "main":
                    if pg.mouse.get_pressed()[0] == 1:
                        mouse = pg.mouse.get_pos()
                        if mouse[0] in range(width // 2 - 200,
                                             width // 2 - 200 + 400) and\
                                mouse[1] in range(300, 400):
                            current_menu = "credits"
                            screen.fill(pg.Color("orange"))
                            display_credits_tab()
                        elif mouse[0] in range(width // 2 - 200,
                                               width // 2 - 200 + 400) and\
                                mouse[1] in range(200, 300):
                            global waves, current_wave, screenshots_taken
                            global n_enemies, wave_count, start_timer_n
                            global tower_hp
                            pg.time.set_timer(start_timer_event_id, 1000)
                            tower_hp = 100
                            waves, current_wave = create_waves()
                            screenshots_taken = 0
                            n_enemies = 0
                            wave_count = 20
                            start_timer_n = 10

                            return
                        elif mouse[0] in range(width // 2 - 200,
                                               width // 2 - 200 + 400) and\
                                mouse[1] in range(400, 500):
                            terminate()
                elif current_menu == "credits":
                    if pg.mouse.get_pressed()[0] == 1:
                        mouse = pg.mouse.get_pos()
                        if mouse[0] in range(width // 2 - 200,
                                             width // 2 - 200 + 400) and\
                                mouse[1] in range(525, 625):
                            current_menu = "main"
                            screen.fill(pg.Color("orange"))
                            display_start_menu()

        pg.display.flip()
        clock.tick(fps)


event_id = 2

load_map("map.map")

heart = pg.sprite.Sprite()
heart.image = pg.image.load("Sprites/heart.png")
heart.image = pg.transform.scale(heart.image, (64, 55))
heart.rect = heart.image.get_rect()
heart.rect.center = (50, 50)

coin = pg.sprite.Sprite()
coin.image = pg.image.load("Sprites/coin.png")
coin.image = pg.transform.scale(coin.image, (64, 55))
coin.rect = coin.image.get_rect()
coin.rect.center = (50, 120)

arrow = pg.sprite.Sprite()
arrow.image = pg.image.load("Sprites/arrow.png")
arrow.image = pg.transform.scale(arrow.image, (64, 64))
arrow.rect = arrow.image.get_rect()
arrow.rect.center = (50, 350)

gc.collect()
start_screen()

while app_running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            app_running = False
        if event.type == start_timer_event_id:
            start_timer_n -= 1
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                wave_count = 0
        if event.type == event_id:
            if n_enemies < len(current_wave):
                path = find_path((0, 3), (15, 3))
                path_string = create_path_string(path)
                enemy = current_wave[n_enemies]
                enemy.set_directions(path_string)
                enemies.add(enemy)
                n_enemies += 1
            else:
                pg.time.set_timer(event_id, 0)
                n_enemies = 0
                wave_count -= 1

                try:
                    current_wave = next(waves)
                    Thread(target=check_for_killed).start()
                except StopIteration:
                    print("Game over")

        if event.type == pg.MOUSEBUTTONDOWN:
            x, y = pg.mouse.get_pos()
            cell = x // cell_size, y // cell_size
            if event.button == pg.BUTTON_RIGHT:
                if game_map[cell[1]][cell[0]] == "@":
                    game_map[cell[1]][cell[0]] = "#"
                    coins += 25
                    for i in towers:
                        if i.rect.center[0] // 100 == cell[0] and\
                            i.rect.center[1] // 100 == cell[1]:

                            i.kill()
            elif event.button == pg.BUTTON_LEFT:
                mouse = pg.mouse.get_pos()
                if mouse[0] in range(width // 2 - 200,
                                     width // 2 - 200 + 400) and\
                        mouse[1] in range(width // 2 - 310, width // 2 + 70):
                    current_menu = "main"
                    start_screen()

                if game_map[cell[1]][cell[0]] != "@" and coins - 50 >= 0:
                    temp_map = game_map[:]
                    temp_map[cell[1]][cell[0]] = "@"
                    path = find_path((0, 3), (15, 3), temp_map)
                    if len(path) > 0 and not (cell[0] == 0 and cell[1] == 3):
                        coins -= 50
                        tw = Tower("Sprites/rocket.png", cell[0], cell[1])
                        towers.add(tw)
                        game_map[cell[1]][cell[0]] = "@"

    for target in enemies:
        for tw in towers:
            if tw.get_pos().distance_to(target.get_pos()) < 200 and\
                    target in enemies and tw.has_target() is False:
                tw.set_target(target)
                tw.hit_target()
    for tw in towers:
        if tw.has_target():
            tw.update_()

    enemies.update()
    tiles.draw(screen)
    towers.draw(screen)
    screen.blit(arrow.image, arrow.rect)
    enemies.draw(screen)
    for enemy in enemies:
        pg.draw.rect(screen, pg.Color("red"),
                     (enemy.rect.x, enemy.rect.y - 20, 50, 8))
        w = enemy.hp / enemy.max_hp
        pg.draw.rect(screen, pg.Color("green"),
                     (enemy.rect.x, enemy.rect.y - 20, 50 * w, 8))
            
    if start_timer_n > 0:
        message_display("First wave in " + str(start_timer_n), width // 2, 50)
    elif start_timer_n == 0:
        pg.time.set_timer(event_id, 800)
        pg.time.set_timer(start_timer_event_id, 0)
        start_timer_n -= 1

    if wave_count == 0 or tower_hp <= 0:
        pg.time.set_timer(event_id, 0)
        if screenshots_taken == 0:
            pg.image.save(screen, "temp.png")
            screenshots_taken += 1
        screenshot = pg.transform.scale(pg.image.load("temp.png"), 
                                        (width // 2, height // 2))
        screen.fill(pg.Color("orange"))
        screen.blit(screenshot, (width // 4, height // 4))
        menu_button = pg.transform.scale(
            pg.image.load("Sprites/button.png"), (400, 100))
        screen.blit(menu_button, (width // 2 - 200, height - 150))
        message_display("<menu", width // 2, height - 100)
        current_menu = "scoring"
    else:
        message_display("Wave " + str(wave_count), width - 150, 50)
        message_display(str(tower_hp), 150, 50)
        message_display(str(coins), 150, 120)
        screen.blit(heart.image, heart.rect)
        screen.blit(coin.image, coin.rect)
    if tower_hp <= 0:
        message_display("Try again", width // 2, 50)
    elif wave_count == 0 and tower_hp > 0:
        message_display("congratulations!", width // 2, 50)
    pg.display.flip()
    clock.tick(fps)

pg.quit()
