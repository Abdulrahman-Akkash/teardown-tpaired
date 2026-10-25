"""MCP adapter: same input -> same output as the CLI (bonus layer)."""
import json
import sys

import anyio
import pytest

mcp = pytest.importorskip("mcp")
from mcp import Client, StdioServerParameters  # noqa: E402

from helpers import GPOWER_CSV, ROOT, STATSMODELS_CSV, cli_args, load_csv, run_cli  # noqa: E402
from tpaired.mcp_server import TOOL_NAME, server  # noqa: E402


def mcp_arguments(mode, tails, dz, alpha, power=None, n=None):
    args = {"mode": mode, "tails": int(tails), "alpha": float(alpha)}
    try:
        args["dz"] = float(dz)
    except ValueError:
        args["dz"] = dz                       # e.g. "abc" (SPEC §3: counts as 0)
    if power not in (None, ""):
        args["power"] = float(power)
    if n not in (None, ""):
        args["n"] = float(n)
    return args


def cases():
    out = []
    for r in load_csv(GPOWER_CSV):
        out.append((r["id"], r["mode"], r["tails"], r["dz"], r["alpha"], r["power_in"], r["n_in"]))
    for r in load_csv(STATSMODELS_CSV)[::25]:
        out.append((r["id"], r["mode"], r["tails"], r["dz"], r["alpha"], r["power_in"], r["n_in"]))
    return out


async def call_all(client, items):
    results = []
    for _id, mode, tails, dz, alpha, power, n in items:
        res = await client.call_tool(TOOL_NAME, mcp_arguments(mode, tails, dz, alpha, power, n))
        assert not res.is_error, res
        results.append((res.structured_content, json.loads(res.content[0].text)))
    return results


def test_cli_and_mcp_agree_on_every_vector():
    items = cases()

    async def go():
        async with Client(server) as client:
            return await call_all(client, items)

    results = anyio.run(go)
    assert len(results) == len(items) > 72
    for (case_id, mode, tails, dz, alpha, power, n), (structured, text) in zip(items, results):
        cli_out, _, code = run_cli(cli_args(mode, tails, dz, alpha, power or None, n or None))
        assert structured == cli_out, case_id
        assert text == cli_out, case_id
        assert ("error" in cli_out) == (code != 0), case_id


def test_tool_schema():
    async def go():
        async with Client(server) as client:
            return await client.list_tools()

    tools = anyio.run(go)
    tools = getattr(tools, "tools", tools)
    assert [t.name for t in tools] == [TOOL_NAME]
    schema = tools[0].input_schema
    assert schema["required"] == ["mode", "tails", "dz", "alpha"]
    assert set(schema["properties"]) == {"mode", "tails", "dz", "alpha", "power", "n"}


def test_stdio_transport_matches_cli():
    """Spawn the server as a real subprocess and talk to it over stdio."""
    params = StdioServerParameters(command=sys.executable, args=["-m", "tpaired.mcp_server"],
                                   cwd=str(ROOT), env={"PYTHONPATH": str(ROOT / "src")})
    items = [c for c in cases() if c[0] in ("GP-001", "GP-021", "GP-036", "GP-032", "GP-044")]

    async def go():
        async with Client(params) as client:
            return await call_all(client, items)

    for (case_id, mode, tails, dz, alpha, power, n), (structured, _) in zip(items, anyio.run(go)):
        cli_out, _, _ = run_cli(cli_args(mode, tails, dz, alpha, power or None, n or None))
        assert structured == cli_out, case_id
