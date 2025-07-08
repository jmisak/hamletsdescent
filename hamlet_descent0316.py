#!/usr/bin/env python3
"""
Hamlet's Descent: Act I and Transition to Level 2
--------------------------------------------------
Features:
  - Loadscreen and opening scene (with tomb background/music and typewriter text)
  - Stage Intro text box for Act I:
      "Stage 1: Fight Your Fears. Given the charge by your father, it is time to let loose your fears and face your demons. One awaits you. A onetime friend now turned ghoul. He's everything you should have been. Ladies and gentlemen, here's Fortinbras!"
  - Act I background:
      Initially uses "Level_1_backgroundstart.png" (scaled preserving aspect ratio and tiled)
      After 5 screen-widths, it switches to "Level_1_background.png".
  - Ghost enemies (from assets/ghost_sheet.png) that have 3 hit points; each hit causes decay (row advances).
  - Player character (from assets/adventurer) is slightly larger.
  - Act I music: "Onloose.mp3".
  - After Act I (after 5 screen scrolls), transition to Level 2 (original level with crow enemies and quotes).
  - Uses Pixel_NES.ttf for white gradient text.
  
The game uses a horizontal camera offset.
"""

import pygame
import random
import sys
import time
import os
import textwrap

print("Working Directory:", os.getcwd())
print("Font file exists:", os.path.exists("Pixel_NES.ttf"))

# ---------------------------
# Global Settings and Constants
# ---------------------------
SPRITE_SCALE = 2.25
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1200
FPS = 60
GRAVITY = 0.5
PLAYER_SPEED = 5
JUMP_STRENGTH = -10

# Level width for scrolling in Act I (and beyond)
LEVEL_WIDTH = 10 * SCREEN_WIDTH

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 128, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Scaling factors
PLAYER_SCALE = SPRITE_SCALE * 1.8      # Make player slightly larger
GHOST_SCALE = SPRITE_SCALE * 0.3       # Ghost enemy appears smaller

# Font – will be loaded after pygame.font.init()
PIXEL_FONT_SIZE = 28
PIXEL_FONT = None

# For white text gradient
TAN_TOP = (255, 255, 255)
TAN_BOTTOM = (255, 255, 255)

