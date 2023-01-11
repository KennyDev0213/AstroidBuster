import pygame
from pygame import time
from pygame import sprite
from pygame.constants import K_ESCAPE, K_SPACE, QUIT
from pygame.sprite import Group, Sprite 
from pygame.time import Clock

import os
import math
import random

pygame.init()

#constants
SPEED = 5
SPEED_LIMIT = 20
METEOR_COUNT = 10
FPS = 60
GAME_FONT = pygame.font.SysFont('agencyfb', 72 )

#colours
RED = (255,0,0)
BLUE = (0,255,0)
GREEN = (0,0,255)

#setting window size
size = w, h = 1024, 600
WIN = pygame.display.set_mode(size)
pygame.display.set_caption("Astroid Buster")

#load music
pygame.mixer.init()
pygame.mixer.music.load(os.getcwd()+"\Assets\Audio\SpookySpace.wav")
pygame.mixer.music.play(-1)

#load sounds
pew = pygame.mixer.Sound(os.getcwd()+"\Assets\Audio\pew.ogg")
boom = pygame.mixer.Sound(os.getcwd()+"\Assets\Audio\explode.ogg")

spaceTile = pygame.image.load(os.getcwd()+"\Assets\Img\spaceTile.png")
spaceShip = pygame.image.load(os.getcwd()+"\Assets\Img\spaceship.png")
energyShield = pygame.transform.scale(pygame.image.load("Assets\Img\Shield.png"), (64,64))

spaceShipSize = 32,32

#meteor class
class Meteor(pygame.sprite.Sprite):

    vel = 5
    dirX = 0
    dirY = 0

    def __init__(self) -> None:
        super().__init__()

        #random location out of screen then into screen
        x,y = 0,0
        side = random.randint(1,4)
        if side == 1: #top
            y = -70
            x = random.randrange(w)
            self.dirY = 1
        elif side == 2: #left
            x = -70
            y = random.randrange(h)
            self.dirX = 1
        elif side == 3: #bottom
            y = h + 70
            x = random.randrange(w)
            self.dirY = -1
        elif side == 4: #right
            x = w + 70
            y = random.randrange(h)
            self.dirX = -1

        self.rot = random.randrange(360)            #random rotation
        #self.dirRot = random.choices([1,-1])[0]    #random direction of rotation //no animation, does not work
        self.size = random.randint(40,120)          #random size
        self.radius = self.size/2
    
        self.original_image =pygame.image.load("Assets\Img\Meteor.png")
        self.image =  pygame.transform.rotate(pygame.transform.scale(self.original_image,[self.size,self.size]),self.rot)
        pos = (x,y)
        self.rect = self.image.get_rect().move(pos)

    def update(self):
        #moves meteor
        self.rect.x += self.dirX * self.vel
        self.rect.y += self.dirY * self.vel
        
#bullet class
class LaserBullet(pygame.sprite.Sprite):

    vel = 10

    def __init__(self, startPos, angle) -> None:
        super().__init__()

        self.image = pygame.transform.scale(pygame.image.load("Assets\Img\Bullet.png"),(8,8))
        self.rect = self.image.get_rect()
        self.radius = self.rect.width/2

        self.rect.x = startPos[0]
        self.rect.y = startPos[1]

        self.angle = math.radians(angle)

    def update(self):
        self.rect.x += math.cos(self.angle) * self.vel
        self.rect.y -= math.sin(self.angle) * self.vel
    
    def colide(self):
        pass

#player class
class NewPlayer(pygame.sprite.Sprite):

    angle = 0

    def __init__(self) -> None:
        super().__init__()
        self.x = w/2
        self.y = h/2

        self.original_image = pygame.transform.scale(spaceShip,spaceShipSize)
        self.image = self.original_image
        self.rect = self.image.get_rect()

        self.width = self.rect.width
        self.height = self.rect.height
        self.radius = self.width/2
    
    def setAngle(self, angle):
        self.angle = angle

    def update(self):
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.rect.x = self.x
        self.rect.y = self.y

