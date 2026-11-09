import tpm2_pytss

def attest_node(pcrs: list[int], nonce: bytes) -> dict:
    """Attest the node's boot state via the TPM."""
    esys = tpm2_pytss.ESYS()
    quote = esys.quote(
        pcrs=pcrs,
        qualifying_data=nonce,
    )
    return {
        "quoted": quote.quoted,
        "signature": quote.signature,
        "attestation_key": quote.attestation_key,
    }
