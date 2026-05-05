import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path


STATE_PATH = Path(__file__).parent.parent / "state.json"

DEFAULT_STATE = {
    "last_run": None,
    "total_runs": 0,
    "cumulative_stats": {
        "total_processed": 0,
        "total_archived": 0,
        "total_urgent": 0,
    },
}


class StateManager:
    """Reads and writes state.json to persist run history across executions.

    last_run is only updated on successful completion of the full pipeline.
    A run that crashes mid-pipeline leaves last_run unchanged, ensuring
    the next run reprocesses any emails that were not fully handled.
    """

    def __init__(self, state_path=STATE_PATH):
        self._path = state_path
        self.state = self._load()

    def _load(self):
        if not self._path.exists():
            return deepcopy(DEFAULT_STATE)

        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save(self):
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)

    @property
    def last_run(self):
        """Returns the last successful run time as a timezone-aware datetime, or None."""
        value = self.state.get("last_run")
        if value is None:
            return None
        return datetime.fromisoformat(value)

    @property
    def total_runs(self):
        return self.state.get("total_runs", 0)

    @property
    def cumulative_stats(self):
        return self.state.get("cumulative_stats", {})

    def mark_complete(self, run_stats):
        """Records a successful run. Call this only after the full pipeline finishes.

        run_stats should be a dict with keys: processed, archived, urgent.
        """
        self.state["last_run"] = datetime.now(timezone.utc).isoformat()
        self.state["total_runs"] = self.total_runs + 1

        cumulative = self.state.setdefault("cumulative_stats", {})
        cumulative["total_processed"] = (
            cumulative.get("total_processed", 0) + run_stats.get("processed", 0)
        )
        cumulative["total_archived"] = (
            cumulative.get("total_archived", 0) + run_stats.get("archived", 0)
        )
        cumulative["total_urgent"] = (
            cumulative.get("total_urgent", 0) + run_stats.get("urgent", 0)
        )

        self._save()