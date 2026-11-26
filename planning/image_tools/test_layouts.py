import re

# Layout A: 2 columns
# Left column: Decision questions (and Command)
# Right column: Outcomes (Module, Raw, Shell + Injection, Script branch)
# Let's see:
# Row 1: Q1 (w=680) -> [yes] -> Module (w=680)
# Row 2: Q2 (w=680) -> [no] -> Raw (w=680)
# Row 3: Q3 (w=680) -> [yes] -> Shell (w=680)
#        Under Shell (in right column): Injection example (w=680)
# Row 4: Command (w=680 on left, reached by [no] from Q3)
#        Script branch on right?
#        Wait, if Script branch is in right column:
#        Does it have Question -> Script?
#        If Q_script (top) -> Script (bottom) in right column?
#        Or Q_script on left and Script on right?
