with open("update_candidate.py") as f:
    text = f.read()

text = text.replace(
    '<line x1="225" y1="347" x2="225" y2="371" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)"/>',
    '<path d="M 225 347 L 225 371" fill="none" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)"/>'
)
text = text.replace(
    '<line x1="335" y1="373" x2="335" y2="349" stroke="#db8129" stroke-width="3" marker-end="url(#arrow-orange)"/>',
    '<path d="M 335 373 L 335 349" fill="none" stroke="#db8129" stroke-width="3" marker-end="url(#arrow-orange)"/>'
)

with open("update_candidate.py", "w") as f:
    f.write(text)

print("Updated update_candidate.py with path arrows")
