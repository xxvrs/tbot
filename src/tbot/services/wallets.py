from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional
import secrets

from ..models import DepositAddress, Wallet


@dataclass(slots=True)
class WalletConfig:
    default_chain: str = "ethereum"
    custody_mode: str = "custodial"  # or "non-custodial"


class WalletManager:
    """Provision and track wallets for Telegram users."""

    def __init__(self, config: WalletConfig | None = None) -> None:
        self._config = config or WalletConfig()
        self._wallets: Dict[str, Wallet] = {}
        self._user_wallets: Dict[int, List[str]] = {}

    def create_wallet(self, user_id: int, chain: Optional[str] = None) -> Wallet:
        chain_name = chain or self._config.default_chain
        wallet_id = secrets.token_hex(8)
        address = self._generate_address(chain_name)
        wallet = Wallet(
            wallet_id=wallet_id,
            owner_id=user_id,
            chain=chain_name,
            address=address,
            is_custodial=self._config.custody_mode == "custodial",
        )
        self._wallets[wallet_id] = wallet
        self._user_wallets.setdefault(user_id, []).append(wallet_id)
        return wallet

    def connect_external_wallet(self, user_id: int, address: str, chain: str) -> Wallet:
        wallet_id = secrets.token_hex(8)
        wallet = Wallet(
            wallet_id=wallet_id,
            owner_id=user_id,
            chain=chain,
            address=address,
            is_custodial=False,
        )
        self._wallets[wallet_id] = wallet
        self._user_wallets.setdefault(user_id, []).append(wallet_id)
        return wallet

    def list_wallets(self, user_id: int) -> List[Wallet]:
        wallet_ids = self._user_wallets.get(user_id, [])
        return [self._wallets[wallet_id] for wallet_id in wallet_ids]

    def get_wallet(self, wallet_id: str) -> Optional[Wallet]:
        return self._wallets.get(wallet_id)

    def deposit_address(self, wallet_id: str) -> Optional[DepositAddress]:
        wallet = self._wallets.get(wallet_id)
        if not wallet:
            return None
        return DepositAddress(wallet_id=wallet.wallet_id, chain=wallet.chain, address=wallet.address)

    def _generate_address(self, chain: str) -> str:
        prefix = {
            "ethereum": "0x",
            "solana": "So",
        }.get(chain, "0x")
        return prefix + secrets.token_hex(20)
