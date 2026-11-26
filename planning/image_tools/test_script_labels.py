import xml.etree.ElementTree as ET
import re
import sys

# Define all 16 exact expected labels
expected_labels = [
    "ExceptionGroup and except*: each handler takes its matches and the rest move on",
    "action3 raises ExceptionGroup(Nest*, [IndexError(1), TypeError(2), SyntaxError(3)])",
    "action2: except* IndexError: print(Got IE)",
    "action1: except* TypeError: print(Got TE)",
    "SyntaxError(3)",
    "+ Exception Group Traceback ... ExceptionGroup: Nest* (1 sub-exception) ... SyntaxError: 3",
    "Got IE, Got TE, then the traceback",
    "Why",
    "a script that waits on a whole rack of hosts can fail in several ways at once, and one exception object cannot carry them all; Python 3.11 added ExceptionGroup",
    "in except* IndexError as E: each E is bound to a sub-ExceptionGroup of the matches, available as E.exceptions",
    "unmatched exceptions continue upward in a new ExceptionGroup",
    "one try statement can run multiple except* clauses",
    "asyncio.TaskGroup uses this mechanism (chapter 3.6)",
    "you cannot mix except* with a plain except in the same try; you cannot put return, break or continue inside an except* clause",
    "plain except: the first matching handler consumes the whole exception",
    "A group keeps moving until every item in it has been matched"
]

print("Expected labels count:", len(expected_labels))
