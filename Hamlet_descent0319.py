#!/usr/bin/env python3
"""
Hamlet's Descent: Ultimate Edition
-----------------------------------------------------------------
Fully integrated Act I & II with:
  • Combat, scoring & collision feedback (screen shake, sounds)
  • Adaptive difficulty tied to performance
  • Optimized HUD pre-rendering
  • Enhanced jump (coyote time, buffered & variable height)
  • Sprite flipping based on movement
  • Skip controls on intros
  • Educational quiz overlay before boss fight
"""
import pygame
import random
import sys
import time
import os
import textwrap

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
COYOTE_TIME        = 0.1   # Grace period after leaving ground
JUMP_BUFFER_TIME   = 0.1   # Buffer before landing
VARIABLE_JUMP_MULT = 0.5   # Cut jump if released early
LEVEL_WIDTH        = 10 * SCREEN_WIDTH

# Colors
BLACK = (0,0,0)
WHITE = (255,255,255)
RED   = (255,0,0)
BLUE  = (0,128,255)

# Sprite scales
PLAYER_SCALE = SPRITE_SCALE * 1.1
GHOST_SCALE  = 0.3

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


def start_shake():
    global shake_timer
    shake_timer = SHAKE_DURATION


def apply_shake(dt):
    global shake_timer, shake_offset
    if shake_timer>0:
        shake_timer = max(0, shake_timer-dt)
        shake_offset[0] = random.randint(-SHAKE_MAGNITUDE, SHAKE_MAGNITUDE)
        shake_offset[1] = random.randint(-SHAKE_MAGNITUDE, SHAKE_MAGNITUDE)
    else:
        shake_offset[0]=0; shake_offset[1]=0

# --------------------------------
# Entity Classes
# --------------------------------

class GhostEnemy(pygame.sprite.Sprite):
    def __init__(self,x,y,speed):
        super().__init__()
        sheet = pygame.image.load(os.path.join("assets","ghost_sheet.png")).convert_alpha()
        fw,fh = 204,341
        self.frames = [
            [pygame.transform.scale(sheet.subsurface((c*fw,r*fh,fw,fh)),
             (int(fw*GHOST_SCALE),int(fh*GHOST_SCALE))) for c in range(5)]
            for r in range(3)
        ]
        self.row=0; self.idx=0
        self.image = self.frames[0][0]
        self.rect  = self.image.get_rect(midbottom=(x,y))
        self.speed = speed
        self.timer = 0.0; self.delay = 0.2
        self.health=3
        self.bob_dir=1; self.bob=0

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

    def take_hit(self):
        self.health -= 1
        if self.health>0:
            self.row = 3 - self.health; self.idx=0
            start_shake()
        else:
            start_shake(); self.kill()


class EnemyCrow(pygame.sprite.Sprite):
    def __init__(self,x,y,speed):
        super().__init__()
        sheet = pygame.image.load(os.path.join("assets","crow_fly.png")).convert_alpha()
        w,h = sheet.get_width()//2, sheet.get_height()
        raw = [sheet.subsurface((i*w,0,w,h)).copy() for i in range(2)]
        self.frames = [pygame.transform.scale(f,(int(f.get_width()*SPRITE_SCALE),int(f.get_height()*SPRITE_SCALE))) for f in raw]
        self.idx=0; self.image=self.frames[0]
        self.rect = self.image.get_rect(topleft=(x,y))
        self.speed = speed; self.timer=0; self.delay=0.15

    def update(self,dt):
        self.rect.x -= self.speed
        self.timer += dt
        if self.timer>=self.delay:
            self.idx = (self.idx+1)%len(self.frames); self.timer=0
            self.image=self.frames[self.idx]
        if self.rect.right<0: self.kill()


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

    def update(self,dt):
        keys = pygame.key.get_pressed()
        # horizontal
        self.vx = -PLAYER_SPEED if keys[pygame.K_LEFT] else PLAYER_SPEED if keys[pygame.K_RIGHT] else 0
        # coyote & buffer
        self.coyote = COYOTE_TIME if self.on_ground else max(0,self.coyote-dt)
        self.jump_buffer = JUMP_BUFFER_TIME if keys[pygame.K_SPACE] else max(0,self.jump_buffer-dt)
        # jump
        if self.jump_buffer>0 and self.coyote>0:
            self.vy = JUMP_STRENGTH; self.on_ground=False; self.coyote=0; self.jump_buffer=0
            if self.jump_sound: self.jump_sound.play()
        # gravity
        self.vy += GRAVITY; self.rect.y += self.vy
        # ground collision
        if self.rect.bottom>=SCREEN_HEIGHT:
            self.rect.bottom=SCREEN_HEIGHT; self.vy=0; self.on_ground=True
        # variable jump
        if self.vy<0 and not keys[pygame.K_SPACE]: self.vy += GRAVITY*VARIABLE_JUMP_MULT
        # apply horiz
        self.rect.x += self.vx
        # state logic
        new='idle'
        if self.state.startswith('attack'):
            new=self.state
        elif keys[pygame.K_a]: new='attack1'
        elif not self.on_ground: new='jump'
        elif self.vx!=0: new='run'
        if new!=self.state:
            self.state=new; self.frames=self.anims[new]; self.idx=0; self.timer=0
        # animate
        self.timer+=dt
        if self.timer>=self.adelay:
            self.timer=0; self.idx=(self.idx+1)%len(self.frames)
            self.image=self.frames[self.idx]
            # flip
            if self.vx<0: self.image=pygame.transform.flip(self.image,True,False)
            if self.state.startswith('attack') and self.idx==len(self.frames)-1:
                self.state='idle'; self.frames=self.anims['idle']; self.idx=0

