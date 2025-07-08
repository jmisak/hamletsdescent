#!/usr/bin/env python3
"""
End-of-Act I Boss Battle:
 - Boss: Fortinbras, loaded from boss1_sheet.png (3 rows, 8 columns).
   Row 0 = idle, Row 1 = walk, Row 2 = attack.
 - Boss deals 5 damage per hit. Player deals 3 per attack.
 - Random attack intervals (3–5 seconds).
 - Player can block by holding S, reducing incoming damage.
 - Background: boss_battle1_back.png
 - Music: bossbattle1.mp3
 - This snippet assumes you have a Player class from earlier acts,
   but adds a 'block' state triggered by S key.
"""

import pygame
import random
import sys
import time
import os

# Constants
SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 1200
FPS = 60
GRAVITY = 0.5
PLAYER_SPEED = 5
JUMP_STRENGTH = -10
SPRITE_SCALE = 2.25
PLAYER_SCALE = SPRITE_SCALE * 1.1
BOSS_SCALE   = 7.0   # Adjust to make the boss bigger or smaller

# Damage values
PLAYER_ATTACK_DAMAGE = 1
BOSS_ATTACK_DAMAGE   = 5
BLOCKED_DAMAGE       = 2  # If player is blocking, they take 2 damage instead of 5

# Define font after pygame.font.init()
PIXEL_FONT = None
PIXEL_FONT_SIZE = 28
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# -------------
# Helper: Render Gradient Text
# -------------
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

# -------------
# Boss Class
# -------------
class BossFortinbras(pygame.sprite.Sprite):
    """
    Boss sprite using boss1_sheet.png.
    The sheet contains several animations, but only the first three rows are used:
      - Row 0: idle
      - Row 1: walk
      - Row 2: attack
    Each row has 8 frames and each frame is 112x93 pixels.
    """
    def __init__(self, x, y):
        super().__init__()
        self.health = 150  # Set boss HP as needed
        self.load_sprites()
        
        self.state = "idle"  # Possible states: "idle", "walk", "attack"
        self.current_frame = 0
        self.image = self.idle_frames[self.current_frame]
        self.rect = self.image.get_rect()
        # Position the boss so its bottom aligns at y
        self.world_x = x
        self.world_y = y - self.rect.height
        self.rect.x = self.world_x
        self.rect.y = self.world_y
        
        self.animation_timer = 0.0
        self.animation_delay = 0.15
        # Randomize attack interval between 3 and 5 seconds
        self.next_attack_time = time.time() + random.uniform(3, 5)
        self.vel_x = 0  # Adjust movement if needed

    def load_sprites(self):
        sheet_path = os.path.join("boss1_sheet.png")
        if not os.path.exists(sheet_path):
            # Fallback: simple red square if the sheet isn't found
            fallback = pygame.Surface((100, 100), pygame.SRCALPHA)
            fallback.fill((255, 0, 0))
            self.idle_frames = [fallback]
            self.walk_frames = [fallback]
            self.attack_frames = [fallback]
            return
       
        sheet = pygame.image.load(sheet_path).convert_alpha()
        # Each frame is 112x93 and there are 8 frames per row.
        frame_width = 112
        frame_height = 93
        
        # Use only the first three rows (rows 0, 1, 2) for idle, walk, attack
        self.idle_frames = []
        self.walk_frames = []
        self.attack_frames = []
        
        # Row 0: idle
        for col in range(10):
            rect = pygame.Rect(col * frame_width, 0, frame_width, frame_height)
            frame = sheet.subsurface(rect).copy()
            # If you need to scale the boss sprite, adjust BOSS_SCALE here.
            BOSS_SCALE = 3.0  # Change as needed
            scaled = pygame.transform.scale(frame, (int(frame_width * BOSS_SCALE), int(frame_height * BOSS_SCALE)))
            self.idle_frames.append(scaled)
        
        # Row 1: walk
        for col in range(10):
            rect = pygame.Rect(col * frame_width, frame_height, frame_width, frame_height)
            frame = sheet.subsurface(rect).copy()
            BOSS_SCALE = 3.0
            scaled = pygame.transform.scale(frame, (int(frame_width * BOSS_SCALE), int(frame_height * BOSS_SCALE)))
            self.walk_frames.append(scaled)
        
        # Row 2: attack
        for col in range(10):
            rect = pygame.Rect(col * frame_width, frame_height * 2, frame_width, frame_height)
            frame = sheet.subsurface(rect).copy()
            BOSS_SCALE = 3.0
            scaled = pygame.transform.scale(frame, (int(frame_width * BOSS_SCALE), int(frame_height * BOSS_SCALE)))
            self.attack_frames.append(scaled)
        # Any additional rows on the sheet are ignored.

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
                    # Deal damage if collision occurs during attack
                    if self.rect.colliderect(player.rect):
                        if player.state == "block":
                            player.health -= 2  # Damage reduced when blocking
                        else:
                            player.health -= 5
                else:
                    self.image = self.attack_frames[self.current_frame]
        self.world_x += self.vel_x
        self.rect.x = self.world_x


