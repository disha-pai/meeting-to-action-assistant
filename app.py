"""A beginner-friendly, rules-based meeting notes assistant."""

import re

import streamlit as st


# Users can load this example into the text box to try the app immediately.
SAMPLE_TRANSCRIPT = """Maya: We agreed to launch the pilot with the support team next month.
Jordan will send the revised budget by Friday.
Priya will share the onboarding checklist.
We decided to review the pilot results after two weeks.
"""


def split_sentences(transcript: str) -> list[str]:
    """Split transcript text into simple sentence-sized pieces."""
    pieces = re.split(r"(?<=[.!?])\s+|\n+", transcript)
    return [piece.strip(" \t-*\u2022") for piece in pieces if piece.strip(" \t-*\u2022")]


def find_deadline(text: str) -> str | None:
    """Return a deadline only when the transcript states one explicitly."""
    deadline_pattern = re.compile(
        r"\b(?:by|before|due(?:\s+on)?)\s+"
        r"((?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)"
        r"(?:\s+(?:morning|afternoon|evening))?|"
        r"today|tomorrow|tonight|EOD|end of day|next week|next month|"
        r"\d{1,2}(?:st|nd|rd|th)?\s+"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"(?:\s+\d{4})?|"
        r"(?:January|February|March|April|May|June|July|August|September|October|November|December)"
        r"\s+\d{1,2}(?:st|nd|rd|th)?(?:,?\s+\d{4})?)\b",
        re.IGNORECASE,
    )
    match = deadline_pattern.search(text)
    return match.group(1).strip() if match else None


def extract_action(sentence: str) -> dict[str, str | None] | None:
    """Find one explicitly labeled action or a person's explicit 'will' commitment."""
    action_label = re.search(r"\bAction\s*:\s*(.+)", sentence, re.IGNORECASE)
    if action_label:
        details = action_label.group(1)
        task = re.split(r"\s*[;|]\s*(?:Owner|Responsible|Deadline|Due)\s*:", details, maxsplit=1, flags=re.IGNORECASE)[0]
        owner_match = re.search(
            r"\b(?:Owner|Responsible)\s*:\s*([^;|]+)", details, re.IGNORECASE
        )
        deadline_match = re.search(
            r"\b(?:Deadline|Due)\s*:\s*([^;|]+)", details, re.IGNORECASE
        )
        owner = owner_match.group(1).strip().rstrip(".") if owner_match else None
        deadline = deadline_match.group(1).strip().rstrip(".") if deadline_match else find_deadline(details)
        return {
            "task": task.strip().rstrip("."),
            "owner": owner or None,
            "deadline": deadline,
        }

    commitment = re.search(
        r"\b(?P<owner>I|we|they|he|she|[A-Z][A-Za-z'-]*(?:\s+[A-Z][A-Za-z'-]*){0,2})"
        r"\s+will\s+(?P<task>[^.!?;]+)",
        sentence,
        re.IGNORECASE,
    )
    if commitment:
        stated_owner = commitment.group("owner")
        # Pronouns do not identify a specific person, so leave ownership unresolved.
        owner = None if stated_owner.lower() in {"i", "we", "they", "he", "she"} else stated_owner
        task = commitment.group("task").strip().rstrip(",")
        return {"task": task, "owner": owner, "deadline": find_deadline(sentence)}

    # A commitment without a stated subject is still useful to surface for clarification.
    subjectless_commitment = re.search(r"\bwill\s+(?P<task>[^.!?;]+)", sentence, re.IGNORECASE)
    if subjectless_commitment:
        task = subjectless_commitment.group("task").strip().rstrip(",")
        return {"task": task, "owner": None, "deadline": find_deadline(sentence)}

    return None


def analyze_transcript(transcript: str) -> dict[str, list]:
    """Extract notes using visible, conservative text rules; do not generate new facts."""
    sentences = split_sentences(transcript)
    summary = sentences[:2]

    decisions = []
    actions = []
    seen_actions = set()

    for sentence in sentences:
        explicit_decision = re.search(
            r"\bdecision(?:s)?\s*:|\b(?:we|the team|team)\s+"
            r"(?:have\s+)?(?:decided|agreed|approved|voted)\b",
            sentence,
            re.IGNORECASE,
        )
        if explicit_decision:
            decisions.append(sentence)

        action = extract_action(sentence)
        if action and action["task"]:
            action_key = (action["task"].lower(), action["owner"], action["deadline"])
            if action_key not in seen_actions:
                actions.append(action)
                seen_actions.add(action_key)

    clarifications = []
    for action in actions:
        if not action["owner"]:
            clarifications.append(f"Owner not clearly stated for: {action['task']}")
        if not action["deadline"]:
            clarifications.append(f"Deadline not clearly stated for: {action['task']}")

    return {
        "summary": summary,
        "decisions": decisions,
        "actions": actions,
        "clarifications": clarifications,
    }


def show_results(results: dict[str, list]) -> None:
    """Display each extracted category, including empty-result messages."""
    st.subheader("Meeting summary")
    if results["summary"]:
        for sentence in results["summary"]:
            st.write(sentence)
    else:
        st.write("No summary could be created from the provided text.")

    st.subheader("Decisions made")
    if results["decisions"]:
        for decision in results["decisions"]:
            st.markdown(f"- {decision}")
    else:
        st.write("No explicit decisions found.")

    st.subheader("Action items")
    if results["actions"]:
        for action in results["actions"]:
            owner = action["owner"] or "Not stated"
            deadline = action["deadline"] or "Not stated"
            st.markdown(f"- **Task:** {action['task']}  \n  **Responsible:** {owner}  \n  **Deadline:** {deadline}")
    else:
        st.write("No explicit action items found.")

    st.subheader("Needs clarification")
    if results["clarifications"]:
        for item in results["clarifications"]:
            st.markdown(f"- {item}")
    else:
        st.write("No missing action owners or deadlines detected.")


def main() -> None:
    """Build the Streamlit page and handle the user's request."""
    st.set_page_config(page_title="Meeting-to-Action Assistant", page_icon="📝", layout="centered")
    st.title("AI-Powered Meeting-to-Action Assistant")
    st.caption("A free, rules-based first version. It uses only the text you provide and does not call an AI service.")

    with st.expander("Try the sample transcript"):
        st.write(SAMPLE_TRANSCRIPT)
        if st.button("Load sample transcript"):
            st.session_state["transcript"] = SAMPLE_TRANSCRIPT

    transcript = st.text_area(
        "Paste a meeting transcript",
        key="transcript",
        height=260,
        placeholder="Paste meeting notes or a transcript here...",
    )

    if st.button("Generate meeting notes", type="primary"):
        if not transcript.strip():
            st.warning("Please paste a meeting transcript before generating notes.")
        else:
            show_results(analyze_transcript(transcript))


if __name__ == "__main__":
    main()
