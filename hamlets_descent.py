#!/usr/bin/env python3
"""
Hamlet's Descent: A Learning Platform Adventure

A 2D platformer inspired by Shakespeare’s Hamlet where you control Hamlet through
castle-like levels. The game adapts its difficulty by “learning” from your performance:
if you die frequently, enemy behavior eases up; if you perform well, the game becomes more challenging.

This updated version includes:
  - Parallax background with three layers.
  - Background music loaded from a MIDI file ("bg_music.mid").
  - Animated sprites for the player and enemy ghosts using sprite sheets.
  - Fact messages displayed on enemy collisions.

Ensure that your asset files are in the same folder as the script or adjust the filepaths as needed.
"""

import pygame
import random
import sys
import time
import os

# ---------------------------
# Utility: Load Frames from a Sprite Sheet
# ---------------------------
def load_frames(sheet_path, frame_width, frame_height):
    """Load individual frames from a sprite sheet."""
    try:
        sheet = pygame.image.load(sheet_path).convert_alpha()
    except Exception as e:
        print("Error loading sheet:", e)
        return []
    sheet_rect = sheet.get_rect()
    frames = []
    for y in range(0, sheet_rect.height, frame_height):
        for x in range(0, sheet_rect.width, frame_width):
            frame = sheet.subsurface(pygame.Rect(x, y, frame_width, frame_height))
            frames.append(frame)
    return frames

# ---------------------------
# Initialize Pygame and Mixer
# ---------------------------
pygame.init()
try:
    pygame.mixer.init()
except Exception as e:
    print("Error initializing mixer:", e)

# ---------------------------
# Global Constants & Settings
# ---------------------------
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GRAVITY = 0.5
PLAYER_SPEED = 5
JUMP_STRENGTH = -10

# Colors (R, G, B)
BLACK   = (  0,   0,   0)
WHITE   = (255, 255, 255)
BLUE    = (  0, 128, 255)  # fallback color for the player
GREEN   = (  0, 255,   0)  # Platforms
RED     = (255,   0,   0)  # fallback color for enemies

