from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.grid import Grid
from threading import Thread
import pygame as pg
import math
import glob
import time
import os
import gc


fps = 60
app_running = True
cell_size = 100
tower_hp = 100
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

        self.image = pg.Surface([cell_size // 2, cell_size // 2])
        self.image.fill(pg.Color("red"))
        self.rect = self.image.get_rect().move(cell_size * x + 25, cell_size * y + 25)
        self.hp = hp
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
    
    def get_name(self):
        return self.name
    
    def hit(self, tower, damage: int):
        if self.hp - damage <= 0:
            self.kill()
            del self
            return True
        else:
            self.hp -= damage
            return False
    
    def get_pos(self):
        return pg.math.Vector2(self.rect.center[0], self.rect.center[1])


class Tower(pg.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()

        self.image = pg.image.load(img)
        self.image = pg.transform.scale(self.image, (cell_size, cell_size))
        # self.image = pg.transform.flip(self.image, False, True)
        self.rect = self.image.get_rect().move(100 * x, 100 * y)
        self.target = None
        self.x = x
        self.n = 0
    
    def set_target(self, target: Enemy):
        self.target = target
    
    def hit_target(self):
        res = self.target.hit(self, 25)
        if self.target not in enemies:
            self.target = None
            self.n = 0
    
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
    
    def has_target(self):
        return self.target is not None
    
    def rotate(self):
        if self.has_target():
            direction = self.target.get_pos() - self.get_pos()
            radius, angle = direction.as_polar()
            self.image = pg.transform.rotate(self.image, -angle)
            self.rect = self.image.get_rect(center=self.rect.center)
    
    def get_pos(self):
        return pg.math.Vector2(self.rect.center[0], self.rect.center[1])


def load_map(path: str):
    global tiles
    tile_assets = {"#": "Sprites/grass_tile_1.png", ".": "Sprites/sand_tile.png"}
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


def text_objects(text, font):
    textSurface = font.render(text, True, pg.Color("black"))
    return textSurface, textSurface.get_rect()


def message_display(text: str, x: int, y: int):
    largeText = pg.font.Font('joystix.ttf', 50)
    TextSurf, TextRect = text_objects(text, largeText)
    TextRect.center = (x, y)
    screen.blit(TextSurf, TextRect)


def find_path(start: tuple, end: tuple) -> list:
    matrix = list()
    for i in game_map:
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

def create_enemy():
    path = find_path((0, 3), (15, 3))
    path_string = create_path_string(path)    
    enemy = Enemy(None, 1000, 0, 3)  
    enemy.set_directions(path_string)
    enemies.add(enemy)

event_id = 2
n_enemies = 0

load_map("map.map")

heart = pg.sprite.Sprite()
heart.image = pg.image.load("Sprites/heart.png")
heart.image = pg.transform.scale(heart.image, (64, 55))
heart.rect = heart.image.get_rect()
heart.rect.center = (50, 50)

gc.collect()

while app_running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            app_running = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                pg.time.set_timer(event_id, 500)
                create_enemy()
        if event.type == event_id:
            if n_enemies < 10:
                create_enemy()
                n_enemies += 1
            else:
                pg.time.set_timer(event_id, 0)
                n_enemies = 0

        if event.type == pg.MOUSEBUTTONDOWN:
            x, y = pg.mouse.get_pos()
            cell = x // cell_size, y // cell_size
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
    enemies.draw(screen)
    message_display("Wave 20", width - 150, 50)
    message_display(str(tower_hp), 150, 50)
    screen.blit(heart.image, heart.rect)
    pg.display.flip()
    clock.tick(fps)
        
pg.quit()