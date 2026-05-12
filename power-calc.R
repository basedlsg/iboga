# Iboga v0.5 — Power Analysis for Pre-Registration
# ---
# Status: draft, target lock 2026-07-01
# Purpose: justify the n=80 paired-observations sample size and α-budget
# Output: power-calc-output.txt (committed before pre-reg lock)
#
# Run from R 4.x. Requires: WMWssp (or pwr as fallback)

suppressPackageStartupMessages({
  has_wmwssp <- requireNamespace("WMWssp", quietly = TRUE)
  if (!has_wmwssp) {
    message("WMWssp not installed; falling back to pwr (less precise for Wilcoxon)")
    has_pwr <- requireNamespace("pwr", quietly = TRUE)
    stopifnot(has_pwr)
  }
})

# ---- Configuration matching prereg.md §9 ----

PRIMARY_ALPHA  <- 0.025         # Holm-Bonferroni split of 0.05 across H1a + H1b
SECONDARY_ALPHA <- 0.05
EFFECT_SIZES   <- c(0.2, 0.3, 0.4, 0.5)
N_VALUES       <- c(60, 70, 80, 90, 100)
NONINF_MARGIN  <- -0.05

# ---- Helpers ----

# Paired Wilcoxon power via WMWssp (preferred) or pwr (fallback)
power_paired_wilcox <- function(d, n, alpha, alternative = "less") {
  if (has_wmwssp) {
    # WMWssp wants WMW relative effect, not Cohen's d. Approximate:
    # p_relative ≈ 0.5 + d / sqrt(2 * pi)  (under normality assumption)
    p_rel <- 0.5 + d / sqrt(2 * pi)
    p_rel <- pmin(pmax(p_rel, 0.5 + 0.01), 0.99)
    tryCatch({
      WMWssp::WMWssp(p_rel, alpha = alpha, power = NA, n = n)$power
    }, error = function(e) {
      message("WMWssp failed at d=", d, " n=", n, ": ", conditionMessage(e))
      NA
    })
  } else {
    # pwr.t.test with paired adjustment, slightly conservative for Wilcoxon
    tryCatch({
      pwr::pwr.t.test(n = n, d = d, sig.level = alpha, type = "paired",
                      alternative = if (alternative == "less") "greater" else alternative)$power
    }, error = function(e) {
      message("pwr.t.test failed: ", conditionMessage(e))
      NA
    })
  }
}

# ---- H1a: one-tailed paired Wilcoxon power ----

cat("\n=== H1a: erosion slope AA < unstructured, one-tailed paired Wilcoxon ===\n")
cat("α =", PRIMARY_ALPHA, "(Holm-Bonferroni)\n\n")

h1a_table <- expand.grid(d = EFFECT_SIZES, n = N_VALUES)
h1a_table$power <- mapply(function(d, n) power_paired_wilcox(d, n, PRIMARY_ALPHA),
                          h1a_table$d, h1a_table$n)
print(h1a_table)

# ---- H1b: TOST non-inferiority power ----

cat("\n=== H1b: solve rate non-inferiority, TOST one-tailed ===\n")
cat("α =", PRIMARY_ALPHA, ", non-inferiority margin =", NONINF_MARGIN, "\n")
cat("Power computed approximately via paired t-test analog (TOST exact power requires nonparametric estimator)\n\n")

# For TOST non-inferiority with margin Δ, power ≈ paired t-test detecting
# true difference at d_actual relative to margin
# Conservative: assume true mean diff is 0 (AA solve rate equals unstructured),
# power = P(reject NI null at margin Δ) = 1 - β
# Approximate via shifted paired t-test:
tost_power <- function(true_d, n, alpha, margin) {
  # Effect to detect: true_d − margin (in standardized units, assuming SD≈1)
  d_eff <- true_d - (margin / 1)
  if (!has_wmwssp) {
    pwr::pwr.t.test(n = n, d = d_eff, sig.level = alpha, type = "paired",
                    alternative = "greater")$power
  } else {
    power_paired_wilcox(d_eff, n, alpha, alternative = "greater")
  }
}

h1b_table <- expand.grid(true_d = c(-0.1, -0.05, 0, 0.05), n = N_VALUES)
h1b_table$power <- mapply(function(d, n) tost_power(d, n, PRIMARY_ALPHA, NONINF_MARGIN),
                          h1b_table$true_d, h1b_table$n)
print(h1b_table)

# ---- Secondary: H2 + H3 power ----

cat("\n=== H2 (AA vs neutral) + H3 (verbosity AA vs unstructured) — α =", SECONDARY_ALPHA, "===\n\n")
sec_table <- expand.grid(d = EFFECT_SIZES, n = N_VALUES)
sec_table$power_h2 <- mapply(function(d, n) power_paired_wilcox(d, n, SECONDARY_ALPHA, "two.sided"),
                              sec_table$d, sec_table$n)
sec_table$power_h3 <- mapply(function(d, n) power_paired_wilcox(d, n, SECONDARY_ALPHA, "less"),
                              sec_table$d, sec_table$n)
print(sec_table)

# ---- Summary ----

cat("\n=== SUMMARY ===\n")
cat("Pre-registered n = 80 (per arm contrast)\n\n")

cat("At n=80, α=0.025 one-tailed:\n")
for (d in EFFECT_SIZES) {
  p <- power_paired_wilcox(d, 80, PRIMARY_ALPHA)
  cat(sprintf("  d = %.2f → power = %.3f\n", d, p))
}

cat("\nAt n=80, α=0.05 two-tailed (secondary):\n")
for (d in EFFECT_SIZES) {
  p <- power_paired_wilcox(d, 80, SECONDARY_ALPHA, "two.sided")
  cat(sprintf("  d = %.2f → power = %.3f\n", d, p))
}

cat("\nPre-registered minimum-detectable effect at 80% power, α=0.025:\n")
# Find smallest d giving power ≥ 0.80 at n=80
for (d in seq(0.1, 1, by = 0.05)) {
  p <- power_paired_wilcox(d, 80, PRIMARY_ALPHA)
  if (!is.na(p) && p >= 0.80) {
    cat(sprintf("  MDE ≈ d = %.2f (power = %.3f)\n", d, p))
    break
  }
}

# ---- Save to file ----

out_path <- file.path(getwd(), "power-calc-output.txt")
sink(out_path, type = "output")
cat("Iboga v0.5 Power Analysis Output\n")
cat("Generated:", format(Sys.time(), "%Y-%m-%dT%H:%M:%S"), "\n")
cat("================================\n\n")
cat("Pre-registered n = 80 paired observations per arm contrast.\n")
cat("Primary α = 0.025 (Holm-Bonferroni). Secondary α = 0.05.\n\n")
cat("H1a power table (one-tailed paired Wilcoxon):\n")
print(h1a_table)
cat("\nH1b TOST non-inferiority power:\n")
print(h1b_table)
cat("\nH2 + H3 power:\n")
print(sec_table)
sink()

cat("\nOutput saved to:", out_path, "\n")
cat("Commit this file to iboga/power-calc-output.txt before pre-reg lock.\n")
