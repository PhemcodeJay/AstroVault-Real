import os
import random
import time
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional, List
from web3 import Web3
from web3.exceptions import Web3Exception
from dotenv import load_dotenv
import uuid

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Load Environment Variables ---
load_dotenv()

# --- Config (override via environment vars) ---
INFURA_API_KEY = os.getenv("INFURA_API_KEY")
if not INFURA_API_KEY:
    raise ValueError("INFURA_API_KEY environment variable is required for Ethereum")

RPC_URLS = {
    "ethereum": os.getenv("ETH_RPC_URL", f"https://mainnet.infura.io/v3/{INFURA_API_KEY}"),
    "bsc": os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org/"),
    "arbitrum": os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc"),
    "optimism": os.getenv("OPTIMISM_RPC_URL", "https://mainnet.optimism.io"),
    "base": os.getenv("BASE_RPC_URL", "https://mainnet.base.org"),
    "avalanche": os.getenv("AVALANCHE_RPC_URL", "https://api.avax.network/ext/bc/C/rpc"), 
    "solana": os.getenv("SOLANA_EVM_RPC_URL", "https://neon-proxy-mainnet.solana.p2p.org"),  # Neon EVM
    
}

CHAIN_IDS = {
    "ethereum": 1,
    "bsc": 56,
    "arbitrum": 42161,
    "optimism": 10,
    "base": 8453,
    "avalanche": 43114,
    "solana": 245022934,  
}

BALANCE_SYMBOLS = {
    "ethereum": "ETH",
    "bsc": "BNB",
    "arbitrum": "ETH",
    "optimism": "ETH",
    "base": "ETH",
    "avalanche": "AVAX",
    "solana": "NEON",
}

NETWORK_NAMES = {
    "ethereum": "Ethereum",
    "bsc": "BSC",
    "arbitrum": "Arbitrum",
    "optimism": "Optimism",
    "base": "Base",
    "avalanche": "Avalanche",
    "solana": "Solana (Neon)",
}

WALLET_ICONS = {
    "evm": "🦊",
}

@dataclass
class Position:
    """Represents an open DeFi position."""
    id: str
    opportunity_name: str
    chain: str
    amount_invested: float
    current_value: float
    apy: float
    entry_date: datetime
    status: str
    tx_hash: Optional[str] = None

class RealWallet:
    """Wallet helper for Streamlit with read capabilities for EVM chains."""

    def __init__(self, wallet_type: str, chain: str):
        self.wallet_type = wallet_type.lower()
        if self.wallet_type != "evm":
            raise ValueError(f"Unsupported wallet type: {self.wallet_type}. Only EVM is supported.")
        self.chain = chain.lower()
        self.connected = False
        self.address = ""
        self.balance = 0.0
        self.chain_id = CHAIN_IDS.get(self.chain)
        self.network_name = NETWORK_NAMES.get(self.chain, self.chain.capitalize())
        self.rpc_url = RPC_URLS.get(self.chain)
        self.web3 = Web3(Web3.HTTPProvider(self.rpc_url)) if self.rpc_url else None
        
        logger.info(f"Initialized wallet: {self.network_name} (EVM)")

    def connect(self, address: str) -> bool:
        if not address:
            raise ValueError("Address is required to connect")
        if self.web3 is None:
            raise ValueError(f"Web3 not initialized for chain: {self.chain}")

        address = address.strip()
        self.address = address
        logger.info(f"Connecting wallet: {self.network_name} address {self.address}")

        try:
            for attempt in range(3):
                try:
                    if not self.web3.is_connected():
                        raise Web3Exception(f"EVM RPC connection failed for {self.network_name}")
                    break
                except Web3Exception as e:
                    logger.warning(f"EVM connection retry {attempt + 1}/3 failed: {e}")
                    if attempt == 2:
                        raise Web3Exception(f"EVM RPC connection failed after retries: {e}")
                    time.sleep(2)

            if not self.web3.is_address(self.address):
                raise ValueError(f"Invalid address for {self.network_name}")

            checksum_address = self.web3.to_checksum_address(self.address)
            wei = self.web3.eth.get_balance(checksum_address)
            self.balance = float(self.web3.from_wei(wei, "ether"))

            fetched_chain_id = self.web3.eth.chain_id
            if fetched_chain_id != self.chain_id:
                raise ValueError(f"RPC chain ID mismatch: expected {self.chain_id}, got {fetched_chain_id}")

            self.connected = True
            logger.info(f"Wallet connected: {self.network_name} balance {self.balance} {self.get_balance_symbol()}")
            return True

        except Exception as e:
            self.disconnect()
            logger.error(f"Wallet connection failed: {str(e)}")
            raise RuntimeError(f"Wallet connection failed: {str(e)}")

    def disconnect(self):
        self.connected = False
        self.address = ""
        self.balance = 0.0
        logger.info(f"Wallet disconnected: {self.network_name}")

    def get_balance_symbol(self) -> str:
        return BALANCE_SYMBOLS.get(self.chain, "TOKEN")

    def get_wallet_icon(self) -> str:
        return WALLET_ICONS.get(self.wallet_type, "💳")

