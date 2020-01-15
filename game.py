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
        self.rect = self.image.get_rect().move(cell_size // 2 * x + 12, cell_size // 2 * y + 12)
        self.hp = hp
    
    def update(self):
        self.rect.x += 2
    
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


load_map("map.map")
tower = Tower("Sprites/rocket.png", 2, 2)
tower1 = Tower("Sprites/rocket.png", 3, 2)
towers.add(tower)
towers.add(tower1)
enemy = Enemy(None, 100, 0, 6)
enemy1 = Enemy(None, 150, -7, 6)
enemy2 = Enemy(None, 200, -10, 6)
enemies.add(enemy)
enemies.add(enemy1)
enemies.add(enemy2)

heart = pg.sprite.Sprite()
heart.image = pg.image.load("heart.png")
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