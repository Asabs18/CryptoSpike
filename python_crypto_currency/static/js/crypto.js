// crypto.js - Cryptographic functions

async function sha256 (msg) {
  const encoder = new TextEncoder()
  const data = encoder.encode(msg)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')
}

async function signTransaction (privateKeyHex, receiver, amount) {
  const EC = elliptic.ec
  const ec = new EC('secp256k1')
  const key = ec.keyFromPrivate(privateKeyHex)
  const message = `${receiver}:${amount.toFixed(2)}`
  const msgHashHex = await sha256(message)

  const signature = key.sign(msgHashHex, { canonical: true })

  // Convert r and s to 32-byte hex and concatenate
  const r = signature.r.toArrayLike(Uint8Array, 'be', 32)
  const s = signature.s.toArrayLike(Uint8Array, 'be', 32)
  const sigBytes = new Uint8Array([...r, ...s])

  const sigHex = Array.from(sigBytes)
    .map(b => b.toString(16).padStart(2, '0'))
    .join('')

  console.log('✅ Signature (raw hex):', sigHex)
  return sigHex
}
