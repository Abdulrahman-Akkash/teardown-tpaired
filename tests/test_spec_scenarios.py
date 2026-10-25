"""One test per Gherkin scenario in SPEC.md §6.

Numeric checks run against the engine (full precision, 1e-7 as in the SPEC);
every scenario is also run through the CLI to check the exit code and the
4-digit JSON contract (SPEC §5).
"""
import pytest

from helpers import cli_args, close, run_cli
from tpaired.engine import InputError, solve


def ok(mode, tails, dz, alpha, power=None, n=None):
    res = solve(mode, tails, dz, alpha, power=power, n=n)
    out, _, code = run_cli(cli_args(mode, tails, dz, alpha, power, n))
    assert code == 0 and "error" not in out
    assert out["n_total"] == res.n_total and out["df"] == res.df
    return res


def err(mode, tails, dz, alpha, power=None, n=None):
    with pytest.raises(InputError) as exc:
        solve(mode, tails, dz, alpha, power=power, n=n)
    out, _, code = run_cli(cli_args(mode, tails, dz, alpha, power, n))
    assert code != 0
    assert set(out) == {"error"} and out["error"] == str(exc.value)
    return out["error"]


# Scenario: Kılavuzdaki post hoc örneği
def test_manual_post_hoc_example():
    r = ok("post-hoc", 2, 0.421637, 0.05, n=50)
    assert r.df == 49
    assert close(r.ncp, 2.9814238)
    assert close(r.critical, 2.0095752)
    assert close(r.power, 0.8321145)


# Scenario: Tipik a priori hesap
def test_typical_a_priori():
    r = ok("a-priori", 2, 0.5, 0.05, power=0.95)
    assert r.n_total == 54
    assert close(r.power, 0.9502120)
    assert close(r.critical, 2.0057460)
    assert r.df == 53
    assert close(r.ncp, 3.6742346)
    out, _, _ = run_cli(cli_args("a-priori", 2, 0.5, 0.05, power=0.95))
    assert out == {"n_total": 54, "actual_power": 0.9502, "critical": 2.0057, "df": 53, "ncp": 3.6742}


# Scenario: Büyük N yukarı yuvarlanır
def test_large_n_rounded_up():
    r = ok("a-priori", 2, 0.1, 0.01, power=0.90)
    assert r.n_total == 1492
    assert close(r.power, 0.9001687)


# Scenario: Güç alfaya eşitse N alt sınıra (2) çekilir
def test_power_equal_alpha_clamps_to_two():
    r = ok("a-priori", 2, 0.5, 0.05, power=0.05)
    assert r.n_total == 2 and r.df == 1
    assert close(r.power, 0.0619486)


# Scenario: Güç alfadan küçükse hata
def test_power_below_alpha_is_error():
    msg = err("a-priori", 2, 0.5, 0.05, power=0.03)
    assert "Power must be greater than or equal to alpha" in msg


# Scenario: A priori N int sınırını aşabilir
# SPEC §7 lists GP-057 as a known deviation: no error is required, exact N is not.
def test_a_priori_n_may_exceed_int_range():
    r = ok("a-priori", 2, 0.00002, 0.05, power=0.80)
    assert r.n_total > 2_147_483_646
    assert abs(r.n_total - 19622220504) / 19622220504 < 1e-4


@pytest.mark.xfail(reason="SPEC §7 known deviation (N > 1e10): exact N not expected", strict=False)
def test_a_priori_n_may_exceed_int_range_exact():
    assert solve("a-priori", 2, 0.00002, 0.05, power=0.80).n_total == 19622220504


# Scenario Outline: A priori etki büyüklüğü alt eşiği
def test_effect_size_floor_zero_is_error():
    err("a-priori", 2, 0, 0.05, power=0.80)


def test_effect_size_floor_exact_threshold_is_valid():
    r = ok("a-priori", 2, 0.00001, 0.05, power=0.80)
    assert abs(r.n_total - 78488272181) / 78488272181 < 1e-4


@pytest.mark.xfail(reason="SPEC §7 known deviation (GP-071, N > 1e10): exact N not expected", strict=False)
def test_effect_size_floor_exact_threshold_exact_n():
    assert solve("a-priori", 2, 0.00001, 0.05, power=0.80).n_total == 78488272181


# Scenario Outline: Etki büyüklüğü aralığı
@pytest.mark.parametrize("mode,dz,third,expected", [
    ("post-hoc", 20, {"n": 10}, 1.0),
    ("post-hoc", 20.5, {"n": 10}, None),
    ("post-hoc", -20.5, {"n": 10}, None),
    ("a-priori", 25, {"power": 0.80}, None),
])
def test_effect_size_range(mode, dz, third, expected):
    if expected is None:
        err(mode, 2, dz, 0.05, **third)
    else:
        assert close(ok(mode, 2, dz, 0.05, **third).power, expected)


# Scenario Outline: Alfa ve güç aralıkları
@pytest.mark.parametrize("alpha,power,expected_n", [
    (0, 0.80, None),
    (1, 0.80, None),
    (0.0000001, 0.80, 167),
    (0.05, 1, None),
    (0.05, 0, None),
])
def test_alpha_and_power_ranges(alpha, power, expected_n):
    if expected_n is None:
        err("a-priori", 2, 0.5, alpha, power=power)
    else:
        assert ok("a-priori", 2, 0.5, alpha, power=power).n_total == expected_n


# Scenario Outline: Post hoc N yuvarlama ve aralık
@pytest.mark.parametrize("n,expected_df", [
    (0, None), (1, None), (2, None), (2.4, None),
    (2.5, 2), (3, 2), (3.4999, 2), (3.5, 3), (4.5, 4),
])
def test_post_hoc_n_rounding_and_range(n, expected_df):
    if expected_df is None:
        err("post-hoc", 2, 0.5, 0.05, n=n)
    else:
        assert ok("post-hoc", 2, 0.5, 0.05, n=n).df == expected_df


# Scenario: Negatif dz aynı gücü verir, işaretler döner
def test_negative_dz_same_power_signs_flip():
    r = ok("post-hoc", 2, -0.5, 0.05, n=30)
    assert close(r.power, 0.7539647)
    assert close(r.ncp, -2.7386128)
    assert close(r.critical, -2.0452296)


# Scenario: dz sıfırken güç alfaya eşittir
def test_zero_dz_power_equals_alpha():
    assert close(ok("post-hoc", 2, 0, 0.05, n=30).power, 0.0500000)


# Scenario: Sayı olmayan dz sıfır sayılır
def test_non_numeric_dz_counts_as_zero():
    msg_abc = err("a-priori", 2, "abc", 0.05, power=0.80)
    msg_zero = err("a-priori", 2, 0, 0.05, power=0.80)
    assert msg_abc == msg_zero
