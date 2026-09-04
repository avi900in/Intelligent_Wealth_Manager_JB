"""
Wealth Management Intelligence Data Layer
Handles ingestion, caching, and relational querying across all 12 source files:
- clients.csv
- portfolios.csv
- holdings.csv
- instruments.csv
- mandates.csv
- credit_facilities.csv
- commitments.csv
- planned_cash_needs.csv
- market_context.csv
- event_log.csv
- transactions.csv
- rm_notes.json
"""

import os
import json
import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

@dataclass
class LookThroughDetail:
    instrument_id: str
    instrument_name: str
    is_structured: bool
    underlying_type: str  # 'single_equity', 'worst_of_basket', 'commodity', 'private_equity', 'accumulator', 'vanilla'
    underlying_references: List[str]
    raw_reference: str
    effective_asset_class: str
    effective_sector: str
    effective_region: str
    leverage_or_barrier_notes: str

class WealthDataRepository:
    _instance = None

    def __init__(self, data_dir: str = DATA_DIR):
        self.data_dir = data_dir
        self.clients_df: pd.DataFrame = pd.DataFrame()
        self.portfolios_df: pd.DataFrame = pd.DataFrame()
        self.holdings_df: pd.DataFrame = pd.DataFrame()
        self.instruments_df: pd.DataFrame = pd.DataFrame()
        self.mandates_df: pd.DataFrame = pd.DataFrame()
        self.credit_facilities_df: pd.DataFrame = pd.DataFrame()
        self.commitments_df: pd.DataFrame = pd.DataFrame()
        self.planned_cash_needs_df: pd.DataFrame = pd.DataFrame()
        self.market_context_df: pd.DataFrame = pd.DataFrame()
        self.event_log_df: pd.DataFrame = pd.DataFrame()
        self.transactions_df: pd.DataFrame = pd.DataFrame()
        self.rm_notes_data: List[Dict[str, Any]] = []
        self.look_through_map: Dict[str, LookThroughDetail] = {}
        
        self.load_all()

    @classmethod
    def get_instance(cls, data_dir: str = DATA_DIR) -> "WealthDataRepository":
        if cls._instance is None:
            cls._instance = cls(data_dir=data_dir)
        return cls._instance

    def load_all(self):
        """Loads all 12 dataset files from disk."""
        self.clients_df = pd.read_csv(os.path.join(self.data_dir, "clients.csv"))
        self.portfolios_df = pd.read_csv(os.path.join(self.data_dir, "portfolios.csv"))
        self.holdings_df = pd.read_csv(os.path.join(self.data_dir, "holdings.csv"))
        self.instruments_df = pd.read_csv(os.path.join(self.data_dir, "instruments.csv"))
        self.mandates_df = pd.read_csv(os.path.join(self.data_dir, "mandates.csv"))
        self.credit_facilities_df = pd.read_csv(os.path.join(self.data_dir, "credit_facilities.csv"))
        self.commitments_df = pd.read_csv(os.path.join(self.data_dir, "commitments.csv"))
        self.planned_cash_needs_df = pd.read_csv(os.path.join(self.data_dir, "planned_cash_needs.csv"))
        self.market_context_df = pd.read_csv(os.path.join(self.data_dir, "market_context.csv"))
        self.event_log_df = pd.read_csv(os.path.join(self.data_dir, "event_log.csv"))
        self.transactions_df = pd.read_csv(os.path.join(self.data_dir, "transactions.csv"))
        
        notes_path = os.path.join(self.data_dir, "rm_notes.json")
        if os.path.exists(notes_path):
            with open(notes_path, "r", encoding="utf-8") as f:
                self.rm_notes_data = json.load(f)

        self._build_look_through_index()

    def _build_look_through_index(self):
        """Builds structured product look-through unbundling mapping."""
        self.look_through_map = {}
        for _, row in self.instruments_df.iterrows():
            iid = str(row["instrument_id"])
            iname = str(row["instrument_name"])
            aclass = str(row["asset_class"])
            sub_aclass = str(row["sub_asset_class"])
            sector = str(row["sector"]) if pd.notna(row["sector"]) else "Diversified"
            region = str(row["region"]) if pd.notna(row["region"]) else "Global"
            ref = str(row["underlying_reference"]) if pd.notna(row["underlying_reference"]) else ""

            is_struct = bool(ref and ref.strip() and ref.lower() != "nan")
            u_type = "vanilla"
            u_refs = []
            notes = ""

            if is_struct:
                ref_lower = ref.lower()
                if "worst-of basket" in ref_lower:
                    u_type = "worst_of_basket"
                    if ":" in ref:
                        parts = ref.split(":", 1)[1].split(".")[0]
                        u_refs = [p.strip() for p in parts.split("/")]
                    else:
                        u_refs = [ref]
                    notes = "Worst-of barrier structure, look-through to individual equity names."
                elif "single underlying" in ref_lower or "underlying:" in ref_lower:
                    u_type = "single_equity" if ("cloud" in ref_lower or "inc" in ref_lower or "properties" in ref_lower) else "commodity"
                    u_refs = [ref]
                    notes = "Direct exposure to underlying asset price and volatility."
                elif "accumulation" in ref_lower:
                    u_type = "accumulator"
                    u_refs = ["Golden Harbour Properties"] if "golden harbour" in ref_lower else [ref]
                    notes = "Accumulator structure with daily leverage & knock-out barrier."
                elif "xau spot" in ref_lower:
                    u_type = "commodity"
                    u_refs = ["Gold (XAU) Spot Physical Vault"]
                    notes = "Physical gold allocated holding look-through."
                elif "series d" in ref_lower or "enterprise saas" in ref_lower:
                    u_type = "private_equity"
                    u_refs = ["Private SaaS AI Infrastructure"]
                    notes = "Unlisted venture/growth equity."
                else:
                    u_type = "structured_wrapper"
                    u_refs = [ref]
            else:
                u_refs = [iname]

            self.look_through_map[iid] = LookThroughDetail(
                instrument_id=iid,
                instrument_name=iname,
                is_structured=is_struct,
                underlying_type=u_type,
                underlying_references=u_refs,
                raw_reference=ref,
                effective_asset_class=aclass,
                effective_sector=sector,
                effective_region=region,
                leverage_or_barrier_notes=notes
            )

    # --- Query Methods ---
    def get_all_clients(self) -> List[Dict[str, Any]]:
        return self.clients_df.to_dict(orient="records")

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        rows = self.clients_df[self.clients_df["client_id"] == client_id]
        if rows.empty:
            return None
        return rows.iloc[0].to_dict()

    def get_portfolios_for_client(self, client_id: str) -> List[Dict[str, Any]]:
        rows = self.portfolios_df[self.portfolios_df["client_id"] == client_id]
        return rows.to_dict(orient="records")

    def get_portfolio(self, portfolio_id: str) -> Optional[Dict[str, Any]]:
        rows = self.portfolios_df[self.portfolios_df["portfolio_id"] == portfolio_id]
        if rows.empty:
            return None
        return rows.iloc[0].to_dict()

    def get_snapshot_dates(self) -> List[str]:
        dates = sorted(self.holdings_df["snapshot_date"].unique().tolist())
        return dates

    def get_holdings(self, portfolio_id: str, snapshot_date: str) -> List[Dict[str, Any]]:
        sub = self.holdings_df[
            (self.holdings_df["portfolio_id"] == portfolio_id) & 
            (self.holdings_df["snapshot_date"] == snapshot_date)
        ]
        return sub.to_dict(orient="records")

    def get_all_holdings_for_client(self, client_id: str, snapshot_date: str) -> List[Dict[str, Any]]:
        sub = self.holdings_df[
            (self.holdings_df["client_id"] == client_id) & 
            (self.holdings_df["snapshot_date"] == snapshot_date)
        ]
        return sub.to_dict(orient="records")

    def get_mandate_for_code(self, mandate_code: str) -> List[Dict[str, Any]]:
        sub = self.mandates_df[self.mandates_df["mandate_code"] == mandate_code]
        return sub.to_dict(orient="records")

    def get_credit_facilities_for_client(self, client_id: str) -> List[Dict[str, Any]]:
        sub = self.credit_facilities_df[self.credit_facilities_df["client_id"] == client_id]
        return sub.to_dict(orient="records")

    def get_commitments_for_client(self, client_id: str) -> List[Dict[str, Any]]:
        sub = self.commitments_df[self.commitments_df["client_id"] == client_id]
        return sub.to_dict(orient="records")

    def get_planned_cash_needs_for_client(self, client_id: str) -> List[Dict[str, Any]]:
        sub = self.planned_cash_needs_df[self.planned_cash_needs_df["client_id"] == client_id]
        return sub.to_dict(orient="records")

    def get_rm_notes_for_client(self, client_id: str) -> List[Dict[str, Any]]:
        return [n for n in self.rm_notes_data if n.get("client_id") == client_id]

    def get_transactions_for_portfolio(self, portfolio_id: str) -> List[Dict[str, Any]]:
        sub = self.transactions_df[self.transactions_df["portfolio_id"] == portfolio_id]
        return sub.to_dict(orient="records")

    def get_market_context(self, snapshot_date: Optional[str] = None) -> List[Dict[str, Any]]:
        if snapshot_date:
            sub = self.market_context_df[self.market_context_df["snapshot_date"] == snapshot_date]
            return sub.to_dict(orient="records")
        return self.market_context_df.to_dict(orient="records")

    def get_events(self) -> List[Dict[str, Any]]:
        return self.event_log_df.to_dict(orient="records")
