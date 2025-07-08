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
PLAYER_SCALE = SPRITE_SCALE * 1.5  # Increased from 1.1 to 1.5
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
    "collector": False,
    "scholar": False,
    "soliloquy_master": False
}

# Hamlet Educational Content
hamlet_quotes = [
    {"quote": "To be, or not to be, that is the question", "context": "Hamlet contemplates life and death"},
    {"quote": "Something is rotten in the state of Denmark", "context": "Marcellus senses corruption in the kingdom"},
    {"quote": "Neither a borrower nor a lender be", "context": "Polonius gives advice to his son Laertes"},
    {"quote": "This above all: to thine own self be true", "context": "Polonius on the importance of authenticity"},
    {"quote": "The lady doth protest too much, methinks", "context": "Gertrude watching the play within the play"},
    {"quote": "Brevity is the soul of wit", "context": "Polonius, ironically being long-winded"},
    {"quote": "There are more things in heaven and earth, Horatio", "context": "Hamlet on the limits of knowledge"},
    {"quote": "Frailty, thy name is woman!", "context": "Hamlet's disappointment with his mother"},
    {"quote": "O, what a rogue and peasant slave am I!", "context": "Hamlet berates himself for inaction"},
    {"quote": "The play's the thing wherein I'll catch the conscience of the king", "context": "Hamlet's plan to expose Claudius"}
]

hamlet_trivia = [
    {
        "question": "Who killed Hamlet's father?",
        "options": ["Claudius", "Polonius", "Laertes", "Fortinbras"],
        "correct": 0,
        "explanation": "Claudius, Hamlet's uncle, poisoned the king while he slept in the garden."
    },
    {
        "question": "What is the name of Hamlet's love interest?",
        "options": ["Gertrude", "Ophelia", "Rosalind", "Juliet"],
        "correct": 1,
        "explanation": "Ophelia is Polonius's daughter and Hamlet's tragic love interest."
    },
    {
        "question": "Where does Hamlet study before returning to Denmark?",
        "options": ["Oxford", "Cambridge", "Wittenberg", "Paris"],
        "correct": 2,
        "explanation": "Hamlet was a student at the University of Wittenberg in Germany."
    },
    {
        "question": "What does the ghost of Hamlet's father demand?",
        "options": ["Forgiveness", "Revenge", "Prayer", "Exile"],
        "correct": 1,
        "explanation": "The ghost demands Hamlet avenge his murder by killing Claudius."
    },
    {
        "question": "How does Ophelia die?",
        "options": ["Poison", "Stabbing", "Drowning", "Illness"],
        "correct": 2,
        "explanation": "Ophelia drowns, possibly by suicide, after going mad from grief."
    }
]