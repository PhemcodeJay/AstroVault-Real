# wallet_utils.py — Live on-chain wallet + transaction execution
from __future__ import annotations

import os
import time
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from uuid import uuid4

from web3 import Web3
from web3.exceptions import Web3Exception
from eth_account import Account
from eth_account.signers.local import LocalAccount
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────
# NETWORK CONFIG
# ─────────────────────────────────────────────────────────────
INFURA_API_KEY = os.getenv("INFURA_API_KEY", "")

RPC_URLS: Dict[str, str] = {
    "ethereum":  os.getenv("ETH_RPC_URL",  f"https://mainnet.infura.io/v3/{INFURA_API_KEY}" if INFURA_API_KEY else "https://eth.llamarpc.com"),
    "bsc":       os.getenv("BSC_RPC_URL",  "https://bsc-dataseed.binance.org/"),
    "arbitrum":  os.getenv("ARB_RPC_URL",  "https://arb1.arbitrum.io/rpc"),
    "optimism":  os.getenv("OP_RPC_URL",   "https://mainnet.optimism.io"),
    "base":      os.getenv("BASE_RPC_URL", "https://mainnet.base.org"),
    "avalanche": os.getenv("AVAX_RPC_URL", "https://api.avax.network/ext/bc/C/rpc"),
    "polygon":   os.getenv("POLY_RPC_URL", "https://polygon-rpc.com"),
}

CHAIN_IDS: Dict[str, int] = {
    "ethereum": 1, "bsc": 56, "arbitrum": 42161,
    "optimism": 10, "base": 8453, "avalanche": 43114, "polygon": 137,
}

BALANCE_SYMBOLS: Dict[str, str] = {
    "ethereum": "ETH", "bsc": "BNB", "arbitrum": "ETH",
    "optimism": "ETH", "base": "ETH", "avalanche": "AVAX", "polygon": "POL",
}

NETWORK_NAMES: Dict[str, str] = {
    "ethereum": "Ethereum", "bsc": "BSC", "arbitrum": "Arbitrum",
    "optimism": "Optimism", "base": "Base", "avalanche": "Avalanche", "polygon": "Polygon",
}

EXPLORER_URLS: Dict[str, str] = {
    "ethereum":  "https://etherscan.io/tx/",
    "bsc":       "https://bscscan.com/tx/",
    "arbitrum":  "https://arbiscan.io/tx/",
    "optimism":  "https://optimistic.etherscan.io/tx/",
    "base":      "https://basescan.org/tx/",
    "avalanche": "https://snowtrace.io/tx/",
    "polygon":   "https://polygonscan.com/tx/",
}

# ─────────────────────────────────────────────────────────────
# AAVE V3 ADDRESSES  (Pool + WETHGateway for native deposits)
# ─────────────────────────────────────────────────────────────
AAVE_V3_POOL: Dict[str, str] = {
    "ethereum":  "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
    "arbitrum":  "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "optimism":  "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "base":      "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
    "polygon":   "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
    "avalanche": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
}

AAVE_WETH_GATEWAY: Dict[str, str] = {
    "ethereum":  "0xD322A49006FC828F9B5B37Ab215F99B4E5caB19C",
    "arbitrum":  "0xecD4bd3121F9FD604ffaC631bF6d41ec12f1fafb",
    "optimism":  "0xe9E52021f4e11DEAD8661812A0A6c8627abA2a54",
    "base":      "0x8be473dCfA93132658821E67CbEB684ec8Ea2E74",
    "polygon":   "0x1e4b7A6b903680eab0be3dF36ad00a2d57266D3a",
    "avalanche": "0xa938d8536aEed1Bd48f548380394Ab30Aa11B00e",
}

WRAPPED_NATIVE: Dict[str, str] = {
    "ethereum":  "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
    "arbitrum":  "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
    "optimism":  "0x4200000000000000000000000000000000000006",
    "base":      "0x4200000000000000000000000000000000000006",
    "polygon":   "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    "bsc":       "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
    "avalanche": "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7",
}

