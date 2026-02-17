# DeFi Opportunities Dashboard

## Overview

This is a Streamlit-based web application that serves as a comprehensive DeFi (Decentralized Finance) opportunities dashboard. The application scans and analyzes various DeFi protocols across multiple blockchain networks to identify high-yield investment opportunities and trending meme coins. It provides users with real-time data visualization, wallet connectivity simulation, and categorized investment recommendations based on risk levels and return rates.

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes (August 20, 2025)

### Major Architecture Upgrade - Production-Ready DeFi Dashboard
- **Multi-Chain Wallet Support**: Added SUI and TAO wallets alongside MetaMask and Phantom
- **Advanced Position Management**: Implemented full position lifecycle (enter, track, close positions)
- **Professional UI/UX**: Redesigned with modern CSS styling, gradients, and responsive design
- **Real-time P&L Tracking**: Position values update automatically with time-based APY calculations
- **Enhanced Data Visualization**: Added comprehensive charts, metrics, and interactive elements
- **Production Features**: Transaction simulation, portfolio summaries, position management tabs

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application framework for rapid prototyping and deployment
- **Visualization**: Plotly Express and Plotly Graph Objects for interactive charts and data visualization
- **Layout**: Wide layout with expandable sidebar for wallet management and filtering options
- **State Management**: Streamlit session state for maintaining wallet connections and user preferences

### Backend Architecture
- **Data Processing**: Pandas for data manipulation and analysis of DeFi opportunities
- **API Integration**: Direct HTTP requests using the requests library to fetch data from external DeFi APIs
- **Data Classification**: Custom algorithms to categorize yield opportunities by type, risk level, and blockchain network
- **Mock Services**: Simulated wallet functionality for demonstration purposes without requiring actual blockchain connections

### Core Components
1. **DeFi Scanner Module** (`defi_scanner.py`):
   - Fetches yield opportunities from DefiLlama and other DeFi data providers
   - Classifies opportunities by protocol type (Vaults, Lending/Borrowing, Yield Farming, Staking)
   - Filters based on configurable minimum APY, TVL, and liquidity thresholds
   - Supports multiple blockchain networks (Ethereum, Solana, BSC, Arbitrum, etc.)

2. **Wallet Management** (`wallet_utils.py`):
   - Mock wallet implementation for MetaMask and Phantom wallets
   - Simulates wallet connection, balance tracking, and transaction capabilities
   - Provides wallet state management across user sessions

3. **Dashboard Interface** (`app.py`):
   - Main application entry point with Streamlit configuration
   - Integrates wallet connectivity with DeFi opportunity display
   - Implements responsive design with sidebar navigation

### Data Architecture
- **In-Memory Processing**: All data processing occurs in memory using Pandas DataFrames
- **Real-Time Fetching**: Direct API calls to external services without local caching
- **Configuration-Driven**: Extensive use of configuration constants for easy customization of filtering criteria

### Design Patterns
- **Modular Design**: Clear separation between data fetching, wallet management, and UI components
- **Dataclass Usage**: Structured data representation for yield opportunities and meme coin entries
- **Mock Pattern**: Wallet utilities implement mock functionality for development and demonstration

## External Dependencies

### DeFi Data Providers
- **DefiLlama API**: Primary source for yield farming pools, TVL data, and protocol information
- **Multiple Blockchain Networks**: Ethereum, Solana, Binance Smart Chain, Arbitrum, Optimism, Base, Sui, and Tao

### Python Libraries
- **Streamlit**: Web application framework and UI components
- **Pandas**: Data manipulation and analysis
- **Plotly**: Interactive data visualization and charting
- **Requests**: HTTP client for API communications
- **FPDF**: PDF generation for reports (referenced in attached assets)

### Blockchain Integrations
- **Protocol Support**: Focuses on major DeFi protocols including Beefy, Yearn, Aave, Venus, Morpho, PancakeSwap, Raydium, Lido, Marinade, and EigenLayer
- **Wallet Compatibility**: Designed to support MetaMask (Ethereum) and Phantom (Solana) wallet connections
- **Layer 2 Networks**: Includes support for Arbitrum, Optimism, zkSync, Base, Scroll, and Linea

### Optional Services
- **Telegram Integration**: Framework exists for Telegram bot notifications (configured but not active)
- **PDF Reporting**: Capability for generating PDF reports of opportunities (referenced in supporting files)