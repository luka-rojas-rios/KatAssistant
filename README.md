# Kat Assistant

A local AI agent that reads, classifies, and summarises email from a central Gmail inbox using the Anthropic API. Runs on a schedule, applies Gmail labels, and delivers a daily digest of what needs attention.

---

## What this is

Managing email across multiple business accounts — each with its own domain, forwarding rules, and expected response time — is a context-switching problem that does not benefit from being solved manually. This agent runs once per day, fetches everything received since its last run, sends batches to Claude for classification, applies Gmail labels, and produces an HTML report and email summary.

The model is responsible for judgment. The code is responsible for plumbing.

This is a pipeline agent: the sequence of operations is fixed, and the model is called at one point in the pipeline to classify a batch of emails. There is no agentic loop in v1. That is an intentional scope decision, not a limitation — the architecture is designed to make the step to v2 (tool-calling loop) straightforward.

---

## Architecture

```
[launchd Scheduler]
        |
        v
[main.py -- Orchestrator]
        |
        |---> [ConfigManager]     loads config.yaml on every run
        |
        |---> [GmailReader]       fetches unread email via Gmail API (OAuth2)
        |
        |---> [EmailClassifier]   sends batches to Claude API for classification
        |
        |---> [ActionExecutor]    applies Gmail labels and archives
        |
        |---> [ReportGenerator]   builds HTML report and sends email summary
        |
        |---> [StateManager]      persists last_run timestamp and cumulative stats
```

### Pipeline

```
start
  -> load config
  -> fetch emails since last_run
  -> extract metadata (sender, subject, date, snippet)
  -> classify in batches via Claude API
  -> apply Gmail labels and archive
  -> generate HTML report
  -> send email summary
  -> update state (last_run, stats)
end
```

---

## Tech stack

| Layer        | Technology                      |
|--------------|---------------------------------|
| Language     | Python 3.11+                    |
| AI model     | Claude via Anthropic SDK        |
| Email access | Gmail API (google-api-python-client) |
| Templates    | Jinja2                          |
| Email send   | smtplib (Gmail SMTP)            |
| Scheduling   | macOS launchd                   |
| Config       | PyYAML                          |
| State        | JSON file                       |
| Logging      | Python logging (rotating file)  |

---

## Project structure

```
email-agent/
|
|-- main.py                    # Orchestrator and entry point
|-- config.yaml                # All user configuration
|-- state.json                 # Runtime state (gitignored)
|-- requirements.txt
|
|-- modules/
|   |-- config_manager.py
|   |-- gmail_reader.py
|   |-- email_classifier.py
|   |-- action_executor.py
|   |-- report_generator.py
|   `-- state_manager.py
|
|-- templates/
|   `-- report.html.j2
|
|-- credentials/               # Gitignored entirely
|   |-- gmail_credentials.json
|   `-- gmail_token.json
|
|-- reports/                   # Generated at runtime, gitignored
|-- logs/                      # Rotating log file, gitignored
`-- com.kat.emailagent.plist   # launchd schedule definition (macOS only)
```

---

## Setup

### Prerequisites

- Python 3.11 or later
- A Google Cloud project with the Gmail API enabled and OAuth2 credentials downloaded
- An Anthropic API key

### Installation

```bash
git clone git@github.com:yourusername/email-agent.git
cd email-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Credentials

Place your `gmail_credentials.json` (downloaded from Google Cloud Console) in the `credentials/` directory. This file is gitignored and should never be committed.

Set your Anthropic API key as an environment variable. On macOS, add this to `~/.zshrc`:

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

On Linux, add it to `~/.bashrc` or `~/.profile`.

### Gmail OAuth

The first time the agent runs, it will open a browser window to complete the OAuth2 flow. This must be done on the machine where the agent will run (macOS). The resulting `gmail_token.json` is saved to `credentials/` and auto-refreshes on subsequent runs.

### Configuration

Open `config.yaml` and set at minimum:

- `accounts.hub.email` — your central Gmail address
- `output.email_summary.recipients` — where the daily summary is sent
- `vip_senders.emails` — senders whose email is always flagged important

All other defaults are functional out of the box.

---

## Running

```bash
source .venv/bin/activate
python3 main.py
```

On macOS, the agent can also be scheduled via launchd (see `com.kat.emailagent.plist`).

---

## Development notes

This project is developed on Pop!_OS (Linux) and deployed on macOS. A few things follow from that.

The Gmail OAuth browser flow must be completed on the Mac. The resulting `gmail_token.json` is machine-local and gitignored. Do not attempt to copy it between machines.

`launchd` is macOS-specific. On Linux, run `python3 main.py` manually, or configure a cron job if you want scheduled execution during development.

The HTML report is opened automatically using `open` on macOS and `xdg-open` on Linux. The agent detects the platform and uses the appropriate command.

Python environments are maintained separately on each machine. Both use the same `requirements.txt` but have independent virtual environments.

The standard workflow across machines:

```bash
# On Pop OS after editing code
git add .
git commit -m "your message"
git push origin feature/your-branch

# On Mac before running
git pull origin feature/your-branch
python3 main.py
```

---

## Design decisions

**Why Claude for classification rather than rule-based logic?**

Rule-based approaches require you to enumerate every case explicitly. A language model handles novel senders, ambiguous subjects, and mixed-language content (Spanish and English in this case) without code changes. The tradeoff is API cost and non-determinism. Both are managed: cost by batching and classifying on metadata only (not full body), non-determinism by logging every classification with a confidence score so runs can be audited.

**Why classify on metadata only in v1?**

Sender, subject line, and a 200-character snippet are sufficient to correctly classify the large majority of email. Sending full message bodies to the API would increase cost and latency in proportion to inbox volume. Full body access is documented as an expansion point and can be enabled per-message for ambiguous cases in v2.

**Why a linear pipeline rather than an agentic loop?**

v1 has a fixed task with a known, invariant structure. An agentic loop — where the model decides which tools to call and in what order — adds meaningful complexity without benefit when the sequence of operations never changes. The step to v2 is specifically the point where classification results need to drive non-linear action: for example, drafting a reply for urgent emails before archiving them. The module boundaries are drawn to make that transition clean.

**Why launchd instead of a cron job?**

On macOS, launchd is the native job scheduler and handles missed runs correctly — if the machine was off at the scheduled time, the job runs once on next wake. Cron on macOS does not reliably handle this. The scheduling is intentionally kept outside the Python code so the agent itself has no awareness of time; it simply processes everything since `last_run` whenever it is invoked.

---

## Expanding the agent

Expansion points are marked with `# EXPANSION POINT` comments throughout the codebase. Planned v2 additions include Notion task creation from classified email, draft generation for urgent items, and an agentic tool-calling loop replacing the current linear classifier call.

---

## License

MIT. See [LICENSE](LICENSE).