# ---------------------------
# Parallax Background Class
# ---------------------------
class ParallaxBackground:
    """
    Handles a parallax background with 3 layers.
    Each layer scrolls horizontally at a different speed.
    """
    def __init__(self):
        # Load layer 1 (farthest; moves slowest)
        layer1_path = "bg_layer1.png"
        if os.path.exists(layer1_path):
            self.layer1 = pygame.image.load(layer1_path).convert()
            self.layer1 = pygame.transform.scale(self.layer1, (SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            self.layer1 = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.layer1.fill((30, 30, 30))
            
        # Load layer 2 (middle)
        layer2_path = "bg_layer2.png"
        if os.path.exists(layer2_path):
            self.layer2 = pygame.image.load(layer2_path).convert_alpha()
            self.layer2 = pygame.transform.scale(self.layer2, (SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            self.layer2 = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            self.layer2.fill((60, 60, 60, 128))

        # Load layer 3 (closest; moves fastest)
        layer3_path = "bg_layer3.png"
        if os.path.exists(layer3_path):
            self.layer3 = pygame.image.load(layer3_path).convert_alpha()
            self.layer3 = pygame.transform.scale(self.layer3, (SCREEN_WIDTH, SCREEN_HEIGHT))
        else:
            self.layer3 = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            self.layer3.fill((90, 90, 90, 128))
            
        # Scrolling speeds (in pixels per second)
        self.speed1 = 10   # farthest layer: slowest
        self.speed2 = 20   # middle layer: moderate
        self.speed3 = 40   # closest layer: fastest
        
        # Horizontal offsets for each layer
        self.offset1 = 0
        self.offset2 = 0
        self.offset3 = 0

    def update(self, dt):
        # Update offsets based on speed and elapsed time (dt)
        self.offset1 = (self.offset1 - self.speed1 * dt) % SCREEN_WIDTH
        self.offset2 = (self.offset2 - self.speed2 * dt) % SCREEN_WIDTH
        self.offset3 = (self.offset3 - self.speed3 * dt) % SCREEN_WIDTH

    def draw(self, screen):
        # Helper to draw a scrolling layer (draw twice for seamless looping)
        def draw_layer(layer, offset):
            screen.blit(layer, (offset - SCREEN_WIDTH, 0))
            screen.blit(layer, (offset, 0))
        
        draw_layer(self.layer1, self.offset1)
        draw_layer(self.layer2, self.offset2)
        draw_layer(self.layer3, self.offset3)

# ---------------------------
# Player Class with Animation
# ---------------------------
class Player(pygame.sprite.Sprite):
    """The player character (Hamlet) with animated medieval detail."""
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.frames = []
        # Try to load the sprite sheet for the player
        knight_sheet_path = "knight_sheet.png"
        if os.path.exists(knight_sheet_path):
            self.frames = load_frames(knight_sheet_path, 50, 50)
        if not self.frames:
            # Fallback: Create a single-frame blue box with crossed white lines
            fallback_image = pygame.Surface((50, 50), pygame.SRCALPHA)
            fallback_image.fill(BLUE)
            pygame.draw.line(fallback_image, WHITE, (0, 0), (50, 50), 3)
            pygame.draw.line(fallback_image, WHITE, (50, 0), (0, 50), 3)
            self.frames = [fallback_image]
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.vel_y = 0
        self.on_ground = False
        self.deaths = 0
        # Animation timer and delay (in seconds)
        self.animation_timer = 0.0
        self.animation_delay = 0.15

    def update(self, platforms, dt):
        keys = pygame.key.get_pressed()

        # Horizontal movement
        if keys[pygame.K_LEFT]:
            self.rect.x -= PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.rect.x += PLAYER_SPEED

        # Apply gravity
        self.vel_y += GRAVITY
        self.rect.y += self.vel_y

        # Platform collision detection
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True

        # Jumping (if on the ground)
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vel_y = JUMP_STRENGTH

        # Update animation frame based on elapsed time
        self.animation_timer += dt
        if self.animation_timer >= self.animation_delay:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
            self.animation_timer = 0.0

# ---------------------------
# Platform Class
# ---------------------------
class Platform(pygame.sprite.Sprite):
    """A static platform for the player to stand on."""
    def __init__(self, x, y, width, height):
        pygame.sprite.Sprite.__init__(self)
        self.image = pygame.Surface((width, height))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# ---------------------------
# Enemy (Ghost) Class with Animation
# ---------------------------
class Enemy(pygame.sprite.Sprite):
    """An enemy ghost with animation."""
    def __init__(self, x, y, speed):
        pygame.sprite.Sprite.__init__(self)
        self.frames = []
        ghost_sheet_path = "ghost_sheet.png"
        if os.path.exists(ghost_sheet_path):
            self.frames = load_frames(ghost_sheet_path, 40, 40)
        if not self.frames:
            # Fallback: Create a single-frame red square
            fallback_image = pygame.Surface((40, 40), pygame.SRCALPHA)
            fallback_image.fill(RED)
            self.frames = [fallback_image]
        self.current_frame = 0
        self.image = self.frames[self.current_frame]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed
        self.animation_timer = 0.0
        self.animation_delay = 0.15

    def update(self, dt):
        # Move enemy leftwards
        self.rect.x -= self.speed

        # Update animation frame
        self.animation_timer += dt
        if self.animation_timer >= self.animation_delay:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.image = self.frames[self.current_frame]
            self.animation_timer = 0.0

        # Remove enemy if it goes off-screen
        if self.rect.right < 0:
            self.kill()

# ---------------------------
# Adaptive Engine Class
# ---------------------------
class AdaptiveEngine:
    """
    A simple system that adjusts enemy spawn rate and speed based on performance.
    """
    def __init__(self):
        self.difficulty = 1.0  # Multiplier affecting spawn frequency
        self.enemy_speed = 2   # Base enemy speed
        self.death_count = 0

    def update_difficulty(self, performance):
        if performance['deaths'] > 3:
            self.difficulty = max(0.5, self.difficulty * 0.9)
            self.enemy_speed = max(1, self.enemy_speed * 0.9)
        elif performance['deaths'] == 0 and performance['time'] < 60:
            self.difficulty = min(2.0, self.difficulty * 1.1)
            self.enemy_speed = min(5, self.enemy_speed * 1.1)
        print("Adaptive Engine Update: Difficulty =", self.difficulty,
              "Enemy Speed =", self.enemy_speed)

# ---------------------------
# Level Class
# ---------------------------
class Level:
    """Handles platforms and enemy spawning."""
    def __init__(self, adaptive_engine):
        self.platform_list = pygame.sprite.Group()
        self.enemy_list = pygame.sprite.Group()
        self.adaptive_engine = adaptive_engine
        self.create_level()

    def create_level(self):
        # Ground platform
        ground = Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40)
        self.platform_list.add(ground)
        # Create several random platforms
        for i in range(5):
            width = random.randint(100, 200)
            x = random.randint(0, SCREEN_WIDTH - width)
            y = random.randint(100, SCREEN_HEIGHT - 100)
            plat = Platform(x, y, width, 20)
            self.platform_list.add(plat)

    def update(self, dt):
        # Update enemies with the elapsed time
        self.enemy_list.update(dt)
        # Spawn a new enemy based on adaptive difficulty
        if random.random() < 0.01 * self.adaptive_engine.difficulty:
            enemy_y = random.randint(50, SCREEN_HEIGHT - 80)
            enemy = Enemy(SCREEN_WIDTH, enemy_y, self.adaptive_engine.enemy_speed)
            self.enemy_list.add(enemy)

# ---------------------------
# Main Game Loop
# ---------------------------
def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hamlet's Descent")
    clock = pygame.time.Clock()

    # Load and play background music (MIDI)
    bg_music_path = "bg_music.mid"
    if os.path.exists(bg_music_path):
        try:
            pygame.mixer.music.load(bg_music_path)
            pygame.mixer.music.play(-1)  # Loop indefinitely
            print("Background music loaded and playing.")
        except Exception as e:
            print("Error loading background music:", e)
    else:
        print("Background music file not found.")

    # Create the parallax background
    parallax_bg = ParallaxBackground()

    # Initialize adaptive engine and level
    adaptive_engine = AdaptiveEngine()
    level = Level(adaptive_engine)

    # Create the player instance starting at a designated position
    player = Player(100, SCREEN_HEIGHT - 100)

    # Group for platforms and player
    all_sprites = pygame.sprite.Group()
    all_sprites.add(player)
    for platform in level.platform_list:
        all_sprites.add(platform)

    # Performance metrics for adaptive adjustments
    performance = {'deaths': 0, 'time': 0}
    level_start_time = time.time()

    # Shakespearean quotes and Hamlet facts
    quote_timer = 0
    quotes = [
        "To be, or not to be: that is the question.",
        "The play's the thing.",
        "Frailty, thy name is woman!",
        "This above all: to thine own self be true.",
        "There are more things in heaven and earth, Horatio, than are dreamt of in your philosophy."
    ]
    current_quote = ""
    facts = [
        "Hamlet is one of Shakespeare's longest plays.",
        "The play explores themes of betrayal, revenge, and madness.",
        "Hamlet was written around 1600 and is considered a tragedy.",
        "The famous soliloquy 'To be, or not to be' questions the meaning of existence.",
        "The ghost in Hamlet raises questions about the afterlife and retribution.",
        "Hamlet has been adapted into numerous films, stage productions, and even operas.",
        "Set in Denmark, the play delves into political intrigue and familial betrayal.",
        "Hamlet's complexity has sparked debates and analyses for centuries."
    ]
    fact_message = ""
    fact_end_time = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time in seconds

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update background and game objects
        parallax_bg.update(dt)
        player.update(level.platform_list, dt)
        level.update(dt)

        # Check for collisions between player and any enemy (ghost)
        enemy_hits = pygame.sprite.spritecollide(player, level.enemy_list, False)
        if enemy_hits:
            player.deaths += 1
            performance['deaths'] = player.deaths
            fact_message = random.choice(facts)
            fact_end_time = time.time() + 3  # Display fact for 3 seconds
            print("Alas! Hamlet has fallen. Total deaths:", player.deaths)
            player.rect.x = 100
            player.rect.y = SCREEN_HEIGHT - 100
            player.vel_y = 0

        # Check if player has reached the right side of the screen to complete the level
        if player.rect.x > SCREEN_WIDTH - 50:
            performance['time'] = time.time() - level_start_time
            print("Level complete in {:.2f} seconds.".format(performance['time']))
            adaptive_engine.update_difficulty(performance)
            level = Level(adaptive_engine)
            all_sprites.empty()
            all_sprites.add(player)
            for platform in level.platform_list:
                all_sprites.add(platform)
            player.rect.x = 100
            player.rect.y = SCREEN_HEIGHT - 100
            level_start_time = time.time()

        # Update and change the displayed quote every 5 seconds
        quote_timer += dt
        if quote_timer > 5:
            current_quote = random.choice(quotes)
            quote_timer = 0

        # ---------------------------
        # Drawing Section
        # ---------------------------
        parallax_bg.draw(screen)
        for entity in all_sprites:
            screen.blit(entity.image, entity.rect)
        for enemy in level.enemy_list:
            screen.blit(enemy.image, enemy.rect)
        font = pygame.font.SysFont("arial", 20)
        quote_surface = font.render(current_quote, True, WHITE)
        screen.blit(quote_surface, (20, 20))
        if time.time() < fact_end_time:
            fact_surface = font.render("Fact: " + fact_message, True, WHITE)
            screen.blit(fact_surface, (20, 50))
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
