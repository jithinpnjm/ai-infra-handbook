import tpm2_pytss

def verify_attestation_chain(pcr_quote: bytes, dpu_quote: bytes, cvm_quote: bytes) -> bool:
    """Verify the attestation chain from TPM to DPU to CVM."""
    pcr_valid = tpm2_pytss.verify(pcr_quote)
    dpu_valid = tpm2_pytss.verify(dpu_quote)
    cvm_valid = tpm2_pytss.verify(cvm_quote)
    return pcr_valid and dpu_valid and cvm_valid
