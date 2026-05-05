import yaml
from pathlib import Path


CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


class ConfigError(Exception):
    pass


class ConfigManager:
    """Loads and validates config.yaml, and exposes its values to other modules.

    Instantiated once per run in main.py. If the config file is missing or
    malformed, raises ConfigError immediately so the pipeline never starts
    with bad configuration.
    """

    def __init__(self, config_path=CONFIG_PATH):
        self._path = config_path
        self.data = self._load()

    def _load(self):
        if not self._path.exists():
            raise ConfigError(f"Config file not found: {self._path}")

        with open(self._path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data:
            raise ConfigError("Config file is empty or contains no valid YAML")

        self._validate(data)
        return data

    def _validate(self, data):
        # Each tuple is a path of keys that must exist and hold a non-empty value.
        required_fields = [
            ("agent", "name"),
            ("agent", "run_hour"),
            ("accounts", "hub", "email"),
            ("output", "email_summary", "sender"),
            ("output", "email_summary", "recipients"),
            ("claude", "model"),
            ("claude", "batch_size"),
        ]

        for field_path in required_fields:
            node = data
            for key in field_path:
                if not isinstance(node, dict) or key not in node:
                    raise ConfigError(
                        f"Missing required config field: {'.'.join(str(k) for k in field_path)}"
                    )
                node = node[key]

            if node is None or node == "" or node == []:
                raise ConfigError(
                    f"Config field cannot be empty: {'.'.join(str(k) for k in field_path)}"
                )

    # --- Account ---

    @property
    def hub_email(self):
        return self.data["accounts"]["hub"]["email"]

    # --- Claude ---

    @property
    def claude_model(self):
        return self.data["claude"]["model"]

    @property
    def batch_size(self):
        return int(self.data["claude"]["batch_size"])

    @property
    def classify_body(self):
        return bool(self.data["claude"].get("classify_body", False))

    @property
    def claude_max_tokens(self):
        return int(self.data["claude"].get("max_tokens", 1000))

    # --- VIP rules ---

    @property
    def vip_emails(self):
        return self.data.get("vip_senders", {}).get("emails", [])

    @property
    def vip_domains(self):
        return self.data.get("vip_senders", {}).get("domains", [])

    @property
    def urgency_keywords(self):
        return self.data.get("urgency_keywords", [])

    @property
    def vip_topics(self):
        return self.data.get("vip_topics", [])

    # --- Labels ---

    @property
    def labels(self):
        return self.data.get("labels", {})

    # --- Brand routing ---

    @property
    def brand_routing(self):
        return self.data.get("brand_routing", [])

    # --- Output ---

    @property
    def email_recipients(self):
        return self.data["output"]["email_summary"]["recipients"]

    @property
    def email_sender(self):
        return self.data["output"]["email_summary"]["sender"]

    @property
    def email_summary_enabled(self):
        return bool(self.data["output"]["email_summary"].get("enabled", True))

    @property
    def html_report_enabled(self):
        return bool(self.data["output"]["html_report"].get("enabled", True))

    @property
    def html_auto_open(self):
        return bool(self.data["output"]["html_report"].get("auto_open", True))

    @property
    def report_save_path(self):
        return Path(self.data["output"]["html_report"].get("save_path", "reports/"))

    @property
    def keep_last_n_reports(self):
        return int(self.data["output"]["html_report"].get("keep_last_n", 7))

    # --- Agent ---

    @property
    def log_level(self):
        return self.data.get("agent", {}).get("log_level", "INFO")