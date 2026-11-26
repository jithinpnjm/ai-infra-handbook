# Precise layout calculator and validator
import xml.etree.ElementTree as ET
import re

def compute_layout():
    # Let's define the positions of all 9 nodes
    # Width = 1600, Height = 1150
    # Col 0: cx = 250
    # Col 1: cx = 800
    # Col 2: cx = 1350
    
    # Row 0: cy = 200
    # Row 1: cy = 550
    # Row 2: cy = 900
    
    nodes = {
        "Provisioned":    {"cx": 250,  "cy": 200, "w": 240, "h": 120},
        "Configured":     {"cx": 800,  "cy": 200, "w": 240, "h": 120},
        "Decommissioned": {"cx": 1350, "cy": 200, "w": 284, "h": 120},
        "Quarantined":    {"cx": 250,  "cy": 550, "w": 240, "h": 120},
        "Validating":     {"cx": 800,  "cy": 550, "w": 240, "h": 120},
        "Ready":          {"cx": 1350, "cy": 550, "w": 240, "h": 120},
        "Draining":       {"cx": 250,  "cy": 900, "w": 240, "h": 120},
        "Maintenance":    {"cx": 800,  "cy": 900, "w": 240, "h": 120},
        "Cordoned":       {"cx": 1350, "cy": 900, "w": 240, "h": 120},
    }
    return nodes

print("Layout nodes defined.")
