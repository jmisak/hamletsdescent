#!/usr/bin/env python3
"""
Hamlet's Descent: Enhanced Gameplay Edition
-----------------------------------------------------------------
Building on the existing foundation with:
  • Power-ups and collectibles system
  • Combo multiplier for chained attacks
  • Boss fight with attack patterns
  • Multiple enemy types with varied behaviors
  • Dash mechanic and special abilities
  • Environmental hazards and platforms
  • Achievement system
  • Sound effect integration
"""
import pygame
import random
import sys
import time
import os
import textwrap
import math

# ---------------------------
# Global Constants & Settings
# ---------------------------
SPRITE_SCALE       = 2.25
SCREEN_WIDTH       = 1600
SCREEN_HEIGHT      = 1200
FPS                = 60
GRAVITY            = 0.5
PLAYER_SPEED       = 5
JUMP_STRENGTH      = -12
COYOTE_TIME        = 0.1
JUMP_BUFFER_TIME   = 0.1
VARIABLE_JUMP_MULT = 0.5
LEVEL_WIDTH        = 10 * SCREEN_WIDTH
DASH_SPEED         = 15
DASH_DURATION      = 0.2
DASH_COOLDOWN      = 1.0

# Colors
BLACK = (0,0,0)
WHITE = (255,255,255)
RED   = (255,0,0)
BLUE  = (0,128,255)
GREEN = (0,255,0)
YELLOW = (255,255,0)
PURPLE = (128,0,255)

# Sprite scales
PLAYER_SCALE = SPRITE_SCALE * 1.1
GHOST_SCALE  = 0.3
POWERUP_SCALE = 0.5

# Font
PIXEL_FONT_SIZE = 28
PIXEL_FONT      = None
TAN_TOP         = WHITE
TAN_BOTTOM      = WHITE

# Screen shake
SHAKE_DURATION   = 0.3
SHAKE_MAGNITUDE  = 8
shake_timer      = 0.0
shake_offset     = [0,0]

# Combo system
combo_timer = 0.0
combo_count = 0
COMBO_TIMEOUT = 2.0

# Achievements
achievements = {
    "first_blood": False,
    "combo_master": False,
    "untouchable": False,
    "speedrun": False,
    "collector": False
}

# --------------------------------
# Utility & Helper Functions
# --------------------------------

