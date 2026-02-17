# gas-fees.py
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GAS_API_URL = os.getenv("ETH_GAS_URL", "https://mainnet.infura.io/v3/" + os.getenv("INFURA_API_KEY", ""))


# Simple ETH price fetcher (using CoinGecko API)
def get_eth_price_usd():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": "ethereum", "vs_currencies": "usd"}
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        return data["ethereum"]["usd"]
    except Exception as e:
        print("⚠️ Failed to fetch ETH price:", e)
        return None

def get_gas_fees():
    headers = {"Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "eth_gasPrice",
        "params": []
    }

    try:
        response = requests.post(GAS_API_URL, json=payload, headers=headers, timeout=5)
        response.raise_for_status()
        result = response.json()

        if "result" in result:
            wei = int(result["result"], 16)
            gwei = wei / 10**9
            eth = wei / 10**18

            eth_price_usd = get_eth_price_usd()
            if eth_price_usd:
                usd = eth * eth_price_usd
                print(f"⛽ Current Gas Price:")
                print(f"   • {gwei:.2f} Gwei")
                print(f"   • {eth:.8f} ETH")
                print(f"   • ${usd:.8f} USD (approx)")
            else:
                print(f"⛽ Gas Price: {gwei:.2f} Gwei | {eth:.8f} ETH")
        else:
            print("❌ Error:", result)
    except Exception as e:
        print("⚠️ Failed to fetch gas fees:", e)

if __name__ == "__main__":
    get_gas_fees()