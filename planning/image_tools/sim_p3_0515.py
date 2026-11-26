import re

spec = """Three-state diagram for pod vllm. State A 'no policy selects the pod for a direction: non-isolated, all traffic in that direction allowed'. State B 'at least one policy selects it and lists that direction in policyTypes: isolated, only traffic allowed by the union of all matching rules gets in'. Beside it two guest lists: 'Policy 1 names gateway' and 'Policy 2 names the monitoring pod'; result 'anyone on at least one list is admitted; nothing on a list ever removes a name from another list; no deny rules and no ordering'. Syntax strip: 'ingress: [] or no rules with policyTypes [Ingress] denies all ingress', 'ingress: [{}] allows all', 'omitted ports means any port', 'policyTypes defaults to Ingress always and to Egress only when the policy has egress rules, so set it explicitly', 'stateful: reply traffic of an allowed connection passes via conntrack', 'a CNI without policy support (plain Flannel) accepts the object and silently ignores it'. Text at least 24px."""

title = "Isolated or not: how policies add up for one pod"

quotes = re.findall(r"'([^']+)'", spec)
print(f"Total quotes: {len(quotes)}")
for i, q in enumerate(quotes, 1):
    print(f"{i:2d}. {q}")

all_expected = [title] + quotes
print(f"\nTotal expected labels: {len(all_expected)}")
