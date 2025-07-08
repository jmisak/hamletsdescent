#!/usr/bin/env python3
"""
Hamlet's Descent: A Learning Platform Adventure with Level-Based Backgrounds,
a Knight Battle, a HUD, a Dynamic Quote Mechanism, a Mentor Encounter, and a Chest Puzzle

This version includes:
  - A loadscreen (loadscreen.png)
  - An opening scene with a tomb background (tomb.png), tomb music (tomb_music.mp3),
    and typewriter-effect text that appears word by word.
  - After the opening text is complete, the game waits three seconds and then tells the player
    to press X to start the main game.
  - A parallax background for each level built from two layers.
  - At the end of level 0, a battle with the Knight occurs.
  - After the first screen scroll, a mentor helper (Ophelia) appears.
    Her idle image is loaded from assets/mentor_sheet.png.
    When the player collides with her, a centered popup appears with her narrative.
  - On four screen-width scrolls, a chest appears.
    The chest uses frames from chest_sheet.png in assets.
    When the player attacks the chest (colliding while in attack state), it opens (plays its open animation).
    Once opened, the chest reveals a letter (letter.png from assets) and a popup text appears.
  - Background music loaded from "bg_music.mp3" for the main game.
  - Animated sprites for the player from assets/adventurer.
  - A tiled visual ground (from ground.png) at the bottom.
  - Animated crow enemies from crow_fly.png.
  - Sound effects (sword.mp3 and jump.mp3).
  - A HUD displaying Health, Score, and Time.
  - A quote mechanism that initially shows the original Shakespearean quote in the center.
    On the first crow kill it updates to a modern translation; on the second, to a contextual definition,
    which stays on screen for 4 seconds before a new quote appears.
  
The world scrolls continuously via a camera offset so that the player remains fixed horizontally.
During the Knight battle, combat rules apply (player: 100 HP, Knight: 75 HP, damage as specified).
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

LEVEL_WIDTH = 10 * SCREEN_WIDTH  # Each level spans 10 screen widths
CHEST_FRAME_WIDTH = 80
CHEST_FRAME_HEIGHT = 80

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 128, 255)   # fallback for player
GREEN = (0, 255, 0)    # fallback for ground
RED = (255, 0, 0)      # fallback for enemies

# We'll initialize PIXEL_FONT later (after pygame.font.init())
PIXEL_FONT_SIZE = 28
PIXEL_FONT = None  # global font variable; assigned later

# For white text, set both gradient colors to white:
TAN_TOP = (255, 255, 255)
TAN_BOTTOM = (255, 255, 255)

# ---------------------------
# Helper: Render Gradient Text
# ---------------------------
def render_gradient_text(text, font, color_start, color_end):
    """
    Renders text with a vertical gradient.
    Returns a surface with gradient text.
    """
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
    """Trim transparent pixels from a surface and return the trimmed surface."""
    mask = pygame.mask.from_surface(surface)
    rects = mask.get_bounding_rects()
    if rects:
        rect = rects[0]
    else:
        rect = surface.get_rect()
    return surface.subsurface(rect).copy()

def load_individual_frames(base_folder, animation, frame_count, variant=""):
    """
    Load individual frames for an animation from base_folder.
    Filenames follow the convention:
      adventurer-{animation}{-variant if provided}-{frame_index:02d}.png
    """
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

def show_loadscreen(screen):
    """Display the loadscreen image for 3 seconds or until a key is pressed."""
    loadscreen_path = "loadscreen.png"
    if os.path.exists(loadscreen_path):
        load_img = pygame.image.load(loadscreen_path).convert_alpha()
    else:
        load_img = pygame.Surface((768, 768), pygame.SRCALPHA)
        load_img.fill((0, 0, 0))
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
                pygame.quit()
                sys.exit()
        if time.time() - start_time > 10:
            waiting = False

def show_opening_scene(screen):
    """
    Displays the opening scene:
      - Background: tomb.png
      - Music: tomb_music.mp3
      - Typewriter effect text appearing word by word (rendered in PIXEL_FONT with gradient).
      - After text is complete, wait 3 seconds then display "Press X to start the game".
      - Wait for X key press before returning.
    """
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
    word_delay = 300  # milliseconds delay per word
    last_word_time = pygame.time.get_ticks()
    word_index = 0

    opening_done = False

    while not opening_done:
        dt = clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        
        screen.blit(bg, (0, 0))
        current_time = pygame.time.get_ticks()
        if word_index < len(words) and current_time - last_word_time >= word_delay:
            if displayed_text:
                displayed_text += " " + words[word_index]
            else:
                displayed_text = words[word_index]
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
                        pygame.quit()
                        sys.exit()
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

def load_parallax_layers():
    """
    Load two parallax background layers.
    Each layer is scaled to SCREEN_HEIGHT, tiled horizontally to LEVEL_WIDTH,
    and paired with a parallax factor.
    """
    layers = []
    filenames = ["bg_layer1.png", "bg_layer2.png"]
    factors = [0.3, 0.7]
    for i, file in enumerate(filenames):
        if os.path.exists(file):
            img = pygame.image.load(file).convert_alpha()
        else:
            img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            img.fill((100 + i * 50, 100, 100, 150))
        scale_factor = SCREEN_HEIGHT / img.get_height()
        new_width = int(img.get_width() * scale_factor)
        scaled_img = pygame.transform.scale(img, (new_width, SCREEN_HEIGHT))
        layer_surface = pygame.Surface((LEVEL_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for x in range(0, LEVEL_WIDTH, new_width):
            layer_surface.blit(scaled_img, (x, 0))
        layers.append((layer_surface, factors[i]))
    return layers

# ---------------------------
# Global Quote Variables
# ---------------------------
quotes = [
    {
        "original": "O, that this too, too sullied flesh would melt, Thaw, and resolve itself into a dew!",
        "modern": "Oh, if only my corrupt body could just melt away!",
        "explanation": "Hamlet laments his decaying body and life, expressing his deep despair."
    },
    {
        "original": "There is nothing either good or bad, but thinking makes it so.",
        "modern": "Things aren’t inherently good or bad; it’s our perception that defines them.",
        "explanation": "Hamlet reflects on how our opinions give meaning to things."
    },
    {
        "original": "What a piece of work is a man! How noble in reason, how infinite in faculty!",
        "modern": "Man is an amazing creation—so wise and capable!",
        "explanation": "Despite his melancholy, Hamlet admires human potential and complexity."
    },
    {
        "original": "The lady doth protest too much, methinks.",
        "modern": "I think she overdoes her denials.",
        "explanation": "Excessive protestation may reveal hidden guilt or deception."
    }
]
quote_index = 0
current_quote = quotes[quote_index]
current_quote_kill_count = 0
current_quote_display = current_quote["original"]
quote_reset_time = None

# ---------------------------
# Mentor Class
# ---------------------------
class Mentor(pygame.sprite.Sprite):
    """A helper character that does not move. Loads its idle image from mentor_sheet.png."""
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        mentor_image_path = os.path.join("assets", "mentor_sheet.png")
        if os.path.exists(mentor_image_path):
            image = pygame.image.load(mentor_image_path).convert_alpha()
            mentor_scale = SPRITE_SCALE * 0.75
            self.image = pygame.transform.scale(image, (int(image.get_width() * mentor_scale),
                                                          int(image.get_height() * mentor_scale)))
        else:
            self.image = pygame.Surface((80, 100), pygame.SRCALPHA)
            self.image.fill((200, 200, 200))
        self.rect = self.image.get_rect()
        self.world_x = x
        self.world_y = SCREEN_HEIGHT - self.rect.height
        self.rect.x = self.world_x
        self.rect.y = self.world_y

    def update(self, dt):
        pass

# ---------------------------
# show_narrative Function
# ---------------------------
def show_narrative(screen, mentor):
    """
    Displays a centered popup with Ophelia's narrative.
    The popup uses gradient text rendered in PIXEL_FONT.
    It remains visible until either three key presses have occurred or 10 seconds have passed.
    """
    narrative_text = ("Ghost of Ophelia: You've returned. Did you ever really love me? "
                      "Only with a pure heart can you find the truth...and me.")
    popup_width = 1200
    popup_height = 400
    popup = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
    popup.fill((0, 0, 0, 200))
    wrapped_text = textwrap.wrap(narrative_text, width=50)
    y_offset = 20
    for line in wrapped_text:
        line_surface = render_gradient_text(line, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        popup.blit(line_surface, (20, y_offset))
        y_offset += PIXEL_FONT.get_height() + 5
    popup_rect = popup.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    screen.blit(popup, popup_rect)
    pygame.display.flip()
    start_time = time.time()
    key_press_count = 0
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                key_press_count += 1
                if key_press_count >= 3:
                    waiting = False
            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        if time.time() - start_time >= 10.0:
            waiting = False

# ---------------------------
# Chest Class
# ---------------------------
class Chest(pygame.sprite.Sprite):
    """A chest that opens when attacked. Uses frames from chest_sheet.png."""
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        chest_sheet_path = os.path.join("assets", "chest_sheet.png")
        if os.path.exists(chest_sheet_path):
            self.frames = load_individual_frames(os.path.join("assets"), "chest", 4, variant="sheet")
            self.frames = [pygame.transform.scale(frame, (int(frame.get_width()*SPRITE_SCALE),
                                                            int(frame.get_height()*SPRITE_SCALE)))
                           for frame in self.frames]
        else:
            self.frames = [pygame.Surface((80, 80), pygame.SRCALPHA)]
            self.frames[0].fill(RED)
        self.state = "closed"
        self.opened = False
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.world_x = x
        self.world_y = y
        self.rect.x = self.world_x
        self.rect.y = self.world_y
        self.animation_timer = 0.0
        self.animation_delay = 0.2

    def update(self, dt):
        if self.state == "opening" and not self.opened:
            self.animation_timer += dt
            if self.animation_timer >= self.animation_delay:
                self.animation_timer = 0.0
                self.current_frame += 1
                if self.current_frame >= len(self.frames):
                    self.current_frame = len(self.frames) - 1
                    self.opened = True
                    self.state = "open"
                self.image = self.frames[self.current_frame]

# ---------------------------
# show_letter Function
# ---------------------------
def show_letter(screen):
    """
    Displays a popup with the letter.
    The letter image and narrative text are rendered with gradient text.
    The popup remains for 4 seconds or until a key is pressed.
    """
    letter_path = os.path.join("assets", "letter.png")
    if os.path.exists(letter_path):
        letter_img = pygame.image.load(letter_path).convert_alpha()
        letter_img = pygame.transform.scale(letter_img, (int(letter_img.get_width()*SPRITE_SCALE),
                                                           int(letter_img.get_height()*SPRITE_SCALE)))
    else:
        letter_img = pygame.Surface((100, 100), pygame.SRCALPHA)
        letter_img.fill(WHITE)
    popup_width = 800
    popup_height = 400
    popup = pygame.Surface((popup_width, popup_height), pygame.SRCALPHA)
    popup.fill((0, 0, 0, 200))
    letter_rect = letter_img.get_rect()
    letter_rect.centerx = popup_width // 2
    letter_rect.y = 20
    popup.blit(letter_img, letter_rect)
    letter_text = ("You've found a letter, apparently to Hamlet's mother, dated before the King's death. "
                   "'Dearest Gertrude: I promise I will do whatever necessary so we can be together. "
                   "I need only hear your command and I will act. Forever yours, Claudius.'")
    wrapped_text = textwrap.wrap(letter_text, width=70)
    y_offset = letter_rect.bottom + 20
    for line in wrapped_text:
        line_surface = render_gradient_text(line, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        popup.blit(line_surface, (20, y_offset))
        y_offset += PIXEL_FONT.get_height() + 5
    popup_rect = popup.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
    screen.blit(popup, popup_rect)
    pygame.display.flip()
    start_time = time.time()
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                waiting = False
            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        if time.time() - start_time >= 4.0:
            waiting = False

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
        for key in self.animations:
            self.animations[key] = [pygame.transform.scale(frame, (int(frame.get_width()*SPRITE_SCALE),
                                                                    int(frame.get_height()*SPRITE_SCALE)))
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
# Knight Class
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
# Battle Function (Knight Battle)
# ---------------------------
def battle_with_knight(screen, player, score):
    """Handles the battle between the player and the Knight."""
    knight = Knight(player.world_x + 500, 0)
    player.health = 100
    knight.health = 75
    battle_clock = pygame.time.Clock()
    battle_running = True
    battle_start_time = time.time()
    font = PIXEL_FONT
    while battle_running:
        dt = battle_clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        player.update(dt)
        knight.update(dt, player)
        if player.rect.colliderect(knight.rect):
            if player.state.startswith("attack") and player.bounce_cooldown <= 0:
                knight.health -= 15
                player.bounce_cooldown = 0.5
            if knight.state == 'attack' and knight.attack_cooldown <= 0:
                player.health -= 2
                knight.attack_cooldown = 1.0
        if knight.health <= 0:
            score += 20
            battle_running = False
            result_text = "Victory! You defeated the Knight."
        if player.health <= 0:
            battle_running = False
            result_text = "Defeat! You were slain by the Knight."
        camera_x = (player.world_x + knight.world_x) / 2 - SCREEN_WIDTH / 2
        screen.fill(BLACK)
        player_screen_rect = player.rect.copy()
        player_screen_rect.x = player.world_x - camera_x
        knight_screen_rect = knight.rect.copy()
        knight_screen_rect.x = knight.world_x - camera_x
        screen.blit(player.image, player_screen_rect)
        screen.blit(knight.image, knight_screen_rect)
        p_health_surface = render_gradient_text(f"Player HP: {player.health}", PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        k_health_surface = render_gradient_text(f"Knight HP: {knight.health}", PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        score_surface = render_gradient_text(f"Score: {score}", PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        battle_time = int(time.time() - battle_start_time)
        time_surface = render_gradient_text(f"Battle Time: {battle_time} sec", PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        screen.blit(p_health_surface, (20, 20))
        screen.blit(k_health_surface, (20, 60))
        screen.blit(score_surface, (20, 100))
        screen.blit(time_surface, (20, 140))
        pygame.display.flip()
    end_clock = pygame.time.Clock()
    end_time = time.time()
    while time.time() - end_time < 3:
        dt = end_clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        screen.fill(BLACK)
        result_surface = render_gradient_text(result_text, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        result_rect = result_surface.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        screen.blit(result_surface, result_rect)
        pygame.display.flip()
    return score

# ---------------------------
# Enemy Class (Crow)
# ---------------------------
class EnemyCrow(pygame.sprite.Sprite):
    """Crow enemy that animates using a sprite sheet from crow_fly.png."""
    def __init__(self, x, y, speed):
        pygame.sprite.Sprite.__init__(self)
        # Load the crow sprite sheet from assets
        crow_sheet_path = os.path.join("assets", "crow_fly.png")
        if os.path.exists(crow_sheet_path):
            try:
                sheet = pygame.image.load(crow_sheet_path).convert_alpha()
                sheet_rect = sheet.get_rect()
                # Assume the sheet has 2 frames arranged horizontally
                frame_width = sheet_rect.width // 2
                frame_height = sheet_rect.height
                self.frames = []
                for i in range(2):
                    frame = sheet.subsurface(pygame.Rect(i * frame_width, 0, frame_width, frame_height)).copy()
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
        # Scale frames
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
# Helper Function for Enemy Sprite Sheet
# ---------------------------
def load_frames(sheet_path, frame_width, frame_height, trim=True):
    try:
        sheet = pygame.image.load(sheet_path).convert_alpha()
    except Exception as e:
        print("Error loading sheet:", e)
        return []
    sheet_rect = sheet.get_rect()
    frames = []
    for y in range(0, sheet_rect.height - frame_height + 1, frame_height):
        for x in range(0, sheet_rect.width - frame_width + 1, frame_width):
            frame = sheet.subsurface(pygame.Rect(x, y, frame_width, frame_height)).copy()
            if trim:
                frame = trim_surface(frame)
            frames.append(frame)
    for i, frame in enumerate(frames):
        print(f"Enemy frame {i} size: {frame.get_size()}")
    return frames

# ---------------------------
# Adaptive Engine Class
# ---------------------------
class AdaptiveEngine:
    """Adjusts enemy spawn rate and speed based on performance."""
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
# Level Class (Handles enemy spawning and visual ground)
# ---------------------------
class Level:
    """Handles enemy spawning and draws a visual ground."""
    def __init__(self, adaptive_engine):
        self.enemy_list = pygame.sprite.Group()
        self.adaptive_engine = adaptive_engine
        self.create_ground()

    def create_ground(self):
        self.ground_sprite = None
        ground_path = "ground.png"
        if os.path.exists(ground_path):
            ground_image = pygame.image.load(ground_path).convert_alpha()
            desired_ground_height = SCREEN_HEIGHT // 4
            scale_factor = desired_ground_height / ground_image.get_height()
            new_ground_width = int(ground_image.get_width() * scale_factor)
            scaled_ground = pygame.transform.scale(ground_image, (new_ground_width, desired_ground_height))
            tiled_ground = pygame.Surface((SCREEN_WIDTH, desired_ground_height), pygame.SRCALPHA)
            for x in range(0, SCREEN_WIDTH, new_ground_width):
                tiled_ground.blit(scaled_ground, (x, 0))
            ground_sprite = pygame.sprite.Sprite()
            ground_sprite.image = tiled_ground
            ground_sprite.rect = tiled_ground.get_rect()
            ground_sprite.rect.x = 0
            ground_sprite.rect.y = SCREEN_HEIGHT - desired_ground_height
            self.ground_sprite = ground_sprite

    def update(self, dt):
        self.enemy_list.update(dt)
        # For demonstration, we'll alternate between spawning the crow enemy and others.
        if random.random() < 0.01 * self.adaptive_engine.difficulty:
            # Here, we create a crow enemy.
            enemy_y = random.randint(SCREEN_HEIGHT - 300, SCREEN_HEIGHT - 80)
            # Using EnemyCrow class instead of the generic Enemy class.
            enemy = EnemyCrow(player.world_x + SCREEN_WIDTH, enemy_y, self.adaptive_engine.enemy_speed)
            self.enemy_list.add(enemy)

# ---------------------------
# Global Mentor and Chest Variables
# ---------------------------
mentor = None
mentor_spawned = False
mentor_spoken = False
chest = None
chest_spawned = False
letter_shown = False

# ---------------------------
# Main Game Loop
# ---------------------------
def main():
    global quote_index, current_quote, current_quote_kill_count, current_quote_display, quote_reset_time
    global mentor, mentor_spawned, mentor_spoken, chest, chest_spawned, letter_shown, player, score, PIXEL_FONT

    pygame.init()
    pygame.font.init()  # Ensure the font module is initialized
    try:
        pygame.mixer.init()
    except Exception as e:
        print("Error initializing mixer:", e)
    # Now load the global font after font init:
    PIXEL_FONT = pygame.font.Font("Pixel_NES.ttf", PIXEL_FONT_SIZE)
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hamlet's Descent")
    clock = pygame.time.Clock()

    # Show the loadscreen and opening scene
    show_loadscreen(screen)
    show_opening_scene(screen)
    
    # Load main game music
    bg_music_path = "bg_music.mp3"
    if os.path.exists(bg_music_path):
        try:
            pygame.mixer.music.load(bg_music_path)
            pygame.mixer.music.play(-1)
            print("Background music loaded and playing.")
        except Exception as e:
            print("Error loading background music:", e)
    else:
        print("Background music file not found.")

    sword_sound = pygame.mixer.Sound("sword.mp3") if os.path.exists("sword.mp3") else None
    jump_sound = pygame.mixer.Sound("jump.mp3") if os.path.exists("jump.mp3") else None

    adaptive_engine = AdaptiveEngine()
    level = Level(adaptive_engine)
    player = Player(100, SCREEN_HEIGHT - 100)
    player.jump_sound = jump_sound

    parallax_layers = load_parallax_layers()

    current_level_index = 0
    level_start_x = 0
    fixed_player_screen_x = 100

    performance = {'deaths': 0, 'time': 0}
    level_start_time = time.time()

    score = 0

    while True:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        player.update(dt)
        level.update(dt)
        camera_x = player.world_x - fixed_player_screen_x

        if not mentor_spawned and player.world_x >= SCREEN_WIDTH:
            mentor_x = SCREEN_WIDTH * 1.1
            mentor = Mentor(mentor_x, SCREEN_HEIGHT - 100)
            mentor_spawned = True

        if mentor is not None and not mentor_spoken:
            if player.rect.colliderect(mentor.rect):
                show_narrative(screen, mentor)
                mentor_spoken = True
                player.world_x = mentor.rect.right + 10

        if not chest_spawned and player.world_x >= 4 * SCREEN_WIDTH:
            chest_x = player.world_x + 200
            chest_y = SCREEN_HEIGHT - (SCREEN_HEIGHT // 4) - 50
            chest = Chest(chest_x, chest_y)
            chest_spawned = True

        if chest is not None and not chest.opened:
            if player.rect.colliderect(chest.rect) and player.state.startswith("attack"):
                chest.state = "opening"

        if chest is not None:
            chest.update(dt)
            if chest.opened and not letter_shown:
                show_letter(screen)
                letter_shown = True

        if player.world_x >= level_start_x + LEVEL_WIDTH:
            if current_level_index == 0:
                score = battle_with_knight(screen, player, score)
            else:
                prompt = "Solve the puzzle to advance! (Press SPACE to continue)"
                prompt_surface = render_gradient_text(prompt, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
                prompt_rect = prompt_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                waiting = True
                while waiting:
                    for event in pygame.event.get():
                        if event.type == pygame.QUIT:
                            pygame.quit()
                            sys.exit()
                        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                            waiting = False
                    screen.fill(BLACK)
                    screen.blit(prompt_surface, prompt_rect)
                    pygame.display.flip()
            current_level_index += 1
            level_start_x = player.world_x
            level_start_time = time.time()

        enemy_hits = pygame.sprite.spritecollide(player, level.enemy_list, False)
        if enemy_hits and player.bounce_cooldown <= 0:
            if player.state.startswith("attack"):
                for enemy in enemy_hits:
                    enemy.kill()
                    score += 2
                    current_quote_kill_count += 1
                    if current_quote_kill_count == 1:
                        current_quote_display = current_quote["modern"]
                    elif current_quote_kill_count == 2:
                        current_quote_display = current_quote["explanation"]
                        quote_reset_time = time.time() + 4.0
                if sword_sound:
                    sword_sound.play()
                player.vel_y = JUMP_STRENGTH
                player.bounce_cooldown = 0.5
            else:
                player.vel_y = JUMP_STRENGTH
                player.bounce_cooldown = 0.5

        if quote_reset_time is not None and time.time() >= quote_reset_time:
            current_quote_kill_count = 0
            quote_index = (quote_index + 1) % len(quotes)
            current_quote = quotes[quote_index]
            current_quote_display = current_quote["original"]
            quote_reset_time = None

        screen.fill(BLACK)
        for layer_surface, factor in parallax_layers:
            layer_offset = -camera_x * factor
            screen.blit(layer_surface, (layer_offset, 0))
        if level.ground_sprite:
            ground_rect = level.ground_sprite.rect.copy()
            ground_rect.x -= camera_x
            screen.blit(level.ground_sprite.image, ground_rect)
        if mentor is not None:
            mentor_rect = mentor.rect.copy()
            mentor_rect.x = mentor.world_x - camera_x
            screen.blit(mentor.image, mentor_rect)
        if chest is not None:
            chest_rect = chest.rect.copy()
            chest_rect.x = chest.world_x - camera_x
            screen.blit(chest.image, chest_rect)
        player_screen_rect = player.rect.copy()
        player_screen_rect.x = player.world_x - camera_x
        screen.blit(player.image, player_screen_rect)
        for enemy in level.enemy_list:
            enemy_screen_rect = enemy.rect.copy()
            enemy_screen_rect.x = enemy.world_x - camera_x
            screen.blit(enemy.image, enemy_screen_rect)
        hud_text = f"Score: {score}   Health: {player.health}   Time: {int(time.time()-level_start_time)} sec"
        hud_surface = render_gradient_text(hud_text, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        screen.blit(hud_surface, (20, 20))
        quote_surface = render_gradient_text(current_quote_display, PIXEL_FONT, TAN_TOP, TAN_BOTTOM)
        quote_rect = quote_surface.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        padding = 20
        bg_rect = quote_rect.inflate(padding, padding)
        s = pygame.Surface((bg_rect.width, bg_rect.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 150))
        screen.blit(s, bg_rect)
        screen.blit(quote_surface, quote_rect)
        pygame.display.flip()

if __name__ == '__main__':
    main()
