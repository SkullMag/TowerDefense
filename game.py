import pygame as pg
from threading import Thread
import glob
import time


pg.init()
width, height = 1280, 720
screen = pg.display.set_mode((width, height))
clock = pg.time.Clock()

fps = 60
speed = 4
app_running = True

towers = pg.sprite.Group()
tiles = pg.sprite.Group()
enemies = pg.sprite.Group()


class Tile(pg.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()

        self.image = pg.image.load(img)
        self.image = pg.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect().move(50 * x, 50 * y)
    
    def get_pos(self):
        return pg.math.Vector2(self.rect.center[0], self.rect.center[1])


class Enemy(pg.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()

        self.image = pg.Surface([25, 25])
        self.image.fill(pg.Color("red"))
        self.rect = self.image.get_rect().move(25 * x + 12, 25 * y + 12)
        self.hp = 100
    
    def update(self):
        self.rect.x += 1
    
    def hit(self, damage: int):
        if self.hp - damage < 0:
            self.kill()
        else:
            self.hp -= damage
    
    def get_pos(self):
        return pg.math.Vector2(self.rect.center[0], self.rect.center[1])


class Tower(pg.sprite.Sprite):
    def __init__(self, img, x, y):
        super().__init__()

        self.image = pg.image.load(img)
        self.image = pg.transform.scale(self.image, (50, 50))
        self.image = pg.transform.flip(self.image, False, True)
        self.rect = self.image.get_rect().move(100 * x, 100 * y)
        self.target = None
    
    def set_target(self, target: Enemy):
        self.target = target
    
    def hit_target(self):
        enemy.hit(25)
    
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


load_map("map.map")
tower = Tower("Sprites/rocket.png", 2, 0)
towers.add(tower)
enemy = Enemy(None, 0, 2)
enemies.add(enemy)

while app_running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            app_running = False
    
    if tower.get_pos().distance_to(enemy.get_pos()) < 80:
        tower.set_target(enemy)
        tower.hit_target()
    enemies.update()
    tiles.draw(screen)
    towers.draw(screen)
    enemies.draw(screen)
    pg.display.flip()
    clock.tick(fps)
        
pg.quit()