def render_gradient_text(text, font, c0, c1):
    surf = font.render(text, True, WHITE).convert_alpha()
    w,h = surf.get_size()
    grad = pygame.Surface((w,h)).convert_alpha()
    for y in range(h):
        ratio = y/float(h)
        r = int(c0[0]*(1-ratio)+c1[0]*ratio)
        g = int(c0[1]*(1-ratio)+c1[1]*ratio)
        b = int(c0[2]*(1-ratio)+c1[2]*ratio)
        pygame.draw.line(grad,(r,g,b),(0,y),(w,y))
    surf.blit(grad,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
    return surf


def load_frames(folder, anim, count, variant=""):
    frames=[]
    for i in range(count):
        part = f"-{variant}" if variant else ""
        name = f"adventurer-{anim}{part}-{i:02d}.png"
        path = os.path.join(folder,name)
        if os.path.exists(path):
            try: frames.append(pygame.image.load(path).convert_alpha())
            except: print(f"Failed load: {path}")
        else:
            print(f"Missing: {path}")
    return frames


def trim_surface(surf):
    mask = pygame.mask.from_surface(surf)
    rects = mask.get_bounding_rects()
    if rects: return surf.subsurface(rects[0]).copy()
    return surf.copy()


def start_shake(magnitude=SHAKE_MAGNITUDE):
    global shake_timer, SHAKE_MAGNITUDE
    shake_timer = SHAKE_DURATION
    SHAKE_MAGNITUDE = magnitude


def apply_shake(dt):
    global shake_timer, shake_offset
    if shake_timer>0:
        shake_timer = max(0, shake_timer-dt)
        shake_offset[0] = random.randint(-SHAKE_MAGNITUDE, SHAKE_MAGNITUDE)
        shake_offset[1] = random.randint(-SHAKE_MAGNITUDE, SHAKE_MAGNITUDE)
    else:
        shake_offset[0]=0; shake_offset[1]=0

def create_particle(x, y, color, vx, vy, lifetime=0.5):
    return {
        'x': x, 'y': y, 'vx': vx, 'vy': vy,
        'color': color, 'lifetime': lifetime,
        'max_life': lifetime, 'size': 5
    }

# --------------------------------
# Entity Classes
# --------------------------------

class Particle:
    def __init__(self, x, y, color, vx, vy, lifetime=0.5):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.lifetime = lifetime
        self.max_life = lifetime
        self.size = 5
        
    def update(self, dt):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        self.vy += GRAVITY * dt * 60
        self.lifetime -= dt
        return self.lifetime > 0
        
    def draw(self, screen, cam_x):
        alpha = self.lifetime / self.max_life
        size = int(self.size * alpha)
        if size > 0:
            pygame.draw.circle(screen, self.color, 
                             (int(self.x - cam_x), int(self.y)), size)

class PowerUp(pygame.sprite.Sprite):
    def __init__(self, x, y, ptype):
        super().__init__()
        self.ptype = ptype
        self.bob = 0
        self.bob_speed = 2
        
        # Create powerup visual
        size = 40
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        if ptype == "health":
            pygame.draw.circle(self.image, RED, (size//2, size//2), size//2)
            pygame.draw.rect(self.image, WHITE, (size//2-8, size//2-2, 16, 4))
            pygame.draw.rect(self.image, WHITE, (size//2-2, size//2-8, 4, 16))
        elif ptype == "speed":
            pygame.draw.polygon(self.image, YELLOW, 
                              [(size//2, 5), (size-5, size//2), 
                               (size//2, size-5), (5, size//2)])
        elif ptype == "damage":
            pygame.draw.polygon(self.image, PURPLE,
                              [(size//2, 5), (size-5, size-5), (5, size-5)])
        
        self.rect = self.image.get_rect(center=(x, y))
        self.start_y = y
        
    def update(self, dt):
        self.bob += dt * self.bob_speed
        self.rect.y = self.start_y + math.sin(self.bob) * 10

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, moving=False):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill((100, 100, 100))
        pygame.draw.rect(self.image, (150, 150, 150), (0, 0, width, 5))
        self.rect = self.image.get_rect(topleft=(x, y))
        self.moving = moving
        self.move_range = 200
        self.move_speed = 2
        self.start_x = x
        self.direction = 1
        
    def update(self, dt):
        if self.moving:
            self.rect.x += self.move_speed * self.direction
            if abs(self.rect.x - self.start_x) > self.move_range:
                self.direction *= -1

class GhostEnemy(pygame.sprite.Sprite):
    def __init__(self,x,y,speed):
        super().__init__()
        sheet = pygame.image.load(os.path.join("assets","ghost_sheet.png")).convert_alpha() if os.path.exists(os.path.join("assets","ghost_sheet.png")) else None
        if sheet:
            fw,fh = 204,341
            self.frames = [
                [pygame.transform.scale(sheet.subsurface((c*fw,r*fh,fw,fh)),
                 (int(fw*GHOST_SCALE),int(fh*GHOST_SCALE))) for c in range(5)]
                for r in range(3)
            ]
        else:
            # Fallback ghost
            size = 60
            frame = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(frame, (200, 200, 255), (size//2, size//2), size//2)
            pygame.draw.circle(frame, BLACK, (size//3, size//3), 5)
            pygame.draw.circle(frame, BLACK, (2*size//3, size//3), 5)
            self.frames = [[frame for _ in range(5)] for _ in range(3)]
            
        self.row=0; self.idx=0
        self.image = self.frames[0][0]
        self.rect  = self.image.get_rect(midbottom=(x,y))
        self.speed = speed
        self.timer = 0.0; self.delay = 0.2
        self.health=3
        self.bob_dir=1; self.bob=0
        self.attack_cooldown = 0

    def update(self,dt):
        # bobbing
        self.bob += dt*20*self.bob_dir
        if abs(self.bob)>6: self.bob_dir*=-1
        self.rect.y += dt*20*self.bob_dir
        # move
        self.rect.x -= self.speed
        # animate
        self.timer += dt
        if self.timer>=self.delay:
            self.idx = (self.idx+1)%5; self.timer=0
            self.image = self.frames[self.row][self.idx]
        # off-screen cleanup
        if self.rect.right<0: self.kill()
        
        self.attack_cooldown = max(0, self.attack_cooldown - dt)

    def take_hit(self):
        self.health -= 1
        if self.health>0:
            self.row = min(2, 3 - self.health); self.idx=0
            start_shake()
            return 10  # points
        else:
            start_shake(); self.kill()
            return 20  # bonus points

class SwordGhost(GhostEnemy):
    def __init__(self, x, y, speed):
        super().__init__(x, y, speed)
        self.health = 5
        self.attack_range = 100
        
        # Add sword to visual
        if not hasattr(self, '_has_sword'):
            for row in self.frames:
                for frame in row:
                    sword = pygame.Surface((20, 40), pygame.SRCALPHA)
                    pygame.draw.rect(sword, (180, 180, 180), (8, 0, 4, 30))
                    pygame.draw.rect(sword, (150, 150, 150), (0, 25, 20, 5))
                    frame.blit(sword, (frame.get_width()-20, frame.get_height()//2))
            self._has_sword = True

class EnemyCrow(pygame.sprite.Sprite):
    def __init__(self,x,y,speed):
        super().__init__()
        sheet = pygame.image.load(os.path.join("assets","crow_fly.png")).convert_alpha() if os.path.exists(os.path.join("assets","crow_fly.png")) else None
        if sheet:
            w,h = sheet.get_width()//2, sheet.get_height()
            raw = [sheet.subsurface((i*w,0,w,h)).copy() for i in range(2)]
            self.frames = [pygame.transform.scale(f,(int(f.get_width()*SPRITE_SCALE),int(f.get_height()*SPRITE_SCALE))) for f in raw]
        else:
            # Fallback crow
            size = 40
            frame = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(frame, BLACK, (size//2, size//2), size//3)
            pygame.draw.polygon(frame, BLACK, [(0, size//2), (size//4, size//3), (size//4, 2*size//3)])
            self.frames = [frame, frame]
            
        self.idx=0; self.image=self.frames[0]
        self.rect = self.image.get_rect(topleft=(x,y))
        self.speed = speed; self.timer=0; self.delay=0.15
        self.dive_speed = 0
        self.diving = False

    def update(self,dt):
        self.rect.x -= self.speed
        
        # Dive attack behavior
        if not self.diving and random.random() < 0.005:
            self.diving = True
            self.dive_speed = 8
            
        if self.diving:
            self.rect.y += self.dive_speed
            self.dive_speed = max(-8, self.dive_speed - 0.3)
            if self.dive_speed < -7:
                self.diving = False
                
        self.timer += dt
        if self.timer>=self.delay:
            self.idx = (self.idx+1)%len(self.frames); self.timer=0
            self.image=self.frames[self.idx]
        if self.rect.right<0 or self.rect.top > SCREEN_HEIGHT: self.kill()

class Boss(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Create boss visual
        self.size = 150
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        # Ghost king appearance
        pygame.draw.circle(self.image, (100, 0, 150), (self.size//2, self.size//2), self.size//2)
        pygame.draw.polygon(self.image, (200, 150, 255), 
                          [(self.size//2-30, 20), (self.size//2, 5), (self.size//2+30, 20)])
        pygame.draw.circle(self.image, RED, (self.size//3, self.size//3), 10)
        pygame.draw.circle(self.image, RED, (2*self.size//3, self.size//3), 10)
        
        self.rect = self.image.get_rect(center=(x, y))
        self.health = 50
        self.max_health = 50
        self.phase = 1
        self.attack_timer = 0
        self.attack_pattern = 0
        self.vx = 0
        self.vy = 0
        
    def update(self, dt, player_pos):
        # Movement AI
        dx = player_pos[0] - self.rect.centerx
        dy = player_pos[1] - self.rect.centery
        
        # Hover movement
        self.vy = math.sin(pygame.time.get_ticks() * 0.002) * 2
        self.rect.y += self.vy
        
        # Attack patterns
        self.attack_timer += dt
        
        if self.health < self.max_health * 0.5 and self.phase == 1:
            self.phase = 2
            start_shake(15)
            
        if self.phase == 1:
            # Phase 1: Simple attacks
            if self.attack_timer > 3:
                self.attack_pattern = (self.attack_pattern + 1) % 2
                self.attack_timer = 0
                return self.execute_attack()
        else:
            # Phase 2: Aggressive attacks
            if self.attack_timer > 2:
                self.attack_pattern = (self.attack_pattern + 1) % 3
                self.attack_timer = 0
                return self.execute_attack()
                
        return []
        
    def execute_attack(self):
        attacks = []
        if self.attack_pattern == 0:
            # Circular shot
            for i in range(8):
                angle = i * math.pi / 4
                attacks.append({
                    'type': 'projectile',
                    'x': self.rect.centerx,
                    'y': self.rect.centery,
                    'vx': math.cos(angle) * 5,
                    'vy': math.sin(angle) * 5
                })
        elif self.attack_pattern == 1:
            # Summon minions
            for i in range(3):
                attacks.append({
                    'type': 'summon',
                    'x': self.rect.centerx + (i-1) * 100,
                    'y': self.rect.centery
                })
        return attacks
        
    def take_hit(self, damage=1):
        self.health -= damage
        if self.health <= 0:
            self.kill()
            return 100  # Boss points
        return 5

class Projectile(pygame.sprite.Sprite):
    def __init__(self, x, y, vx, vy, color=PURPLE):
        super().__init__()
        self.image = pygame.Surface((10, 10), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (5, 5), 5)
        self.rect = self.image.get_rect(center=(x, y))
        self.vx = vx
        self.vy = vy
        
    def update(self, dt):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.rect.right < 0 or self.rect.left > LEVEL_WIDTH or self.rect.bottom < 0 or self.rect.top > SCREEN_HEIGHT:
            self.kill()

class Player(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        self._load_anims()
        self.state='idle'; self.frames=self.anims['idle']; self.idx=0
        self.image=self.frames[0]
        self.rect=self.image.get_rect(midbottom=(x,y))
        self.vx=0; self.vy=0; self.on_ground=False
        self.timer=0; self.adelay=0.15
        self.jump_buffer=0; self.coyote=0
        self.jump_sound = pygame.mixer.Sound("jump.mp3") if os.path.exists("jump.mp3") else None
        self.health = 100
        self.max_health = 100
        self.invulnerable = 0
        self.facing_right = True
        
        # New mechanics
        self.dash_cooldown = 0
        self.dashing = False
        self.dash_timer = 0
        self.damage_multiplier = 1.0
        self.speed_multiplier = 1.0
        self.powerup_timers = {'speed': 0, 'damage': 0}

    def _load_anims(self):
        base="assets/adventurer"
        keys=[('idle',3),('run',3),('jump',3),('attack1',3),('attack2',3)]
        self.anims={}
        for k,n in keys:
            fr = load_frames(base,k,n)
            if not fr:
                fallback=pygame.Surface((50,50),pygame.SRCALPHA)
                pygame.draw.rect(fallback,BLUE,fallback.get_rect(),3)
                fr=[fallback]
            self.anims[k]=[pygame.transform.scale(f,(int(f.get_width()*PLAYER_SCALE),int(f.get_height()*PLAYER_SCALE))) for f in fr]

    def update(self,dt,platforms=None):
        keys = pygame.key.get_pressed()
        
        # Update powerup timers
        for key in self.powerup_timers:
            self.powerup_timers[key] = max(0, self.powerup_timers[key] - dt)
        
        self.speed_multiplier = 1.5 if self.powerup_timers['speed'] > 0 else 1.0
        self.damage_multiplier = 2.0 if self.powerup_timers['damage'] > 0 else 1.0
        
        # Dash mechanic
        self.dash_cooldown = max(0, self.dash_cooldown - dt)
        if keys[pygame.K_LSHIFT] and self.dash_cooldown == 0 and not self.dashing:
            self.dashing = True
            self.dash_timer = DASH_DURATION
            self.dash_cooldown = DASH_COOLDOWN
            self.invulnerable = DASH_DURATION
            
        if self.dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0:
                self.dashing = False
            else:
                dash_dir = 1 if self.facing_right else -1
                self.vx = DASH_SPEED * dash_dir
        else:
            # Normal movement
            self.vx = 0
            if keys[pygame.K_LEFT]:
                self.vx = -PLAYER_SPEED * self.speed_multiplier
                self.facing_right = False
            elif keys[pygame.K_RIGHT]:
                self.vx = PLAYER_SPEED * self.speed_multiplier
                self.facing_right = True
                
        # Invulnerability
        self.invulnerable = max(0, self.invulnerable - dt)
        
        # coyote & buffer
        self.coyote = COYOTE_TIME if self.on_ground else max(0,self.coyote-dt)
        self.jump_buffer = JUMP_BUFFER_TIME if keys[pygame.K_SPACE] else max(0,self.jump_buffer-dt)
        
        # jump
        if self.jump_buffer>0 and self.coyote>0:
            self.vy = JUMP_STRENGTH; self.on_ground=False; self.coyote=0; self.jump_buffer=0
            if self.jump_sound: self.jump_sound.play()
            
        # gravity
        self.vy += GRAVITY
        self.rect.y += self.vy
        
        # Platform collision
        self.on_ground = False
        if platforms:
            for platform in platforms:
                if self.vy > 0 and self.rect.bottom > platform.rect.top and self.rect.bottom < platform.rect.bottom:
                    if self.rect.left < platform.rect.right and self.rect.right > platform.rect.left:
                        self.rect.bottom = platform.rect.top
                        self.vy = 0
                        self.on_ground = True
                        
        # ground collision
        if self.rect.bottom>=SCREEN_HEIGHT:
            self.rect.bottom=SCREEN_HEIGHT; self.vy=0; self.on_ground=True
            
        # variable jump
        if self.vy<0 and not keys[pygame.K_SPACE]: self.vy += GRAVITY*VARIABLE_JUMP_MULT
        
        # apply horiz
        self.rect.x += self.vx
        
        # state logic
        new='idle'
        if self.dashing:
            new = 'dash'
        elif self.state.startswith('attack'):
            new=self.state
        elif keys[pygame.K_a]: new='attack1'
        elif keys[pygame.K_s]: new='attack2'
        elif not self.on_ground: new='jump'
        elif self.vx!=0: new='run'
        
        if new!=self.state:
            self.state=new
            self.frames=self.anims.get(new, self.anims['idle'])
            self.idx=0; self.timer=0
            
        # animate
        self.timer+=dt
        if self.timer>=self.adelay:
            self.timer=0; self.idx=(self.idx+1)%len(self.frames)
            self.image=self.frames[self.idx]
            # flip
            if not self.facing_right:
                self.image=pygame.transform.flip(self.image,True,False)
            if self.state.startswith('attack') and self.idx==len(self.frames)-1:
                self.state='idle'; self.frames=self.anims['idle']; self.idx=0
                
        # Visual feedback for powerups
        if self.invulnerable > 0 and int(self.invulnerable * 10) % 2:
            self.image.set_alpha(128)
        else:
            self.image.set_alpha(255)

# Adaptive difficulty
class AdaptiveEngine:
    def __init__(self): 
        self.diff=1.0
        self.espeed=2
        self.spawn_rate = 0.01
        
    def update(self,perf):
        if perf['deaths']>3:
            self.diff=max(0.5,self.diff*0.9)
            self.espeed=max(1,self.espeed*0.9)
            self.spawn_rate = max(0.005, self.spawn_rate * 0.9)
        elif perf['deaths']==0 and perf['time']<60:
            self.diff=min(2.0,self.diff*1.1)
            self.espeed=min(5,self.espeed*1.1)
            self.spawn_rate = min(0.02, self.spawn_rate * 1.1)
        print(f"AdaptiveEngine → diff={self.diff:.2f}, speed={self.espeed}, spawn={self.spawn_rate:.3f}")

# --------------------------------
# Level & Scene Functions
# --------------------------------
def show_loadscreen(screen):
    img = pygame.image.load("loadscreen.png").convert_alpha() if os.path.exists("loadscreen.png") else pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
    t0=time.time(); skip=False
    while True:
        for e in pygame.event.get():
            if e.type in (pygame.QUIT, pygame.KEYDOWN): skip=True
        if skip or time.time()-t0>5: break
        screen.fill(BLACK); screen.blit(pygame.transform.scale(img,(SCREEN_WIDTH,SCREEN_HEIGHT)),(0,0)); pygame.display.flip()

def show_opening_scene(screen):
    bg = pygame.image.load("tomb.png").convert_alpha() if os.path.exists("tomb.png") else pygame.Surface((SCREEN_WIDTH,SCREEN_HEIGHT))
    bg = pygame.transform.scale(bg,(SCREEN_WIDTH,SCREEN_HEIGHT))
    try: pygame.mixer.music.load("tomb_music.mp3"); pygame.mixer.music.play(-1)
    except: pass
    text = ("Dear Son, I have forsaken you... Keep your sword at hand and trust no one. Your Father.")
    words = text.split(); disp=""; idx=0; delay=300; last=pygame.time.get_ticks()
    clock=pygame.time.Clock()
    while True:
        dt=clock.tick(FPS)
        for e in pygame.event.get():
            if e.type==pygame.KEYDOWN: return
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
        now=pygame.time.get_ticks()
        if idx<len(words) and now-last>delay:
            disp += (" " if disp else "")+words[idx]; idx+=1; last=now
        screen.blit(bg,(0,0))
        y=50
        for line in textwrap.wrap(disp,width=60):
            surf=render_gradient_text(line,PIXEL_FONT,TAN_TOP,TAN_BOTTOM)
            screen.blit(surf,(50,y)); y+=PIXEL_FONT_SIZE+4
        pygame.display.flip()

def show_stage_intro(screen):
    text=("Stage 1: Fight Your Fears... Ladies and gentlemen, here's Fortinbras!")
    surf=render_gradient_text(text,PIXEL_FONT,TAN_TOP,TAN_BOTTOM)
    box=pygame.Surface((surf.get_width()+40,surf.get_height()+40),pygame.SRCALPHA); box.fill((0,0,0,180))
    rect=box.get_rect(center=(SCREEN_WIDTH//2,SCREEN_HEIGHT//2))
    screen.fill(BLACK); screen.blit(box,rect); screen.blit(surf,surf.get_rect(center=rect.center)); pygame.display.flip()
    while True:
        for e in pygame.event.get():
            if e.type in (pygame.KEYDOWN, pygame.QUIT): return

def load_background_act1(start=True):
    fn = "Level_1_backgroundstart.png" if start else "Level_1_background.png"
    if os.path.exists(fn):
        b=pygame.image.load(fn).convert_alpha(); sf=SCREEN_HEIGHT/b.get_height(); w=int(b.get_width()*sf)
        b=pygame.transform.scale(b,(w,SCREEN_HEIGHT))
        surf=pygame.Surface((LEVEL_WIDTH,SCREEN_HEIGHT))
        for x in range(0,LEVEL_WIDTH,w): surf.blit(b,(x,0))
        return surf
    s=pygame.Surface((LEVEL_WIDTH,SCREEN_HEIGHT)); s.fill((30,30,30)); return s

def load_parallax_layers():
    layers=[]; files=["bg_layer1.png","bg_layer2.png"]; facts=[0.3,0.7]
    for fct,file in zip(facts,files):
        if os.path.exists(file): img=pygame.image.load(file).convert_alpha()
        else: img=pygame.Surface((800,600),pygame.SRCALPHA); img.fill((80,80,100))
        sf=SCREEN_HEIGHT/img.get_height(); nw,nh=int(img.get_width()*sf),SCREEN_HEIGHT
        si=pygame.transform.scale(img,(nw,nh))
        surf=pygame.Surface((LEVEL_WIDTH,SCREEN_HEIGHT),pygame.SRCALPHA)
        for x in range(0,LEVEL_WIDTH,nw): surf.blit(si,(x,0))
        layers.append((surf,fct))
    return layers

def boss_fight(screen, player, score, clock, adaptive):
    """Enhanced boss fight with multiple phases"""
    boss = Boss(SCREEN_WIDTH//2 + 400, SCREEN_HEIGHT//2)
    enemies = pygame.sprite.Group()
    projectiles = pygame.sprite.Group()
    particles = []
    platforms = pygame.sprite.Group()
    
    # Add some platforms for the boss arena
    platforms.add(Platform(SCREEN_WIDTH//4, SCREEN_HEIGHT - 200, 200, 20))
    platforms.add(Platform(3*SCREEN_WIDTH//4, SCREEN_HEIGHT - 300, 200, 20))
    platforms.add(Platform(SCREEN_WIDTH//2, SCREEN_HEIGHT - 400, 300, 20, moving=True))
    
    bg = load_background_act1(False)
    fixed_x = SCREEN_WIDTH//2
    boss_defeated = False
    
    # Boss music
    try:
        pygame.mixer.music.load("boss_music.mp3" if os.path.exists("boss_music.mp3") else "Onloose.mp3")
        pygame.mixer.music.play(-1)
    except: pass
    
    while not boss_defeated:
        dt = clock.tick(FPS)/1000.0
        apply_shake(dt)
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT: 
                pygame.quit(); sys.exit()
                
        # Update entities
        player.update(dt, platforms)
        platforms.update(dt)
        enemies.update(dt)
        projectiles.update(dt)
        
        # Boss AI
        if boss.alive():
            attacks = boss.update(dt, (player.rect.centerx, player.rect.centery))
            for attack in attacks:
                if attack['type'] == 'projectile':
                    projectiles.add(Projectile(attack['x'], attack['y'], attack['vx'], attack['vy']))
                elif attack['type'] == 'summon':
                    enemies.add(GhostEnemy(attack['x'], attack['y'], adaptive.espeed))
        else:
            boss_defeated = True
            
        # Update particles
        particles = [p for p in particles if p.update(dt)]
        
        # Combat
        if player.state.startswith('attack'):
            # Check boss hit
            if boss.alive() and player.rect.colliderect(boss.rect):
                points = boss.take_hit(player.damage_multiplier)
                score += points
                start_shake(10)
                # Create hit particles
                for _ in range(10):
                    particles.append(Particle(
                        boss.rect.centerx, boss.rect.centery,
                        PURPLE, random.uniform(-5, 5), random.uniform(-5, 5)
                    ))
                    
            # Check enemy hits
            hits = pygame.sprite.spritecollide(player, enemies, False)
            for enemy in hits:
                points = enemy.take_hit()
                score += points * (combo_count + 1)
                # Particles
                for _ in range(5):
                    particles.append(Particle(
                        enemy.rect.centerx, enemy.rect.centery,
                        WHITE, random.uniform(-3, 3), random.uniform(-3, 3)
                    ))
                    
        # Player damage
        if player.invulnerable <= 0:
            # Enemy collisions
            enemy_hits = pygame.sprite.spritecollide(player, enemies, False)
            proj_hits = pygame.sprite.spritecollide(player, projectiles, True)
            
            if enemy_hits or proj_hits:
                player.health -= 10
                player.invulnerable = 1.0
                start_shake()
                
            # Boss collision
            if boss.alive() and player.rect.colliderect(boss.rect):
                player.health -= 20
                player.invulnerable = 1.5
                start_shake(12)
                
        # Camera
        cam = player.rect.x - fixed_x + shake_offset[0]
        
        # Render
        screen.fill(BLACK)
        screen.blit(bg, (-cam + shake_offset[0], shake_offset[1]))
        
        # Platforms
        for platform in platforms:
            r = platform.rect.copy()
            r.x -= cam
            screen.blit(platform.image, r)
            
        # Entities
        for enemy in enemies:
            r = enemy.rect.copy()
            r.x -= cam
            screen.blit(enemy.image, r)
            
        for proj in projectiles:
            r = proj.rect.copy()
            r.x -= cam
            screen.blit(proj.image, r)
            
        # Boss
        if boss.alive():
            r = boss.rect.copy()
            r.x -= cam
            screen.blit(boss.image, r)
            
            # Boss health bar
            bar_width = 400
            bar_height = 30
            bar_x = SCREEN_WIDTH//2 - bar_width//2
            bar_y = 50
            pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
            health_width = int(bar_width * (boss.health / boss.max_health))
            pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_width, bar_height))
            boss_text = render_gradient_text("GHOST KING", PIXEL_FONT, WHITE, PURPLE)
            screen.blit(boss_text, (bar_x + bar_width//2 - boss_text.get_width()//2, bar_y - 30))
            
        # Player
        pr = player.rect.copy()
        pr.x -= cam
        screen.blit(player.image, pr)
        
        # Particles
        for particle in particles:
            particle.draw(screen, cam)
            
        # HUD
        hud_text = f"Score: {score}  Health: {player.health}/{player.max_health}"
        if combo_count > 0:
            hud_text += f"  COMBO x{combo_count}"
        hud = render_gradient_text(hud_text, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        screen.blit(hud, (20, 20))
        
        # Powerup indicators
        y_offset = 60
        if player.powerup_timers['speed'] > 0:
            speed_text = render_gradient_text(f"SPEED BOOST: {player.powerup_timers['speed']:.1f}s", PIXEL_FONT, YELLOW, WHITE)
            screen.blit(speed_text, (20, y_offset))
            y_offset += 30
            
        if player.powerup_timers['damage'] > 0:
            damage_text = render_gradient_text(f"DAMAGE x2: {player.powerup_timers['damage']:.1f}s", PIXEL_FONT, PURPLE, WHITE)
            screen.blit(damage_text, (20, y_offset))
            
        # Dash cooldown indicator
        if player.dash_cooldown > 0:
            dash_text = render_gradient_text(f"DASH: {player.dash_cooldown:.1f}s", PIXEL_FONT, BLUE, WHITE)
            screen.blit(dash_text, (SCREEN_WIDTH - 200, 20))
        else:
            dash_text = render_gradient_text("DASH READY!", PIXEL_FONT, GREEN, WHITE)
            screen.blit(dash_text, (SCREEN_WIDTH - 200, 20))
            
        pygame.display.flip()
        
        if player.health <= 0:
            return score, False  # Player died
            
    # Boss defeated!
    return score, True

def main_level2(screen, player, score, clock, adaptive):
    """Enhanced Act 2 with powerups and platforms"""
    parallax = load_parallax_layers()
    enemies = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    particles = []
    
    # Add platforms throughout the level
    for i in range(5):
        x = 400 + i * 600
        y = SCREEN_HEIGHT - 200 - random.randint(0, 200)
        platforms.add(Platform(x, y, 200, 20, random.choice([True, False])))
    
    fixed_x = 100
    start = time.time()
    quote = "To be, or not to be..."
    powerup_spawn_timer = 0
    
    while time.time() - start < 60:  # Extended time
        dt = clock.tick(FPS)/1000.0
        apply_shake(dt)
        
        global combo_timer, combo_count
        combo_timer = max(0, combo_timer - dt)
        if combo_timer == 0:
            combo_count = 0
            
        for e in pygame.event.get():
            if e.type == pygame.QUIT: 
                pygame.quit(); sys.exit()
                
        player.update(dt, platforms)
        platforms.update(dt)
        enemies.update(dt)
        powerups.update(dt)
        
        # Update particles
        particles = [p for p in particles if p.update(dt)]
        
        # Spawn enemies with variety
        if random.random() < adaptive.spawn_rate:
            enemy_type = random.choice(['crow', 'ghost', 'sword'])
            y = random.randint(100, SCREEN_HEIGHT - 100)
            
            if enemy_type == 'crow':
                enemies.add(EnemyCrow(player.rect.x + SCREEN_WIDTH, y, adaptive.espeed))
            elif enemy_type == 'ghost':
                enemies.add(GhostEnemy(player.rect.x + SCREEN_WIDTH, y, adaptive.espeed))
            else:
                enemies.add(SwordGhost(player.rect.x + SCREEN_WIDTH, y, adaptive.espeed * 0.7))
                
        # Spawn powerups
        powerup_spawn_timer += dt
        if powerup_spawn_timer > 5:
            powerup_spawn_timer = 0
            ptype = random.choice(['health', 'speed', 'damage'])
            x = player.rect.x + SCREEN_WIDTH - 200
            y = random.randint(200, SCREEN_HEIGHT - 200)
            powerups.add(PowerUp(x, y, ptype))
            
        # Combat
        if player.state.startswith('attack'):
            hits = pygame.sprite.spritecollide(player, enemies, False)
            for enemy in hits:
                points = enemy.take_hit()
                score += points * (combo_count + 1)
                combo_count += 1
                combo_timer = COMBO_TIMEOUT
                
                # Particles
                for _ in range(5):
                    particles.append(Particle(
                        enemy.rect.centerx, enemy.rect.centery,
                        WHITE, random.uniform(-3, 3), random.uniform(-3, 3)
                    ))
                    
                # Achievement check
                if combo_count >= 5 and not achievements["combo_master"]:
                    achievements["combo_master"] = True
                    print("Achievement Unlocked: Combo Master!")
                    
        # Enemy collisions
        if player.invulnerable <= 0:
            hits = pygame.sprite.spritecollide(player, enemies, False)
            for enemy in hits:
                player.health -= 10
                player.invulnerable = 1.0
                start_shake()
                enemy.kill()
                
        # Powerup collection
        collected = pygame.sprite.spritecollide(player, powerups, True)
        for powerup in collected:
            if powerup.ptype == 'health':
                player.health = min(player.max_health, player.health + 30)
                color = RED
            elif powerup.ptype == 'speed':
                player.powerup_timers['speed'] = 10
                color = YELLOW
            elif powerup.ptype == 'damage':
                player.powerup_timers['damage'] = 10
                color = PURPLE
                
            # Celebration particles
            for _ in range(20):
                particles.append(Particle(
                    powerup.rect.centerx, powerup.rect.centery,
                    color, random.uniform(-5, 5), random.uniform(-5, 5), 1.0
                ))
                
        # Camera
        cam = player.rect.x - fixed_x + shake_offset[0]
        
        # Render
        screen.fill(BLACK)
        for surf, f in parallax:
            screen.blit(surf, (-cam * f + shake_offset[0], shake_offset[1]))
            
        # Platforms
        for platform in platforms:
            r = platform.rect.copy()
            r.x -= cam
            screen.blit(platform.image, r)
            
        # Entities
        pr = player.rect.copy()
        pr.x -= cam
        screen.blit(player.image, pr)
        
        for en in enemies:
            r = en.rect.copy()
            r.x -= cam
            screen.blit(en.image, r)
            
        for pu in powerups:
            r = pu.rect.copy()
            r.x -= cam
            screen.blit(pu.image, r)
            
        # Particles
        for particle in particles:
            particle.draw(screen, cam)
            
        # HUD
        hud_text = f"Score: {score}  Health: {player.health}/{player.max_health}"
        if combo_count > 0:
            hud_text += f"  COMBO x{combo_count}"
        screen.blit(render_gradient_text(hud_text, PIXEL_FONT, TAN_TOP, TAN_BOTTOM), (20, 20))
        
        # Quote
        qs = render_gradient_text(quote, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        qr = qs.get_rect(center=(SCREEN_WIDTH/2, 100))
        screen.blit(qs, qr)
        
        pygame.display.flip()
        
        if player.health <= 0:
            return score, False
            
    # Transition to boss
    return boss_fight(screen, player, score, clock, adaptive)

# --------------------------------
# Main Game Loop (Act I)
# --------------------------------

def main():
    global PIXEL_FONT, dt, combo_timer, combo_count
    pygame.init()
    pygame.font.init()
    try: 
        pygame.mixer.init()
    except: 
        pass
        
    PIXEL_FONT = pygame.font.Font("Pixel_NES.ttf", PIXEL_FONT_SIZE) if os.path.exists("Pixel_NES.ttf") else pygame.font.Font(None, PIXEL_FONT_SIZE)
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hamlet's Descent - Enhanced Edition")
    clock = pygame.time.Clock()

    show_loadscreen(screen)
    show_opening_scene(screen)
    show_stage_intro(screen)

    if os.path.exists("Onloose.mp3"):
        try: 
            pygame.mixer.music.load("Onloose.mp3")
            pygame.mixer.music.play(-1)
        except: 
            pass

    adaptive = AdaptiveEngine()
    act1_bg_start = load_background_act1(True)
    act1_bg_main = load_background_act1(False)
    player = Player(100, SCREEN_HEIGHT-100)
    ghosts = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    particles = []
    
    # Add some platforms in Act 1
    for i in range(3):
        x = 500 + i * 800
        y = SCREEN_HEIGHT - 200 - random.randint(0, 150)
        platforms.add(Platform(x, y, 250, 20))

    score = 0
    deaths = 0
    last_score, last_health = -1, -1
    fixed_x = 100
    start_x = player.rect.x
    transition_x = start_x + 5*SCREEN_WIDTH
    level_start = time.time()
    powerup_spawn_timer = 0

    running = True
    while running:
        dt = clock.tick(FPS)/1000.0
        apply_shake(dt)
        
        # Update combo
        combo_timer = max(0, combo_timer - dt)
        if combo_timer == 0:
            combo_count = 0
            
        for e in pygame.event.get():
            if e.type == pygame.QUIT: 
                running = False
                
        player.update(dt, platforms)
        ghosts.update(dt)
        powerups.update(dt)
        platforms.update(dt)
        
        # Update particles
        particles = [p for p in particles if p.update(dt)]
        
        # Spawn ghosts with variety
        if random.random() < adaptive.spawn_rate:
            y = random.randint(SCREEN_HEIGHT-300, SCREEN_HEIGHT-80)
            if random.random() < 0.3:
                ghosts.add(SwordGhost(player.rect.x + SCREEN_WIDTH, y, adaptive.espeed * 0.8))
            else:
                ghosts.add(GhostEnemy(player.rect.x + SCREEN_WIDTH, y, adaptive.espeed))
                
        # Spawn powerups
        powerup_spawn_timer += dt
        if powerup_spawn_timer > 8:
            powerup_spawn_timer = 0
            ptype = random.choice(['health', 'speed', 'damage'])
            x = player.rect.x + random.randint(400, 800)
            y = random.randint(200, SCREEN_HEIGHT - 200)
            powerups.add(PowerUp(x, y, ptype))
            
        # Combat collisions
        if player.state.startswith('attack'):
            hits = pygame.sprite.spritecollide(player, ghosts, False)
            for g in hits:
                points = g.take_hit()
                score += points * (combo_count + 1)
                combo_count += 1
                combo_timer = COMBO_TIMEOUT
                
                # Create particles
                for _ in range(5):
                    particles.append(Particle(
                        g.rect.centerx, g.rect.centery,
                        WHITE, random.uniform(-3, 3), random.uniform(-3, 3)
                    ))
                    
        # Ghost hits player
        if player.invulnerable <= 0:
            hits = pygame.sprite.spritecollide(player, ghosts, False)
            for g in hits:
                player.health -= 10
                player.invulnerable = 1.0
                start_shake()
                g.kill()
                
                if player.health <= 0:
                    deaths += 1
                    player.health = player.max_health
                    player.rect.x = start_x
                    combo_count = 0
                    
        # Collect powerups
        collected = pygame.sprite.spritecollide(player, powerups, True)
        for powerup in collected:
            if powerup.ptype == 'health':
                player.health = min(player.max_health, player.health + 30)
                color = RED
            elif powerup.ptype == 'speed':
                player.powerup_timers['speed'] = 10
                color = YELLOW
            elif powerup.ptype == 'damage':
                player.powerup_timers['damage'] = 10
                color = PURPLE
                
            # Celebration particles
            for _ in range(20):
                particles.append(Particle(
                    powerup.rect.centerx, powerup.rect.centery,
                    color, random.uniform(-5, 5), random.uniform(-5, 5), 1.0
                ))
                
        # HUD update only on change
        hud_text = f"Score: {score}  Health: {player.health}/{player.max_health}"
        if combo_count > 0:
            hud_text += f"  COMBO x{combo_count}"
        if score != last_score or player.health != last_health or combo_count > 0:
            hud_surf = render_gradient_text(hud_text, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
            last_score, last_health = score, player.health
            
        # Transition check
        if player.rect.x >= transition_x:
            adaptive.update({'deaths': deaths, 'time': time.time()-level_start})
            final_score, victory = main_level2(screen, player, score, clock, adaptive)
            
            # Game over screen
            screen.fill(BLACK)
            if victory:
                msg = f"VICTORY! Final Score: {final_score}"
                color1, color2 = YELLOW, WHITE
            else:
                msg = f"GAME OVER. Score: {final_score}"
                color1, color2 = RED, WHITE
                
            text = render_gradient_text(msg, PIXEL_FONT, color1, color2)
            screen.blit(text, text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2)))
            
            # Show achievements
            y = SCREEN_HEIGHT//2 + 100
            for name, unlocked in achievements.items():
                if unlocked:
                    ach_text = render_gradient_text(f"✓ {name.replace('_', ' ').title()}", PIXEL_FONT, GREEN, WHITE)
                    screen.blit(ach_text, (SCREEN_WIDTH//2 - 200, y))
                    y += 40
                    
            pygame.display.flip()
            pygame.time.wait(5000)
            running = False
            
        # Render
        cam = player.rect.x - fixed_x + shake_offset[0]
        screen.fill(BLACK)
        bg = act1_bg_start if player.rect.x < transition_x - SCREEN_WIDTH else act1_bg_main
        screen.blit(bg, (-cam + shake_offset[0], shake_offset[1]))
        
        # Platforms
        for platform in platforms:
            r = platform.rect.copy()
            r.x -= cam
            screen.blit(platform.image, r)
            
        # Entities
        pr = player.rect.copy()
        pr.x -= cam
        screen.blit(player.image, pr)
        
        for g in ghosts:
            r = g.rect.copy()
            r.x -= cam
            screen.blit(g.image, r)
            
        for p in powerups:
            r = p.rect.copy()
            r.x -= cam
            screen.blit(p.image, r)
            
        # Particles
        for particle in particles:
            particle.draw(screen, cam)
            
        # HUD
        screen.blit(hud_surf, (20 + shake_offset[0], 20 + shake_offset[1]))
        
        # Powerup indicators
        y_offset = 60
        if player.powerup_timers['speed'] > 0:
            speed_text = render_gradient_text(f"SPEED: {player.powerup_timers['speed']:.1f}s", PIXEL_FONT, YELLOW, WHITE)
            screen.blit(speed_text, (20, y_offset))
            y_offset += 30
            
        if player.powerup_timers['damage'] > 0:
            damage_text = render_gradient_text(f"DMG x2: {player.powerup_timers['damage']:.1f}s", PIXEL_FONT, PURPLE, WHITE)
            screen.blit(damage_text, (20, y_offset))
            
        # Dash indicator
        if player.dash_cooldown > 0:
            dash_text = render_gradient_text(f"DASH: {player.dash_cooldown:.1f}s", PIXEL_FONT, BLUE, WHITE)
            screen.blit(dash_text, (SCREEN_WIDTH - 200, 20))
        else:
            dash_text = render_gradient_text("DASH READY! (SHIFT)", PIXEL_FONT, GREEN, WHITE)
            screen.blit(dash_text, (SCREEN_WIDTH - 200, 20))
            
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__': 
    main()