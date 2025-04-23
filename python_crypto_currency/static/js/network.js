// network.js - Peer management and network synchronization

async function loadPeers () {
  const res = await fetch('/peers')
  const json = await res.json()
  const list = document.getElementById('peerList')
  list.innerHTML = ''
  json.peers.forEach(peer => {
    const li = document.createElement('li')
    li.textContent = peer
    list.appendChild(li)
  })
}

function setupPeerForm () {
  document.getElementById('peerForm').addEventListener('submit', async e => {
    e.preventDefault()
    const input = document.getElementById('newPeer').value.trim()
    if (!input) {
      showAlert('⚠️ Please enter a peer port or URL.', 'warning')
      return
    }
    const peerUrl = input.startsWith('http')
      ? input
      : `http://localhost:${input}`
    try {
      await fetch('/peers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ peer: peerUrl })
      })
      showAlert('✅ Peer added!', 'success')
      document.getElementById('newPeer').value = ''
      loadPeers()
    } catch (err) {
      showAlert('❌ Failed to add peer', 'danger')
    }
  })
}

async function syncMempool () {
  setSyncing(true)
  const peersRes = await fetch('/peers')
  const { peers } = await peersRes.json()
  for (const peer of peers) {
    try {
      const res = await fetch(`${peer}/mempool`)
      const peerTxs = await res.json()
      await fetch('/mempool/merge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(peerTxs)
      })
    } catch (err) {
      console.warn('Failed to sync mempool with', peer)
    }
  }
  setSyncing(false)
}

// 🔁 Periodic sync function
async function periodicSync () {
  if (!wallet) return // Skip syncing if wallet not loaded

  const peersRes = await fetch('/peers')
  const { peers } = await peersRes.json()
  if (peers.length === 0) return // Skip spinner if no peers

  setSyncing(true)

  try {
    await fetch('/resolve')
    await fetchChain()
    await syncMempool()
    await renderMempool()
  } catch (err) {
    console.warn('Periodic sync error:', err)
  }

  setSyncing(false)
}

// 🔁 Start sync interval
function startSyncInterval () {
  setInterval(periodicSync, 5000)
}
