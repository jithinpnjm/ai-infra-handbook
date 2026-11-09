# Snippets: hardware or third-party APIs that were not run here

`tpm_attestation.py`, `attestation_verifier.py` use tpm2-pytss and need a TPM; `model_watermark.py` calls a
watermarking library whose API was not verified. Syntax-checked only. Use `establish_chain.py` and
`verify_chain.py` in the parent directory for a tested model of the measurement-chain logic.
