"""SAGE SPEK Cryptographic Attestation Tests."""

from sage_cos_core.sage.core.attestation import CryptographicAttestationProvider


def test_attestation_signing_and_verification():
    """Verify core signing and verification interface of the AttestationProvider."""
    provider = CryptographicAttestationProvider(key_seed="secure_test_seed")

    payload = {"data_field_1": "value_1", "numeric_field": 42}

    # Generate signature
    signature = provider.sign(payload)
    assert signature.startswith("deterministic_local_attestation_")

    # Verify signature - correct payload
    is_valid = provider.verify(payload, signature)
    assert is_valid is True

    # Verify signature - modified payload must fail
    modified_payload = {"data_field_1": "value_changed", "numeric_field": 42}
    is_valid_modified = provider.verify(modified_payload, signature)
    assert is_valid_modified is False

    # Verify signature - empty signature must fail
    assert provider.verify(payload, "") is False


def test_pluggable_replacement():
    """Verify that multiple providers can co-exist and are pluggable."""
    prov_local = CryptographicAttestationProvider(provider_type="deterministic_local")
    prov_hsm = CryptographicAttestationProvider(provider_type="hsm")

    payload = {"test": "data"}

    sig_local = prov_local.sign(payload)
    sig_hsm = prov_hsm.sign(payload)

    assert sig_local != sig_hsm
    assert sig_local.startswith("deterministic_local_attestation_")
    assert sig_hsm.startswith("hsm_attestation_")
