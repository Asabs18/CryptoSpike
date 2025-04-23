/**
 * crypto.js - Cryptographic helper functions for signing and hashing.
 *
 * Includes:
 * - SHA-256 hashing using Web Crypto API
 * - ECDSA signature generation using elliptic.js (secp256k1)
 */

/**
 * 🔒 Compute a SHA-256 hash of the given message.
 *
 * @param {string} msg - The input message to hash.
 * @returns {Promise<string>} - A hex string representing the SHA-256 hash.
 */
async function sha256 (msg) {
  const encoder = new TextEncoder()
  const data = encoder.encode(msg)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)

  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')
}

/**
 * ✍️ Sign a transaction message using ECDSA (secp256k1).
 *
 * Format of message: "receiver:amount" (e.g., "addr123:50.00")
 * The output is a raw 64-byte hex string: r || s
 *
 * @param {string} privateKeyHex - The sender's private key in hex.
 * @param {string} receiver - The recipient's wallet address.
 * @param {number} amount - The transaction amount.
 * @returns {Promise<string>} - A raw 64-byte hex-encoded signature.
 */
async function signTransaction (privateKeyHex, receiver, amount) {
  const EC = elliptic.ec
  const ec = new EC('secp256k1')
  const key = ec.keyFromPrivate(privateKeyHex)

  const message = `${receiver}:${amount.toFixed(2)}`
  const msgHashHex = await sha256(message)

  const signature = key.sign(msgHashHex, { canonical: true })

  const r = signature.r.toArrayLike(Uint8Array, 'be', 32)
  const s = signature.s.toArrayLike(Uint8Array, 'be', 32)
  const sigBytes = new Uint8Array([...r, ...s])

  const sigHex = Array.from(sigBytes)
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')

  console.log('✅ Signature (raw hex):', sigHex)
  return sigHex
}
