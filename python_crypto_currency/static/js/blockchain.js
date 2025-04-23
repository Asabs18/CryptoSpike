/**
 * blockchain.js - Chain and transaction interaction functions
 *
 * Handles:
 * - Fetching and displaying the blockchain
 * - Managing the mempool
 * - Broadcasting transactions and blocks
 * - Mining blocks
 * - Submitting transactions via UI
 */

/**
 * ⛓️ Fetch the blockchain and render each block and its transactions.
 */
async function fetchChain () {
  const res = await fetch('/chain')
  const json = await res.json()
  const container = document.getElementById('chainDisplay')
  container.innerHTML = ''

  json.forEach(block => {
    const div = document.createElement('div')
    div.className = 'mined-block'
    div.innerHTML = `
      <strong>Block #${block.index}</strong><br/>
      🧱 Hash: <code>${block.hash.slice(0, 20)}...</code><br/>
      🔗 Prev: <code>${block.previous_hash.slice(0, 20)}...</code><br/>
      ⛏️ Nonce: ${block.nonce}<br/>
      ⏱️ Time: ${new Date(block.timestamp * 1000).toLocaleString()}<br/>
      📦 Transactions (${block.transactions.length}):<br/>
      <div class="tx-list">
        ${block.transactions
          .map(
            tx => `
            <div class="tx-entry">
              ${
                tx.sender === 'SYSTEM'
                  ? "🎁 <span class='text-success'>Reward → " +
                    tx.receiver.slice(0, 12) +
                    '... (' +
                    tx.amount +
                    ')</span>'
                  : `🔄 ${tx.sender.slice(0, 12)}... → ${tx.receiver.slice(
                      0,
                      12
                    )}... (${tx.amount})`
              }
            </div>
          `
          )
          .join('')}
      </div>
    `
    container.appendChild(div)
  })

  updateBalance()
  renderMempool()
}

/**
 * 💰 Calculate the balance for the current wallet and update the display.
 */
async function updateBalance () {
  if (!wallet) return
  const res = await fetch('/chain')
  const json = await res.json()

  let balance = 0
  json.forEach(block => {
    block.transactions.forEach(tx => {
      if (tx.sender === wallet.address) balance -= tx.amount
      if (tx.receiver === wallet.address) balance += tx.amount
    })
  })

  document.getElementById('walletBalance').textContent = balance
}

/**
 * 📬 Render the current mempool in the UI, highlighting newly created local transactions.
 */
async function renderMempool () {
  const res = await fetch('/mempool')
  const txs = await res.json()
  const container = document.getElementById('mempoolDisplay')
  const old = new Set(
    [...container.querySelectorAll('.tx-entry')].map(e => e.dataset.txid)
  )

  container.innerHTML = ''

  if (txs.length === 0) {
    container.innerHTML =
      '<div class="text-muted">No pending transactions</div>'
    return
  }

  for (const tx of txs) {
    const id = `${tx.sender}-${tx.receiver}-${tx.amount}`
    const entry = document.createElement('div')
    entry.className = 'tx-entry'
    entry.dataset.txid = id

    entry.innerHTML = `🔄 <b>${tx.sender.slice(
      0,
      12
    )}...</b> → <b>${tx.receiver.slice(0, 12)}...</b> (${tx.amount})`

    // Highlight if new and created by local wallet
    if (!old.has(id) && wallet && tx.sender === wallet.address) {
      entry.style.background = '#dff0d8'
      setTimeout(() => (entry.style.background = ''), 1500)
    }

    container.appendChild(entry)
  }
}

/**
 * 📡 Broadcast a single transaction to all known peers.
 *
 * @param {Object} tx - The transaction object to broadcast.
 */
async function broadcastTransaction (tx) {
  await fetch('/broadcast/transaction', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(tx)
  })
}

/**
 * 📡 Broadcast the latest block to all peers and resolve chain conflicts.
 */
async function broadcastLastBlock () {
  const res = await fetch('/chain')
  const chain = await res.json()
  const latestBlock = chain[chain.length - 1]

  await fetch('/broadcast/block', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(latestBlock)
  })

  await fetch('/resolve')
  await renderMempool()
}

/**
 * ⛏️ Setup the mining button to trigger block mining.
 */
function setupMiningButton () {
  document.getElementById('mineBtn').addEventListener('click', async () => {
    if (!wallet) return showAlert('⚠️ Generate a wallet first.', 'warning')

    const button = document.getElementById('mineBtn')
    setLoading(button, true)

    try {
      const res = await fetch(`/mine?miner=${wallet.address}`)
      const json = await res.json()
      showAlert(json.message || '✅ Block mined!', 'success')
      await fetchChain()
      await broadcastLastBlock()
      await renderMempool()
    } catch (err) {
      showAlert('❌ Mining failed.', 'danger')
    } finally {
      setLoading(button, false)
    }
  })
}

/**
 * 💸 Setup the transaction form to send signed transactions to the server.
 */
function setupTransactionForm () {
  document.getElementById('txForm').addEventListener('submit', e => {
    e.preventDefault()
    if (!wallet) return showAlert('⚠️ Generate a wallet first.', 'warning')

    requestWalletUnlock(async passphrase => {
      const receiver = document.getElementById('receiver').value
      const amount = parseFloat(document.getElementById('amount').value)
      const button = document.querySelector('#txForm button[type="submit"]')
      setLoading(button, true)

      const signature = await signTransaction(
        wallet.private_key,
        receiver,
        amount
      )

      const res = await fetch('/transaction/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sender: wallet.address,
          receiver,
          amount,
          signature,
          public_key: wallet.public_key
        })
      })

      const json = await res.json()
      showAlert(
        json.message || json.error,
        json.transaction ? 'success' : 'danger'
      )

      if (json.transaction) {
        await broadcastTransaction(json.transaction)
        fetchChain()
      }

      setLoading(button, false)
    })
  })
}
