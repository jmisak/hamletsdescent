# SYNTAX FIX FOR HAMLET GAME
# Replace the problematic section in the main function with this corrected code:

# ORIGINAL BROKEN CODE (around line 820-830):
"""
# Add knowledge scrolls in Act 1
for i in range(2):
    x = 800 + i * 1200
    y = SCREEN_HEIGHT - 350
    scrolls.add(KnowledgeScroll(x, y, hamlet_quotes[i + 7])) in range(3):
    x = 500 + i * 800
    y = SCREEN_HEIGHT - 200 - random.randint(0, 150)
    platforms.add(Platform(x, y, 250, 20))
"""

# CORRECTED CODE - Replace the above with this:

# Add some platforms in Act 1
for i in range(3):
    x = 500 + i * 800
    y = SCREEN_HEIGHT - 200 - random.randint(0, 150)
    platforms.add(Platform(x, y, 250, 20))
    
# Add knowledge scrolls in Act 1
for i in range(2):
    x = 800 + i * 1200
    y = SCREEN_HEIGHT - 350
    scrolls.add(KnowledgeScroll(x, y, hamlet_quotes[i + 7]))

# This separates the code into two distinct for loops as intended