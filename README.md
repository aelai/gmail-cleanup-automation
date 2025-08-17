# Gmail Cleanup Automation

This project provides a starting point for automating the cleanup of your
Gmail inbox.  It combines an n8n workflow, a set of declarative cleanup
rules, and an optional email classifier powered by a local large
language model (LLM) served by [Ollama](https://ollama.com/).  The goal
is to help you regularly delete or archive unimportant messages while
flagging potentially important ones for review.

## Features

- **Scheduled cleanup** — The n8n workflow runs every two months (on
  the first day) by default.  You can adjust the cron expression in
  the `Schedule Cleanup` node of the workflow.
- **Contact-aware rules** — The workflow fetches your Google Contacts
  via the People API and makes them available for custom logic.  This
  allows you to avoid deleting messages from people you know.
- **Declarative rules** — Cleanup criteria are defined in
  `rules/cleanup_rules.yaml`.  Each rule contains a Gmail search
  query, an action (`delete` or `review`), and an optional label to
  apply.  The queries use the same syntax as Gmail’s advanced search.
- **Local LLM classification** — When static rules are insufficient,
  the workflow can call a local LLM via Ollama to classify ambiguous
  emails.  A helper script (`scripts/classify_with_llm.py`) is
  provided for testing and integration.
- **Test mode** — Before deleting anything, you can run the workflow
  in test mode where messages are merely labeled (e.g. `NeedsReview`)
  instead of deleted.  Review the labels and adjust rules before
  turning on deletions.

## Prerequisites

- **n8n** — A self‑hosted n8n instance running in Docker on your
  machine.  Follow the [n8n installation guide](https://docs.n8n.io/hosting/self-hosted/docker/) if you haven’t already.
- **Google Cloud project** with the Gmail API and People API enabled.
  Create OAuth credentials and ensure you have consent to access your
  Gmail and contacts.  This project uses OAuth2 credentials rather
  than service accounts.
- **Gmail labels** — Create labels referenced in your rules (e.g.
  `NeedsReview`, `LargeAttachment`) ahead of time in Gmail.
- **Python 3.8+** (optional) and the `requests` library if you plan to
  use the provided classification script.

## Setup

1. **Clone this repository**

   ```sh
   git clone https://github.com/your-username/gmail-cleanup-automation.git
   cd gmail-cleanup-automation
   ```

2. **Configure environment variables**

   Copy the example configuration file and fill in your credentials:

   ```sh
   cp .env.example .env
   # Edit .env with your editor of choice and set your client IDs, secrets, etc.
   ```

   - `GMAIL_CLIENT_ID`, `GMAIL_CLIENT_SECRET` and `GMAIL_REFRESH_TOKEN`
     authenticate the Gmail and People nodes.  See the [Gmail
     documentation](https://developers.google.com/gmail/api/quickstart/python) for guidance on obtaining these.
   - `GOOGLE_PEOPLE_API_KEY` can be left blank if you authenticate via
     OAuth2.  Some users prefer to provide an API key for the People
     API.
   - `OLLAMA_ENDPOINT` and `OLLAMA_MODEL` point to your local
     Ollama server and model.  The defaults assume Ollama is
     accessible at `http://localhost:11434` and the model name is
     `llama3`.  Adjust these as needed.
   - `OPENAI_API_KEY` is optional.  If provided, the classifier will
     fall back to OpenAI’s API when your local model is unavailable.

3. **Import the n8n workflow**

   In the n8n editor UI:

   - Click “Workflows” → “Import from File”.
   - Select `n8n/gmail_cleanup_v1.json` from this repository.
   - n8n will prompt you to provide credentials for the Gmail and
     Google People nodes.  Use the OAuth2 credentials referenced in
     your `.env` file.  After importing, open the `Fetch Contacts` and
     Gmail nodes and select the appropriate credentials.

4. **Review and edit rules**

   The default cleanup criteria live in `rules/cleanup_rules.yaml`.
   Each rule has a human‑readable name, a Gmail query, and an action.
   You can edit this file to suit your inbox habits.  For example,
   change `older_than:30d` to a different time period or add new
   rules for newsletters and bulk senders.

5. **Test mode**

   Before permanently deleting messages, run the workflow in test
   mode.  To do this, leave the `Delete Promotions` and other delete
   nodes disabled or set their actions to apply labels instead of
   deleting.  Inspect your Gmail labels (`NeedsReview`, etc.) to
   confirm that the automation is working as expected.  Once
   satisfied, enable the delete nodes.

6. **Optional: Enable LLM classification**

   The provided script `scripts/classify_with_llm.py` demonstrates
   calling a local LLM via Ollama to classify ambiguous emails.  To
   test it manually:

   ```sh
   python3 scripts/classify_with_llm.py --sender alice@example.com \
       --subject "Your receipt" --body "Thank you for your purchase"
   ```

   To integrate classification into n8n, add an HTTP Request node
   after extracting sender/subject data from an email and map the
   result to determine whether to delete, label, or keep the message.

## Caveats and further work

- **Loops and dynamic rules** — The provided workflow demonstrates two
  example rules (promotions deletion and unread review).  n8n does
  not natively loop through an arbitrary list of queries, so to add
  additional rules you need to duplicate the search and action nodes
  in the workflow.  For more complex scenarios consider using the
  [Execute Command](https://docs.n8n.io/nodes/executeCommand/) node to
  run a Python script that reads `rules/cleanup_rules.yaml` and calls
  the Gmail API directly.
- **Contact matching** — Currently the workflow fetches a list of
  emails from your contacts but does not yet use that list in any
  rule.  You can extend the Function node or add an IF node to
  compare the sender of each message against this list to prevent
  deleting messages from known contacts.
- **Logging** — For visibility into what the workflow does, you may
  want to add nodes that write to a Google Sheet, send yourself a
  summary email, or log to a file.  n8n provides nodes for these
  services.

Feel free to modify, extend, and share this workflow to suit your
personal email management needs.
