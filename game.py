from pathfinding.finder.a_star import AStarFinder
from pathfinding.core.grid import Grid
from threading import Thread
import pygame as pg
import glob
import time
import os
import gc


pg.init()
width, height = 1280, 720
screen = pg.display.set_mode((width, height))
clock = pg.time.Clock()

fps = 60
app_running = True
cell_size = 100
game_map = list()
for i in open("map.map", "r", encoding="utf-8").readlines():
    a = []
    for j in i.strip("\n"):
        a.append(j)
    game_map.append(a)
print(*game_map, sep="\n")

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
        self.rect = self.image.get_rect().move(cell_size // 2 * x + 25, cell_size // 2 * y + 25)
        self.hp = hp
        self.current_direction = ""
        self.directions = None
        self.steps = 0
    
    def update(self):
        if self.current_direction == "r":
            self.rect.x += 2.5
        elif self.current_direction == "l":
            self.rect.x -= 2.5
        elif self.current_direction == "d":
            self.rect.y += 2.5
        elif self.current_direction == "u":
            self.rect.y -= 2.5
        self.steps += 2.5
        if self.steps == 25:
            self.next_direction()
            self.steps = 0
    
    def next_direction(self):
        try:
            self.current_direction = next(self.directions)
        except StopIteration:
            self.kill()
            del self
    
    def set_directions(self, directions):
        self.directions = directions
    
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
        self.image = pg.transform.flip(self.image, False, True)
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
                if self.get_pos().distance_to(self.target.get_pos()) < 80:
                    self.hit_target()
                else:
                    self.target = None
                self.n = 0
    
    def has_target(self):
        return self.target is not None
    
    
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
    print(grid.grid_str(path=path, start=start, end=end))
    return path


def create_path_string(path: list) -> str:
    s = "r"
    for i in range(len(path)):
        try:
            if path[i][0] < path[i + 1][0]:
                s += "rrrr"
            elif path[i][0] > path[i + 1][0]:
                s += "llll"
            elif path[i][1] < path[i + 1][1]:
                s += "ddddd"
            elif path[i][1] > path[i + 1][1]:
                s += "uuuuu"
        except:
            pass
    return (i for i in s)


game_map[4][2] = "@"
game_map[4][3] = "@"
path = find_path((0, 4), (15, 4))
path_string = create_path_string(path)
load_map("map.map")
tower = Tower("Sprites/rocket.png", 2, 3)
tower1 = Tower("Sprites/rocket.png", 3, 3)
towers.add(tower)
towers.add(tower1)
enemy = Enemy(None, 200, 0, 6)
enemy.set_directions(path_string)
enemies.add(enemy)

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
    message_display("100", 150, 50)
    screen.blit(heart.image, heart.rect)
    pg.display.flip()
    clock.tick(fps)
        
pg.quit()