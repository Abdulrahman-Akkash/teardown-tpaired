"""MCP server: a thin adapter that exposes the engine as one tool.

No computation here: the tool forwards to `tpaired.output.run`, the same
function the CLI uses, so both return the same JSON for the same input.
Run with `tpaired-mcp` or `python -m tpaired.mcp_server` (stdio transport).
"""
from __future__ import annotations

from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from tpaired import __version__
from tpaired.output import run

TOOL_NAME = "t_paired_power"

server = MCPServer(
    name="tpaired-power",
    version=__version__,
    instructions=("Power analysis for the paired-samples t test. Use mode 'a-priori' with "
                  "'power' to get the required number of pairs, or 'post-hoc' with 'n' to get "
                  "the achieved power."),
)


@server.tool(
    name=TOOL_NAME,
    description=(
        "Paired-samples t test power analysis (same engine and output as the "
        "`gpower-clone --test t-paired` CLI). "
        "mode: 'a-priori' (needs power; returns n_total, actual_power, critical, df, ncp) or "
        "'post-hoc' (needs n; returns n_total, power, critical, df, ncp). "
        "tails: 1 or 2. dz: effect size, -20..20 (a non-numeric dz counts as 0). "
        "alpha and power: 1e-7..0.9999999. n: number of pairs, rounded half up, 3..2147483646. "
        "Decimals are rounded to 4 places. Invalid input returns {\"error\": \"...\"}."
    ),
)
def t_paired_power(
    mode: Annotated[str, Field(description="'a-priori' or 'post-hoc'")],
    tails: Annotated[int, Field(description="1 or 2")],
    dz: Annotated[float | str, Field(description="effect size dz, -20..20; non-numeric counts as 0")],
    alpha: Annotated[float, Field(description="significance level, 1e-7..0.9999999")],
    power: Annotated[float | None, Field(description="target power (a-priori only), alpha..0.9999999")] = None,
    n: Annotated[float | None, Field(description="number of pairs (post-hoc only), 3..2147483646")] = None,
) -> dict[str, Any]:
    payload, _ok = run("t-paired", mode, tails, dz, alpha, power=power, n=n)
    return payload


def main() -> None:
    server.run("stdio")


if __name__ == "__main__":
    main()