# -------------
# Player Class
# -------------
class Player(pygame.sprite.Sprite):
    """Same as before, but with an added 'block' state triggered by S key."""
    def __init__(self, x, y):
        super().__init__()
        self.health = 100
        self.load_sprites()
        
        self.state = 'idle'  # idle, run, jump, attack1, attack2, block
        self.current_frame = 0
        self.image = self.animations['idle'][0]
        self.rect = self.image.get_rect()
        self.world_x = x
        self.world_y = y - self.rect.height
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

    def load_sprites(self):
        # This code is very similar to prior acts. Just ensure you have a 'block' fallback.
        base_path = os.path.join("assets", "adventurer")
        # We'll define an empty block anim or reuse idle frames if you don't have block frames.
        self.animations = {'idle': [], 'run': [], 'jump': [], 'attack1': [], 'attack2': [], 'block': []}

        # Suppose you already have idle, run, jump, attack1, attack2 loaded from earlier code...
        # We'll do a fallback block animation that just uses idle frames.
        # Or define real block frames if you have them.
        self.animations['block'] = []

        def load_anim(anim_name, frame_count):
            frames = []
            for i in range(frame_count):
                filename = f"adventurer-{anim_name}-{i:02d}.png"
                full_path = os.path.join(base_path, filename)
                if os.path.exists(full_path):
                    img = pygame.image.load(full_path).convert_alpha()
                else:
                    # fallback
                    img = pygame.Surface((50,50), pygame.SRCALPHA)
                    img.fill((0,255,0))
                scaled = pygame.transform.scale(
                    img,
                    (int(img.get_width()*PLAYER_SCALE), int(img.get_height()*PLAYER_SCALE))
                )
                frames.append(scaled)
            return frames

        self.animations['idle']    = load_anim("idle", 3)
        self.animations['run']     = load_anim("run", 3)
        self.animations['jump']    = load_anim("jump", 3)
        self.animations['attack1'] = load_anim("attack1", 3)
        self.animations['attack2'] = load_anim("attack2", 3)

        # For block, let's just copy idle frames as a fallback
        self.animations['block'] = self.animations['idle'][:]

    def update(self, dt):
        keys = pygame.key.get_pressed()
        
        # Horizontal movement (no changes from earlier)
        if not self.state.startswith("attack") and self.state != "block":
            if keys[pygame.K_LEFT]:
                self.vel_x = -PLAYER_SPEED
            elif keys[pygame.K_RIGHT]:
                self.vel_x = PLAYER_SPEED
            else:
                self.vel_x = 0
        
        self.world_x += self.vel_x

        # Gravity
        self.vel_y += GRAVITY
        self.world_y += self.vel_y
        if self.world_y + self.rect.height >= SCREEN_HEIGHT:
            self.world_y = SCREEN_HEIGHT - self.rect.height
            self.vel_y = 0
            self.on_ground = True
            self.jump_count = 0
        else:
            self.on_ground = False

        # Jump logic
        if keys[pygame.K_SPACE]:
            if not self.jump_pressed and self.jump_count < self.max_jumps:
                if self.jump_sound:
                    self.jump_sound.play()
                self.vel_y = JUMP_STRENGTH
                self.jump_count += 1
                self.jump_pressed = True
        else:
            self.jump_pressed = False

        # Attack or block logic
        if self.state.startswith("attack"):
            new_state = self.state
        else:
            if keys[pygame.K_a]:
                new_state = 'attack1'
            elif keys[pygame.K_s]:
                # user is blocking
                new_state = 'block'
            elif not self.on_ground:
                new_state = 'jump'
            elif self.vel_x != 0:
                new_state = 'run'
            else:
                new_state = 'idle'

        # If state changed, reset frames
        if new_state != self.state:
            self.state = new_state
            self.current_frame = 0
            self.animation_timer = 0.0
        
        # Animate
        self.animation_timer += dt
        if self.animation_timer >= self.animation_delay:
            old_bottom = self.rect.bottom
            if self.state.startswith("attack"):
                # Attack anim logic
                if self.current_frame < len(self.animations[self.state]) - 1:
                    self.current_frame += 1
                else:
                    # Return to idle after attack
                    self.state = 'idle'
                    self.current_frame = 0
                self.animation_timer = 0.0
            else:
                # normal anim cycle
                self.current_frame = (self.current_frame + 1) % len(self.animations[self.state])
                self.animation_timer = 0.0
            
            self.image = self.animations[self.state][self.current_frame]
            self.rect = self.image.get_rect()
            self.rect.bottom = old_bottom
        self.rect.x = self.world_x
        self.rect.y = self.world_y

