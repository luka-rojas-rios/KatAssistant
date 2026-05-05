import logging
import sys
from pathlib import Path

from modules.config_manager import ConfigManager, ConfigError
from modules.state_manager import StateManager


def setup_logging(log_level):
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    level = getattr(logging, log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("logs/agent.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def run():
    # Config is loaded first. If it fails, there is nothing else to do.
    try:
        config = ConfigManager()
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        sys.exit(1)

    setup_logging(config.log_level)
    logger = logging.getLogger("main")

    state = StateManager()

    logger.info("Starting run — hub: %s — last run: %s",
                config.hub_email, state.last_run or "never")

    run_stats = {
        "processed": 0,
        "archived": 0,
        "urgent": 0,
    }

    try:
        # Phase 2: fetch emails received since state.last_run
        # emails = GmailReader(config).fetch_since(state.last_run)

        # Phase 3: classify the batch via Claude API
        # results = EmailClassifier(config).classify(emails)

        # Phase 4: apply Gmail labels and archive
        # run_stats = ActionExecutor(config).execute(emails, results)

        # Phase 5: generate HTML report and send email summary
        # ReportGenerator(config).generate(emails, results, run_stats)

        pass

    except Exception:
        logger.exception("Pipeline failed — last_run will not be updated")
        sys.exit(1)

    # Only reached if the full pipeline completed without error.
    state.mark_complete(run_stats)
    logger.info(
        "Run complete — processed: %d  archived: %d  urgent: %d",
        run_stats["processed"], run_stats["archived"], run_stats["urgent"],
    )


if __name__ == "__main__":
    run()
