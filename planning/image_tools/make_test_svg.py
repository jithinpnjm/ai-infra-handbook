#!/usr/bin/env python3
import subprocess, pathlib

# Let's write a full candidate generator and test script to see the actual SVG rendered
svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>The life of a job</title>
  <desc>Sequence diagram showing the lifecycle of a Slurm job across login node, controller, database, and compute nodes.</desc>
  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />
    </marker>
  </defs>
  <rect width="1600" height="1200" fill="#f5f8f5"/>
</svg>'''

p = pathlib.Path("test_job_life.svg")
p.write_text(svg_code)
print("Saved dummy SVG")
