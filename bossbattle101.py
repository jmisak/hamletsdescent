#!/usr/bin/env python3
"""
Boss Battle Scene (End-of-Act I)
--------------------------------
- Boss sprite uses boss1_sheet.png with 3 rows (idle, walk, attack) and 8 frames per row.
- Each frame is 112×93 pixels.
- The boss deals 5 damage per blow; the player hits for 3.
- The boss attacks every 3–5 seconds (randomized).
- The player can block (state "block") via the S key to reduce incoming damage.
- The background is loaded from boss_battle1_back.png.
- Boss music is loaded from bossbattle1.mp3.
"""

import pygame
import random
import sys
import time
import os

# ---------------------------
# Global Settings and Constants
# ---------------------------
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1200
FPS = 60

# Movement, physics, and damage constants
PLAYER_SPEED = 5
JUMP_STRENGTH = -10
GRAVITY = 0.5
PLAYER_ATTACK_DAMAGE = 3
BOSS_ATTACK_DAMAGE = 5
BLOCKED_DAMAGE = 2

# Scaling factors (adjust as desired)
SPRITE_SCALE = 2.25
PLAYER_SCALE = SPRITE_SCALE * 1.1   # make the player slightly larger
BOSS_SCALE = 1.0                   # set to 1.0; change this variable only once

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Font settings
PIXEL_FONT_SIZE = 28
PIXEL_FONT = None

# ---------------------------
# Helper Functions
# ---------------------------
def render_gradient_text(text, font, color_start, color_end):
    """Render text with a vertical gradient (here both colors are white)."""
    text_surface = font.render(text, True, WHITE)
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
# Boss Class
# ---------------------------
class BossFortinbras(pygame.sprite.Sprite):
    """
    Boss sprite using boss1_sheet.png.
    The sheet has 3 rows (idle, walk, attack) and 8 frames per row.
    Each frame is 112x93 pixels.
    """
    def __init__(self, x, y):
        super().__init__()
        self.health = 50  # Boss HP
        self.load_sprites()
        self.state = "idle"  # states: "idle", "walk", "attack"
        self.current_frame = 0
        self.image = self.idle_frames[self.current_frame]
        self.rect = self.image.get_rect()
        # Use floating point for smooth movement
        self.world_x = float(x)
        self.world_y = float(y - self.rect.height)  # align bottom at y
        self.rect.x = int(self.world_x)
        self.rect.y = int(self.world_y)
        self.animation_timer = 0.1
        self.animation_delay = 0.18  # lower delay for smoother animation
        self.next_attack_time = time.time() + random.uniform(3, 5)
        self.vel_x = 0.0  # If you want the boss to move horizontally

    def load_sprites(self):
        sheet_path = os.path.join("boss1_sheet.png")
        if not os.path.exists(sheet_path):
            fallback = pygame.Surface((100, 100), pygame.SRCALPHA)
            fallback.fill((255, 0, 0))
            self.idle_frames = [fallback]
            self.walk_frames = [fallback]
            self.attack_frames = [fallback]
            return
        
        sheet = pygame.image.load(sheet_path).convert_alpha()
        frame_width = 112
        frame_height = 93
        
        self.idle_frames = []
        self.walk_frames = []
        self.attack_frames = []
        
        # Row 0: idle
        for col in range(8):
            rect = pygame.Rect(col * frame_width, 0, frame_width, frame_height)
            frame = sheet.subsurface(rect).copy()
            scaled = pygame.transform.scale(frame, (int(frame_width * BOSS_SCALE), int(frame_height * BOSS_SCALE)))
            self.idle_frames.append(scaled)
        
        # Row 1: walk
        for col in range(8):
            rect = pygame.Rect(col * frame_width, frame_height, frame_width, frame_height)
            frame = sheet.subsurface(rect).copy()
            scaled = pygame.transform.scale(frame, (int(frame_width * BOSS_SCALE), int(frame_height * BOSS_SCALE)))
            self.walk_frames.append(scaled)
        
        # Row 2: attack
        for col in range(8):
            rect = pygame.Rect(col * frame_width, frame_height * 2, frame_width, frame_height)
            frame = sheet.subsurface(rect).copy()
            scaled = pygame.transform.scale(frame, (int(frame_width * BOSS_SCALE), int(frame_height * BOSS_SCALE)))
            self.attack_frames.append(scaled)
    
    def update(self, dt, player):
        now = time.time()
        if now >= self.next_attack_time:
            self.state = "attack"
            self.current_frame = 0
            self.next_attack_time = now + random.uniform(3, 5)
        self.animation_timer += dt
        if self.animation_timer >= self.animation_delay:
            self.animation_timer = 0.0
            self.current_frame += 1
            if self.state == "idle":
                if self.current_frame >= len(self.idle_frames):
                    self.current_frame = 0
                self.image = self.idle_frames[self.current_frame]
            elif self.state == "walk":
                if self.current_frame >= len(self.walk_frames):
                    self.current_frame = 0
                self.image = self.walk_frames[self.current_frame]
            elif self.state == "attack":
                if self.current_frame >= len(self.attack_frames):
                    self.current_frame = 0
                    self.state = "idle"  # Return to idle after attack
                    # Deal damage if in collision
                    if self.rect.colliderect(player.rect):
                        if player.state == "block":
                            player.health -= BLOCKED_DAMAGE
                        else:
                            player.health -= BOSS_ATTACK_DAMAGE
                else:
                    self.image = self.attack_frames[self.current_frame]
        # Update movement smoothly using dt
        self.world_x += self.vel_x * dt
        self.rect.x = int(self.world_x)

