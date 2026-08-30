"""Small, dependency-free planning helpers for the registered pilot.

These calculations are intentionally labelled as approximations.  The final
sample size must be simulated using the planned clustered analysis after the
pilot estimates event rates, missingness, and discordance.
"""

from __future__ import annotations

import argparse
import json
import math


def paired_binary_group_count(
    effect: float,
    discordance: float,
    *,
    alpha: float = 0.05,
    power: float = 0.80,
) -> int:
    """Approximate groups for a paired binary comparison.

    The approximation treats the discordant-pair rate as fixed and uses a
    normal approximation to the paired difference.  It is for planning only;
    a confirmatory design must use simulation with the actual analysis model.
    """

    if not 0 < effect < 1:
        raise ValueError("effect must be between 0 and 1")
    if not 0 < discordance <= 1:
        raise ValueError("discordance must be in (0, 1]")
    if not 0 < alpha < 1 or not 0 < power < 1:
        raise ValueError("alpha and power must be between 0 and 1")
    # z values for the common planning defaults, with a compact inverse-normal
    # approximation so the module has no scipy dependency.
    z_alpha = _normal_quantile(1 - alpha / 2)
    z_power = _normal_quantile(power)
    variance = discordance
    n = ((z_alpha + z_power) ** 2 * variance) / (effect**2)
    return max(1, math.ceil(n))


def _normal_quantile(p: float) -> float:
    """Acklam-style inverse normal CDF approximation."""

    if not 0 < p < 1:
        raise ValueError("p must be between 0 and 1")
    a = (-39.6968302866538, 220.946098424521, -275.928510446969, 138.357751867269, -30.6647980661472, 2.50662827745924)
    b = (-54.4760987982241, 161.585836858041, -155.698979859887, 66.8013118877197, -13.2806815528857)
    c = (-0.00778489400243029, -0.322396458041136, -2.40075827716184, -2.54973253934373, 4.37466414146497, 2.93816398269878)
    d = (0.00778469570904146, 0.32246712907004, 2.445134137143, 3.75440866190742)
    def poly(coefficients: tuple[float, ...], value: float) -> float:
        result = 0.0
        for coefficient in coefficients:
            result = result * value + coefficient
        return result

    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        numerator = poly(c, q)
        denominator = poly(d + (1.0,), q)
        return numerator / denominator
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        numerator = poly(c, q)
        denominator = poly(d + (1.0,), q)
        return -numerator / denominator
    q = p - 0.5
    r = q * q
    return poly(a, r) * q / (poly(b, r) * r + 1)


def planning_grid() -> list[dict[str, float | int]]:
    return [
        {"effect": effect, "discordance": discordance, "groups": paired_binary_group_count(effect, discordance)}
        for effect, discordance in (
            (0.08, 0.20),
            (0.08, 0.25),
            (0.08, 0.40),
            (0.10, 0.25),
            (0.12, 0.25),
            (0.15, 0.25),
        )
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="Print the Iboga paired-binary planning grid")
    parser.add_argument("--effect", type=float)
    parser.add_argument("--discordance", type=float)
    args = parser.parse_args()
    if (args.effect is None) != (args.discordance is None):
        parser.error("provide both --effect and --discordance, or neither")
    value = (
        {"effect": args.effect, "discordance": args.discordance, "groups": paired_binary_group_count(args.effect, args.discordance)}
        if args.effect is not None
        else planning_grid()
    )
    print(json.dumps(value, indent=2))


if __name__ == "__main__":
    main()
