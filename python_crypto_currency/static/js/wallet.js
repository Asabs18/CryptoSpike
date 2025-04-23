// wallet.js - Wallet management functions

// Global wallet variable
let wallet = null
let walletUnlockCallback = null

// 🔓 Prompt unlock modal with callback
function requestWalletUnlock (callback) {
  walletUnlockCallback = callback
  const modal = new bootstrap.Modal(
    document.getElementById('walletUnlockModal')
  )
  modal.show()
}

// 🔐 Handle unlock modal submission
function unlockWallet () {
  const passphrase = document
    .getElementById('walletPassphraseInput')
    .value.trim()
  const modalEl = document.getElementById('walletUnlockModal')
  const modal = bootstrap.Modal.getInstance(modalEl)
  modal.hide()
  document.getElementById('walletPassphraseInput').value = ''
  if (walletUnlockCallback && passphrase) {
    walletUnlockCallback(passphrase)
    console.log('Unlock modal submitted with passphrase:', passphrase)
  }
}

// 🔐 Re-prompt unlock if passphrase was incorrect
async function tryDecryptWalletWith (passphrase) {
  try {
    const encrypted = localStorage.getItem('wallet_encrypted')
    if (!encrypted) return

    wallet = await decryptWallet(JSON.parse(encrypted), passphrase)
    showWalletInfo()
  } catch (err) {
    showAlert('❌ Incorrect passphrase or corrupted wallet.', 'danger')
    // Re-prompt modal after brief delay
    setTimeout(() => requestWalletUnlock(tryDecryptWalletWith), 1000)
  }
}

// 🔑 Derive AES key from passphrase
async function deriveKey (passphrase, salt) {
  const enc = new TextEncoder()
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    enc.encode(passphrase),
    { name: 'PBKDF2' },
    false,
    ['deriveKey']
  )
  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: salt,
      iterations: 100000,
      hash: 'SHA-256'
    },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    true,
    ['encrypt', 'decrypt']
  )
}

// 🧊 Encrypt wallet with passphrase
async function encryptWallet (walletObj, passphrase) {
  const enc = new TextEncoder()
  const salt = crypto.getRandomValues(new Uint8Array(16))
  const iv = crypto.getRandomValues(new Uint8Array(12))
  const key = await deriveKey(passphrase, salt)
  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    enc.encode(JSON.stringify(walletObj))
  )
  return {
    encrypted: btoa(String.fromCharCode(...new Uint8Array(encrypted))),
    iv: Array.from(iv),
    salt: Array.from(salt)
  }
}

// 🔓 Decrypt wallet with passphrase
async function decryptWallet (encryptedData, passphrase) {
  const enc = new TextEncoder()
  const dec = new TextDecoder()
  const { encrypted, iv, salt } = encryptedData
  const key = await deriveKey(passphrase, new Uint8Array(salt))
  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: new Uint8Array(iv) },
    key,
    Uint8Array.from(atob(encrypted), c => c.charCodeAt(0))
  )
  return JSON.parse(dec.decode(decrypted))
}

async function generateWallet () {
  requestWalletUnlock(async passphrase => {
    try {
      const res = await fetch('/wallet/create')
      const data = await res.json()
      const plainWallet = {
        address: data.address,
        public_key: data.public_key,
        private_key: data.private_key
      }
      const encrypted = await encryptWallet(plainWallet, passphrase)
      localStorage.setItem('wallet_encrypted', JSON.stringify(encrypted))
      wallet = plainWallet
      showWalletInfo()
      fetchChain()
      showAlert('✅ Wallet generated successfully!', 'success')
    } catch (err) {
      showAlert('❌ Failed to generate wallet', 'danger')
    }
  })
}

function resetWallet () {
  localStorage.removeItem('wallet_encrypted')
  wallet = null
  document.getElementById('walletInfo').style.display = 'none'
  document.getElementById('walletAddress').textContent = ''
  document.getElementById('walletBalance').textContent = 'Loading...'
  document.getElementById('txStatus').textContent = ''
  document.getElementById('mineStatus').textContent = ''
  showAlert('Wallet reset successfully.', 'info')
}

function showWalletInfo () {
  document.getElementById('walletInfo').style.display = 'block'
  document.getElementById('walletAddress').textContent = wallet.address
  updateBalance()
}

// 🚀 Attempt wallet load on startup with retry on failure
function initializeWallet () {
  const encrypted = localStorage.getItem('wallet_encrypted')
  if (!encrypted) return

  // Attempt to decrypt wallet with retry logic
  requestWalletUnlock(async function tryUnlock (passphrase) {
    try {
      wallet = await decryptWallet(JSON.parse(encrypted), passphrase)
      showWalletInfo()
      showAlert('🔓 Wallet unlocked!', 'success')
    } catch (err) {
      showAlert('❌ Incorrect passphrase or corrupted wallet.', 'danger')
      setTimeout(() => requestWalletUnlock(tryUnlock), 1000) // re-prompt after 1s
    }
  })
}