# -------------
# Boss Battle Scene
# -------------
def boss_battle_act1(screen, player):
    """
    Plays boss music, loads background, spawns boss,
    and runs a loop until boss or player is defeated.
    """
    # Load boss music
    boss_music_path = "bossbattle1.mp3"
    try:
        pygame.mixer.music.load(boss_music_path)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print("Error loading bossbattle1.mp3:", e)

    # Load background
    bg_path = "boss_battle1_back.png"
    if os.path.exists(bg_path):
        bg_img = pygame.image.load(bg_path).convert_alpha()
        # scale to fill screen or preserve ratio, up to you:
        bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
    else:
        bg_img = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_img.fill((50,50,50))

    # Create boss
    boss = BossFortinbras(x=SCREEN_WIDTH*0.7, y=SCREEN_HEIGHT)  # place near the right side
    boss_group = pygame.sprite.Group(boss)

    # Basic stats
    player.health = 100
    boss.health   = 50

    clock = pygame.time.Clock()
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

        # Update player
        player.update(dt)

        # If player is attacking and collides with boss, deal damage
        if player.state.startswith("attack"):
            if boss.rect.colliderect(player.rect):
                boss.health -= PLAYER_ATTACK_DAMAGE
                # small bounce or something
                player.vel_y = JUMP_STRENGTH

        # Update boss
        boss.update(dt, player)

        # Check health
        if boss.health <= 0:
            # Boss defeated
            running = False
            result_text = "Victory! You defeated Fortinbras."
        elif player.health <= 0:
            # Player defeated
            running = False
            result_text = "Defeat! Fortinbras has overcome you."

        # Draw scene
        screen.blit(bg_img, (0,0))
        # Draw player
        screen.blit(player.image, player.rect)
        # Draw boss
        screen.blit(boss.image, boss.rect)
        # Draw HUD
        font_surface = render_gradient_text(f"Player HP: {player.health}  |  Boss HP: {boss.health}", PIXEL_FONT, WHITE, WHITE)
        screen.blit(font_surface, (20, 20))
        pygame.display.flip()

    # End result screen
    end_time = time.time()
    while time.time() - end_time < 3:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        screen.fill(BLACK)
        r_surface = render_gradient_text(result_text, PIXEL_FONT, WHITE, WHITE)
        r_rect = r_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        screen.blit(r_surface, r_rect)
        pygame.display.flip()

# -------------
# Example Main Loop
# -------------
def main():
    pygame.init()
    pygame.font.init()
    global PIXEL_FONT
    PIXEL_FONT = pygame.font.Font("Pixel_NES.ttf", PIXEL_FONT_SIZE)

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Hamlet's Descent - Boss Battle Test")
    clock = pygame.time.Clock()

    # Suppose we have a Player instance from earlier acts:
    player = Player(200, SCREEN_HEIGHT)  # place near left
    # Jump sound, etc., if you want:
    # if os.path.exists("jump.mp3"):
    #    player.jump_sound = pygame.mixer.Sound("jump.mp3")

    # Start the boss battle
    boss_battle_act1(screen, player)

    # After boss battle, quit or transition
    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()
