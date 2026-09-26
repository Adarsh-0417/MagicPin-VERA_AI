import json
from pathlib import Path

from app.context_store import ContextStore
from app.models import ContextPayload


class DatasetLoader:
    """
    Loads the expanded challenge dataset into ContextStore.

    Expected structure:

    dataset/expanded/
    ├── categories/
    ├── merchants/
    ├── customers/
    └── triggers/
    """

    def __init__(self, dataset_dir: str, store: ContextStore):
        self.dataset_dir = Path(dataset_dir)
        self.store = store

    def _load_json(self, path: Path) -> dict:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _load_directory(self, directory: Path) -> list[dict]:
        if not directory.exists():
            return []

        records = []

        for file_path in sorted(directory.glob("*.json")):
            records.append(self._load_json(file_path))

        return records

    def load_categories(self) -> int:
        directory = self.dataset_dir / "categories"
        records = self._load_directory(directory)

        loaded = 0

        for category in records:
            context = ContextPayload(
                scope="category",
                context_id=category["slug"],
                version=1,
                payload=category,
            )

            self.store.upsert(context)
            loaded += 1

        return loaded

    def load_merchants(self) -> int:
        directory = self.dataset_dir / "merchants"
        records = self._load_directory(directory)

        loaded = 0

        for merchant in records:
            context = ContextPayload(
                scope="merchant",
                context_id=merchant["merchant_id"],
                version=1,
                payload=merchant,
            )

            self.store.upsert(context)
            loaded += 1

        return loaded

    def load_customers(self) -> int:
        directory = self.dataset_dir / "customers"
        records = self._load_directory(directory)

        loaded = 0

        for customer in records:
            context = ContextPayload(
                scope="customer",
                context_id=customer["customer_id"],
                version=1,
                payload=customer,
            )

            self.store.upsert(context)
            loaded += 1

        return loaded

    def load_triggers(self) -> int:
        directory = self.dataset_dir / "triggers"
        records = self._load_directory(directory)

        loaded = 0

        for trigger in records:
            context = ContextPayload(
                scope="trigger",
                context_id=trigger["id"],
                version=1,
                payload=trigger,
            )

            self.store.upsert(context)
            loaded += 1

        return loaded

    def load_all(self) -> dict:
        """
        Load all four context types.

        Returns counts for observability.
        """

        categories = self.load_categories()
        merchants = self.load_merchants()
        customers = self.load_customers()
        triggers = self.load_triggers()

        return {
            "category": categories,
            "merchant": merchants,
            "customer": customers,
            "trigger": triggers,
            "total": (
                categories
                + merchants
                + customers
                + triggers
            ),
        }