# ---------------------------
# Player Class (with block state)
# ---------------------------
class Player(pygame.sprite.Sprite):
    """Player character with an added block state (triggered by S key)."""
    def __init__(self, x, y):
        super().__init__()
        self.health = 100
        self.load_sprites()
        self.state = 'idle'  # states: idle, run, jump, attack1, attack2, block
        self.current_frame = 0
        self.image = self.animations['idle'][self.current_frame]
        self.rect = self.image.get_rect()
        self.world_x = float(x)
        self.world_y = float(y - self.rect.height)
        self.rect.x = int(self.world_x)
        self.rect.y = int(self.world_y)
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = False
        self.bounce_cooldown = 0.0
        self.jump_sound = None
        self.animation_timer = 0.0
        self.animation_delay = 0.15
        self.jump_pressed = False
        self.jump_count = 0
        self.max_jumps = 3

    def load_sprites(self):
        base_path = os.path.join("assets", "adventurer")
        self.animations = {'idle': [], 'run': [], 'jump': [], 'attack1': [], 'attack2': [], 'block': []}
        def load_anim(anim_name, frame_count):
            frames = []
            for i in range(frame_count):
                filename = f"adventurer-{anim_name}-{i:02d}.png"
                full_path = os.path.join(base_path, filename)
                if os.path.exists(full_path):
                    img = pygame.image.load(full_path).convert_alpha()
                else:
                    img = pygame.Surface((50,50), pygame.SRCALPHA)
                    img.fill((0,255,0))
                scaled = pygame.transform.scale(img, (int(img.get_width()*PLAYER_SCALE), int(img.get_height()*PLAYER_SCALE)))
                frames.append(scaled)
            return frames
        self.animations['idle']    = load_anim("idle", 3)
        self.animations['run']     = load_anim("run", 3)
        self.animations['jump']    = load_anim("jump", 3)
        self.animations['attack1'] = load_anim("attack1", 3)
        self.animations['attack2'] = load_anim("attack2", 3)
        # For block, just reuse idle frames as a fallback
        self.animations['block'] = self.animations['idle'][:]

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if self.state not in ("attack1", "attack2", "block"):
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
        if self.state in ("attack1", "attack2"):
            new_state = self.state
        else:
            if keys[pygame.K_a]:
                new_state = 'attack1'
            elif keys[pygame.K_s]:
                new_state = 'block'
            elif not self.on_ground:
                new_state = 'jump'
            elif self.vel_x != 0:
                new_state = 'run'
            else:
                new_state = 'idle'
        if new_state != self.state:
            self.state = new_state
            self.current_frame = 0
            self.animation_timer = 0.0
        self.animation_timer += dt
        if self.animation_timer >= self.animation_delay:
            self.animation_timer = 0.0
            old_bottom = self.rect.bottom
            self.current_frame = (self.current_frame + 1) % len(self.animations[self.state])
            self.image = self.animations[self.state][self.current_frame]
            self.rect = self.image.get_rect()
            self.rect.bottom = old_bottom
        self.rect.x = int(self.world_x)
        self.rect.y = int(self.world_y)

# ---------------------------
# Boss Battle Scene
# ---------------------------
def boss_battle_act1(screen, player):
    # Load boss battle background
    bg_path = "boss_battle1_back.png"
    if os.path.exists(bg_path):
        bg_img = pygame.image.load(bg_path).convert_alpha()
        bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    else:
        bg_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_img.fill((50,50,50))
    # Load boss music
    boss_music_path = "bossbattle1.mp3"
    try:
        pygame.mixer.music.load(boss_music_path)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print("Error loading bossbattle1.mp3:", e)
    
    boss = BossFortinbras(x=SCREEN_WIDTH * 0.7, y=SCREEN_HEIGHT)
    boss_group = pygame.sprite.Group(boss)
    
    # Main boss battle loop
    clock = pygame.time.Clock()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        player.update(dt)
        boss_group.update(dt, player)
        # If player is attacking and collides with boss, deal damage
        if player.state.startswith("attack"):
            if boss.rect.colliderect(player.rect):
                boss.health -= PLAYER_ATTACK_DAMAGE
                player.vel_y = JUMP_STRENGTH
        if boss.health <= 0:
            running = False
            result_text = "Victory! You defeated Fortinbras."
        elif player.health <= 0:
            running = False
            result_text = "Defeat! Fortinbras has overcome you."
        
        screen.blit(bg_img, (0,0))
        screen.blit(player.image, player.rect)
        screen.blit(boss.image, boss.rect)
        hud_text = f"Player HP: {player.health}  |  Boss HP: {boss.health}"
        hud_surface = render_gradient_text(hud_text, PIXEL_FONT, WHITE, WHITE)
        screen.blit(hud_surface, (20,20))
        pygame.display.flip()
    
    # End result screen
    end_time = time.time()
    while time.time() - end_time < 3:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        screen.fill(BLACK)
        result_surface = render_gradient_text(result_text, PIXEL_FONT, WHITE, WHITE)
        result_rect = result_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        screen.blit(result_surface, result_rect)
        pygame.display.flip()

# ---------------------------
# Main Function
# ---------------------------
def main():
    pygame.init()
    pygame.font.init()
    global PIXEL_FONT
    PIXEL_FONT = pygame.font.Font("Pixel_NES.ttf", PIXEL_FONT_SIZE)
    
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hamlet's Descent - Boss Battle")
    clock = pygame.time.Clock()
    
    player = Player(200, SCREEN_HEIGHT)  # Starting position for the player
    # Optional: load jump sound, etc.
    if os.path.exists("jump.mp3"):
        player.jump_sound = pygame.mixer.Sound("jump.mp3")
    
    boss_battle_act1(screen, player)
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