#tile background
def set_background_tile(img):
    imgSize = img.get_rect().size
    y = 0
    while y < h:
        x = 0
        while x < w:
            WIN.blit(img, (x,y))
            x += imgSize[0]
        y += imgSize[1]

#get the angle for rotating the ship and where to shoot
def ship_mouse_angle(player):
    mx = pygame.mouse.get_pos()[0]
    my = pygame.mouse.get_pos()[1]

    px = player.x + player.width/2
    py = player.y + player.height/2

    vecX = mx - px
    vecY = my - py

    rad = math.atan2(vecY, vecX)
    angle = rad*(180/math.pi)*-1
    return angle

#draw window
def draw_win(player, angle, entities, score, life):
    set_background_tile(spaceTile)

    #draws all entities
    entities.draw(WIN)

    #transformedShip = pygame.transform.rotozoom(spaceShip, angle, 32)
    scaledShip = pygame.transform.scale(spaceShip, spaceShipSize)
    transformedShip = pygame.transform.rotate(scaledShip, angle)
    WIN.blit(transformedShip, (player.x, player.y))

    #dispaly score text
    scoreText = GAME_FONT.render(str(score), True, RED)
    WIN.blit(scoreText, (0,0))

    #display lives
    lifeText = GAME_FONT.render(str(life), True, RED)
    lifeTextMarginX = w - lifeText.get_rect().size[0]
    WIN.blit(lifeText, (lifeTextMarginX,0))

