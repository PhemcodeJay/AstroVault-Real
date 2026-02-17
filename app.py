import streamlit as st
from datetime import datetime
import pandas as pd
from uuid import uuid4
from web3 import Web3
from dotenv import load_dotenv
import os

from wallet_utils import (
    RealWallet,
    init_wallets,
    get_all_wallets,
    get_connected_wallet,
    create_position,
    add_position_to_session,
    update_position_values,
    close_position,
    BALANCE_SYMBOLS,
    NETWORK_NAMES
)

from defi_scanner import classify_yield_opportunities, get_meme_coins, get_top_picks

# --- Load Environment Variables ---
load_dotenv()

# --- Page Config ---
st.set_page_config(
    page_title="Madlion DeFi Dashboard",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Modern DeFi Design ---
st.markdown("""
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
body {
    font-family: 'Inter', sans-serif;
    background: #0a0a1f;
    color: #e0e7ff;
}
.stApp {
    background: transparent;
}
h1, h2, h3, h4 {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
}
.card {
    transition: all 0.3s ease;
    background: #1a1a3b;
    border-radius: 16px;
    padding: 1.5rem;
    border: 1px solid rgba(99, 102, 241, 0.2);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}
.card:hover {
    transform: translateY(-6px);
    box-shadow: 0 8px 30px rgba(99, 102, 241, 0.3);
    border-color: #6366f1;
}
.gradient-btn {
    background: linear-gradient(135deg, #7c3aed, #ec4899);
    color: white;
    border: none;
    padding: 0.75rem 1.5rem;
    border-radius: 12px;
    font-weight: 600;
    transition: all 0.3s ease;
    font-family: 'Space Grotesk', sans-serif;
}
.gradient-btn:hover {
    background: linear-gradient(135deg, #6d28d9, #db2777);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
}
.sidebar .stButton > button {
    width: 100%;
    font-family: 'Inter', sans-serif;
    font-weight: 500;
    background: linear-gradient(135deg, #4f46e5, #8b5cf6);
    color: white;
    border-radius: 12px;
    padding: 0.85rem;
    transition: all 0.3s ease;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}
.sidebar .stButton > button:hover {
    background: linear-gradient(135deg, #4338ca, #7c3aed);
    transform: scale(1.02);
}
.stNumberInput input, .stSelectbox div[data-baseweb="select"] > div, .stTextInput input {
    border-radius: 12px;
    border: 1px solid rgba(99, 102, 241, 0.2);
    padding: 0.75rem;
    background: #1a1a3b;
    color: #e0e7ff;
    transition: all 0.3s ease;
}
.stNumberInput input:focus, .stSelectbox div[data-baseweb="select"] > div:focus, .stTextInput input:focus {
    border-color: #6366f1;
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.2);
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 500;
    color: #a5b4fc;
    padding: 0.85rem 1.75rem;
    border-radius: 12px 12px 0 0;
    background: #1a1a3b;
    margin-right: 6px;
    transition: all 0.3s ease;
}
.stTabs [data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #7c3aed, #ec4899);
    color: white;
}
.stTabs [data-baseweb="tab"]:hover {
    background: #2e2e5b;
    color: #e0e7ff;
}
.warning-box {
    background: linear-gradient(135deg, #f59e0b, #d97706);
    border: 1px solid rgba(99, 102, 241, 0.2);
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 1.25rem;
    color: white;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
}
.table-container {
    background: #1a1a3b;
    border-radius: 16px;
    padding: 2rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}
.table-container table {
    color: #e0e7ff;
    width: 100%;
    font-size: 0.9rem;
}
.table-container th {
    background: #2e2e5b;
    padding: 1rem;
    font-weight: 600;
    border-bottom: 1px solid rgba(99, 102, 241, 0.2);
}
.table-container td {
    padding: 1rem;
    border-bottom: 1px solid rgba(99, 102, 241, 0.2);
}
.sticky-sidebar {
    position: sticky;
    top: 0;
    background: #11112e;
    padding: 1.5rem;
    border-radius: 16px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    margin-bottom: 1rem;
}
.sidebar .sidebar-content {
    background: transparent;
}
.icon-spin {
    animation: spin 2s linear infinite;
}
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
</style>
""", unsafe_allow_html=True)

# --- Initialize Session State ---
if 'wallets' not in st.session_state:
    init_wallets(st.session_state)
if 'positions' not in st.session_state:
    st.session_state.positions = []

update_position_values(st.session_state)

# --- Chain Connection Setup ---
def connect_to_chain(chain_name):
    try:
        rpc_urls = {
            "ethereum": f"https://mainnet.infura.io/v3/{os.getenv('INFURA_API_KEY')}",
            "bsc": os.getenv('BSC_RPC_URL', "https://bsc-dataseed.binance.org/"),
            "arbitrum": os.getenv('ARBITRUM_RPC_URL', "https://arb1.arbitrum.io/rpc"),
            "optimism": os.getenv('OPTIMISM_RPC_URL', "https://mainnet.optimism.io"),
            "base": os.getenv('BASE_RPC_URL', "https://mainnet.base.org"),
            "avalanche": os.getenv('AVALANCHE_RPC_URL', "https://api.avax.network/ext/bc/C/rpc"),
            "solana": "https://neon-proxy-mainnet.solana.p2p.org",
        }
        rpc_url = rpc_urls.get(chain_name)
        if not rpc_url:
            return None
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        if w3.is_connected():
            return w3
        return None
    except Exception as e:
        st.error(f"Failed to connect to {chain_name}: {str(e)}")
        return None

# --- Header ---
st.markdown("""
<div class="text-center py-8">
    <h1 class="text-5xl font-bold mb-3 bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-500">🦁 Madlion DeFi</h1>
    <p class="text-lg text-indigo-200">Your gateway to DeFi yields, meme coins, and portfolio management</p>
</div>
""", unsafe_allow_html=True)

# --- Security Note ---
st.markdown("""
<div class="warning-box flex items-center">
    <i class="fas fa-shield-alt mr-2"></i>
    <p class="font-semibold">Use MetaMask or manually enter a wallet address for secure EVM connections.</p>
</div>
""", unsafe_allow_html=True)

# --- Refresh Button ---
if st.button("🔄 Refresh Data", key="refresh_data", type="primary"):
    with st.spinner("Refreshing..."):
        try:
            for wallet in get_all_wallets(st.session_state):
                if wallet.address:
                    wallet.connect(wallet.address)
            update_position_values(st.session_state)
            opportunities = classify_yield_opportunities()
            meme_coins = get_meme_coins()
            all_opps = opportunities["focus"] + opportunities["long_term"] + opportunities["short_term"] + opportunities["layer2"]
            top_picks = get_top_picks(all_opps)
            st.success("✅ Data Refreshed!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Refresh failed: {str(e)}")

# --- Sidebar: Wallet Management ---
st.sidebar.markdown("""
<div class="sticky-sidebar">
    <h2 class="text-2xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-500">🔗 Wallet</h2>
</div>
""", unsafe_allow_html=True)

selected_chain = st.sidebar.selectbox("Select Chain", list(NETWORK_NAMES.keys()), key="chain_selector")

# Sidebar: Wallet Connection
st.sidebar.markdown("<h3 class='text-lg font-semibold mb-3 text-indigo-200'>Wallet Connection</h3>", unsafe_allow_html=True)

if selected_chain:
    w3 = connect_to_chain(selected_chain)

    # --- MetaMask Connection ---
    if st.sidebar.button("Connect MetaMask", key=f"connect_metamask_{selected_chain}", type="primary"):
        try:
            if w3:
                component_key = f"wallet_{selected_chain}"
                st.markdown(f"""
                <script>
                async function connectMetaMask() {{
                    try {{
                        const accounts = await window.ethereum.request({{ method: 'eth_requestAccounts' }});
                        parent.document.getElementById('{component_key}').value = accounts[0];
                    }} catch (error) {{
                        parent.document.getElementById('{component_key}').value = 'error:' + error.message;
                    }}
                }}
                connectMetaMask();
                </script>
                """, unsafe_allow_html=True)

                address = st.text_input("MetaMask Address", key=component_key, disabled=True)

                if address and not address.startswith("error"):
                    wallet = st.session_state.wallets[selected_chain]
                    wallet.address = Web3.to_checksum_address(address)
                    wallet.connect(wallet.address)
                    st.sidebar.success(f"✅ Connected to {selected_chain.capitalize()} via MetaMask!")
                    st.rerun()
                elif address.startswith("error"):
                    st.sidebar.error(f"❌ {address}")
                else:
                    st.sidebar.error("❌ MetaMask not detected or failed.")
            else:
                st.sidebar.error(f"❌ Failed to connect to {selected_chain}.")
        except Exception as e:
            st.sidebar.error(f"❌ Connection failed: {str(e)}")

    # --- Manual Wallet Address Input ---
    manual_address = st.sidebar.text_input("Enter Wallet Address", key=f"manual_address_{selected_chain}")
    if st.sidebar.button("Connect Wallet", key=f"connect_manual_{selected_chain}", type="primary"):
        try:
            if w3 and manual_address:
                if Web3.is_address(manual_address):
                    wallet = st.session_state.wallets[selected_chain]
                    wallet.address = Web3.to_checksum_address(manual_address)
                    wallet.connect(wallet.address)
                    st.sidebar.success(f"✅ Connected to {selected_chain.capitalize()} manually!")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Invalid wallet address format.")
            else:
                st.sidebar.error(f"❌ Failed to connect to {selected_chain}.")
        except Exception as e:
            st.sidebar.error(f"❌ Connection failed: {str(e)}")

else:
    st.sidebar.info("ℹ️ Please select a chain to connect your wallet.")


# --- Sidebar: Connected Wallets ---
st.sidebar.markdown("<h3 class='text-lg font-semibold mb-3 text-indigo-200'>Connected Chains</h3>", unsafe_allow_html=True)
wallets = get_all_wallets(st.session_state)
for wallet in wallets:
    status_color = "text-green-400" if wallet.connected else "text-red-400"
    st.sidebar.markdown(f"<p class='text-sm {status_color} flex items-center'><i class='fas fa-wallet mr-2'></i>{wallet.network_name}: {'Connected' if wallet.connected else 'Not Connected'}</p>", unsafe_allow_html=True)

# --- Fetch Data with Fallback ---
try:
    with st.spinner("Scanning DeFi opportunities..."):
        opportunities = classify_yield_opportunities()
except Exception as e:
    st.error(f"❌ Failed to fetch opportunities: {str(e)}")
    opportunities = {"focus": [], "long_term": [], "short_term": [], "layer2": []}

try:
    with st.spinner("Fetching meme coins..."):
        meme_coins = get_meme_coins()
except Exception as e:
    st.error(f"❌ Failed to fetch meme coins: {str(e)}")
    meme_coins = []

all_opps = opportunities["focus"] + opportunities["long_term"] + opportunities["short_term"] + opportunities["layer2"]
top_picks = get_top_picks(all_opps) if all_opps else []

# --- Explorer URLs ---
explorer_urls = {
    "ethereum": "https://etherscan.io/tx/",
    "bsc": "https://bscscan.com/tx/",
    "arbitrum": "https://arbiscan.io/tx/",
    "optimism": "https://optimistic.etherscan.io/tx/",
    "base": "https://basescan.org/tx/",
    "avalanche": "https://snowtrace.io/tx/",
    "solana": "https://explorer.neon-labs.org/tx/",
}

# --- Helper: Render Wallet Cards ---
def render_wallet_cards(wallets_list, columns=4):
    for i in range(0, len(wallets_list), columns):
        cols = st.columns(columns)
        for j, wallet in enumerate(wallets_list[i:i+columns]):
            with cols[j]:
                status_color = "text-green-400" if wallet.connected else "text-red-400"
                bg_color = "bg-gradient-to-br from-indigo-900/30 to-blue-900/30"
                address_display = wallet.address[:6] + "..." + wallet.address[-4:] if wallet.connected else "N/A"
                balance_display = f"{wallet.balance:.4f}" if wallet.connected else "N/A"
                balance_symbol = wallet.get_balance_symbol() if wallet.connected else ""
                st.markdown(f"""
                    <div class="card {bg_color} mb-4">
                        <h4 class="text-lg font-semibold flex items-center bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-blue-400"><i class="fas fa-wallet mr-2"></i>{wallet.network_name}</h4>
                        <div class="mt-3 space-y-2">
                            <p class="text-sm {status_color}"><i class="fas fa-circle mr-2"></i><strong>Status:</strong> {'Connected' if wallet.connected else 'Not Connected'}</p>
                            <p class="text-sm text-indigo-200"><i class="fas fa-address-card mr-2"></i><strong>Address:</strong> <code>{address_display}</code></p>
                            <p class="text-sm text-indigo-200"><i class="fas fa-coins mr-2"></i><strong>Balance:</strong> {balance_display} {balance_symbol}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                if wallet.connected:
                    if st.button("Disconnect", key=f"disc_{wallet.chain}_{uuid4()}", type="primary"):
                        wallet.disconnect()
                        st.rerun()

# --- Helper: Render Grid Cards with Invest ---
def render_grid_cards(opps_list, category_name, columns=3, bg_color="bg-white/10"):
    if not opps_list:
        st.markdown(f"""
            <div class="card {bg_color}">
                <p class="text-indigo-200 text-sm flex items-center"><i class="fas fa-info-circle mr-2"></i>No {category_name} opportunities available.</p>
            </div>
        """, unsafe_allow_html=True)
        return

    for i in range(0, len(opps_list), columns):
        cols = st.columns(columns)
        for j, opp in enumerate(opps_list[i:i+columns]):
            with cols[j]:
                st.markdown(f"""
                    <div class="card {bg_color} mb-4">
                        <h4 class="text-lg font-semibold flex items-center bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-400"><i class="fas fa-coins mr-2"></i>{opp.project} ({opp.symbol})</h4>
                        <div class="mt-3 space-y-2">
                            <p class="text-sm text-indigo-200"><i class="fas fa-link mr-2"></i><strong>Chain:</strong> {opp.chain}</p>
                            <p class="text-sm text-indigo-200"><i class="fas fa-chart-line mr-2"></i><strong>APY:</strong> {opp.apy_str}</p>
                            <p class="text-sm text-indigo-200"><i class="fas fa-lock mr-2"></i><strong>TVL:</strong> {opp.tvl_str}</p>
                            <p class="text-sm text-rose-400"><i class="fas fa-exclamation-triangle mr-2"></i><strong>Risk:</strong> {opp.risk}</p>
                            <p class="text-sm text-indigo-200"><i class="fas fa-tag mr-2"></i><strong>Type:</strong> {opp.type}</p>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

                connected_wallet = get_connected_wallet(st.session_state, opp.chain)
                if connected_wallet:
                    widget_suffix = f"{category_name}_{opp.project}_{i}_{j}_{uuid4()}"
                    amount = st.number_input(
                        f"Invest in {opp.project}",
                        min_value=0.001,
                        value=0.1,
                        step=0.001,
                        format="%.4f",
                        key=f"invest_amt_{widget_suffix}"
                    )
                    if st.button("💸 Invest", key=f"btn_invest_{widget_suffix}", type="primary"):
                        try:
                            w3 = connect_to_chain(opp.chain)
                            if w3:
                                tx_hash = f"0x{uuid4().hex}"
                                result = create_position(
                                    amount=amount,
                                    opportunity_name=opp.project,
                                    chain=opp.chain,
                                    apy=float(opp.apy_str.replace("%", "")),
                                    tx_hash=tx_hash
                                )
                                if result["success"]:
                                    add_position_to_session(st.session_state, result["position"])
                                    connected_wallet.connect(connected_wallet.address)
                                    explorer_url = explorer_urls.get(opp.chain.lower(), "")
                                    st.markdown(f"✅ Invested {amount} {connected_wallet.get_balance_symbol()} in {opp.project} (Tx: <a href='{explorer_url}{tx_hash}' target='_blank'>{tx_hash[:8]}...</a>)", unsafe_allow_html=True)
                                    st.rerun()
                                else:
                                    st.error(f"❌ {result['error']}")
                            else:
                                st.error("❌ Failed to connect to chain.")
                        except Exception as e:
                            st.error(f"❌ Transaction failed: {str(e)}")

# --- Tabs Setup ---
tabs = st.tabs(["Wallets", "Top Picks", "Focus", "Long-Term", "Short-Term", "Layer 2", "Meme Coins", "My Positions"])

with tabs[0]:
    st.markdown('<h3 class="text-2xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-blue-400"><i class="fas fa-wallet mr-2"></i>Wallets Overview</h3>', unsafe_allow_html=True)
    render_wallet_cards(wallets)

with tabs[1]:
    st.markdown('<h3 class="text-2xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-400"><i class="fas fa-star mr-2"></i>Top Picks</h3>', unsafe_allow_html=True)
    render_grid_cards(top_picks, "Top Picks", bg_color="bg-gradient-to-br from-indigo-900/30 to-blue-900/30")

with tabs[2]:
    st.markdown('<h3 class="text-2xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-emerald-400 to-teal-400"><i class="fas fa-bullseye mr-2"></i>Focus</h3>', unsafe_allow_html=True)
    render_grid_cards(opportunities["focus"], "Focus", bg_color="bg-gradient-to-br from-emerald-900/30 to-teal-900/30")

with tabs[3]:
    st.markdown('<h3 class="text-2xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-cyan-400"><i class="fas fa-seedling mr-2"></i>Long-Term</h3>', unsafe_allow_html=True)
    render_grid_cards(opportunities["long_term"], "Long-Term", bg_color="bg-gradient-to-br from-blue-900/30 to-cyan-900/30")

with tabs[4]:
    st.markdown('<h3 class="text-2xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-amber-400 to-orange-400"><i class="fas fa-bolt mr-2"></i>Short-Term</h3>', unsafe_allow_html=True)
    render_grid_cards(opportunities["short_term"], "Short-Term", bg_color="bg-gradient-to-br from-amber-900/30 to-orange-900/30")

with tabs[5]:
    st.markdown('<h3 class="text-2xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 to-pink-400"><i class="fas fa-layer-group mr-2"></i>Layer 2</h3>', unsafe_allow_html=True)
    render_grid_cards(opportunities["layer2"], "Layer 2", bg_color="bg-gradient-to-br from-indigo-900/30 to-pink-900/30")

with tabs[6]:
    st.markdown('<h3 class="text-2xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-rose-400 to-orange-400"><i class="fas fa-rocket mr-2"></i>Meme Coins</h3>', unsafe_allow_html=True)
    if not meme_coins:
        st.markdown('<div class="card bg-gradient-to-br from-rose-900/30 to-orange-900/30"><p class="text-indigo-200 text-sm flex items-center"><i class="fas fa-info-circle mr-2"></i>No trending meme coins available.</p></div>', unsafe_allow_html=True)
    else:
        for i in range(0, len(meme_coins), 3):
            cols = st.columns(3)
            for j, coin in enumerate(meme_coins[i:i+3]):
                with cols[j]:
                    change_color = "text-green-400" if float(coin.change_24h_pct.replace("%","")) >=0 else "text-red-400"
                    st.markdown(f"""
                        <div class="card bg-gradient-to-br from-rose-900/30 to-orange-900/30 mb-4">
                            <h4 class="text-lg font-semibold flex items-center bg-clip-text text-transparent bg-gradient-to-r from-rose-400 to-orange-400"><i class="fas fa-coins mr-2"></i>{coin.symbol}</h4>
                            <div class="mt-3 space-y-2">
                                <p class="text-sm text-indigo-200"><i class="fas fa-dollar-sign mr-2"></i><strong>Price:</strong> ${coin.price_usd}</p>
                                <p class="text-sm text-indigo-200"><i class="fas fa-water mr-2"></i><strong>Liquidity:</strong> {coin.liquidity_usd}</p>
                                <p class="text-sm text-indigo-200"><i class="fas fa-chart-bar mr-2"></i><strong>Volume (24h):</strong> {coin.volume_24h_usd}</p>
                                <p class="text-sm text-indigo-200"><i class="fas fa-link mr-2"></i><strong>Chain:</strong> {coin.chain}</p>
                                <p class="text-sm {change_color}"><i class="fas fa-arrow-trend-up mr-2"></i><strong>Change (24h):</strong> {coin.change_24h_pct}</p>
                                <p class="text-sm text-rose-400"><i class="fas fa-exclamation-triangle mr-2"></i><strong>Risk:</strong> {coin.risk}</p>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

with tabs[7]:
    st.markdown('<h3 class="text-2xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-gray-400 to-gray-200"><i class="fas fa-briefcase mr-2"></i>My Positions</h3>', unsafe_allow_html=True)
    if not st.session_state.get("positions", []):
        st.markdown('<div class="card bg-gradient-to-br from-gray-900/30 to-gray-700/30"><p class="text-indigo-200 text-sm flex items-center"><i class="fas fa-info-circle mr-2"></i>No active positions.</p></div>', unsafe_allow_html=True)
    else:
        df = pd.DataFrame([{
            "ID": pos.id,
            "Opportunity": pos.opportunity_name,
            "Chain": pos.chain.capitalize(),
            "Invested": f"{pos.amount_invested:.4f} {BALANCE_SYMBOLS.get(pos.chain, 'TOKEN')}",
            "Current Value": f"{pos.current_value:.4f} {BALANCE_SYMBOLS.get(pos.chain, 'TOKEN')}",
            "PnL": f"{(pos.current_value - pos.amount_invested):.4f} {BALANCE_SYMBOLS.get(pos.chain, 'TOKEN')}",
            "APY": f"{pos.apy:.2f}%",
            "Status": pos.status.capitalize(),
            "Tx Hash": f'<a href="{explorer_urls.get(pos.chain.lower(), "")}{pos.tx_hash}" target="_blank">{pos.tx_hash[:8]}...</a>' if pos.tx_hash else "N/A",
            "Entry Date": pos.entry_date.strftime("%Y-%m-%d %H:%M:%S")
        } for pos in st.session_state.positions])
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        st.markdown(df.to_html(escape=False, index=False, classes="w-full text-sm"), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        for pos in st.session_state.positions:
            if pos.status == "active":
                wallet = get_connected_wallet(st.session_state, pos.chain)
                if wallet:
                    with st.container():
                        st.markdown(f"""
                            <div class="card bg-gradient-to-br from-gray-900/30 to-gray-700/30 mb-4">
                                <p class="text-sm text-indigo-200 flex items-center"><i class="fas fa-briefcase mr-2"></i><strong>{pos.opportunity_name}</strong> ({pos.chain.capitalize()})</p>
                            </div>
                        """, unsafe_allow_html=True)
                    if st.button(f"Close {pos.opportunity_name}", key=f"close_{pos.id}", type="primary"):
                        try:
                            w3 = connect_to_chain(pos.chain)
                            if w3:
                                tx_hash = f"0x{uuid4().hex}"
                                result = close_position(st.session_state, pos.id, tx_hash=tx_hash)
                                if result["success"]:
                                    wallet.connect(wallet.address)
                                    explorer_url = explorer_urls.get(pos.chain.lower(), "")
                                    st.markdown(f"✅ Closed position. Returned {result['amount_returned']:.4f} {BALANCE_SYMBOLS.get(pos.chain, 'TOKEN')} (PnL: {result['pnl']:.4f}) (Tx: <a href='{explorer_url}{tx_hash}' target='_blank'>View</a>)", unsafe_allow_html=True)
                                    st.rerun()
                                else:
                                    st.error(f"❌ {result['error']}")
                            else:
                                st.error("❌ Failed to connect to chain.")
                        except Exception as e:
                            st.error(f"❌ Failed to close position: {str(e)}")