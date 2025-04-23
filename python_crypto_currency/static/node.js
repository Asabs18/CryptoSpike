// Global wallet variables
let wallet = null;
let walletUnlockCallback = null;
let encryptionKey = null;

// 📋 Copy to clipboard
function copyText(id) {
  const el = document.getElementById(id);
  navigator.clipboard.writeText(el.textContent.trim());
}

// 🔓 Prompt unlock modal with callback
function requestWalletUnlock(callback) {
  walletUnlockCallback = callback;
  const modal = new bootstrap.Modal(document.getElementById('walletUnlockModal'));
  modal.show();
}

// 🔐 Handle unlock modal submission
function unlockWallet() {
  const passphrase = document.getElementById('walletPassphraseInput').value.trim();
  const modalEl = document.getElementById('walletUnlockModal');
  const modal = bootstrap.Modal.getInstance(modalEl);
  modal.hide();
  document.getElementById('walletPassphraseInput').value = '';
  if (walletUnlockCallback && passphrase) {
    walletUnlockCallback(passphrase);
    console.log("Unlock modal submitted with passphrase:", passphrase);
  }
}

// 🔑 Derive AES key from passphrase
async function deriveKey(passphrase, salt) {
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    'raw', enc.encode(passphrase), { name: 'PBKDF2' }, false, ['deriveKey']
  );
  return crypto.subtle.deriveKey({
    name: 'PBKDF2',
    salt: salt,
    iterations: 100000,
    hash: 'SHA-256'
  }, keyMaterial, { name: 'AES-GCM', length: 256 }, true, ['encrypt', 'decrypt']);
}

// 🧊 Encrypt wallet with passphrase
async function encryptWallet(walletObj, passphrase) {
  const enc = new TextEncoder();
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const key = await deriveKey(passphrase, salt);
  const encrypted = await crypto.subtle.encrypt(
    { name: 'AES-GCM', iv },
    key,
    enc.encode(JSON.stringify(walletObj))
  );
  return {
    encrypted: btoa(String.fromCharCode(...new Uint8Array(encrypted))),
    iv: Array.from(iv),
    salt: Array.from(salt)
  };
}

// 🔓 Decrypt wallet with passphrase
async function decryptWallet(encryptedData, passphrase) {
  const enc = new TextEncoder();
  const dec = new TextDecoder();
  const { encrypted, iv, salt } = encryptedData;
  const key = await deriveKey(passphrase, new Uint8Array(salt));
  const decrypted = await crypto.subtle.decrypt(
    { name: 'AES-GCM', iv: new Uint8Array(iv) },
    key,
    Uint8Array.from(atob(encrypted), c => c.charCodeAt(0))
  );
  return JSON.parse(dec.decode(decrypted));
}

// 🚀 Attempt wallet load on startup
(async () => {
  const encrypted = localStorage.getItem("wallet_encrypted");
  if (encrypted) {
    requestWalletUnlock(async (passphrase) => {
      try {
        wallet = await decryptWallet(JSON.parse(encrypted), passphrase);
        showWalletInfo();
      } catch (err) {
        alert("❌ Incorrect passphrase or corrupted wallet.");
      }
    });
  }
})();

async function generateWallet() {
  requestWalletUnlock(async (passphrase) => {
    const res = await fetch("/wallet/create");
    const data = await res.json();
    const plainWallet = {
      address: data.address,
      public_key: data.public_key,
      private_key: data.private_key
    };
    const encrypted = await encryptWallet(plainWallet, passphrase);
    localStorage.setItem("wallet_encrypted", JSON.stringify(encrypted));
    wallet = plainWallet;
    showWalletInfo();
    fetchChain();
  });
}

function resetWallet() {
  localStorage.removeItem("wallet_encrypted");
  wallet = null;
  document.getElementById("walletInfo").style.display = "none";
  document.getElementById("walletAddress").textContent = "";
  document.getElementById("walletBalance").textContent = "Loading...";
  document.getElementById("txStatus").textContent = "";
  document.getElementById("mineStatus").textContent = "";
}

const port = window.location.port;
document.getElementById("nodePort").textContent = port;

async function fetchChain() {
  const res = await fetch("/chain");
  const json = await res.json();
  const container = document.getElementById("chainDisplay");
  container.innerHTML = "";
  json.forEach((block) => {
    const div = document.createElement("div");
    div.className = "mined-block";
    div.innerHTML = `
      <strong>Block #${block.index}</strong><br/>
      🧱 Hash: <code>${block.hash.slice(0, 20)}...</code><br/>
      🔗 Prev: <code>${block.previous_hash.slice(0, 20)}...</code><br/>
      ⛏️ Nonce: ${block.nonce}<br/>
      ⏱️ Time: ${new Date(block.timestamp * 1000).toLocaleString()}<br/>
      📦 Transactions (${block.transactions.length}):<br/>
      <div class="tx-list">
        ${block.transactions.map(tx => `
          <div class="tx-entry">🔄 ${tx.sender.slice(0, 12)}... → ${tx.receiver.slice(0, 12)}... (${tx.amount})</div>
        `).join('')}
      </div>
    `;
    container.appendChild(div);
  });
  updateBalance();
  renderMempool();
}