#main method
def main():
    START_STATE = True
    PAUSE_STATE = False
    DEAD_STATE = False
    INVINCIBLE_MODE = False

    BULLET_LIMIT_STATE = False
    BULLET_LIMIT = 5

    LIFE = 3
    SCORE = 0
    MOMENTUM_Y = 0
    MOMENTUM_X = 0

    #remove bullets when offscreen
    BORDERMARGIN = 100

    #player = pygame.transform.scale(spaceShip,spaceShipSize).get_rect()

    clock = pygame.time.Clock()
    invincibleTime = 0

    #might change to a general sprite group to include meteors
    entities = pygame.sprite.Group()
    bullets = pygame.sprite.Group()

    player = NewPlayer()
    entities.add(player)

    #main game loop
    run = True
    while run:

        #fps
        clock.tick(FPS)

        getAngle = ship_mouse_angle(player)
        player.setAngle(getAngle)

        METEOR_COUNT = (SCORE/150 ) + 1

        if pygame.time.get_ticks() - invincibleTime > 3000:
            INVINCIBLE_MODE = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN and DEAD_STATE == False and PAUSE_STATE == False and START_STATE == False:
                if event.key == K_SPACE and BULLET_LIMIT_STATE == False:
                    playerCenter = (player.x + player.width/2, player.y + player.height/2)
                    bullet = LaserBullet(playerCenter, getAngle)
                    entities.add(bullet)
                    bullets.add(bullet)
                    pew.play()

        #key presses (continuous)
        keys_pressed = pygame.key.get_pressed()
        if PAUSE_STATE == False and START_STATE == False:
            if keys_pressed[pygame.K_ESCAPE]:
                PAUSE_STATE = True
            if keys_pressed[pygame.K_w]:
                MOMENTUM_Y += -0.2
            if keys_pressed[pygame.K_a]:
                MOMENTUM_X += -0.2
            if keys_pressed[pygame.K_s]:
                MOMENTUM_Y += 0.2
            if keys_pressed[pygame.K_d]:
                MOMENTUM_X += 0.2
        elif PAUSE_STATE == True and START_STATE == False:
            if keys_pressed[pygame.K_e]:
                run = False
            if keys_pressed[pygame.K_SPACE]:
                PAUSE_STATE = False
        elif keys_pressed[pygame.K_SPACE]:
            START_STATE =  False

        
        if not PAUSE_STATE and not START_STATE:   #basicaly if the game is paused, dont do anything
            #bind momentum
            if MOMENTUM_X > SPEED_LIMIT:
                MOMENTUM_X = SPEED_LIMIT
            elif MOMENTUM_X < -SPEED_LIMIT:
                MOMENTUM_X = -SPEED_LIMIT
            if MOMENTUM_Y > SPEED_LIMIT:
                MOMENTUM_Y = SPEED_LIMIT
            elif MOMENTUM_Y < -SPEED_LIMIT:
                MOMENTUM_Y = -SPEED_LIMIT

            #passive slow down
            MOMENTUM_X -= (MOMENTUM_X * 0.01)
            MOMENTUM_Y -= (MOMENTUM_Y * 0.01)

            player.x += MOMENTUM_X
            player.y += MOMENTUM_Y
            
            #player bounderies
            if player.x - SPEED < 0 - spaceShipSize[0]:
                player.x = w 
            elif player.x + SPEED > w :
                player.x = 0 - spaceShipSize[0]
            if player.y - SPEED < 0 - spaceShipSize[0]:
                player.y = h  
            elif player.y + SPEED > h :
                player.y = 0 - spaceShipSize[0]

            meteorCount = 0
            bulletCount = 0

            #cycle through the entities
            for b in entities:
                b.update()
                #if the entity goes out of bounds, remove
                if b.rect.x < -BORDERMARGIN or b.rect.x > w + BORDERMARGIN or b.rect.y < -BORDERMARGIN or b.rect.y > h+BORDERMARGIN:
                    entities.remove(b)
                #updates the meteor, if collides with bullet then remove meteor and bullet
                if isinstance(b, Meteor):
                    for l in bullets:
                        if pygame.sprite.collide_circle(l,b):
                            boom.play()
                            SCORE += 15
                            l.kill()
                            b.kill()
                    #if hit turn on invincible mode and take one life away
                    if pygame.sprite.collide_circle(player, b) and INVINCIBLE_MODE == False: 
                        LIFE -= 1
                        INVINCIBLE_MODE = True
                        invincibleTime = pygame.time.get_ticks()
                        b.kill()
                        if LIFE <= 0:
                            DEAD_STATE = True
                            run = False
                    meteorCount += 1
                if isinstance(b, LaserBullet):
                    bulletCount += 1
            if meteorCount < METEOR_COUNT:
                newMeteor = Meteor()
                entities.add(newMeteor)
            if bulletCount >= BULLET_LIMIT:
                BULLET_LIMIT_STATE = True
            else:
                BULLET_LIMIT_STATE = False
            draw_win(player, getAngle, entities, SCORE, LIFE)
            if INVINCIBLE_MODE:
                WIN.blit(energyShield, (player.x - 14, player.y - 14))
        elif not START_STATE:   #pause page
                pausedText = GAME_FONT.render("PAUSED", True, RED)
                textWidth = pausedText.get_rect().width / 2
                instructText = GAME_FONT.render("Press SPACE to continue, E to exit", True, RED)
                textWidth2 = instructText.get_rect().width / 2

                WIN.blit(pausedText, (w/2 - textWidth,h/4))
                WIN.blit(instructText, (w/2 - textWidth2,h/2))
        else:   #start page
                titleText = GAME_FONT.render("ASTROID BUSTER", True, RED)
                titleTextWidth = titleText.get_rect().width / 2
                startText = GAME_FONT.render("Press SPACE to start!", True, RED)
                startTextWidth2 = startText.get_rect().width / 2

                WIN.blit(titleText, (w/2 - titleTextWidth,h/4))
                WIN.blit(startText, (w/2 - startTextWidth2,h/2))
        pygame.display.flip()
    print("Final score is " + str(SCORE))

#runs the main function ONLY when this file is ran directly instead from an import
if __name__ == "__main__":
    main()
    pygame.quit()