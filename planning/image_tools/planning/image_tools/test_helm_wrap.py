#!/usr/bin/env python3

def measure_sans(text, font_size=24):
    return len(text) * font_size * 0.6

def measure_mono(text, font_size=24):
    return len(text) * font_size * 0.62

helm_notes = '{{ .Values.image.tag | quote }}, {{- if .Values.gpu }}, {{ include "chart.fullname" . }}, toYaml | nindent 4; trim with {{- and -}}'

# Let's split helm notes into lines:
# Option A (3 lines):
lines_a = [
    '{{ .Values.image.tag | quote }}, {{- if .Values.gpu }},',
    '{{ include "chart.fullname" . }}, toYaml | nindent 4;',
    'trim with {{- and -}}'
]
for l in lines_a:
    print(f"Option A line: '{l}' len={len(l)} mono_w={measure_mono(l):.1f} sans_w={measure_sans(l):.1f}")

# Option B (4 lines):
lines_b = [
    '{{ .Values.image.tag | quote }},',
    '{{- if .Values.gpu }}, {{ include "chart.fullname" . }},',
    'toYaml | nindent 4; trim with {{- and -}}'
]
# Wait, let's check line 2 of lines_b:
print("line 2 len:", len(lines_b[1]), measure_mono(lines_b[1]))

# Option C (4 lines):
lines_c = [
    '{{ .Values.image.tag | quote }}, {{- if .Values.gpu }},',
    '{{ include "chart.fullname" . }},',
    'toYaml | nindent 4; trim with {{- and -}}'
]
for l in lines_c:
    print(f"Option C line: '{l}' len={len(l)} mono_w={measure_mono(l):.1f}")