# ─────────────────────────────────────────────────────────────
# MINIMAL ABIs
# ─────────────────────────────────────────────────────────────
ERC20_ABI = [
    {"inputs":[{"name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"stateMutability":"view","type":"function"},
]

AAVE_POOL_ABI = [
    {"inputs":[{"name":"asset","type":"address"},{"name":"amount","type":"uint256"},{"name":"onBehalfOf","type":"address"},{"name":"referralCode","type":"uint16"}],"name":"supply","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"asset","type":"address"},{"name":"amount","type":"uint256"},{"name":"to","type":"address"}],"name":"withdraw","outputs":[{"name":"","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
]

WETH_GATEWAY_ABI = [
    {"inputs":[{"name":"lendingPool","type":"address"},{"name":"onBehalfOf","type":"address"},{"name":"referralCode","type":"uint16"}],"name":"depositETH","outputs":[],"stateMutability":"payable","type":"function"},
    {"inputs":[{"name":"lendingPool","type":"address"},{"name":"amount","type":"uint256"},{"name":"to","type":"address"}],"name":"withdrawETH","outputs":[],"stateMutability":"nonpayable","type":"function"},
]

AWETH_ABI = [
    {"inputs":[{"name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
]

# aWETH token addresses per chain (for Aave withdrawals via gateway)
AWETH_ADDRESS: Dict[str, str] = {
    "ethereum":  "0x4d5F47FA6A74757f35C14fD3a6Ef8E3C9BC514E8",
    "arbitrum":  "0xe50fA9b3c56FfB159cB0FCA61F5c9D750e8128c8",
    "optimism":  "0xe50fA9b3c56FfB159cB0FCA61F5c9D750e8128c8",
    "base":      "0xD4a0e0b9149BCee3C920d2E00b5dE09138fd8bb7",
    "polygon":   "0x6d80113e533a2C0fe82EaBD35f1875DcEA89Ea97",
    "avalanche": "0x6d80113e533a2C0fe82EaBD35f1875DcEA89Ea97",
}

# ─────────────────────────────────────────────────────────────
# POSITION MODEL
# ─────────────────────────────────────────────────────────────
@dataclass
class Position:
    id: str
    opportunity_name: str
    chain: str
    amount_invested: float          # in native token units
    current_value: float            # accrued value
    apy: float
    entry_date: datetime
    status: str                     # "active" | "closed"
    tx_hash: Optional[str] = None
    close_tx_hash: Optional[str] = None
    protocol: str = "unknown"       # "aave" | "unknown"
    asset_address: Optional[str] = None  # token deposited

# ─────────────────────────────────────────────────────────────
# WALLET CLASS
# ─────────────────────────────────────────────────────────────
class RealWallet:
    """
    EVM wallet with optional hot-wallet signing.
    - Read-only mode: address only (track balances, show positions)
    - Signing mode:   private key loaded from env; can sign + broadcast txs
    """

    def __init__(self, chain: str):
        self.chain = chain.lower()
        self.connected = False
        self.address: str = ""
        self.balance: float = 0.0
        self.network_name = NETWORK_NAMES.get(self.chain, self.chain.capitalize())
        self.chain_id = CHAIN_IDS.get(self.chain, 1)
        self._account: Optional[LocalAccount] = None

        rpc = RPC_URLS.get(self.chain, "")
        self.w3: Optional[Web3] = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 12})) if rpc else None

        # Load private key if present (hot wallet mode)
        pk_env = f"PRIVATE_KEY_{self.chain.upper()}"
        pk_fallback = os.getenv("PRIVATE_KEY", "")
        pk = os.getenv(pk_env, pk_fallback)
        if pk and pk.startswith("0x") and len(pk) == 66:
            try:
                self._account = Account.from_key(pk)
                logger.info(f"[{self.network_name}] Hot wallet loaded: {self._account.address[:8]}...")
            except Exception as e:
                logger.warning(f"[{self.network_name}] Failed to load private key: {e}")

    # ── connection ──────────────────────────────────────────
    def connect(self, address: str) -> bool:
        if not self.w3:
            raise RuntimeError(f"No RPC configured for {self.chain}")
        address = address.strip()
        if not Web3.is_address(address):
            raise ValueError(f"Invalid EVM address: {address}")

        checksum = Web3.to_checksum_address(address)
        # Verify chain id matches
        on_chain_id = self.w3.eth.chain_id
        if on_chain_id != self.chain_id:
            raise ValueError(f"RPC chain_id={on_chain_id} does not match expected {self.chain_id} for {self.chain}")

        wei = self.w3.eth.get_balance(checksum)
        self.address = checksum
        self.balance = float(Web3.from_wei(wei, "ether"))
        self.connected = True
        logger.info(f"[{self.network_name}] Connected {checksum[:8]}... balance={self.balance:.6f}")
        return True

    def auto_connect(self) -> bool:
        """Auto-connect if private key loaded (hot wallet)."""
        if self._account and not self.connected:
            try:
                return self.connect(self._account.address)
            except Exception as e:
                logger.warning(f"[{self.network_name}] Auto-connect failed: {e}")
        return False

    def disconnect(self):
        self.connected = False
        self.address = ""
        self.balance = 0.0

    def refresh_balance(self):
        if self.connected and self.w3:
            try:
                wei = self.w3.eth.get_balance(Web3.to_checksum_address(self.address))
                self.balance = float(Web3.from_wei(wei, "ether"))
            except Exception:
                pass

    def get_balance_symbol(self) -> str:
        return BALANCE_SYMBOLS.get(self.chain, "TOKEN")

    @property
    def can_sign(self) -> bool:
        return self._account is not None and self.connected

    # ── gas helpers ─────────────────────────────────────────
    def _get_gas_params(self) -> dict:
        """EIP-1559 gas params where supported, else legacy."""
        if not self.w3:
            return {}
        try:
            latest = self.w3.eth.get_block("latest")
            if "baseFeePerGas" in latest:
                base = latest["baseFeePerGas"]
                priority = self.w3.to_wei(1, "gwei")
                return {
                    "maxFeePerGas": base * 2 + priority,
                    "maxPriorityFeePerGas": priority,
                }
        except Exception:
            pass
        return {"gasPrice": self.w3.eth.gas_price}

    def estimate_gas_cost_native(self, gas_units: int = 250_000) -> float:
        if not self.w3:
            return 0.0
        try:
            params = self._get_gas_params()
            price = params.get("maxFeePerGas") or params.get("gasPrice", 0)
            return float(Web3.from_wei(price * gas_units, "ether"))
        except Exception:
            return 0.0

    # ── core signing + broadcast ─────────────────────────────
    def _sign_and_send(self, tx: dict) -> str:
        """Signs and broadcasts a transaction. Returns tx_hash hex string."""
        if not self.can_sign:
            raise RuntimeError("Wallet is not in signing mode. Set PRIVATE_KEY in .env")
        if not self.w3:
            raise RuntimeError(f"No Web3 for {self.chain}")

        nonce = self.w3.eth.get_transaction_count(self._account.address, "pending")
        tx["nonce"] = nonce
        tx["chainId"] = self.chain_id
        tx.setdefault("from", self._account.address)

        # Add gas params
        gas_params = self._get_gas_params()
        tx.update(gas_params)

        # Estimate gas
        try:
            tx["gas"] = int(self.w3.eth.estimate_gas(tx) * 1.2)
        except Exception:
            tx["gas"] = 300_000

        signed = self._account.sign_transaction(tx)
        raw = signed.raw_transaction
        tx_hash = self.w3.eth.send_raw_transaction(raw)
        return tx_hash.hex()

    def wait_receipt(self, tx_hash: str, timeout: int = 120) -> dict:
        if not self.w3:
            raise RuntimeError(f"No Web3 for {self.chain}")
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
        if receipt["status"] != 1:
            raise RuntimeError(f"Transaction reverted: {tx_hash}")
        return dict(receipt)

    # ── ERC-20 helpers ───────────────────────────────────────
    def _erc20_contract(self, token_addr: str):
        return self.w3.eth.contract(
            address=Web3.to_checksum_address(token_addr), abi=ERC20_ABI
        )

    def get_token_balance(self, token_addr: str) -> Tuple[float, str]:
        try:
            c = self._erc20_contract(token_addr)
            raw = c.functions.balanceOf(Web3.to_checksum_address(self.address)).call()
            dec = c.functions.decimals().call()
            sym = c.functions.symbol().call()
            return raw / (10 ** dec), sym
        except Exception:
            return 0.0, "?"

    def ensure_allowance(self, token_addr: str, spender: str, amount_wei: int) -> Optional[str]:
        """
        Check allowance; if insufficient, send approve tx.
        Returns approve tx_hash if a tx was sent, else None.
        """
        if not self.can_sign:
            raise RuntimeError("Signing required for approve")
        c = self._erc20_contract(token_addr)
        current = c.functions.allowance(
            Web3.to_checksum_address(self.address),
            Web3.to_checksum_address(spender)
        ).call()
        if current >= amount_wei:
            return None
        # Send max approve
        MAX = 2**256 - 1
        tx = c.functions.approve(
            Web3.to_checksum_address(spender), MAX
        ).build_transaction({"from": self._account.address, "value": 0})
        tx_hash = self._sign_and_send(tx)
        self.wait_receipt(tx_hash)
        logger.info(f"[{self.chain}] Approved {token_addr[:8]} for {spender[:8]}: {tx_hash}")
        return tx_hash

    # ── AAVE V3 supply / withdraw ────────────────────────────
    def aave_deposit_native(self, amount_eth: float) -> str:
        """
        Deposit native token (ETH/AVAX/etc.) into Aave v3 via WETHGateway.
        Returns deposit tx_hash.
        """
        if not self.can_sign:
            raise RuntimeError("Signing required")

        gateway_addr = AAVE_WETH_GATEWAY.get(self.chain)
        pool_addr = AAVE_V3_POOL.get(self.chain)
        if not gateway_addr or not pool_addr:
            raise ValueError(f"Aave v3 not supported on {self.chain}")

        amount_wei = Web3.to_wei(amount_eth, "ether")
        gateway = self.w3.eth.contract(
            address=Web3.to_checksum_address(gateway_addr), abi=WETH_GATEWAY_ABI
        )
        tx = gateway.functions.depositETH(
            Web3.to_checksum_address(pool_addr),
            Web3.to_checksum_address(self._account.address),
            0  # referral code
        ).build_transaction({
            "from": self._account.address,
            "value": amount_wei,
        })
        tx_hash = self._sign_and_send(tx)
        logger.info(f"[{self.chain}] Aave depositETH {amount_eth} → {tx_hash}")
        return tx_hash

    def aave_withdraw_native(self, amount_eth: float) -> str:
        """
        Withdraw native token from Aave v3 via WETHGateway.
        amount_eth = 0 means withdraw all (uses aWETH balance).
        Returns withdraw tx_hash.
        """
        if not self.can_sign:
            raise RuntimeError("Signing required")

        gateway_addr = AAVE_WETH_GATEWAY.get(self.chain)
        pool_addr = AAVE_V3_POOL.get(self.chain)
        aweth_addr = AWETH_ADDRESS.get(self.chain)
        if not gateway_addr or not pool_addr or not aweth_addr:
            raise ValueError(f"Aave v3 withdrawal not supported on {self.chain}")

        # Determine amount
        if amount_eth <= 0:
            # withdraw all: use aWETH balance
            aweth = self.w3.eth.contract(address=Web3.to_checksum_address(aweth_addr), abi=AWETH_ABI)
            amount_wei = aweth.functions.balanceOf(Web3.to_checksum_address(self._account.address)).call()
        else:
            amount_wei = Web3.to_wei(amount_eth, "ether")

        # Approve gateway to spend aWETH
        self.ensure_allowance(aweth_addr, gateway_addr, amount_wei)

        gateway = self.w3.eth.contract(
            address=Web3.to_checksum_address(gateway_addr), abi=WETH_GATEWAY_ABI
        )
        tx = gateway.functions.withdrawETH(
            Web3.to_checksum_address(pool_addr),
            amount_wei,
            Web3.to_checksum_address(self._account.address),
        ).build_transaction({"from": self._account.address, "value": 0})
        tx_hash = self._sign_and_send(tx)
        logger.info(f"[{self.chain}] Aave withdrawETH {amount_eth} → {tx_hash}")
        return tx_hash

    def aave_deposit_token(self, token_addr: str, amount_human: float) -> str:
        """Deposit an ERC-20 token into Aave v3 Pool directly."""
        if not self.can_sign:
            raise RuntimeError("Signing required")

        pool_addr = AAVE_V3_POOL.get(self.chain)
        if not pool_addr:
            raise ValueError(f"Aave v3 not supported on {self.chain}")

        token = self._erc20_contract(token_addr)
        dec = token.functions.decimals().call()
        amount_wei = int(amount_human * 10**dec)

        self.ensure_allowance(token_addr, pool_addr, amount_wei)

        pool = self.w3.eth.contract(
            address=Web3.to_checksum_address(pool_addr), abi=AAVE_POOL_ABI
        )
        tx = pool.functions.supply(
            Web3.to_checksum_address(token_addr),
            amount_wei,
            Web3.to_checksum_address(self._account.address),
            0
        ).build_transaction({"from": self._account.address, "value": 0})
        tx_hash = self._sign_and_send(tx)
        logger.info(f"[{self.chain}] Aave supply token {token_addr[:8]} {amount_human} → {tx_hash}")
        return tx_hash

    # ── generic ETH transfer (for non-Aave protocols) ────────
    def send_native(self, to: str, amount_eth: float) -> str:
        """Send native token to any address."""
        if not self.can_sign:
            raise RuntimeError("Signing required")
        amount_wei = Web3.to_wei(amount_eth, "ether")
        tx = {
            "to": Web3.to_checksum_address(to),
            "value": amount_wei,
            "data": b"",
        }
        return self._sign_and_send(tx)


# ─────────────────────────────────────────────────────────────
# SESSION STATE HELPERS
# ─────────────────────────────────────────────────────────────
def init_wallets(session_state) -> None:
    if "wallets" not in session_state:
        session_state.wallets = {chain: RealWallet(chain) for chain in RPC_URLS}
        # Auto-connect any hot wallets
        for w in session_state.wallets.values():
            w.auto_connect()
    if "positions" not in session_state:
        session_state.positions = []


def get_all_wallets(session_state) -> List[RealWallet]:
    return list(session_state.wallets.values())


def get_connected_wallet(session_state, chain: Optional[str] = None) -> Optional[RealWallet]:
    if chain:
        w = session_state.wallets.get(chain.lower())
        return w if w and w.connected else None
    for w in get_all_wallets(session_state):
        if w.connected:
            return w
    return None


def update_position_values(session_state) -> None:
    """Compound-accrue position values based on APY + elapsed time."""
    now = datetime.utcnow()
    for pos in session_state.get("positions", []):
        if pos.status != "active":
            continue
        delta = (now - pos.entry_date).total_seconds()
        years = delta / (365.25 * 86400)
        pos.current_value = pos.amount_invested * (1 + pos.apy / 100 * years)


def create_position(
    amount: float,
    opportunity_name: str,
    chain: str,
    apy: float,
    tx_hash: str,
    protocol: str = "unknown",
    asset_address: Optional[str] = None,
) -> dict:
    if amount <= 0:
        return {"success": False, "error": "Amount must be > 0"}
    pos = Position(
        id=f"pos_{uuid4().hex[:8]}",
        opportunity_name=opportunity_name,
        chain=chain.lower(),
        amount_invested=float(amount),
        current_value=float(amount),
        apy=float(apy),
        entry_date=datetime.utcnow(),
        status="active",
        tx_hash=tx_hash,
        protocol=protocol,
        asset_address=asset_address,
    )
    return {"success": True, "position": pos}


def add_position_to_session(session_state, position: Position) -> None:
    if "positions" not in session_state:
        session_state.positions = []
    session_state.positions.append(position)


def close_position(session_state, position_id: str, tx_hash: Optional[str] = None) -> dict:
    pos = next((p for p in session_state.positions if p.id == position_id), None)
    if not pos:
        return {"success": False, "error": "Position not found"}
    if pos.status != "active":
        return {"success": False, "error": "Position is not active"}
    pos.status = "closed"
    pos.close_tx_hash = tx_hash
    pnl = pos.current_value - pos.amount_invested
    return {
        "success": True,
        "amount_returned": pos.current_value,
        "pnl": pnl,
        "tx_hash": tx_hash,
    }