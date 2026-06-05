# app.py — Madlion DeFi Dashboard (FULLY LIVE)
# ─────────────────────────────────────────────
# Hot wallet mode:  set PRIVATE_KEY in .env → signs + broadcasts real txs
# Read-only mode:   enter any address → tracks real on-chain balances
# ─────────────────────────────────────────────
import streamlit as st
from datetime import datetime
import pandas as pd
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
    NETWORK_NAMES,
    EXPLORER_URLS,
    AAVE_V3_POOL,
    AAVE_WETH_GATEWAY,
)
from defi_scanner import (
    classify_yield_opportunities,
    get_meme_coins,
    get_top_picks,
    YieldEntry,
)

load_dotenv()

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Madlion DeFi",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# STYLES
# ─────────────────────────────────────────────
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Syne:wght@700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
*, *::before, *::after { box-sizing: border-box; }
body, .stApp { background: #06080f !important; color: #c8d3e8; font-family: 'IBM Plex Mono', monospace; }
h1,h2,h3,h4 { font-family: 'Syne', sans-serif !important; }

.card {
  background: #0c1020;
  border: 1px solid rgba(51,144,255,0.12);
  border-radius: 14px;
  padding: 1.1rem 1.2rem;
  margin-bottom: 0.75rem;
  transition: border-color .2s, box-shadow .2s;
}
.card:hover {
  border-color: rgba(51,144,255,0.4);
  box-shadow: 0 0 18px rgba(51,144,255,0.08);
}
.card-title {
  font-family: 'Syne', sans-serif;
  font-size: 0.95rem;
  font-weight: 700;
  color: #e2eaf8;
}
.tag {
  display: inline-block;
  background: #111d30;
  color: #60aeff;
  border-radius: 5px;
  padding: 1px 7px;
  font-size: 0.68rem;
  margin: 2px 1px;
}
.apy  { color: #34d399; font-weight: 700; font-size: 1rem; }
.risk-low    { color: #34d399; font-size: 0.75rem; }
.risk-medium { color: #fbbf24; font-size: 0.75rem; }
.risk-high   { color: #f87171; font-size: 0.75rem; }
.chain-badge {
  display: inline-block;
  background: #0e1e35;
  border: 1px solid rgba(51,144,255,0.2);
  color: #93c5fd;
  border-radius: 6px;
  padding: 2px 9px;
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
}

.section-title {
  font-family: 'Syne', sans-serif;
  color: #60aeff;
  font-size: 1.15rem;
  font-weight: 700;
  border-bottom: 1px solid rgba(51,144,255,0.18);
  padding-bottom: 0.4rem;
  margin-bottom: 0.9rem;
}
.warn  { background: #150f00; border: 1px solid #fbbf24; border-radius: 10px; padding: 0.8rem 1rem; color: #fbbf24; font-size: 0.82rem; margin-bottom: 0.8rem; }
.info  { background: #001430; border: 1px solid #3390ff; border-radius: 10px; padding: 0.8rem 1rem; color: #93c5fd; font-size: 0.82rem; margin-bottom: 0.8rem; }
.ok    { background: #001a0e; border: 1px solid #34d399; border-radius: 10px; padding: 0.8rem 1rem; color: #34d399; font-size: 0.82rem; margin-bottom: 0.8rem; }
.err   { background: #1a0000; border: 1px solid #f87171; border-radius: 10px; padding: 0.8rem 1rem; color: #f87171; font-size: 0.82rem; margin-bottom: 0.8rem; }

.hot-badge  { display:inline-block; background:#0f2a0f; border:1px solid #34d399; color:#34d399; border-radius:5px; padding:1px 8px; font-size:0.68rem; }
.read-badge { display:inline-block; background:#0e1e35; border:1px solid #60aeff; color:#60aeff;  border-radius:5px; padding:1px 8px; font-size:0.68rem; }

.kpi-box { background:#0c1020; border:1px solid rgba(51,144,255,0.15); border-radius:12px; padding:0.9rem 1.1rem; text-align:center; }
.kpi-val { font-family:'Syne',sans-serif; font-size:1.4rem; font-weight:800; color:#e2eaf8; }
.kpi-lbl { font-size:0.7rem; color:#5a6e8c; margin-top:2px; }

div[data-testid="stButton"] button {
  font-family: 'IBM Plex Mono', monospace !important;
  font-weight: 600 !important;
  border-radius: 8px !important;
  font-size: 0.8rem !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SESSION INIT
# ─────────────────────────────────────────────
init_wallets(st.session_state)
update_position_values(st.session_state)

# ─────────────────────────────────────────────
# DATA FETCH (cached via defi_scanner internals)
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_opportunities():
    return classify_yield_opportunities()

@st.cache_data(ttl=300, show_spinner=False)
def load_meme_coins():
    return get_meme_coins()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def risk_class(risk: str) -> str:
    return {"Low": "risk-low", "Medium": "risk-medium", "High": "risk-high"}.get(risk, "risk-medium")

def explorer_link(chain: str, tx_hash: str) -> str:
    base = EXPLORER_URLS.get(chain.lower(), "")
    return f"[{tx_hash[:10]}…]({base}{tx_hash})" if base else tx_hash[:10]

def protocol_supports_live(opp: YieldEntry) -> bool:
    """True if we can execute a real on-chain tx for this protocol."""
    return opp.project.lower() in ("aave", "aave-v3") and opp.chain in AAVE_WETH_GATEWAY

def execute_deposit(wallet: RealWallet, opp: YieldEntry, amount: float) -> str:
    """
    Route the deposit to the correct on-chain function.
    Returns tx_hash string.
    """
    proj = opp.project.lower()
    chain = opp.chain

    if proj in ("aave", "aave-v3"):
        if chain in AAVE_WETH_GATEWAY:
            return wallet.aave_deposit_native(amount)
        raise ValueError(f"Aave not supported on {chain}")
    # Fallback: raw ETH transfer to opportunity pool address (generic)
    raise ValueError(f"Live execution not yet implemented for {proj}. "
                     f"Use the protocol's UI directly.")

def execute_withdraw(wallet: RealWallet, pos) -> str:
    """Route withdrawal based on recorded protocol."""
    proto = getattr(pos, "protocol", "unknown").lower()
    chain = pos.chain

    if proto in ("aave", "aave-v3"):
        if chain in AAVE_WETH_GATEWAY:
            return wallet.aave_withdraw_native(0)  # 0 = withdraw all aWETH
        raise ValueError(f"Aave withdrawal not supported on {chain}")
    raise ValueError(f"Live withdrawal not implemented for {proto}. "
                     f"Use the protocol's UI to withdraw manually.")

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
col_hdr, col_btn = st.columns([5, 1])
with col_hdr:
    st.markdown("""
    <h1 style="font-family:'Syne',sans-serif;font-size:2.2rem;font-weight:800;
               background:linear-gradient(90deg,#3390ff,#a78bfa);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent;
               margin:0.3rem 0 0.1rem">🦁 Madlion DeFi</h1>
    <p style="color:#3a4d6b;font-size:0.78rem;margin:0 0 0.8rem">
        Live yield data · Real on-chain balances · Hot wallet execution
    </p>
    """, unsafe_allow_html=True)
with col_btn:
    if st.button("🔄 Refresh", key="global_refresh"):
        st.cache_data.clear()
        for w in get_all_wallets(st.session_state):
            if w.connected:
                w.refresh_balance()
        update_position_values(st.session_state)
        st.rerun()

# Hot-wallet status banner
hot_chains = [w.chain for w in get_all_wallets(st.session_state) if w.can_sign]
if hot_chains:
    chains_str = ", ".join(NETWORK_NAMES[c] for c in hot_chains)
    st.markdown(f'<div class="ok">🔑 <b>Hot wallet active</b> on: {chains_str} — transactions will be signed &amp; broadcast automatically.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="info">👁️ <b>Read-only mode.</b> No PRIVATE_KEY found in .env. Connect an address to track balances. Add <code>PRIVATE_KEY=0x…</code> to .env to enable live transactions.</div>', unsafe_allow_html=True)

st.markdown('<div class="warn">⚠️ DeFi carries significant risk. Never deposit more than you can afford to lose. Verify every protocol independently before investing.</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR — WALLET MANAGEMENT
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-title">🔗 Wallets</div>', unsafe_allow_html=True)

    selected_chain = st.selectbox(
        "Chain",
        list(NETWORK_NAMES.keys()),
        format_func=lambda c: NETWORK_NAMES[c],
        key="sidebar_chain_sel",
    )

    wallet_obj: RealWallet = st.session_state.wallets[selected_chain]

    # Show mode badge
    mode_html = '<span class="hot-badge">🔑 HOT</span>' if wallet_obj.can_sign else '<span class="read-badge">👁 READ-ONLY</span>'
    st.markdown(mode_html, unsafe_allow_html=True)

    if wallet_obj.can_sign and not wallet_obj.connected:
        st.caption(f"Auto-connect address: {wallet_obj._account.address}")
        if st.button("Auto-Connect from Key", key=f"auto_{selected_chain}"):
            try:
                wallet_obj.connect(wallet_obj._account.address)
                st.success(f"Connected {wallet_obj.address[:8]}… {wallet_obj.balance:.4f} {wallet_obj.get_balance_symbol()}")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    addr_input = st.text_input(
        "Wallet Address (0x…)",
        placeholder="0xABC…1234",
        key=f"addr_{selected_chain}",
    )
    if st.button("Connect", key=f"connect_{selected_chain}", type="primary"):
        target = addr_input.strip() or (wallet_obj._account.address if wallet_obj._account else "")
        if not target:
            st.error("Enter an address or add PRIVATE_KEY to .env")
        else:
            try:
                wallet_obj.connect(target)
                st.success(f"✅ {wallet_obj.address[:8]}… — {wallet_obj.balance:.6f} {wallet_obj.get_balance_symbol()}")
                st.rerun()
            except Exception as e:
                st.error(f"❌ {e}")

    if st.button("🔄 Refresh Balances", key="refresh_bals"):
        for w in get_all_wallets(st.session_state):
            if w.connected:
                w.refresh_balance()
        st.rerun()

    st.markdown("---")
    st.markdown('<div class="section-title" style="margin-top:0.5rem">Connected</div>', unsafe_allow_html=True)
    for w in get_all_wallets(st.session_state):
        if not w.connected:
            continue
        mode = "🔑" if w.can_sign else "👁"
        st.markdown(f"""
        <div style="font-size:0.75rem;padding:0.35rem 0;border-bottom:1px solid #111d30">
          {mode} <span style="color:#60aeff;font-weight:600">{w.network_name}</span><br>
          <span style="color:#5a6e8c">{w.address[:8]}…{w.address[-4:]}</span>
          <span style="color:#34d399;float:right">{w.balance:.5f} {w.get_balance_symbol()}</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button(f"Disconnect {w.network_name}", key=f"disc_{w.chain}"):
            w.disconnect()
            st.rerun()

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
with st.spinner("Fetching live DeFi data…"):
    opportunities = load_opportunities()
    meme_coins = load_meme_coins()

all_opps = (
    opportunities["focus"]
    + opportunities["long_term"]
    + opportunities["short_term"]
    + opportunities["layer2"]
)
top_picks = get_top_picks(all_opps)

# ─────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────
active_positions = [p for p in st.session_state.positions if p.status == "active"]
total_invested   = sum(p.amount_invested for p in active_positions)
total_current    = sum(p.current_value   for p in active_positions)
total_pnl        = total_current - total_invested
pnl_pct          = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

k1, k2, k3, k4, k5 = st.columns(5)
kpi_data = [
    (str(len(active_positions)),      "Active Positions"),
    (f"{total_invested:.4f}",         "Total Invested (native)"),
    (f"{total_current:.4f}",          "Current Value"),
    (f"{total_pnl:+.4f}",             "Unrealised PnL"),
    (f"{pnl_pct:+.2f}%",              "PnL %"),
]
for col, (val, lbl) in zip([k1, k2, k3, k4, k5], kpi_data):
    with col:
        color = "#34d399" if not val.startswith("-") else "#f87171"
        if lbl in ("Active Positions", "Total Invested (native)"):
            color = "#e2eaf8"
        st.markdown(f"""
        <div class="kpi-box">
          <div class="kpi-val" style="color:{color}">{val}</div>
          <div class="kpi-lbl">{lbl}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# OPPORTUNITY CARD RENDERER
# ─────────────────────────────────────────────
def render_opp_card(opp: YieldEntry, card_id: str):
    rc = risk_class(opp.risk)
    live_tag = '<span class="hot-badge" style="font-size:0.62rem">⚡ LIVE TX</span>' if protocol_supports_live(opp) else ""
    st.markdown(f"""
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem">
        <div>
          <span class="card-title">{opp.project}</span>
          <span class="tag">{opp.symbol}</span>
          {live_tag}
        </div>
        <span class="apy">{opp.apy_str}</span>
      </div>
      <div style="margin-top:0.5rem;display:flex;flex-wrap:wrap;gap:4px;align-items:center">
        <span class="chain-badge">{opp.chain}</span>
        <span class="tag">TVL {opp.tvl_str}</span>
        <span class="tag">Type {opp.type}</span>
        <span class="{rc}">⬤ {opp.risk}</span>
        <span style="color:#3a4d6b;font-size:0.68rem">ROR {opp.ror:.1f}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── invest UI ────────────────────────────────────────────
    wallet = get_connected_wallet(st.session_state, opp.chain)
    if not wallet:
        # Check if any wallet connected on a different chain
        st.caption(f"🔗 Connect a **{opp.chain.upper()}** wallet in the sidebar to invest.")
        return

    gas_cost = wallet.estimate_gas_cost_native() if wallet.can_sign else 0.0
    max_invest = max(0.0, wallet.balance - gas_cost - 0.001)

    col_amt, col_btn_invest, col_link = st.columns([3, 2, 2])
    with col_amt:
        amount = st.number_input(
            "Amount",
            min_value=0.0001,
            max_value=float(max_invest) if max_invest > 0 else 1.0,
            value=min(0.01, float(max_invest)) if max_invest > 0.01 else 0.001,
            step=0.001,
            format="%.5f",
            key=f"amt_{card_id}",
            label_visibility="collapsed",
        )
    with col_btn_invest:
        invest_label = "⚡ Invest (live)" if (wallet.can_sign and protocol_supports_live(opp)) else "📝 Record"
        if st.button(invest_label, key=f"inv_{card_id}", type="primary"):
            if amount > wallet.balance:
                st.error("Insufficient balance")
                return
            with st.spinner("Signing & broadcasting…" if wallet.can_sign else "Recording position…"):
                try:
                    if wallet.can_sign and protocol_supports_live(opp):
                        tx_hash = execute_deposit(wallet, opp, amount)
                        # Wait for confirmation
                        receipt = wallet.wait_receipt(tx_hash, timeout=90)
                        wallet.refresh_balance()
                        protocol_tag = opp.project.lower()
                    else:
                        # Simulate / record only
                        from uuid import uuid4
                        tx_hash = f"0xSIM_{uuid4().hex[:16]}"
                        protocol_tag = "simulated"

                    result = create_position(
                        amount=amount,
                        opportunity_name=opp.project,
                        chain=opp.chain,
                        apy=opp.apy,
                        tx_hash=tx_hash,
                        protocol=protocol_tag,
                    )
                    if result["success"]:
                        add_position_to_session(st.session_state, result["position"])
                        explorer = EXPLORER_URLS.get(opp.chain, "")
                        if wallet.can_sign and protocol_supports_live(opp):
                            st.markdown(f'<div class="ok">✅ Confirmed on-chain! Tx: [{tx_hash[:12]}…]({explorer}{tx_hash})</div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="info">📝 Position recorded (simulation). Connect private key for live execution.</div>', unsafe_allow_html=True)
                        st.rerun()
                    else:
                        st.markdown(f'<div class="err">❌ {result["error"]}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="err">❌ {str(e)}</div>', unsafe_allow_html=True)
    with col_link:
        pool_url = f"https://defillama.com/yields/pool/{opp.pool_id}" if opp.pool_id else "https://defillama.com/yields"
        st.markdown(f"[View Pool ↗]({pool_url})")

    if wallet.can_sign:
        st.caption(f"Balance: {wallet.balance:.5f} {wallet.get_balance_symbol()} · Est. gas: {gas_cost:.6f} {wallet.get_balance_symbol()}")


def render_grid(opps: list, category: str, cols: int = 3):
    if not opps:
        st.markdown('<div class="info">No opportunities in this category right now.</div>', unsafe_allow_html=True)
        return
    for i in range(0, len(opps), cols):
        columns = st.columns(cols)
        for j, opp in enumerate(opps[i:i+cols]):
            with columns[j]:
                render_opp_card(opp, f"{category}_{i+j}")


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tabs = st.tabs([
    "⭐ Top Picks",
    "🎯 Focus",
    "🌱 Long-Term",
    "⚡ Short-Term",
    "🔷 Layer 2",
    "🚀 Meme Coins",
    "💼 My Positions",
    "🔗 Wallets",
])

# ── TOP PICKS ────────────────────────────────
with tabs[0]:
    st.markdown('<div class="section-title">Top Picks — Best Risk-Adjusted Yield</div>', unsafe_allow_html=True)
    render_grid(top_picks, "top")

# ── FOCUS ────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="section-title">Focus — Established Protocols</div>', unsafe_allow_html=True)
    render_grid(opportunities["focus"], "focus")

# ── LONG TERM ────────────────────────────────
with tabs[2]:
    st.markdown('<div class="section-title">Long-Term — Stable, Confident Outlook</div>', unsafe_allow_html=True)
    render_grid(opportunities["long_term"], "lt")

# ── SHORT TERM ───────────────────────────────
with tabs[3]:
    st.markdown('<div class="section-title">Short-Term — High APY, Higher Risk</div>', unsafe_allow_html=True)
    render_grid(opportunities["short_term"], "st")

# ── LAYER 2 ──────────────────────────────────
with tabs[4]:
    st.markdown('<div class="section-title">Layer 2 — Arbitrum, Optimism, Base & more</div>', unsafe_allow_html=True)
    render_grid(opportunities["layer2"], "l2")

# ── MEME COINS ───────────────────────────────
with tabs[5]:
    st.markdown('<div class="section-title">🚀 Trending Meme Coins (DexScreener)</div>', unsafe_allow_html=True)
    st.markdown('<div class="warn">⚠️ Meme coins carry extreme risk. This is not financial advice.</div>', unsafe_allow_html=True)
    if not meme_coins:
        st.info("No trending meme coins found right now.")
    else:
        for i in range(0, len(meme_coins), 3):
            cols = st.columns(3)
            for j, coin in enumerate(meme_coins[i:i+3]):
                with cols[j]:
                    try:
                        chg = float(coin.change_24h_pct.replace("%",""))
                        chg_color = "#34d399" if chg >= 0 else "#f87171"
                        chg_str = coin.change_24h_pct
                    except Exception:
                        chg_color = "#fbbf24"
                        chg_str = coin.change_24h_pct
                    rc = risk_class(coin.risk)
                    dex_link = f'<a href="{coin.dex_url}" target="_blank" style="color:#60aeff;font-size:0.7rem">DexScreener ↗</a>' if coin.dex_url else ""
                    st.markdown(f"""
                    <div class="card">
                      <div class="card-title" style="color:#f87171">{coin.symbol}</div>
                      <div style="margin-top:0.5rem;font-size:0.78rem;line-height:1.9;color:#8899aa">
                        <span class="chain-badge">{coin.chain}</span><br>
                        💲 <b style="color:#e2eaf8">{coin.price_usd}</b><br>
                        💧 Liquidity: {coin.liquidity_usd}<br>
                        📊 Vol 24h: {coin.volume_24h_usd}<br>
                        📈 <span style="color:{chg_color}">24h: {chg_str}</span><br>
                        <span class="{rc}">⬤ Risk: {coin.risk}</span>
                      </div>
                      {dex_link}
                    </div>
                    """, unsafe_allow_html=True)

# ── MY POSITIONS ─────────────────────────────
with tabs[6]:
    st.markdown('<div class="section-title">My Positions</div>', unsafe_allow_html=True)

    all_pos = st.session_state.positions
    if not all_pos:
        st.markdown('<div class="info">No positions yet. Connect a wallet and invest in an opportunity above.</div>', unsafe_allow_html=True)
    else:
        # Build dataframe
        rows = []
        for pos in all_pos:
            pnl = pos.current_value - pos.amount_invested
            pnl_pct_pos = (pnl / pos.amount_invested * 100) if pos.amount_invested else 0
            elapsed_h = (datetime.utcnow() - pos.entry_date).total_seconds() / 3600
            rows.append({
                "ID":          pos.id,
                "Protocol":    pos.opportunity_name,
                "Chain":       pos.chain.upper(),
                "Invested":    f"{pos.amount_invested:.5f}",
                "Current":     f"{pos.current_value:.7f}",
                "PnL":         f"{pnl:+.7f}",
                "PnL %":       f"{pnl_pct_pos:+.4f}%",
                "APY":         f"{pos.apy:.2f}%",
                "Elapsed (h)": f"{elapsed_h:.2f}",
                "Status":      pos.status.upper(),
                "Protocol Tag": getattr(pos, "protocol", "?"),
                "Tx":          pos.tx_hash or "N/A",
            })
        df = pd.DataFrame(rows)
        st.dataframe(df.drop(columns=["ID", "Tx"]), use_container_width=True, hide_index=True)

        # Tx links
        st.markdown("**Transaction Links**")
        for pos in all_pos:
            if pos.tx_hash and not pos.tx_hash.startswith("0xSIM"):
                explorer = EXPLORER_URLS.get(pos.chain, "")
                st.markdown(f"- {pos.opportunity_name} ({pos.chain.upper()}): [{pos.tx_hash[:14]}…]({explorer}{pos.tx_hash})")

        st.markdown("---")
        st.markdown('<div class="section-title">Close a Position</div>', unsafe_allow_html=True)

        active_pos_list = [p for p in all_pos if p.status == "active"]
        if not active_pos_list:
            st.caption("No active positions to close.")
        else:
            pos_labels = {p.id: f"{p.opportunity_name} · {p.chain.upper()} · {p.amount_invested:.5f} {BALANCE_SYMBOLS.get(p.chain,'')} · PnL {(p.current_value - p.amount_invested):+.7f}" for p in active_pos_list}
            chosen_id = st.selectbox("Select position", list(pos_labels.keys()), format_func=lambda x: pos_labels[x])
            chosen_pos = next(p for p in active_pos_list if p.id == chosen_id)
            wallet = get_connected_wallet(st.session_state, chosen_pos.chain)

            proto = getattr(chosen_pos, "protocol", "simulated")
            is_live_closeable = (
                wallet and wallet.can_sign
                and proto in ("aave", "aave-v3")
                and chosen_pos.chain in AAVE_WETH_GATEWAY
                and not chosen_pos.tx_hash.startswith("0xSIM")
            )

            close_label = "⚡ Withdraw (live)" if is_live_closeable else "📝 Close Record"
            if st.button(close_label, key="close_pos_btn", type="primary"):
                with st.spinner("Withdrawing on-chain…" if is_live_closeable else "Closing…"):
                    try:
                        close_tx = None
                        if is_live_closeable:
                            close_tx = execute_withdraw(wallet, chosen_pos)
                            wallet.wait_receipt(close_tx, timeout=90)
                            wallet.refresh_balance()

                        result = close_position(st.session_state, chosen_id, tx_hash=close_tx)
                        if result["success"]:
                            sym = BALANCE_SYMBOLS.get(chosen_pos.chain, "")
                            msg = f"✅ Closed. Returned: {result['amount_returned']:.6f} {sym} · PnL: {result['pnl']:+.6f} {sym}"
                            if close_tx:
                                explorer = EXPLORER_URLS.get(chosen_pos.chain, "")
                                msg += f" · [Tx]({explorer}{close_tx})"
                            st.markdown(f'<div class="ok">{msg}</div>', unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.markdown(f'<div class="err">❌ {result["error"]}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f'<div class="err">❌ {str(e)}</div>', unsafe_allow_html=True)

# ── WALLETS ──────────────────────────────────
with tabs[7]:
    st.markdown('<div class="section-title">Wallet Overview</div>', unsafe_allow_html=True)
    connected_wallets = [w for w in get_all_wallets(st.session_state) if w.connected]
    if not connected_wallets:
        st.markdown('<div class="info">No wallets connected. Use the sidebar to connect.</div>', unsafe_allow_html=True)
    else:
        for w in connected_wallets:
            mode_label = "🔑 HOT WALLET (can sign)" if w.can_sign else "👁 READ-ONLY"
            mode_color = "#34d399" if w.can_sign else "#60aeff"
            gas_est = w.estimate_gas_cost_native() if w.can_sign else 0.0
            st.markdown(f"""
            <div class="card">
              <div style="display:flex;justify-content:space-between;align-items:center">
                <span class="card-title">{w.network_name}</span>
                <span style="color:{mode_color};font-size:0.72rem;font-weight:600">{mode_label}</span>
              </div>
              <div style="font-size:0.78rem;color:#8899aa;margin-top:0.6rem;line-height:2">
                📍 <code style="color:#c8d3e8">{w.address}</code><br>
                💰 Balance: <b style="color:#34d399">{w.balance:.8f} {w.get_balance_symbol()}</b><br>
                ⛽ Est. gas/tx: <span style="color:#fbbf24">{gas_est:.8f} {w.get_balance_symbol()}</span><br>
                🆔 Chain ID: {w.chain_id}
              </div>
            </div>
            """, unsafe_allow_html=True)