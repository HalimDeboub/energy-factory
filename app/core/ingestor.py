from typing import List, Dict, Any
from app.core.base import BaseDataProvider
from app.database.database import EnergyDatabase
from app.config.config import CRITICAL_FIELDS

class UnifiedIngestor:
    """
    A loosely coupled ingestion engine that can synchronize any DataProvider
    with the central SQLite database.
    """

    def __init__(self):
        self.db = EnergyDatabase()

    def sync_provider(self, provider: BaseDataProvider):
        """
        Extracts data from the provider and persists it using a standardized schema.
        """
        if not provider.is_persistent:
            print(f" [Ingestor] Skipping sync for {provider.provider_name} (Persistence Disabled)")
            return 0

        print(f" [Ingestor] Syncing: {provider.provider_name} (Company: {provider.company_id})...")
        
        try:
            # 1. Fetch raw data
            raw_records = provider.fetch_raw_data()
            if not raw_records:
                print(f" [Ingestor] No new data from {provider.provider_name}")
                return 0

            # 2. Get the schema mapping
            mapping = provider.get_schema_mapping()
            
            # 3. Canonicalize the records
            canonical_records = []
            for raw in raw_records:
                canonical = raw.copy()
                for ext_field, int_field in mapping.items():
                    if ext_field in raw:
                        canonical[int_field] = raw[ext_field]
                canonical_records.append(canonical)

            # 4. Save to the database using source_id and company_id
            source_id = provider.provider_name.lower().replace(" ", "_")
            new_count = self.db.store_records(canonical_records, source_id=source_id, company_id=provider.company_id)
            
            if new_count > 0:
                print(f" [Ingestor] Persisted {new_count} new records for {provider.provider_name}")
            return new_count

        except Exception as e:
            print(f" [Ingestor] Failed to sync {provider.provider_name}: {str(e)}")
            return 0

    def sync_all(self, providers: List[BaseDataProvider]):
        """Runs synchronization for a list of providers."""
        total_new = 0
        for provider in providers:
            total_new += self.sync_provider(provider)
        return total_new
