import re

labels = {
    "title": "Model hosting: shared on demand versus dedicated always on",
    "cost": "Cost-optimised: shares instances across many models, loads on demand, bin-packs (fitting as many models onto each machine as possible, like boxes in a van); cheap but reactive, surges hurt; maps to Nebius serverless endpoints for shared pools of popular models (my reading)",
    "latency": "Latency-optimised: dedicated always-on replicas; customer chooses GPU type, GPUs per replica and the replica range; maps to Nebius dedicated endpoints",
    "cold": "a tenant calls a model no replica holds; tens of GB of weights must load onto a GPU, which takes seconds to minutes; cold start latency can cause timeouts and cascading failures",
    "warm": "keep popular models always resident with at least two replicas; keep weights on local NVMe or a node-local cache so a new replica does not download from the object store"
}

# Now let us test the exact SVG generation and parse it with xml.etree.ElementTree!