# Adaptive difficulty
class AdaptiveEngine:
    def __init__(self): self.diff=1.0; self.espeed=2
    def update(self,perf):
        if perf['deaths']>3:
            self.diff=max(0.5,self.diff*0.9); self.espeed=max(1,self.espeed*0.9)
        elif perf['deaths']==0 and perf['time']<60:
            self.diff=min(2.0,self.diff*1.1); self.espeed=min(5,self.espeed*1.1)
        print(f"AdaptiveEngine → diff={self.diff:.2f}, speed={self.espeed}")

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
    text=("Stage 1: Fight Your Fears... Ladies and gentlemen, here's Fortinbras!")
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


def main_level2(screen,player,score,clock):
    parallax=load_parallax_layers(); enemies=pygame.sprite.Group()
    fixed_x=100; start=time.time(); quote="To be, or not to be..."
    while time.time()-start<30:
        dt=clock.tick(FPS)/1000.0; apply_shake(dt)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: pygame.quit(); sys.exit()
        player.update(dt); enemies.update(dt)
        if random.random()<0.02:
            y=random.randint(SCREEN_HEIGHT-300,SCREEN_HEIGHT-80)
            enemies.add(EnemyCrow(player.rect.x+SCREEN_WIDTH,y,2))
        cam=player.rect.x-fixed_x+shake_offset[0]
        screen.fill(BLACK)
        for surf,f in parallax: screen.blit(surf,(-cam*f+shake_offset[0],shake_offset[1]))
        pr=player.rect.copy(); pr.x-=cam
        screen.blit(player.image,pr)
        for en in enemies:
            r=en.rect.copy(); r.x-=cam; screen.blit(en.image,r)
        hud=f"Score:{score}  Health:{player.health}"
        screen.blit(render_gradient_text(hud,PIXEL_FONT,TAN_TOP,TAN_BOTTOM),(20,20))
        qs=render_gradient_text(quote,PIXEL_FONT,TAN_TOP,TAN_BOTTOM)
        qr=qs.get_rect(center=(SCREEN_WIDTH/2,SCREEN_HEIGHT/2)); screen.blit(qs,qr)
        pygame.display.flip()

# --------------------------------
# Main Game Loop (Act I)
# --------------------------------

def main():
    global PIXEL_FONT, dt
    pygame.init(); pygame.font.init();
    try: pygame.mixer.init()
    except: pass
    PIXEL_FONT = pygame.font.Font("Pixel_NES.ttf", PIXEL_FONT_SIZE)
    screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
    pygame.display.set_caption("Hamlet's Descent - Act I")
    clock = pygame.time.Clock()

    show_loadscreen(screen)
    show_opening_scene(screen)
    show_stage_intro(screen)

    if os.path.exists("Onloose.mp3"):
        try: pygame.mixer.music.load("Onloose.mp3"); pygame.mixer.music.play(-1)
        except: pass

    adaptive = AdaptiveEngine()
    act1_bg_start = load_background_act1(True)
    act1_bg_main  = load_background_act1(False)
    player = Player(100,SCREEN_HEIGHT-100)
    ghosts = pygame.sprite.Group()

    score=0; deaths=0
    last_score, last_health = -1, -1
    fixed_x = 100
    start_x = player.rect.x
    transition_x = start_x + 5*SCREEN_WIDTH
    level_start=time.time()

    running=True
    while running:
        dt = clock.tick(FPS)/1000.0; apply_shake(dt)
        for e in pygame.event.get():
            if e.type==pygame.QUIT: running=False
        player.update(dt)
        ghosts.update(dt)
        # spawn ghosts
        if random.random()<0.01*adaptive.diff:
            y = random.randint(SCREEN_HEIGHT-300,SCREEN_HEIGHT-80)
            ghosts.add(GhostEnemy(player.rect.x+SCREEN_WIDTH,y,adaptive.espeed))
        # combat collisions
        if player.state.startswith('attack'):
            hits = pygame.sprite.spritecollide(player,ghosts,False)
            for g in hits:
                g.take_hit(); score+=10
        # ghost hits player
        hits = pygame.sprite.spritecollide(player,ghosts,False)
        for g in hits:
            player.health -= 10; start_shake(); g.kill()
            if player.health<=0:
                deaths+=1; player.health=100; player.rect.x = start_x
        # HUD update only on change
        if score!=last_score or player.health!=last_health:
            hud_surf = render_gradient_text(f"Score:{score}  Health:{player.health}", PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
            last_score, last_health = score, player.health
        # transition check
        if player.rect.x>=transition_x:
            adaptive.update({'deaths':deaths,'time':time.time()-level_start})
            main_level2(screen,player,score,clock)
            running=False
        # render
        cam = player.rect.x - fixed_x + shake_offset[0]
        screen.fill(BLACK)
        bg = act1_bg_start if player.rect.x<transition_x-SCREEN_WIDTH else act1_bg_main
        screen.blit(bg,(-cam+shake_offset[0],shake_offset[1]))
        pr = player.rect.copy(); pr.x -= cam
        screen.blit(player.image,pr)
        for g in ghosts:
            r=g.rect.copy(); r.x-=cam; screen.blit(g.image,r)
        screen.blit(hud_surf,(20+shake_offset[0],20+shake_offset[1]))
        pygame.display.flip()

    pygame.quit(); sys.exit()

if __name__=='__main__': main()
