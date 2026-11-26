import re
import xml.etree.ElementTree as ET

content_labels = [
    'Reflector, DeltaFIFO, indexer and work queue',
    'API server',
    'Reflector: LIST, then WATCH from resourceVersion',
    'Relists on 410 Gone',
    'DeltaFIFO: added, updated, deleted deltas',
    'Informer updates the indexer and calls OnAdd, OnUpdate, OnDelete',
    'Indexer: local cache, lister reads',
    'One shared informer per resource type per process',
    'Event handler enqueues namespace/name key',
    'Work queue: deduplicates keys, one worker per key',
    'Reconcile',
    'Writes directly, conditional on resourceVersion',
    'Event handlers enqueue keys, not objects',
    'Read from listers, write to the API server.'
]

print("Labels count:", len(content_labels))
