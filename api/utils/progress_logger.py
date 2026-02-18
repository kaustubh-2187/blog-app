"""
progress_logger.py

Translates internal pipeline stages into clean, human-readable
progress messages shown to the user in the live log box.

Usage (in blog.py):
    from api.utils.progress_logger import ProgressLogger
    progress = ProgressLogger(run_id, job_logs)
    progress.emit("routing")
"""

from datetime import datetime


# Maps an internal stage key → user-friendly message
STAGE_MESSAGES = {
    # ── Start
    "start":              "Starting up…",

    # ── Router
    "routing":            "Analysing your topic…",
    "route_research":     "Deciding to search the web for up-to-date information…",
    "route_no_research":  "Using built-in knowledge (no web search needed)…",

    # ── Research
    "research_start":     "Searching the web for relevant sources…",
    "research_done":      "Found sources — reviewing and filtering them…",

    # ── Orchestrator
    "planning":           "Building a detailed outline for your blog…",
    "planning_done":      "Outline ready — preparing to write the sections…",

    # ── Workers
    "writing_start":      "Writing the blog sections…",
    "writing_section":    "Writing section {current} of {total}…",   # formatted at call site
    "writing_done":       "All sections written — assembling the full post…",

    # ── Reducer / images
    "merging":            "Putting all sections together…",
    "images_planning":    "Deciding where images would be useful…",
    "images_generating":  "Generating images — this may take a moment…",
    "images_placing":     "Placing images into the blog…",
    "images_skip":        "No images requested — skipping image generation…",

    # ── Finish
    "saving":             "Saving your blog…",
    "done":               "Your blog is ready! 🎉",

    # ── Error
    "error":              "Something went wrong — please try again.",
}


class ProgressLogger:
    """
    Appends clean, user-facing progress lines to a shared job_logs list.
    Only this class should write to the list during generation.
    """

    def __init__(self, run_id: str, job_logs: dict):
        self.run_id = run_id
        self.job_logs = job_logs

    def _ts(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def emit(self, stage: str, **kwargs) -> None:
        """
        Emit a progress message for the given stage key.
        Optional kwargs are used for format placeholders (e.g. current, total).
        """
        template = STAGE_MESSAGES.get(stage, stage)
        try:
            message = template.format(**kwargs) if kwargs else template
        except KeyError:
            message = template

        line = f"[{self._ts()}]  {message}"
        self.job_logs.setdefault(self.run_id, []).append(line)

    def custom(self, message: str) -> None:
        """Emit a one-off message that doesn't map to a stage key."""
        line = f"[{self._ts()}]  {message}"
        self.job_logs.setdefault(self.run_id, []).append(line)
