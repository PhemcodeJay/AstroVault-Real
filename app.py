# app.py — Madlion DeFi Dashboard (FULLY LIVE)
# Hot wallet mode:  set PRIVATE_KEY in .env → real on-chain txs
# Read-only mode:   enter any address → track real balances
import streamlit as st
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv
import re
import os
from uuid import uuid4

from wallet_utils import (
    RealWallet, init_wallets, get_all_wallets, get_connected_wallet,
    create_position, add_position_to_session, update_position_values,
    close_position, BALANCE_SYMBOLS, NETWORK_NAMES, EXPLORER_URLS,
    AAVE_V3_POOL, AAVE_WETH_GATEWAY,
)
from defi_scanner import (
    classify_yield_opportunities, get_meme_coins, get_top_picks, YieldEntry,
)

load_dotenv()

# ── PAGE CONFIG ───────────────────────────────────────────────
st.set_page_config(
    page_title="Madlion DeFi",
    page_icon="🦁",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

.stApp { background: linear-gradient(135deg,#0f0c29,#1a1730,#24243e); font-family:'Inter',sans-serif; }

.kpi-box { background:rgba(255,255,255,0.06); backdrop-filter:blur(10px); border-radius:12px; padding:.8rem; text-align:center; border:1px solid rgba(255,255,255,0.1); transition:all .2s; }
.kpi-box:hover { transform:translateY(-2px); border-color:rgba(96,165,250,0.5); }
.kpi-val { font-size:1.3rem; font-weight:800; }
.kpi-lbl { font-size:.63rem; color:rgba(255,255,255,.55); text-transform:uppercase; letter-spacing:.5px; margin-top:2px; }

.section-title { font-size:1.1rem; font-weight:700; background:linear-gradient(90deg,#60a5fa,#a78bfa); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin:.8rem 0 .5rem; padding-bottom:.3rem; border-bottom:2px solid rgba(96,165,250,0.25); }

.card { background:linear-gradient(135deg,rgba(30,41,59,.97),rgba(15,23,42,.97)); border-radius:14px; padding:1rem; border:1px solid rgba(96,165,250,0.18); transition:all .25s; margin-bottom:.1rem; }
.card:hover { border-color:#60a5fa; box-shadow:0 6px 20px rgba(96,165,250,0.15); }
.card-title { font-weight:700; font-size:.92rem; color:#f1f5f9; }

.apy-value { font-size:1rem; font-weight:800; background:linear-gradient(135deg,#f59e0b,#ef4444); -webkit-background-clip:text; -webkit-text-fill-color:transparent; white-space:nowrap; }
.apy-extreme { font-size:1rem; font-weight:900; color:#ff4444; animation:pulse 1s ease infinite; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.6} }

.tag { padding:.15rem .45rem; border-radius:6px; font-size:.63rem; font-weight:600; display:inline-block; background:rgba(96,165,250,0.12); color:#60a5fa; }
.chain-badge { padding:.15rem .45rem; border-radius:6px; font-size:.63rem; font-weight:600; display:inline-block; background:#1e293b; color:#94a3b8; }
.chain-avalanche { background:#e84142; color:#fff; }
.chain-ethereum  { background:#627eea; color:#fff; }
.chain-bsc       { background:#f3ba2f; color:#000; }
.chain-base      { background:#0052ff; color:#fff; }
.chain-arbitrum  { background:#28a0f0; color:#fff; }
.chain-polygon   { background:#8247e5; color:#fff; }
.chain-optimism  { background:#ff0420; color:#fff; }

.info-row { display:flex; justify-content:space-between; align-items:center; margin:.35rem 0; font-size:.73rem; }
.info-label { color:#94a3b8; }
.info-value { color:#cbd5e1; font-weight:500; }

.risk-high   { color:#ef4444; font-weight:600; }
.risk-medium { color:#facc15; font-weight:600; }
.risk-low    { color:#22c55e; font-weight:600; }

.hot-badge   { padding:.15rem .5rem; border-radius:6px; font-size:.6rem; font-weight:700; display:inline-block; background:linear-gradient(135deg,#f59e0b,#ea580c); color:#fff; }
.live-badge  { padding:.15rem .5rem; border-radius:6px; font-size:.6rem; font-weight:700; display:inline-block; background:linear-gradient(135deg,#22c55e,#16a34a); color:#fff; }
.xtr-badge   { padding:.15rem .5rem; border-radius:6px; font-size:.6rem; font-weight:700; display:inline-block; background:linear-gradient(135deg,#ef4444,#dc2626); color:#fff; animation:pulse 1s infinite; }

.divider { height:1px; background:linear-gradient(90deg,transparent,rgba(96,165,250,0.25),transparent); margin:.6rem 0; }

.info { padding:.45rem .7rem; border-radius:8px; margin:.4rem 0; font-size:.73rem; background:rgba(59,130,246,.1); border-left:3px solid #3b82f6; color:#93c5fd; }
.warn { padding:.45rem .7rem; border-radius:8px; margin:.4rem 0; font-size:.73rem; background:rgba(245,158,11,.1); border-left:3px solid #f59e0b; color:#fcd34d; }
.ok   { padding:.45rem .7rem; border-radius:8px; margin:.4rem 0; font-size:.73rem; background:rgba(34,197,94,.1);  border-left:3px solid #22c55e; color:#86efac; }
.err  { padding:.45rem .7rem; border-radius:8px; margin:.4rem 0; font-size:.73rem; background:rgba(239,68,68,.1);  border-left:3px solid #ef4444; color:#fca5a5; }

.stButton > button { background:linear-gradient(135deg,#667eea,#764ba2); color:#fff; border:none; border-radius:8px; font-size:.78rem; font-weight:600; transition:all .2s; }
.stButton > button:hover { transform:translateY(-1px); box-shadow:0 4px 12px rgba(102,126,234,.3); }

.stTabs [data-baseweb="tab-list"] { gap:.2rem; }
.stTabs [data-baseweb="tab"] { padding:.3rem .7rem; font-size:.78rem; }

::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:#1e293b; border-radius:3px; }
::-webkit-scrollbar-thumb { background:linear-gradient(135deg,#60a5fa,#a78bfa); border-radius:3px; }
</style>
""", unsafe_allow_html=True)

# ── SESSION INIT ──────────────────────────────────────────────
init_wallets(st.session_state)
update_position_values(st.session_state)

# ── DATA LOADING ──────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_opportunities():
    return classify_yield_opportunities()

@st.cache_data(ttl=300, show_spinner=False)
def load_meme_coins():
    return get_meme_coins()

# ── HELPERS ───────────────────────────────────────────────────
def esc(text: str) -> str:
    """Escape text for safe HTML embedding — kills LaTeX, markdown, code-block triggers."""
    s = str(text) if text else ""
    s = re.sub(r'<[^>]+>', '', s)          # strip any HTML tags from source data
    return (s
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("$", "&#36;")             # ← kills LaTeX
        .replace("`", "&#96;")             # ← kills code blocks
        .replace("*", "&#42;")
        .replace("_", "&#95;")
    )

def fmt_apy(apy_str: str) -> tuple[str, float]:
    try:
        v = float(re.sub(r'[^0-9.\-]', '', str(apy_str)))
        if v >= 1_000_000: return f"{v/1_000_000:.1f}M&#37;", v
        if v >= 1_000:     return f"{v/1_000:.1f}K&#37;", v
        return f"{v:.1f}&#37;", v
    except Exception:
        return "N/A", 0.0

def fmt_tvl(tvl_str: str) -> str:
    s = re.sub(r'[^0-9.\-]', '', str(tvl_str))
    try:
        v = float(s)
        if v >= 1_000_000: return f"&#36;{v/1_000_000:.1f}M"
        if v >= 1_000:     return f"&#36;{v/1_000:.0f}K"
        return f"&#36;{v:.0f}"
    except Exception:
        return esc(tvl_str)

def chain_cls(chain: str) -> str:
    c = chain.lower()
    if "avalanche" in c or "avax" in c: return "chain-avalanche"
    if "ethereum"  in c or c == "eth":  return "chain-ethereum"
    if "bsc"       in c or "bnb"  in c: return "chain-bsc"
    if "base"      in c:                return "chain-base"
    if "arbitrum"  in c:                return "chain-arbitrum"
    if "polygon"   in c or "matic" in c:return "chain-polygon"
    if "optimism"  in c:                return "chain-optimism"
    return "chain-badge"

def risk_cls(risk: str) -> str:
    return {"Low":"risk-low","Medium":"risk-medium","High":"risk-high"}.get(risk,"risk-medium")

def risk_icon(risk: str) -> str:
    return {"Low":"&#128994;","Medium":"&#128993;","High":"&#128308;"}.get(risk,"&#9898;")

def protocol_supports_live(opp) -> bool:
    return opp.project.lower() in ("aave","aave-v3") and opp.chain in AAVE_WETH_GATEWAY

def execute_deposit(wallet: RealWallet, opp: YieldEntry, amount: float) -> str:
    if opp.project.lower() in ("aave","aave-v3") and opp.chain in AAVE_WETH_GATEWAY:
        return wallet.aave_deposit_native(amount)
    raise ValueError(f"Live execution not implemented for {opp.project}. Use the protocol UI.")

def execute_withdraw(wallet: RealWallet, pos) -> str:
    proto = getattr(pos, "protocol", "").lower()
    if proto in ("aave","aave-v3") and pos.chain in AAVE_WETH_GATEWAY:
        return wallet.aave_withdraw_native(0)
    raise ValueError(f"Live withdrawal not implemented for {proto}. Use the protocol UI.")

# ── HEADER ────────────────────────────────────────────────────
col_hdr, col_btn = st.columns([5, 1])
with col_hdr:
    st.markdown("""
    <div style="margin:.2rem 0">
        <h1 style="font-size:1.7rem;font-weight:800;background:linear-gradient(135deg,#60a5fa,#a78bfa,#f472b6);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0">
            &#129409; Madlion DeFi
        </h1>
        <p style="color:#475569;font-size:.7rem;margin:.1rem 0 0">
            Live yield data &middot; Real on-chain balances &middot; Hot wallet execution
        </p>
    </div>
    """, unsafe_allow_html=True)
with col_btn:
    if st.button("&#128260; Refresh", key="global_refresh", use_container_width=True):
        st.cache_data.clear()
        for w in get_all_wallets(st.session_state):
            if w.connected: w.refresh_balance()
        update_position_values(st.session_state)
        st.rerun()

hot_chains = [w.chain for w in get_all_wallets(st.session_state) if w.can_sign]
if hot_chains:
    st.markdown(f'<div class="ok">&#128273; <b>Hot wallet active</b> on: {", ".join(NETWORK_NAMES[c] for c in hot_chains)} — txs will be signed &amp; broadcast.</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="info">&#128065;&#65039; <b>Read-only mode.</b> Add <code>PRIVATE_KEY=0x…</code> to .env for live transactions.</div>', unsafe_allow_html=True)
st.markdown('<div class="warn">&#9888;&#65039; DeFi carries significant risk. Never invest more than you can afford to lose.</div>', unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="section-title">&#128279; Wallets</div>', unsafe_allow_html=True)

    selected_chain = st.selectbox("Chain", list(NETWORK_NAMES.keys()),
                                  format_func=lambda c: NETWORK_NAMES[c], key="sidebar_chain_sel")
    wallet_obj: RealWallet = st.session_state.wallets[selected_chain]

    mode_html = '<span class="hot-badge">&#128273; HOT</span>' if wallet_obj.can_sign else '<span class="tag">&#128065; READ</span>'
    st.markdown(mode_html, unsafe_allow_html=True)

    if wallet_obj.can_sign and not wallet_obj.connected:
        if st.button("Auto-Connect from Key", key=f"auto_{selected_chain}", use_container_width=True):
            try:
                wallet_obj.connect(wallet_obj._account.address)
                st.success("Connected!")
                st.rerun()
            except Exception as e:
                st.error(str(e))

    addr_input = st.text_input("Address (0x…)", placeholder="0xABC…1234", key=f"addr_{selected_chain}")
    if st.button("Connect", key=f"connect_{selected_chain}", type="primary", use_container_width=True):
        target = addr_input.strip() or (wallet_obj._account.address if wallet_obj._account else "")
        if not target:
            st.error("Enter an address or add PRIVATE_KEY to .env")
        else:
            try:
                wallet_obj.connect(target)
                st.success(f"Connected: {wallet_obj.address[:8]}… {wallet_obj.balance:.5f} {wallet_obj.get_balance_symbol()}")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")

    if st.button("&#128260; Refresh Balances", key="refresh_bals", use_container_width=True):
        for w in get_all_wallets(st.session_state):
            if w.connected: w.refresh_balance()
        st.rerun()

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title" style="font-size:.85rem">Connected</div>', unsafe_allow_html=True)
    any_connected = False
    for w in get_all_wallets(st.session_state):
        if not w.connected: continue
        any_connected = True
        mode = "&#128273;" if w.can_sign else "&#128065;"
        st.markdown(f"""
        <div style="font-size:.72rem;padding:.3rem 0;border-bottom:1px solid rgba(96,165,250,0.1)">
          {mode} <span style="color:#60a5fa;font-weight:600">{w.network_name}</span>
          <span style="color:#475569;margin:0 .3rem">|</span>
          <span style="color:#64748b">{w.address[:8]}…{w.address[-4:]}</span><br>
          <span style="color:#34d399;font-weight:600">{w.balance:.5f} {w.get_balance_symbol()}</span>
        </div>""", unsafe_allow_html=True)
        if st.button(f"Disconnect {w.network_name}", key=f"disc_{w.chain}"):
            w.disconnect()
            st.rerun()
    if not any_connected:
        st.caption("None connected")

# ── DATA ──────────────────────────────────────────────────────
with st.spinner("Loading live DeFi data…"):
    opportunities = load_opportunities()
    meme_coins    = load_meme_coins()

all_opps  = opportunities["focus"] + opportunities["long_term"] + opportunities["short_term"] + opportunities["layer2"]
top_picks = get_top_picks(all_opps)

# ── KPIs ──────────────────────────────────────────────────────
active_positions = [p for p in st.session_state.positions if p.status == "active"]
total_invested   = sum(p.amount_invested for p in active_positions)
total_current    = sum(p.current_value   for p in active_positions)
total_pnl        = total_current - total_invested
pnl_pct          = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0

for col, (val, lbl, color) in zip(
    st.columns(5),
    [
        (str(len(active_positions)), "Active",    "#60a5fa"),
        (f"{total_invested:.4f}",    "Invested",  "#a78bfa"),
        (f"{total_current:.4f}",     "Value",     "#34d399"),
        (f"{total_pnl:+.4f}",        "PnL",       "#f472b6"),
        (f"{pnl_pct:+.2f}%",         "PnL %",     "#fbbf24"),
    ]
):
    with col:
        st.markdown(f"""
        <div class="kpi-box">
          <div class="kpi-val" style="background:linear-gradient(135deg,{color},#fff);
               -webkit-background-clip:text;-webkit-text-fill-color:transparent">{val}</div>
          <div class="kpi-lbl">{lbl}</div>
        </div>""", unsafe_allow_html=True)

st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# ── CARD + INVEST RENDERER ────────────────────────────────────
def render_opp_card(opp: YieldEntry, card_id: str):
    """
    Renders the static info card (pure HTML — no Streamlit widgets inside),
    then appends the invest controls as native Streamlit widgets below.
    Streamlit processes each st.markdown independently so we keep the card
    self-contained and never mix widgets inside markdown strings.
    """
    apy_display, apy_val = fmt_apy(opp.apy_str)
    apy_class   = "apy-extreme" if apy_val > 100_000 else "apy-value"
    xtr_badge   = '<span class="xtr-badge">&#9888; EXTREME</span> ' if apy_val > 100_000 else ""
    live_badge  = '<span class="live-badge">&#9889; LIVE</span> ' if protocol_supports_live(opp) else ""

    project = esc(opp.project)
    symbol  = esc(opp.symbol)
    chain   = esc(opp.chain)
    otype   = esc(opp.type)
    risk    = esc(opp.risk)
    tvl     = fmt_tvl(opp.tvl_str)
    ror     = f"{opp.ror:.0f}"
    rc      = risk_cls(opp.risk)
    ccls    = chain_cls(opp.chain)
    ri      = risk_icon(opp.risk)

    st.markdown(f"""
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:.5rem;margin-bottom:.6rem">
        <span class="card-title">&#128202; {project}</span>
        <span class="{apy_class}">{apy_display}</span>
      </div>
      <div style="display:flex;flex-wrap:wrap;gap:4px;align-items:center;margin-bottom:.5rem">
        <span class="chain-badge {ccls}">{chain}</span>
        <span class="tag">{symbol}</span>
        {xtr_badge}{live_badge}
      </div>
      <div class="info-row">
        <span class="info-label">&#128176; TVL</span>
        <span class="info-value">{tvl}</span>
      </div>
      <div class="info-row">
        <span class="info-label">&#128202; Type</span>
        <span class="info-value">{otype}</span>
      </div>
      <div class="info-row">
        <span class="info-label">{ri} Risk</span>
        <span class="{rc}">{risk}</span>
        <span class="info-label" style="margin-left:.5rem">ROR</span>
        <span class="info-value" style="color:#60a5fa">{ror}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Invest controls (native Streamlit widgets — no HTML wrapping) ──
    wallet = get_connected_wallet(st.session_state, opp.chain)
    if not wallet:
        st.caption(f"&#128279; Connect a **{opp.chain.upper()}** wallet to invest")
        pool_url = f"https://defillama.com/yields/pool/{opp.pool_id}" if opp.pool_id else "https://defillama.com/yields"
        st.markdown(f"[View on DeFiLlama ↗]({pool_url})", unsafe_allow_html=False)
        return

    gas = wallet.estimate_gas_cost_native() if wallet.can_sign else 0.0
    max_amt = max(0.0001, wallet.balance - gas - 0.001)

    c1, c2 = st.columns([3, 2])
    with c1:
        amount = st.number_input(
            "Amount",
            min_value=0.0001,
            max_value=float(max_amt),
            value=min(0.01, float(max_amt)),
            step=0.001,
            format="%.5f",
            key=f"amt_{card_id}",
            label_visibility="collapsed",
        )
    with c2:
        btn_label = "&#9889; Invest (live)" if (wallet.can_sign and protocol_supports_live(opp)) else "&#128221; Record"
        if st.button(btn_label, key=f"inv_{card_id}", type="primary", use_container_width=True):
            if amount > wallet.balance:
                st.markdown('<div class="err">Insufficient balance</div>', unsafe_allow_html=True)
                return
            with st.spinner("Broadcasting…" if wallet.can_sign else "Recording…"):
                try:
                    if wallet.can_sign and protocol_supports_live(opp):
                        tx_hash = execute_deposit(wallet, opp, amount)
                        wallet.wait_receipt(tx_hash, timeout=90)
                        wallet.refresh_balance()
                        proto = opp.project.lower()
                    else:
                        tx_hash = f"0xSIM_{uuid4().hex[:16]}"
                        proto   = "simulated"

                    result = create_position(
                        amount=amount, opportunity_name=opp.project,
                        chain=opp.chain, apy=opp.apy, tx_hash=tx_hash, protocol=proto,
                    )
                    if result["success"]:
                        add_position_to_session(st.session_state, result["position"])
                        wallet.refresh_balance()
                        if proto != "simulated":
                            exp = EXPLORER_URLS.get(opp.chain, "")
                            st.markdown(f'<div class="ok">&#10003; Confirmed! <a href="{exp}{tx_hash}" target="_blank">[{tx_hash[:12]}…]</a></div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="info">&#128221; Position recorded. Add PRIVATE_KEY for live execution.</div>', unsafe_allow_html=True)
                        st.rerun()
                    else:
                        st.markdown(f'<div class="err">&#10007; {esc(result["error"])}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f'<div class="err">&#10007; {esc(str(e))}</div>', unsafe_allow_html=True)

    if wallet.can_sign:
        st.caption(f"Balance: {wallet.balance:.5f} {wallet.get_balance_symbol()} | Gas est: {gas:.6f}")


def render_grid(opps: list, title: str, cols: int = 3):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    if not opps:
        st.markdown('<div class="info">No opportunities in this category right now.</div>', unsafe_allow_html=True)
        return
    for i in range(0, len(opps), cols):
        columns = st.columns(cols)
        for j, opp in enumerate(opps[i:i+cols]):
            with columns[j]:
                render_opp_card(opp, f"{title[:3]}_{i+j}")


# ── TABS ──────────────────────────────────────────────────────
tabs = st.tabs(["&#11088; Top Picks", "&#127919; Focus", "&#127807; Long-Term",
                "&#9889; Short-Term", "&#128311; Layer 2",
                "&#128640; Meme Coins", "&#128188; Positions", "&#128279; Wallets"])

with tabs[0]:
    render_grid(top_picks,                   "Best Risk-Adjusted Yield")
with tabs[1]:
    render_grid(opportunities["focus"],      "Established Protocols")
with tabs[2]:
    render_grid(opportunities["long_term"],  "Stable &amp; Confident Outlook")
with tabs[3]:
    render_grid(opportunities["short_term"], "High APY, Higher Risk")
with tabs[4]:
    render_grid(opportunities["layer2"],     "Layer 2 Solutions")

# ── MEME COINS ────────────────────────────────────────────────
with tabs[5]:
    st.markdown('<div class="section-title">&#128640; Trending Meme Coins</div>', unsafe_allow_html=True)
    st.markdown('<div class="warn">&#9888;&#65039; Extreme risk. Not financial advice. DYOR!</div>', unsafe_allow_html=True)
    if not meme_coins:
        st.markdown('<div class="info">No trending meme coins found.</div>', unsafe_allow_html=True)
    else:
        for i in range(0, len(meme_coins), 3):
            cols = st.columns(3)
            for j, coin in enumerate(meme_coins[i:i+3]):
                with cols[j]:
                    try:
                        try:
                            chg_raw = re.sub(r'[^0-9.\-]', '', str(coin.change_24h_pct))
                            chg_f   = float(chg_raw)
                            chg_col = "#34d399" if chg_f >= 0 else "#f87171"
                            chg_ico = "&#128200;" if chg_f >= 0 else "&#128201;"
                        except Exception:
                            chg_f, chg_col, chg_ico = 0.0, "#fbbf24", "&#128202;"

                        sym     = esc(coin.symbol)
                        chn     = esc(coin.chain)
                        pri     = esc(coin.price_usd)
                        chg     = esc(coin.change_24h_pct)
                        risk    = esc(coin.risk)
                        ccls    = chain_cls(coin.chain)
                        rc      = risk_cls(coin.risk)
                        ri      = risk_icon(coin.risk)
                        url     = str(coin.dex_url or "#")
                        liq_fmt = fmt_tvl(coin.liquidity_usd)
                        vol_fmt = fmt_tvl(coin.volume_24h_usd)

                        card = (
                            '<div class="card">'
                            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem">' 
                            f'<span class="card-title" style="color:#f472b6">&#127922; {sym}</span>'
                            f'<span class="{rc}">{ri} {risk}</span>'
                            '</div>'
                            f'<div style="margin-bottom:.4rem"><span class="chain-badge {ccls}">{chn}</span></div>'
                            '<div class="info-row"><span class="info-label">Price</span>'
                            f'<span class="info-value" style="color:#fbbf24">&#36;{pri}</span></div>'
                            '<div class="info-row"><span class="info-label">&#128167; Liquidity</span>'
                            f'<span class="info-value">{liq_fmt}</span></div>'
                            '<div class="info-row"><span class="info-label">&#128202; Vol 24h</span>'
                            f'<span class="info-value">{vol_fmt}</span></div>'
                            f'<div class="info-row"><span class="info-label">{chg_ico} 24h</span>'
                            f'<span style="color:{chg_col};font-weight:600;font-size:.73rem">{chg}</span></div>'
                            '<div style="margin-top:.5rem;padding-top:.4rem;border-top:1px solid rgba(96,165,250,0.15);text-align:center">'
                            f'<a href="{url}" target="_blank" style="color:#60a5fa;font-size:.68rem;text-decoration:none">&#128279; DexScreener &#8599;</a>'
                            '</div></div>'
                        )
                        st.markdown(card, unsafe_allow_html=True)
                    except Exception:
                        continue

# ── MY POSITIONS ──────────────────────────────────────────────
with tabs[6]:
    st.markdown('<div class="section-title">&#128188; My Positions</div>', unsafe_allow_html=True)
    all_pos = st.session_state.positions
    if not all_pos:
        st.markdown('<div class="info">No positions yet. Connect a wallet and start investing!</div>', unsafe_allow_html=True)
    else:
        rows = []
        for p in all_pos:
            pnl = p.current_value - p.amount_invested
            pnl_p = (pnl / p.amount_invested * 100) if p.amount_invested else 0
            elapsed_h = (datetime.utcnow() - p.entry_date).total_seconds() / 3600
            is_live = bool(p.tx_hash and not str(p.tx_hash).startswith("0xSIM"))
            rows.append({
                "Protocol": str(p.opportunity_name)[:22],
                "Chain":    str(p.chain).upper(),
                "Invested": f"{p.amount_invested:.5f}",
                "Current":  f"{p.current_value:.7f}",
                "PnL":      f"{pnl:+.7f}",
                "PnL %":    f"{pnl_p:+.2f}%",
                "APY":      f"{p.apy:.0f}%",
                "Age (h)":  f"{elapsed_h:.1f}",
                "Status":   p.status.upper(),
                "Live":     "✅" if is_live else "📝",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True, height=300)

        # Tx links for live positions
        live_pos = [p for p in all_pos if p.tx_hash and not str(p.tx_hash).startswith("0xSIM")]
        if live_pos:
            st.markdown("**On-chain transactions:**")
            for p in live_pos:
                exp = EXPLORER_URLS.get(p.chain, "")
                st.markdown(f"- {p.opportunity_name} ({p.chain.upper()}): [{p.tx_hash[:14]}…]({exp}{p.tx_hash})")

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title" style="font-size:.9rem">Close a Position</div>', unsafe_allow_html=True)
        active_pos = [p for p in all_pos if p.status == "active"]
        if not active_pos:
            st.caption("No active positions.")
        else:
            labels = {
                p.id: f"{p.opportunity_name} · {p.chain.upper()} · {p.amount_invested:.5f} {BALANCE_SYMBOLS.get(p.chain,'')} · PnL {(p.current_value-p.amount_invested):+.5f}"
                for p in active_pos
            }
            chosen_id = st.selectbox("Position", list(labels.keys()), format_func=lambda x: labels[x])
            chosen = next(p for p in active_pos if p.id == chosen_id)
            wallet = get_connected_wallet(st.session_state, chosen.chain)
            proto  = getattr(chosen, "protocol", "simulated").lower()
            is_live_close = (
                wallet and wallet.can_sign
                and proto in ("aave","aave-v3")
                and chosen.chain in AAVE_WETH_GATEWAY
                and not str(chosen.tx_hash).startswith("0xSIM")
            )
            close_label = "&#9889; Withdraw (live)" if is_live_close else "&#128221; Close Record"
            if st.button(close_label, key="close_pos_btn", type="primary"):
                with st.spinner("Withdrawing…" if is_live_close else "Closing…"):
                    try:
                        close_tx = None
                        if is_live_close:
                            close_tx = execute_withdraw(wallet, chosen)
                            wallet.wait_receipt(close_tx, timeout=90)
                            wallet.refresh_balance()
                        result = close_position(st.session_state, chosen_id, tx_hash=close_tx)
                        if result["success"]:
                            sym = BALANCE_SYMBOLS.get(chosen.chain,"")
                            msg = f"Closed. Returned: {result['amount_returned']:.6f} {sym} | PnL: {result['pnl']:+.6f} {sym}"
                            if close_tx:
                                exp = EXPLORER_URLS.get(chosen.chain,"")
                                msg += f" | [{close_tx[:12]}…]({exp}{close_tx})"
                            st.markdown(f'<div class="ok">&#10003; {msg}</div>', unsafe_allow_html=True)
                            st.rerun()
                        else:
                            st.markdown(f'<div class="err">&#10007; {esc(result["error"])}</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.markdown(f'<div class="err">&#10007; {esc(str(e))}</div>', unsafe_allow_html=True)

# ── WALLETS OVERVIEW ──────────────────────────────────────────
with tabs[7]:
    st.markdown('<div class="section-title">&#128279; Wallet Overview</div>', unsafe_allow_html=True)
    connected_wallets = [w for w in get_all_wallets(st.session_state) if w.connected]
    if not connected_wallets:
        st.markdown('<div class="info">No wallets connected. Use the sidebar to connect.</div>', unsafe_allow_html=True)
    else:
        for i in range(0, len(connected_wallets), 3):
            cols = st.columns(3)
            for j, w in enumerate(connected_wallets[i:i+3]):
                with cols[j]:
                    ccls = chain_cls(w.chain)
                    mode_color = "#34d399" if w.can_sign else "#60a5fa"
                    mode_label = "&#128273; HOT WALLET" if w.can_sign else "&#128065; READ-ONLY"
                    gas_est = w.estimate_gas_cost_native() if w.can_sign else 0.0
                    st.markdown(f"""
                    <div class="card">
                      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem">
                        <span class="card-title">&#127970; {esc(w.network_name)}</span>
                        <span style="color:{mode_color};font-size:.62rem;font-weight:700">{mode_label}</span>
                      </div>
                      <div style="margin-bottom:.4rem">
                        <span class="chain-badge {ccls}">{esc(w.chain).upper()}</span>
                      </div>
                      <div class="info-row">
                        <span class="info-label">&#128176; Balance</span>
                        <span class="info-value" style="color:#34d399">{w.balance:.6f} {w.get_balance_symbol()}</span>
                      </div>
                      <div class="info-row">
                        <span class="info-label">&#9981;&#65039; Est Gas</span>
                        <span class="info-value" style="color:#fbbf24">{gas_est:.8f} {w.get_balance_symbol()}</span>
                      </div>
                      <div class="info-row">
                        <span class="info-label">&#128205; Address</span>
                        <span class="info-value" style="font-size:.65rem">{w.address[:10]}…{w.address[-6:]}</span>
                      </div>
                      <div class="info-row">
                        <span class="info-label">&#128272; Chain ID</span>
                        <span class="info-value">{w.chain_id}</span>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

# ── FOOTER ────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:.8rem;margin-top:1rem;border-top:1px solid rgba(96,165,250,0.1)">
  <p style="color:#334155;font-size:.65rem">
    &#129409; Madlion DeFi &mdash; Powered by DeFiLlama &amp; DexScreener &mdash; Always DYOR &#9888;&#65039;
  </p>
</div>
""", unsafe_allow_html=True)