def init_wallets(session_state) -> None:
    try:
        if "wallets" not in session_state:
            session_state.wallets = {
                chain: RealWallet("evm", chain)
                for chain in RPC_URLS
            }

        if "positions" not in session_state:
            session_state.positions = []

        logger.info("Initialized wallets in session_state")
    except Exception as e:
        logger.error(f"Failed to initialize wallets: {str(e)}")
        raise RuntimeError(f"Wallet initialization failed: {str(e)}")

def get_all_wallets(session_state) -> List[RealWallet]:
    try:
        return list(session_state.wallets.values())
    except AttributeError:
        logger.error("Session state does not contain wallets")
        return []

def get_connected_wallet(session_state, chain: Optional[str] = None) -> Optional[RealWallet]:
    try:
        if chain:
            wallet = session_state.wallets.get(chain.lower())
            if wallet and wallet.connected:
                return wallet
        for wallet in get_all_wallets(session_state):
            if wallet.connected:
                return wallet
        return None
    except AttributeError:
        logger.error("Session state does not contain wallets")
        return None

def create_position(amount: float, opportunity_name: str, chain: str, apy: float, tx_hash: str) -> Dict:
    """Create a position with tx_hash from client-side transaction."""
    try:
        if amount <= 0:
            return {"success": False, "error": "Invalid amount: must be greater than 0"}
        position_id = f"pos_{uuid.uuid4()}"
        position = Position(
            id=position_id,
            opportunity_name=opportunity_name,
            chain=chain.lower(),
            amount_invested=float(amount),
            current_value=float(amount),
            apy=float(apy),
            entry_date=datetime.now(),
            status="active",
            tx_hash=tx_hash
        )
        logger.info(f"Created position: {position_id} on {chain} with tx {tx_hash}")
        return {"success": True, "position_id": position_id, "position": position, "message": "Position created successfully"}
    except Exception as e:
        logger.error(f"Create position failed: {str(e)}")
        return {"success": False, "error": str(e)}

def add_position_to_session(session_state, position: Position) -> None:
    try:
        if "positions" not in session_state:
            session_state.positions = []
        session_state.positions.append(position)
        logger.info(f"Added position to session: {position.id}")
    except Exception as e:
        logger.error(f"Failed to add position to session: {str(e)}")
        raise RuntimeError(f"Add position failed: {str(e)}")

def update_position_values(session_state) -> None:
    try:
        if "positions" not in session_state:
            return

        current_time = datetime.now()
        for position in session_state.positions:
            if position.status != "active":
                continue
            delta = current_time - position.entry_date
            days = delta.days + delta.seconds / 86400.0
            daily_rate = (position.apy / 100.0) / 365.0
            growth_factor = (1.0 + daily_rate) ** days
            rnd = random.uniform(0.98, 1.02)
            position.current_value = position.amount_invested * growth_factor * rnd
        logger.info("Updated position values")
    except Exception as e:
        logger.error(f"Failed to update position values: {str(e)}")

def close_position(session_state, position_id: str, tx_hash: Optional[str] = None) -> Dict:
    """Close a position with optional tx_hash from client-side transaction."""
    try:
        if "positions" not in session_state:
            logger.error("Close position failed: No positions found")
            return {"success": False, "error": "No positions found"}

        pos = next((p for p in session_state.positions if p.id == position_id), None)
        if not pos:
            logger.error(f"Close position failed: Position {position_id} not found")
            return {"success": False, "error": f"Position {position_id} not found"}

        if pos.status != "active":
            logger.error(f"Close position failed: Position {position_id} is not active")
            return {"success": False, "error": f"Position {position_id} is not active"}

        pos.status = "closed"
        pos.tx_hash = tx_hash if tx_hash else pos.tx_hash
        pnl = pos.current_value - pos.amount_invested
        logger.info(f"Closed position {position_id} on {pos.chain}: Returned {pos.current_value} {BALANCE_SYMBOLS.get(pos.chain, 'TOKEN')} with tx {tx_hash}")
        return {
            "success": True,
            "tx_hash": tx_hash,
            "amount_returned": pos.current_value,
            "pnl": pnl,
            "message": "Position closed successfully"
        }
    except Exception as e:
        logger.error(f"Close position failed: {str(e)}")
        return {"success": False, "error": str(e)}