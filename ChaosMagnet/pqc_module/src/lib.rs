use pyo3::exceptions::PyValueError;
use pyo3::prelude::*;
use pyo3::types::PyBytes;

// ─── Kyber-512 ────────────────────────────────────────────────────────────────
use pqcrypto_kyber::kyber512::{
    decapsulate as kyber_decapsulate_impl,
    encapsulate as kyber_encapsulate_impl,
    keypair as kyber_keypair_impl,
    Ciphertext as KyberCiphertext,
    PublicKey as KyberPublicKey,
    SecretKey as KyberSecretKey,
    SharedSecret as KyberSharedSecret,
};

// ─── Falcon-512 Signatures ────────────────────────────────────────────────────
use pqcrypto_falcon::falcon512::{
    DetachedSignature as FalconDetachedSignature,
    PublicKey as FalconPublicKey,
    SecretKey as FalconSecretKey,
    detached_sign as falcon_detached_sign_impl,
    keypair as falcon_keypair_impl,
    verify_detached_signature as falcon_verify_impl,
};

// ─── Trait Imports ────────────────────────────────────────────────────────────
use pqcrypto_traits::kem as kem_traits;
use pqcrypto_traits::sign as sign_traits;

// ───────────────────────────────────────────────────────────────────────────────
// Kyber-512 helpers
// ───────────────────────────────────────────────────────────────────────────────

fn kyber_pk_from_bytes(bytes: &[u8]) -> PyResult<KyberPublicKey> {
    <KyberPublicKey as kem_traits::PublicKey>::from_bytes(bytes)
    .map_err(|e| PyValueError::new_err(e.to_string()))
}

fn kyber_sk_from_bytes(bytes: &[u8]) -> PyResult<KyberSecretKey> {
    <KyberSecretKey as kem_traits::SecretKey>::from_bytes(bytes)
    .map_err(|e| PyValueError::new_err(e.to_string()))
}

fn kyber_ct_from_bytes(bytes: &[u8]) -> PyResult<KyberCiphertext> {
    <KyberCiphertext as kem_traits::Ciphertext>::from_bytes(bytes)
    .map_err(|e| PyValueError::new_err(e.to_string()))
}

// ─── Kyber: keygen ────────────────────────────────────────────────────────────

#[pyfunction]
fn kyber_keygen(py: Python) -> PyResult<(Py<PyBytes>, Py<PyBytes>)> {
    let (pk, sk) = kyber_keypair_impl();

    let pk_bytes = <KyberPublicKey as kem_traits::PublicKey>::as_bytes(&pk);
    let sk_bytes = <KyberSecretKey as kem_traits::SecretKey>::as_bytes(&sk);

    Ok((
        PyBytes::new(py, pk_bytes).unbind(),
        PyBytes::new(py, sk_bytes).unbind(),
    ))
}

// ─── Kyber: encapsulate(pk) -> (ciphertext, shared_secret) ────────────────────

#[pyfunction]
fn kyber_encapsulate(py: Python, pk_bytes: &[u8]) -> PyResult<(Py<PyBytes>, Py<PyBytes>)> {
    let pk = kyber_pk_from_bytes(pk_bytes)?;

    let (ss, ct) = kyber_encapsulate_impl(&pk);

    let ss_bytes = <KyberSharedSecret as kem_traits::SharedSecret>::as_bytes(&ss);
    let ct_bytes = <KyberCiphertext as kem_traits::Ciphertext>::as_bytes(&ct);

    Ok((
        PyBytes::new(py, ct_bytes).unbind(),
        PyBytes::new(py, ss_bytes).unbind(),
    ))
}

// ─── Kyber: decapsulate(sk, ct) -> ss ─────────────────────────────────────────

#[pyfunction]
fn kyber_decapsulate(py: Python, sk_bytes: &[u8], ct_bytes: &[u8]) -> PyResult<Py<PyBytes>> {
    let sk = kyber_sk_from_bytes(sk_bytes)?;
    let ct = kyber_ct_from_bytes(ct_bytes)?;

    let ss = kyber_decapsulate_impl(&ct, &sk);
    let ss_bytes = <KyberSharedSecret as kem_traits::SharedSecret>::as_bytes(&ss);

    Ok(PyBytes::new(py, ss_bytes).unbind())
}

// ───────────────────────────────────────────────────────────────────────────────
// Falcon-512 helpers
// ───────────────────────────────────────────────────────────────────────────────

fn falcon_pk_from_bytes(bytes: &[u8]) -> PyResult<FalconPublicKey> {
    <FalconPublicKey as sign_traits::PublicKey>::from_bytes(bytes)
    .map_err(|e| PyValueError::new_err(e.to_string()))
}

fn falcon_sk_from_bytes(bytes: &[u8]) -> PyResult<FalconSecretKey> {
    <FalconSecretKey as sign_traits::SecretKey>::from_bytes(bytes)
    .map_err(|e| PyValueError::new_err(e.to_string()))
}

fn falcon_sig_from_bytes(bytes: &[u8]) -> PyResult<FalconDetachedSignature> {
    <FalconDetachedSignature as sign_traits::DetachedSignature>::from_bytes(bytes)
    .map_err(|e| PyValueError::new_err(e.to_string()))
}

// ─── Falcon: keygen ───────────────────────────────────────────────────────────

#[pyfunction]
fn falcon_keygen(py: Python) -> PyResult<(Py<PyBytes>, Py<PyBytes>)> {
    let (pk, sk) = falcon_keypair_impl();

    let pk_bytes = <FalconPublicKey as sign_traits::PublicKey>::as_bytes(&pk);
    let sk_bytes = <FalconSecretKey as sign_traits::SecretKey>::as_bytes(&sk);

    Ok((
        PyBytes::new(py, pk_bytes).unbind(),
        PyBytes::new(py, sk_bytes).unbind(),
    ))
}

// ─── Falcon: sign(sk, msg) -> detached signature bytes ────────────────────────

#[pyfunction]
fn falcon_sign(py: Python, sk_bytes: &[u8], msg: &[u8]) -> PyResult<Py<PyBytes>> {
    let sk = falcon_sk_from_bytes(sk_bytes)?;
    let sig = falcon_detached_sign_impl(msg, &sk);

    let sig_bytes = <FalconDetachedSignature as sign_traits::DetachedSignature>::as_bytes(&sig);

    Ok(PyBytes::new(py, sig_bytes).unbind())
}

// ─── Falcon: verify(pk, msg, sig) -> bool ─────────────────────────────────────

#[pyfunction]
fn falcon_verify(pk_bytes: &[u8], msg: &[u8], sig_bytes: &[u8]) -> PyResult<bool> {
    let pk = falcon_pk_from_bytes(pk_bytes)?;
    let sig = falcon_sig_from_bytes(sig_bytes)?;

    let result = falcon_verify_impl(&sig, msg, &pk);
    Ok(result.is_ok())
}

// ─── PyO3 Module Registration ─────────────────────────────────────────────────

#[pymodule]
fn pqcrypto_bindings(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(kyber_keygen, m)?)?;
    m.add_function(wrap_pyfunction!(kyber_encapsulate, m)?)?;
    m.add_function(wrap_pyfunction!(kyber_decapsulate, m)?)?;
    m.add_function(wrap_pyfunction!(falcon_keygen, m)?)?;
    m.add_function(wrap_pyfunction!(falcon_sign, m)?)?;
    m.add_function(wrap_pyfunction!(falcon_verify, m)?)?;
    Ok(())
}
