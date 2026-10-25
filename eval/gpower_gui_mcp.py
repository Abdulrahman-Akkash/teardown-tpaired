"""MCP server for the GUI path of the MCP-vs-GUI comparison: G*Power seen only through screenshots.

This is a measurement harness, not part of the product. It lets an agent operate the
real G*Power 3.1.9.7 window (which must already be open) the way a GUI agent would:
look at a screenshot, change one control, look again. No tool returns G*Power's
results as text; the agent must read N and power from the screenshot image.

Compared with real computer use this path is favourable to the GUI: the agent names a
control instead of locating it by pixel coordinates, and an unmatched dropdown option
returns the option list as text instead of requiring the agent to open and look at the
list. Its token count is therefore a lower bound for a screenshot-driven agent.

Run: python eval/gpower_gui_mcp.py   (stdio)
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path
from typing import Annotated

from mcp.server.mcpserver import Image, MCPServer
from pydantic import Field

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from collect_gpower import (OUT_EDITS, capture_window, ctrl, dismiss_dialogs,  # noqa: E402
                            main_window, visible_ctrl, BTN_CALC)

DROPDOWNS = {"test_family": 1000, "statistical_test": 1001,
             "type_of_power_analysis": 1002, "tails": 1040}
# Input parameter fields in the order G*Power shows them for this test.
FIELDS = {"effect_size_dz": 1021, "alpha_err_prob": 1022,
          "power": 1023, "total_sample_size": 1023}
CALC_WAIT = 1.5

server = MCPServer(
    name="gpower-gui",
    instructions=("Operates the open G*Power 3.1.9.7 window. Call `screenshot` to see it; "
                  "results are only visible in screenshots."),
)


def _win():
    return main_window()


@server.tool(name="screenshot", description="Returns a PNG screenshot of the G*Power window.")
def screenshot() -> Image:
    buf = io.BytesIO()
    capture_window(_win().handle).save(buf, format="PNG")
    return Image(data=buf.getvalue(), format="png")


@server.tool(
    name="select_dropdown",
    description=("Selects an option in one of the dropdowns: test_family, statistical_test, "
                 "type_of_power_analysis, tails. `option` is matched case-insensitively against "
                 "the visible option text (a unique substring is enough). Returns 'ok' or, "
                 "if there is no unique match, the list of options."),
)
def select_dropdown(
    dropdown: Annotated[str, Field(description="test_family | statistical_test | type_of_power_analysis | tails")],
    option: Annotated[str, Field(description="visible option text or a unique part of it")],
) -> str:
    if dropdown not in DROPDOWNS:
        return f"unknown dropdown; use one of {list(DROPDOWNS)}"
    cb = ctrl(_win(), "ComboBox", DROPDOWNS[dropdown])
    items = cb.item_texts()
    hits = [i for i, t in enumerate(items) if option.lower() in t.lower()]
    exact = [i for i, t in enumerate(items) if option.lower() == t.lower()]
    pick = exact or hits
    if len(pick) != 1:
        return "no unique match; options: " + " | ".join(items)
    cb.select(pick[0])
    time.sleep(0.4)
    return "ok"


@server.tool(
    name="set_field",
    description=("Types a value into an input parameter field: effect_size_dz, alpha_err_prob, "
                 "power (a priori) or total_sample_size (post hoc). The third input field "
                 "shows power in a priori mode and total sample size in post hoc mode."),
)
def set_field(
    field: Annotated[str, Field(description="effect_size_dz | alpha_err_prob | power | total_sample_size")],
    value: Annotated[str, Field(description="text to type, e.g. 0.05")],
) -> str:
    if field not in FIELDS:
        return f"unknown field; use one of {list(FIELDS)}"
    ctrl(_win(), "Edit", FIELDS[field]).set_edit_text(str(value))
    return "ok"


@server.tool(
    name="click_calculate",
    description=("Clicks Calculate. Returns 'clicked', or the text of an error dialog if one "
                 "opened (the dialog is closed). Results appear only in the next screenshot."),
)
def click_calculate() -> str:
    win = _win()
    # Clear the output fields so a stale result from a previous calculation is not misread.
    for cid in OUT_EDITS:
        c = ctrl(win, "Edit", cid)
        if c.is_visible():
            c.set_edit_text("")
    visible_ctrl(win, "Button", BTN_CALC).click()
    time.sleep(CALC_WAIT)
    err = dismiss_dialogs(win.process_id())
    return f"error dialog: {err}" if err else "clicked"


def reset() -> None:
    """Neutral start state for every evaluation question (called by the runner, not a tool):
    t tests family, the first test in the list, a priori mode."""
    win = _win()
    for cid, idx in ((1000, None), (1001, 0), (1002, 0)):
        cb = ctrl(win, "ComboBox", cid)
        cb.select(cb.item_texts().index("t tests") if idx is None else idx)
        time.sleep(0.4)


if __name__ == "__main__":
    server.run("stdio")
