# AI-Powered Meeting-to-Action Assistant

A beginner-friendly Streamlit app that extracts a short summary, explicit decisions, action items, and missing action details from a pasted meeting transcript. It uses simple local text rules and does not need an API key or paid service.

## Run on Windows

1. Open a terminal in this project folder:

   ```powershell
   cd "$HOME\meeting-to-action-assistant"
   ```

2. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Install the app requirement:

   ```powershell
   python -m pip install -r requirements.txt
   ```

4. Start the app:

   ```powershell
   python -m streamlit run app.py
   ```

Streamlit will print a local URL, usually `http://localhost:8501`, to open in your browser.

## How the rules work

- The summary displays the first two transcript sentences; it does not paraphrase them.
- Explicit `Decision:` labels and affirmative `we/the team decided`, `agreed`, `approved`, or `voted` statements are listed as decisions.
- Explicit `Name will ...` commitments and `Action:` lines are listed as action items.
- Missing owners or deadlines are marked for clarification. Pronouns such as “we” are not treated as a specific owner.
- The rules are intentionally conservative. Review the output against the transcript, especially if meeting notes use different wording.
