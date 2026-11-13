# Voice rewrite, Part 5 chapter 5.21 (batch h)

Scope: docs/part-05-kubernetes/21-certificates-identity-admission-control-and-policy.md only. Uncommitted.
Gates: `python3 tools/rewrite_guard.py HEAD WORKTREE <file>` and `python3 tools/restore/chain_gate.py <file>`.
Not run (out of scope for this batch): `npm run build`, Mermaid check, language_audit, pytest.

## Status

| Chapter | Words before (wc) | Words after (wc) | Growth | Guard (hard failures) | New numbers | Lost numbers | Chain gate |
|---|---|---|---|---|---|---|---|
| 5.21 certificates, identity, admission, policy | 15463 | 20901 | +35.2% | 0 | 0 | 0 | 0.0 per 1000 |

Guard body count: 13063 to 18501 words, residue 0 to 0.

## Structure kept (checked by diff against HEAD)

- Front matter, title, status table, every heading (same text, same order).
- Every code block and Mermaid block: same count of fences, same body text.
- Checkpoint block: 20 `<details>` blocks, copied byte for byte from HEAD (lines 1279 to end). Checkpoint answers NOT voice-rewritten, as in batches a to g.
- Sources and review notes: copied verbatim (author names kept there).
- Lab: 13 steps kept (same commands and facts). Exercises: 9 kept, rewritten to one task per sentence, numbers kept.
- Honest status: status row ("labs **untested**") plus one sentence above the lab ("have not been run against live hardware").

## Attribution handling

- Author names removed from body prose (kept in Sources): Josh Rosso et al. (Production Kubernetes, ch 8), Brendan Burns et al. (Kubernetes: Up and Running, ch 19), Jess Frazelle (amicontained).
- Gem-book titles kept in full, never abbreviated.

## Fact-level changes (review these)

- Sentence "The chapter says Gatekeeper cannot mutate requests" conflicted with the `Assign` mutation example in the same section. Rewritten as "mutation support is more limited than validation support." Owner should confirm the exact Gatekeeper mutation scope for the version the book targets.
- Gatekeeper paragraph "Notice that the default is fail open here" is an explanation of the existing `failurePolicy: Ignore` fact, not a new fact.
- Removed "has not been run here" from the Gatekeeper `Assign` example (one honest-status note per chapter). Kept it on the Ingress worked example, where the API-version warning is a real caveat.
- Removed a duplicate honest-status sentence I had added in the amicontained lab section; the lab section sentence stays.

## Needs source (not added as facts; explanation only)

- Replacing a node: "the new node gets certificates from the new CA when it joins." Inference from the original CA-rotation paragraph, not checked against the Cluster API docs.
- Kyverno `+(...)` add-if-absent anchor, `synchronize: true` meaning, and `mutateDigest` rewriting the image to a digest. Check the Kyverno docs for the version used.
- "A PodDisruptionBudget limits how many replicas a drain can take down at once" and anti-affinity explanation (Kubernetes docs, general).
- Gatekeeper `Config` example uses `extensions/v1beta1` and `networking.k8s.io/v1beta1` Ingress. Explanation says the API version must be checked against the cluster. Owner may want the example updated to current Ingress APIs (not changed, facts kept).
- "Sandboxed runtime puts a second layer between the app and the real kernel" (gVisor, Kata, Firecracker, general).

## Unresolved issues in the ORIGINAL text (left as written, facts not changed)

1. Code: the CSR Go program generates a 1024-bit RSA key (`rsa.GenerateKey(rand.Reader, 1024)`). The prose now says to choose a longer key in production. Owner decision whether to change the code.
2. YAML: the CertificateSigningRequest snippet uses `certificates.k8s.io/v1beta1` and has a duplicated `usages:` key. Both look stale or broken. Needs source before any change. (I believe `v1beta1` of the CSR API was removed in Kubernetes 1.22. Not checked here.)
3. The Go program writes `server.key`; the text in *Production Kubernetes* says `server-key.pem`. Kept as in the original, with the "check which name you get" note.
4. Checkpoint 3 and 19 and other checkpoint answers: not voice-rewritten (scope rule). Checkpoint 17 names the audit fields `status.totalViolations` and `status.violations`; not re-verified.
5. Checkpoint 18 gives a sample digest `sha256:4a8c...`; illustrative only.
6. Section 1, the `kubeadm certs renew` restart workaround with `mv` of the static pod manifest and `sleep 20`: kept as written.
7. Section 4 kube-bench output and amicontained outputs: kept verbatim; these are sample outputs and are not reproduced here.
8. Original chain-of-claims about SPIRE `k8s_psat` and kubelet `TokenReview` caching kept.

## Process note

Long chapter (about 1460 lines) done in chunks. Each rewritten chunk was saved to the scratchpad and assembled at the end. Checkpoints and Sources were copied from HEAD with sed to guarantee they stayed verbatim.