async function updateBalance() {
  if (!wallet) return;
  const res = await fetch("/chain");
  const json = await res.json();
  let balance = 0;
  json.forEach(block => {
    block.transactions.forEach(tx => {
      if (tx.sender === wallet.address) balance -= tx.amount;
      if (tx.receiver === wallet.address) balance += tx.amount;
    });
  });
  document.getElementById("walletBalance").textContent = balance;
}

async function renderMempool() {
  const res = await fetch("/mempool");
  const txs = await res.json();
  const container = document.getElementById("mempoolDisplay");
  container.innerHTML = "";
  if (txs.length === 0) {
    container.innerHTML = '<div class="text-muted">No pending transactions</div>';
    return;
  }
  txs.forEach(tx => {
    const entry = document.createElement("div");
    entry.className = "tx-entry";
    entry.innerHTML = `🔄 <b>${tx.sender.slice(0, 12)}...</b> → <b>${tx.receiver.slice(0, 12)}...</b> (${tx.amount})`;
    container.appendChild(entry);
  });
}

async function sha256(msg) {
  const encoder = new TextEncoder();
  const data = encoder.encode(msg);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  return Array.from(new Uint8Array(hashBuffer))
    .map(b => b.toString(16).padStart(2, "0"))
    .join("");
}

async function signTransaction(privateKeyHex, receiver, amount) {
  const EC = elliptic.ec;
  const ec = new EC("secp256k1");
  const key = ec.keyFromPrivate(privateKeyHex);
  const message = `${receiver}:${amount.toFixed(2)}`;
  const msgHashHex = await sha256(message);

  const signature = key.sign(msgHashHex, { canonical: true });

  // Convert r and s to 32-byte hex and concatenate
  const r = signature.r.toArrayLike(Uint8Array, 'be', 32);
  const s = signature.s.toArrayLike(Uint8Array, 'be', 32);
  const sigBytes = new Uint8Array([...r, ...s]);

  const sigHex = Array.from(sigBytes).map(b => b.toString(16).padStart(2, "0")).join("");

  console.log("✅ Signature (raw hex):", sigHex);
  return sigHex;
}


async function broadcastTransaction(tx) {
  await fetch("/broadcast/transaction", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(tx)
  });
}

async function broadcastLastBlock() {
  const res = await fetch("/chain");
  const chain = await res.json();
  const latestBlock = chain[chain.length - 1];
  await fetch("/broadcast/block", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(latestBlock)
  });
  await fetch("/resolve");
  await renderMempool();
}

function showWalletInfo() {
  document.getElementById("walletInfo").style.display = "block";
  document.getElementById("walletAddress").textContent = wallet.address;
  updateBalance();
}

document.getElementById("txForm").addEventListener("submit", (e) => {
  e.preventDefault();
  if (!wallet) return alert("Generate a wallet first.");

  requestWalletUnlock(async (passphrase) => {
    const receiver = document.getElementById("receiver").value;
    const amount = parseFloat(document.getElementById("amount").value);

    console.log("Signing transaction...");
    console.log("Wallet:", wallet);
    console.log("Passphrase:", passphrase);
    console.log("Receiver:", receiver);
    console.log("Amount:", amount);

    const signature = await signTransaction(wallet.private_key, receiver, amount);

    const res = await fetch("/transaction/create", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sender: wallet.address,
        receiver,
        amount,
        signature,
        public_key: wallet.public_key
      })
    });

    const json = await res.json();
    document.getElementById("txStatus").textContent = json.message || json.error;
    if (json.transaction) {
      await broadcastTransaction(json.transaction);
      fetchChain();
    }
  });
});



document.getElementById("mineBtn").addEventListener("click", async () => {
  if (!wallet) return alert("Generate a wallet first.");
  const minerAddress = wallet.address;
  const mineStatus = document.getElementById("mineStatus");
  mineStatus.innerHTML = `<div class="text-warning">⛏️ Mining block... <span class="spinner-border spinner-border-sm text-secondary"></span></div>`;
  try {
    const res = await fetch(`/mine?miner=${minerAddress}`);
    const json = await res.json();
    mineStatus.innerHTML = `✅ Block mined by <code>${minerAddress}</code>`;
    await fetchChain();
    await broadcastLastBlock();
    await renderMempool();
  } catch (err) {
    mineStatus.innerHTML = `<span class="text-danger">❌ Mining failed.</span>`;
  }
});

document.getElementById("peerForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("newPeer").value.trim();
  if (!input) return;
  const peerUrl = input.startsWith("http") ? input : `http://localhost:${input}`;
  await fetch("/peers", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ peer: peerUrl })
  });
  document.getElementById("newPeer").value = "";
  loadPeers();
});

async function loadPeers() {
  const res = await fetch("/peers");
  const json = await res.json();
  const list = document.getElementById("peerList");
  list.innerHTML = "";
  json.peers.forEach(peer => {
    const li = document.createElement("li");
    li.textContent = peer;
    list.appendChild(li);
  });
}

async function syncMempool() {
  const peersRes = await fetch("/peers");
  const { peers } = await peersRes.json();
  for (const peer of peers) {
    try {
      const res = await fetch(`${peer}/mempool`);
      const peerTxs = await res.json();
      await fetch("/mempool/merge", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(peerTxs)
      });
    } catch (err) {
      console.warn("Failed to sync mempool with", peer);
    }
  }
}

setInterval(() => {
  fetch("/resolve").then(() => fetchChain());
  syncMempool();
  renderMempool();
}, 5000);

fetchChain();
loadPeers();
renderMempool();