# ---------------------------
# Helper: Render Gradient Text
# ---------------------------
def render_gradient_text(text, font, color_start, color_end):
    text_surface = font.render(text, True, (255, 255, 255))
    text_surface = text_surface.convert_alpha()
    width, height = text_surface.get_size()
    gradient = pygame.Surface((width, height)).convert_alpha()
    for y in range(height):
        ratio = y / height
        r = int(color_start[0]*(1 - ratio) + color_end[0]*ratio)
        g = int(color_start[1]*(1 - ratio) + color_end[1]*ratio)
        b = int(color_start[2]*(1 - ratio) + color_end[2]*ratio)
        pygame.draw.line(gradient, (r, g, b), (0, y), (width, y))
    text_surface.blit(gradient, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return text_surface

# ---------------------------
# Utility Functions
# ---------------------------
def trim_surface(surface):
    mask = pygame.mask.from_surface(surface)
    rects = mask.get_bounding_rects()
    if rects:
        rect = rects[0]
    else:
        rect = surface.get_rect()
    return surface.subsurface(rect).copy()

def load_individual_frames(base_folder, animation, frame_count, variant=""):
    frames = []
    for i in range(frame_count):
        variant_part = f"-{variant}" if variant else ""
        filename = f"adventurer-{animation}{variant_part}-{i:02d}.png"
        full_path = os.path.join(base_folder, filename)
        if os.path.exists(full_path):
            try:
                image = pygame.image.load(full_path).convert_alpha()
                frames.append(image)
            except Exception as e:
                print(f"Error loading {full_path}: {e}")
        else:
            print(f"Missing file: {full_path}")
    return frames

# ---------------------------
# Load Background (Act I)
# ---------------------------
def load_background_act1(start=True):
    filename = "Level_1_backgroundstart.png" if start else "Level_1_background.png"
    if os.path.exists(filename):
        bg = pygame.image.load(filename).convert_alpha()
        # Scale preserving aspect ratio: scale height to SCREEN_HEIGHT
        scale_factor = SCREEN_HEIGHT / bg.get_height()
        new_width = int(bg.get_width() * scale_factor)
        scaled_bg = pygame.transform.scale(bg, (new_width, SCREEN_HEIGHT))
        # Tile horizontally over LEVEL_WIDTH
        level_bg = pygame.Surface((LEVEL_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for x in range(0, LEVEL_WIDTH, new_width):
            level_bg.blit(scaled_bg, (x, 0))
        return level_bg
    else:
        bg = pygame.Surface((LEVEL_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        bg.fill((50, 50, 50))
        return bg

# ---------------------------
# Show Loadscreen
# ---------------------------
def show_loadscreen(screen):
    loadscreen_path = "loadscreen.png"
    if os.path.exists(loadscreen_path):
        load_img = pygame.image.load(loadscreen_path).convert_alpha()
    else:
        load_img = pygame.Surface((768, 768), pygame.SRCALPHA)
        load_img.fill(BLACK)
    scale_factor = min(SCREEN_WIDTH / 768, SCREEN_HEIGHT / 768)
    new_width = int(768 * scale_factor)
    new_height = int(768 * scale_factor)
    load_img = pygame.transform.scale(load_img, (new_width, new_height))
    pos_x = (SCREEN_WIDTH - new_width) // 2
    pos_y = (SCREEN_HEIGHT - new_height) // 2
    screen.fill(BLACK)
    screen.blit(load_img, (pos_x, pos_y))
    pygame.display.flip()
    start_time = time.time()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                waiting = False
            elif event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        if time.time() - start_time > 10:
            waiting = False

# ---------------------------
# Show Opening Scene
# ---------------------------
def show_opening_scene(screen):
    tomb_bg_path = "tomb.png"
    if os.path.exists(tomb_bg_path):
        bg = pygame.image.load(tomb_bg_path).convert_alpha()
        bg = pygame.transform.scale(bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
    else:
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill(BLACK)
    
    tomb_music_path = "tomb_music.mp3"
    try:
        pygame.mixer.music.load(tomb_music_path)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print("Error loading tomb music:", e)

    full_text = ("Dear Son, I have forsaken you. Forcing you to revenge led only to sorrow and death. "
                 "'Now, I grant you the chance to fix it. Save your mother, set things right at the castle, "
                 "and find your dear Ophelia. I can only say this: Keep your sword at hand and trust no one. Your Father.'")
    words = full_text.split()
    displayed_text = ""
    
    clock = pygame.time.Clock()
    word_delay = 300
    last_word_time = pygame.time.get_ticks()
    word_index = 0

    opening_done = False
    while not opening_done:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        screen.blit(bg, (0, 0))
        current_time = pygame.time.get_ticks()
        if word_index < len(words) and current_time - last_word_time >= word_delay:
            displayed_text += (" " if displayed_text else "") + words[word_index]
            word_index += 1
            last_word_time = current_time

        lines = textwrap.wrap(displayed_text, width=70)
        y_offset = 50
        for line in lines:
            line_surface = render_gradient_text(line, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
            screen.blit(line_surface, (50, y_offset))
            y_offset += PIXEL_FONT.get_height() + 5
        pygame.display.flip()

        if word_index >= len(words):
            pygame.time.delay(3000)
            prompt = "Press X to start the game"
            prompt_surface = render_gradient_text(prompt, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
            prompt_rect = prompt_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 50))
            waiting_for_key = True
            while waiting_for_key:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit(); sys.exit()
                    if event.type == pygame.KEYDOWN and event.key == pygame.K_x:
                        waiting_for_key = False
                screen.blit(bg, (0, 0))
                lines = textwrap.wrap(displayed_text, width=70)
                y_offset = 50
                for line in lines:
                    line_surface = render_gradient_text(line, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
                    screen.blit(line_surface, (50, y_offset))
                    y_offset += PIXEL_FONT.get_height() + 5
                screen.blit(prompt_surface, prompt_rect)
                pygame.display.flip()
            opening_done = True
    pygame.mixer.music.stop()

# ---------------------------
# Show Stage Intro for Act I
# ---------------------------
def show_stage_intro(screen):
    intro_text = ("Stage 1: Fight Your Fears. Given the charge by your father, it is time to let loose your fears and face your demons. "
                  "One awaits you. A onetime friend now turned ghoul. He's everything you should have been. Ladies and gentlemen, here's Fortinbras!")
    text_surface = render_gradient_text(intro_text, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
    padding = 20
    box_rect = text_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    box_rect.inflate_ip(padding, padding)
    box = pygame.Surface((box_rect.width, box_rect.height), pygame.SRCALPHA)
    box.fill((0, 0, 0, 200))
    screen.fill(BLACK)
    screen.blit(box, box_rect)
    screen.blit(text_surface, text_surface.get_rect(center=box_rect.center))
    pygame.display.flip()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                waiting = False
            elif event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

# ---------------------------
# Act I Background Loader
# ---------------------------
def load_background_act1(start=True):
    filename = "Level_1_backgroundstart.png" if start else "Level_1_background.png"
    if os.path.exists(filename):
        bg = pygame.image.load(filename).convert_alpha()
        # Scale so height equals SCREEN_HEIGHT (preserving aspect ratio)
        scale_factor = SCREEN_HEIGHT / bg.get_height()
        new_width = int(bg.get_width() * scale_factor)
        scaled_bg = pygame.transform.scale(bg, (new_width, SCREEN_HEIGHT))
        # Tile horizontally over LEVEL_WIDTH
        level_bg = pygame.Surface((LEVEL_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for x in range(0, LEVEL_WIDTH, new_width):
            level_bg.blit(scaled_bg, (x, 0))
        return level_bg
    else:
        bg = pygame.Surface((LEVEL_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        bg.fill((50, 50, 50))
        return bg

# ---------------------------
# Ghost Enemy Class (Act I)
# ---------------------------
class GhostEnemy(pygame.sprite.Sprite):
    """
    Ghost enemy from ghost_sheet.png.
    Has 3 hit points; each hit advances its decay row.
    Each frame is 204x341 in a 3-row, 5-column sheet.
    """
    def __init__(self, x, y, speed):
        super().__init__()
        ghost_sheet_path = os.path.join("assets", "ghost_sheet.png")
        if os.path.exists(ghost_sheet_path):
            # Load with alpha
            sheet = pygame.image.load(ghost_sheet_path).convert_alpha()
            # The sheet is 3 rows x 5 columns, each frame 204x341
            frame_width = 204
            frame_height = 341
            self.frames = []
            for row in range(3):
                row_frames = []
                for col in range(5):
                    rect = pygame.Rect(
                        col * frame_width,
                        row * frame_height,
                        frame_width,
                        frame_height
                    )
                    frame = sheet.subsurface(rect).copy()
                    
                    # If you have alpha transparency, you don't need set_colorkey.
                    # If you still see a white box, uncomment:
                    # frame.set_colorkey((255, 255, 255))
                    
                    # Scale the frame
                    scaled_frame = pygame.transform.scale(
                        frame,
                        (
                            int(frame_width * GHOST_SCALE),
                            int(frame_height * GHOST_SCALE)
                        )
                    )
                    row_frames.append(scaled_frame)
                self.frames.append(row_frames)
        else:
            # Fallback if sheet not found
            fallback = pygame.Surface((50, 50), pygame.SRCALPHA)
            fallback.fill((255, 0, 0))
            self.frames = [[fallback] * 5]

        # Start at undamaged row (0), first frame
        self.current_row = 0
        self.current_frame = 0
        self.image = self.frames[self.current_row][self.current_frame]
        self.rect = self.image.get_rect()

        # Place ghost so its bottom aligns at y
        self.world_x = x
        self.world_y = y - self.rect.height
        self.rect.x = self.world_x
        self.rect.y = self.world_y

        self.speed = speed
        self.health = 3
        self.animation_timer = 0.0
        self.animation_delay = 0.2

    def update(self, dt):
        # Move ghost to the left
        self.world_x -= self.speed
        self.rect.x = self.world_x

        # Animate
        self.animation_timer += dt
        if self.animation_timer >= self.animation_delay:
            self.current_frame = (self.current_frame + 1) % 5
            self.image = self.frames[self.current_row][self.current_frame]
            self.animation_timer = 0.0

        # Kill if offscreen
        if self.rect.right < 0:
            self.kill()

    def take_hit(self):
        self.health -= 1
        if self.health > 0:
            # 3 hits total; row 0 = healthy, row 1 = 1 hit, row 2 = 2 hits
            self.current_row = 3 - self.health
            self.current_frame = 0
        else:
            self.kill()

# ---------------------------
# Player Class
# ---------------------------
class Player(pygame.sprite.Sprite):
    """Player character from assets/adventurer with 100 HP and triple jump capability."""
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.world_x = x
        self.world_y = y
        self.health = 100
        self.animations = {}
        base_path = os.path.join("assets", "adventurer")
        frame_width = 71
        frame_height = 86
        self.animations['idle'] = load_individual_frames(base_path, "idle", 3)
        if not self.animations['idle']:
            fallback = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            fallback.fill(BLUE)
            pygame.draw.rect(fallback, WHITE, fallback.get_rect(), 3)
            self.animations['idle'] = [fallback]
        self.animations['run'] = load_individual_frames(base_path, "run", 3)
        if not self.animations['run']:
            fallback = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            fallback.fill(BLUE)
            pygame.draw.rect(fallback, WHITE, fallback.get_rect(), 3)
            self.animations['run'] = [fallback]
        self.animations['jump'] = load_individual_frames(base_path, "jump", 3)
        if not self.animations['jump']:
            fallback = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            fallback.fill(BLUE)
            pygame.draw.rect(fallback, WHITE, fallback.get_rect(), 3)
            self.animations['jump'] = [fallback]
        self.animations['attack1'] = load_individual_frames(base_path, "attack1", 3)
        if not self.animations['attack1']:
            fallback = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            fallback.fill(BLUE)
            pygame.draw.rect(fallback, WHITE, fallback.get_rect(), 3)
            self.animations['attack1'] = [fallback]
        self.animations['attack2'] = load_individual_frames(base_path, "attack2", 3)
        if not self.animations['attack2']:
            fallback = pygame.Surface((frame_width, frame_height), pygame.SRCALPHA)
            fallback.fill(BLUE)
            pygame.draw.rect(fallback, WHITE, fallback.get_rect(), 3)
            self.animations['attack2'] = [fallback]
        # Use PLAYER_SCALE for player sprites
        for key in self.animations:
            self.animations[key] = [pygame.transform.scale(frame, (int(frame.get_width()*PLAYER_SCALE),
                                                                    int(frame.get_height()*PLAYER_SCALE)))
                                    for frame in self.animations[key]]
        self.state = 'idle'
        self.frames = self.animations[self.state]
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.x = self.world_x
        self.rect.y = self.world_y
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.bounce_cooldown = 0.0
        self.jump_sound = None
        self.animation_timer = 0.0
        self.animation_delay = 0.15
        self.jump_pressed = False
        self.jump_count = 0
        self.max_jumps = 3

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if not self.state.startswith("attack"):
            if keys[pygame.K_LEFT]:
                self.vel_x = -PLAYER_SPEED
            elif keys[pygame.K_RIGHT]:
                self.vel_x = PLAYER_SPEED
            else:
                self.vel_x = 0
        self.world_x += self.vel_x
        self.vel_y += GRAVITY
        self.world_y += self.vel_y
        if self.world_y + self.rect.height >= SCREEN_HEIGHT:
            self.world_y = SCREEN_HEIGHT - self.rect.height
            self.vel_y = 0
            self.on_ground = True
            self.jump_count = 0
        else:
            self.on_ground = False
        if keys[pygame.K_SPACE]:
            if not self.jump_pressed and self.jump_count < self.max_jumps:
                if self.jump_sound:
                    self.jump_sound.play()
                self.vel_y = JUMP_STRENGTH
                self.jump_count += 1
                self.jump_pressed = True
        else:
            self.jump_pressed = False
        if self.state.startswith("attack"):
            new_state = self.state
        else:
            if keys[pygame.K_a]:
                new_state = 'attack1'
            elif not self.on_ground:
                new_state = 'jump'
            elif self.vel_x != 0:
                new_state = 'run'
            else:
                new_state = 'idle'
        if new_state != self.state:
            self.state = new_state
            self.frames = self.animations[self.state]
            self.current_frame = 0
            self.animation_timer = 0.0
            self.image = self.frames[self.current_frame]
        self.animation_timer += dt
        if self.animation_timer >= self.animation_delay:
            old_midbottom = self.rect.midbottom
            if self.state.startswith("attack"):
                if self.current_frame < len(self.frames) - 1:
                    self.current_frame += 1
                else:
                    self.state = 'idle'
                    self.frames = self.animations['idle']
                    self.current_frame = 0
                self.image = self.frames[self.current_frame]
            else:
                self.current_frame = (self.current_frame + 1) % len(self.frames)
                self.image = self.frames[self.current_frame]
            self.rect = self.image.get_rect()
            self.rect.midbottom = old_midbottom
            self.animation_timer = 0.0
        if self.bounce_cooldown > 0:
            self.bounce_cooldown -= dt
        self.rect.x = self.world_x
        self.rect.y = self.world_y

# ---------------------------
# Knight Class (Not used in Act I)
# ---------------------------
class Knight(pygame.sprite.Sprite):
    """Knight enemy for the battle with 75 HP from assets/knight."""
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.health = 75
        self.animations = {}
        base_path = os.path.join("assets", "knight")
        try:
            self.animations['walk'] = [pygame.image.load(os.path.join(base_path, "walk.png")).convert_alpha()]
        except Exception as e:
            self.animations['walk'] = []
        try:
            self.animations['jump'] = [pygame.image.load(os.path.join(base_path, "Jump.png")).convert_alpha()]
        except Exception as e:
            self.animations['jump'] = []
        try:
            self.animations['defend'] = [pygame.image.load(os.path.join(base_path, "Defend.png")).convert_alpha()]
        except Exception as e:
            self.animations['defend'] = []
        try:
            self.animations['attack'] = [pygame.image.load(os.path.join(base_path, "Attack_1.png")).convert_alpha(),
                                         pygame.image.load(os.path.join(base_path, "Attack_2.png")).convert_alpha()]
        except Exception as e:
            self.animations['attack'] = []
        if not self.animations['walk']:
            fallback = pygame.Surface((80, 100), pygame.SRCALPHA)
            fallback.fill(RED)
            self.animations['walk'] = [fallback]
        if not self.animations['attack']:
            fallback = pygame.Surface((80, 100), pygame.SRCALPHA)
            fallback.fill(RED)
            self.animations['attack'] = [fallback]
        for key in self.animations:
            self.animations[key] = [pygame.transform.scale(frame, (int(frame.get_width()*SPRITE_SCALE),
                                                                    int(frame.get_height()*SPRITE_SCALE)))
                                    for frame in self.animations[key]]
        self.state = 'walk'
        self.frames = self.animations[self.state]
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.world_x = x
        self.world_y = SCREEN_HEIGHT - self.rect.height
        self.rect.x = self.world_x
        self.rect.y = self.world_y
        self.vel_x = 0
        self.animation_timer = 0.0
        self.animation_delay = 0.3
        self.attack_cooldown = 0.0

    def update(self, dt, player):
        if abs(self.world_x - player.world_x) < 300:
            self.state = 'attack'
        else:
            self.state = 'walk'
        self.frames = self.animations[self.state]
        self.animation_timer += dt
        if self.animation_timer >= self.animation_delay:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
            self.animation_timer = 0.0
        self.rect.x = self.world_x
        self.rect.y = self.world_y
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

# ---------------------------
# Battle Function (Level 2 Transition)
# ---------------------------
def main_level2():
    """
    This function represents Level 2: the original level with crow enemies and quotes.
    For brevity, this is a simplified loop that spawns crow enemies (using EnemyCrow) and displays a quote.
    """
    # (Reusing previous EnemyCrow class and a basic level loop)
    # Load parallax layers for Level 2:
    parallax_layers = load_parallax_layers()
    # Set up a new level loop for Level 2
    score = 0
    level_start_x = player.world_x
    fixed_player_screen_x = 100
    quote_text = "This is a sample quote from Hamlet..."
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        player.update(dt)
        # (For Level 2, spawn crow enemies instead)
        if random.random() < 0.01:
            enemy_y = random.randint(SCREEN_HEIGHT - 300, SCREEN_HEIGHT - 80)
            enemy = EnemyCrow(player.world_x + SCREEN_WIDTH, enemy_y, 2)
            level_obj.enemy_list.add(enemy)
        level_obj.enemy_list.update(dt)
        camera_x = player.world_x - fixed_player_screen_x
        screen.fill(BLACK)
        for layer_surface, factor in parallax_layers:
            layer_offset = -camera_x * factor
            screen.blit(layer_surface, (layer_offset, 0))
        player_screen_rect = player.rect.copy()
        player_screen_rect.x = player.world_x - camera_x
        screen.blit(player.image, player_screen_rect)
        for enemy in level_obj.enemy_list:
            enemy_screen_rect = enemy.rect.copy()
            enemy_screen_rect.x = enemy.world_x - camera_x
            screen.blit(enemy.image, enemy_screen_rect)
        # Display a HUD and quote
        hud_text = f"Score: {score}   Health: {player.health}"
        hud_surface = render_gradient_text(hud_text, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        screen.blit(hud_surface, (20, 20))
        quote_surface = render_gradient_text(quote_text, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        quote_rect = quote_surface.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        screen.blit(quote_surface, quote_rect)
        pygame.display.flip()
        # For demonstration, exit after 30 seconds
        if time.time() - level_start_time > 30:
            running = False

# ---------------------------
# EnemyCrow Class (Level 2)
# ---------------------------
class EnemyCrow(pygame.sprite.Sprite):
    """Crow enemy that animates using a sprite sheet from crow_fly.png."""
    def __init__(self, x, y, speed):
        pygame.sprite.Sprite.__init__(self)
        crow_sheet_path = os.path.join("assets", "crow_fly.png")
        if os.path.exists(crow_sheet_path):
            try:
                sheet = pygame.image.load(crow_sheet_path).convert_alpha()
                sheet_rect = sheet.get_rect()
                frame_width = sheet_rect.width // 2
                frame_height = sheet_rect.height
                self.frames = []
                for i in range(2):
                    rect = pygame.Rect(i * frame_width, 0, frame_width, frame_height)
                    frame = sheet.subsurface(rect).copy()
                    self.frames.append(frame)
            except Exception as e:
                print("Error loading crow_fly.png:", e)
                fallback = pygame.Surface((48, 48), pygame.SRCALPHA)
                fallback.fill(RED)
                self.frames = [fallback]
        else:
            fallback = pygame.Surface((48, 48), pygame.SRCALPHA)
            fallback.fill(RED)
            self.frames = [fallback]
        self.frames = [pygame.transform.scale(frame, (int(frame.get_width()*SPRITE_SCALE),
                                                        int(frame.get_height()*SPRITE_SCALE)))
                       for frame in self.frames]
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.world_x = x
        self.world_y = y
        self.rect.x = self.world_x
        self.rect.y = self.world_y
        self.speed = speed
        self.animation_timer = 0.0
        self.animation_delay = 0.15

    def update(self, dt):
        self.world_x -= self.speed
        self.rect.x = self.world_x
        self.animation_timer += dt
        if self.animation_timer >= self.animation_delay:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
            self.animation_timer = 0.0
        if self.rect.right < 0:
            self.kill()

# ---------------------------
# Adaptive Engine Class
# ---------------------------
class AdaptiveEngine:
    def __init__(self):
        self.difficulty = 1.0
        self.enemy_speed = 2
        self.death_count = 0

    def update_difficulty(self, performance):
        if performance['deaths'] > 3:
            self.difficulty = max(0.5, self.difficulty * 0.9)
            self.enemy_speed = max(1, self.enemy_speed * 0.9)
        elif performance['deaths'] == 0 and performance['time'] < 60:
            self.difficulty = min(2.0, self.difficulty * 1.1)
            self.enemy_speed = min(5, self.enemy_speed * 1.1)
        print("Adaptive Engine Update: Difficulty =", self.difficulty, "Enemy Speed =", self.enemy_speed)

# ---------------------------
# Act I Level Class
# ---------------------------
class ActILevel:
    def __init__(self, adaptive_engine):
        self.enemy_list = pygame.sprite.Group()
        self.adaptive_engine = adaptive_engine
        self.bg_start = load_background_act1(start=True)
        self.bg_main = load_background_act1(start=False)
        self.current_bg = self.bg_start

    def update(self, dt):
        self.enemy_list.update(dt)
        if random.random() < 0.01 * self.adaptive_engine.difficulty:
            enemy_y = random.randint(SCREEN_HEIGHT - 300, SCREEN_HEIGHT - 80)
            enemy = GhostEnemy(player.world_x + SCREEN_WIDTH, enemy_y, self.adaptive_engine.enemy_speed)
            self.enemy_list.add(enemy)

# ---------------------------
# Main Game Loop (Act I)
# ---------------------------
def main():
    global quote_index, current_quote, current_quote_kill_count, current_quote_display, quote_reset_time
    global mentor, mentor_spawned, mentor_spoken, chest, chest_spawned, letter_shown, player, score, PIXEL_FONT, level_obj, level_start_time, clock

    pygame.init()
    pygame.font.init()
    try:
        pygame.mixer.init()
    except Exception as e:
        print("Error initializing mixer:", e)
    PIXEL_FONT = pygame.font.Font("Pixel_NES.ttf", PIXEL_FONT_SIZE)
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hamlet's Descent - Act I")
    clock = pygame.time.Clock()

    show_loadscreen(screen)
    show_opening_scene(screen)
    show_stage_intro(screen)
    
    # Load Act I music ("Onloose.mp3")
    if os.path.exists("Onloose.mp3"):
        try:
            pygame.mixer.music.load("Onloose.mp3")
            pygame.mixer.music.play(-1)
            print("Act I music loaded and playing.")
        except Exception as e:
            print("Error loading Onloose.mp3:", e)
    else:
        print("Onloose.mp3 not found.")

    adaptive_engine = AdaptiveEngine()
    act1_level = ActILevel(adaptive_engine)
    level_obj = act1_level  # For convenience in transition
    player = Player(100, SCREEN_HEIGHT - 100)
    if os.path.exists("jump.mp3"):
        player.jump_sound = pygame.mixer.Sound("jump.mp3")
    else:
        player.jump_sound = None

    score = 0
    level_start_x = player.world_x
    fixed_player_screen_x = 100
    # Transition: after 5 screen-width scrolls from level_start_x, switch to Level 2
    transition_x = level_start_x + 5 * SCREEN_WIDTH
    level_start_time = time.time()

    # Act I Loop
    while True:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        player.update(dt)
        act1_level.update(dt)
        if player.world_x >= transition_x:
            # Transition to Level 2:
            main_level2(screen, player, score, clock)
            pygame.quit()
            sys.exit()

        camera_x = player.world_x - fixed_player_screen_x

        screen.fill(BLACK)
        screen.blit(act1_level.current_bg, (-camera_x, 0))
        player_screen_rect = player.rect.copy()
        player_screen_rect.x = player.world_x - camera_x
        screen.blit(player.image, player_screen_rect)
        for enemy in act1_level.enemy_list:
            enemy_screen_rect = enemy.rect.copy()
            enemy_screen_rect.x = enemy.world_x - camera_x
            screen.blit(enemy.image, enemy_screen_rect)
        hud_text = f"Score: {score}   Health: {player.health}"
        hud_surface = render_gradient_text(hud_text, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        screen.blit(hud_surface, (20, 20))
        pygame.display.flip()

# ---------------------------
# Main Level 2 Loop (Transition Level)
# ---------------------------
def main_level2(screen, player, score, clock):
    """
    Level 2: the original level with crow enemies and quotes.
    This is a simplified loop demonstrating the transition.
    """
    # For Level 2, we'll use parallax layers.
    parallax_layers = load_parallax_layers()
    # Create a simple level object to manage crow enemies.
    level2_enemy_group = pygame.sprite.Group()
    level2_start_x = player.world_x
    fixed_player_screen_x = 100
    start_time = time.time()
    # For quotes, we'll use a simple fixed quote.
    quote_text = "To be, or not to be, that is the question."
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        player.update(dt)
        # Spawn crow enemies randomly
        if random.random() < 0.01:
            enemy_y = random.randint(SCREEN_HEIGHT - 300, SCREEN_HEIGHT - 80)
            enemy = EnemyCrow(player.world_x + SCREEN_WIDTH, enemy_y, 2)
            level2_enemy_group.add(enemy)
        level2_enemy_group.update(dt)
        camera_x = player.world_x - fixed_player_screen_x
        screen.fill(BLACK)
        for layer_surface, factor in parallax_layers:
            layer_offset = -camera_x * factor
            screen.blit(layer_surface, (layer_offset, 0))
        player_screen_rect = player.rect.copy()
        player_screen_rect.x = player.world_x - camera_x
        screen.blit(player.image, player_screen_rect)
        for enemy in level2_enemy_group:
            enemy_screen_rect = enemy.rect.copy()
            enemy_screen_rect.x = enemy.world_x - camera_x
            screen.blit(enemy.image, enemy_screen_rect)
        hud_text = f"Score: {score}   Health: {player.health}"
        hud_surface = render_gradient_text(hud_text, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        screen.blit(hud_surface, (20, 20))
        quote_surface = render_gradient_text(quote_text, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        quote_rect = quote_surface.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        screen.blit(quote_surface, quote_rect)
        pygame.display.flip()
        # For demonstration, exit after 30 seconds in Level 2
        if time.time() - start_time > 30:
            running = False

if __name__ == '__main__':
    main()
