# Iboga v0.5 — Pre-Registered Analysis Script
# ---
# Status: draft, target lock 2026-07-01
# Pre-registered: must be committed unchanged before any treatment trajectory runs
# Reads: ~/iboga-data/sessions/*.json (one per trajectory summary)
# Writes: ~/iboga-data/analysis/results-{date}.json + analysis-{date}.md
#
# Design (matches prereg.md §9):
#   Primary: H1a (erosion slope, AA < unstructured) + H1b (solve rate non-inferiority)
#     - Paired Wilcoxon, Holm-Bonferroni α=0.025 each
#   Secondary: H2 (AA vs neutral erosion slope) + H3 (AA verbosity slope)
#     - Separate α=0.05 budget
#   Exploratory: H_M (SAE features, AA vs neutral on Llama-3.1-8B)
#     - Mann-Whitney + BH-FDR q<0.10 across locked feature set
#   Confirmatory check: mixed-effects regression as sensitivity
#
# Run from R 4.x. Requires: dplyr, tidyr, jsonlite, lme4, WMWssp (power), exactRankTests

suppressPackageStartupMessages({
  library(dplyr)
  library(tidyr)
  library(jsonlite)
  library(lme4)
  library(exactRankTests)  # for paired Wilcoxon
})

# ---- Configuration ----
DATA_DIR <- "~/iboga-data/sessions"
OUT_DIR  <- "~/iboga-data/analysis"
PRIMARY_ALPHA   <- 0.025  # Holm-Bonferroni split of 0.05
SECONDARY_ALPHA <- 0.05
NONINF_MARGIN   <- -0.05  # H1b: AA solve rate not worse than unstructured by more than 5pp
ARMS            <- c("A_iboga", "B_neutral", "C_unstructured")
MODELS          <- c("opus-4.7", "qwen-2.5-32b", "llama-3.1-8b", "deepseek-coder-v3")

dir.create(OUT_DIR, recursive = TRUE, showWarnings = FALSE)
RUN_TIMESTAMP <- format(Sys.time(), "%Y-%m-%dT%H%M%S")

# ---- Load trajectories ----

load_trajectory <- function(path) {
  tryCatch({
    d <- fromJSON(path, simplifyDataFrame = FALSE)
    tibble::tibble(
      trajectory_id   = d$trajectory_id,
      model           = d$model,
      problem_id      = d$problem_id,
      arm             = d$arm,
      erosion_slope   = d$metrics$erosion_slope,
      verbosity_slope = d$metrics$verbosity_slope,
      # solve_rate is precomputed by the trajectory post-processor as
      # solved_checkpoints / expected_checkpoints, matching SlopCodeBench
      # pct_checkpoints_solved / 100.
      solve_rate      = d$metrics$solve_rate,
      excluded        = isTRUE(d$excluded),
      exclude_reason  = d$exclude_reason %||% NA_character_
    )
  }, error = function(e) {
    cat("  skipped: ", path, " (", conditionMessage(e), ")\n", sep = "")
    NULL
  })
}

`%||%` <- function(a, b) if (is.null(a)) b else a

trajectory_files <- list.files(DATA_DIR, pattern = "\\.json$", recursive = TRUE, full.names = TRUE)
cat("Loading", length(trajectory_files), "trajectory files...\n")
trajectories <- bind_rows(lapply(trajectory_files, load_trajectory))

stopifnot(nrow(trajectories) > 0)
cat("Loaded", nrow(trajectories), "trajectories.\n")

# ---- Exclusion ----

n_total <- nrow(trajectories)
trajectories_kept <- trajectories %>% filter(!excluded)
n_kept <- nrow(trajectories_kept)
exclusion_rate <- 1 - (n_kept / n_total)
cat("Exclusion rate:", round(100 * exclusion_rate, 2), "%\n")

if (exclusion_rate > 0.10) {
  warning("Exclusion rate exceeds pre-registered 10% cap. Pre-reg invalidated.")
}

# ---- Sanity checks ----

# Expect: 4 models × 36 problems × 3 arms = 432 trajectories (updated 2026-05-14)
# Each (model, problem) seen in all 3 arms → 144 paired observations per arm contrast
pairing_check <- trajectories_kept %>%
  group_by(model, problem_id) %>%
  summarise(arms_present = paste(sort(unique(arm)), collapse = "|"), .groups = "drop")

complete_pairs <- pairing_check %>%
  mutate(complete = arms_present == paste(sort(ARMS), collapse = "|")) %>%
  filter(complete)

cat("Complete (model, problem) triples:", nrow(complete_pairs), "of", nrow(pairing_check), "\n")
# Only complete triples enter paired analyses
trajectories_paired <- trajectories_kept %>%
  inner_join(complete_pairs %>% select(model, problem_id), by = c("model", "problem_id"))

# ---- Reshape for paired tests ----

wide <- trajectories_paired %>%
  select(model, problem_id, arm, erosion_slope, verbosity_slope, solve_rate) %>%
  pivot_wider(names_from = arm,
              values_from = c(erosion_slope, verbosity_slope, solve_rate))

# Expected columns: erosion_slope_A_iboga, erosion_slope_B_neutral, erosion_slope_C_unstructured, ...

# ---- PRIMARY: H1a — AA erosion slope < unstructured erosion slope ----

cat("\n=== H1a: Erosion slope, AA < unstructured ===\n")
h1a <- wilcox.exact(
  wide$erosion_slope_A_iboga,
  wide$erosion_slope_C_unstructured,
  paired = TRUE,
  alternative = "less",
  conf.int = TRUE,
  conf.level = 1 - PRIMARY_ALPHA
)
h1a_diff <- mean(wide$erosion_slope_A_iboga - wide$erosion_slope_C_unstructured, na.rm = TRUE)
h1a_d_estimate <- h1a_diff / sd(wide$erosion_slope_A_iboga - wide$erosion_slope_C_unstructured, na.rm = TRUE)
cat("  N pairs:", nrow(wide), "\n")
cat("  Mean diff (AA - unstructured):", round(h1a_diff, 4), "\n")
cat("  Estimated Cohen d (paired):", round(h1a_d_estimate, 3), "\n")
cat("  Wilcoxon p:", round(h1a$p.value, 5), "\n")
cat("  Reject H0 at α =", PRIMARY_ALPHA, "?", h1a$p.value < PRIMARY_ALPHA, "\n")

# ---- PRIMARY: H1b — AA solve rate non-inferior to unstructured (TOST) ----

cat("\n=== H1b: Solve rate non-inferiority (TOST, margin", NONINF_MARGIN, ") ===\n")
# TOST = Two One-Sided Tests
# Test 1: AA - unstructured > NONINF_MARGIN (i.e. AA not worse by more than the margin)
# Test 2: AA - unstructured < some upper bound (we ignore the upper side for non-inferiority)
# For non-inferiority, only the lower bound matters.
h1b_lower <- wilcox.exact(
  wide$solve_rate_A_iboga - wide$solve_rate_C_unstructured,
  mu = NONINF_MARGIN,
  alternative = "greater",
  conf.int = TRUE,
  conf.level = 1 - PRIMARY_ALPHA
)
h1b_diff <- mean(wide$solve_rate_A_iboga - wide$solve_rate_C_unstructured, na.rm = TRUE)
cat("  N pairs:", nrow(wide), "\n")
cat("  Mean diff (AA - unstructured):", round(h1b_diff, 4), "\n")
cat("  Non-inferiority p (margin =", NONINF_MARGIN, "):", round(h1b_lower$p.value, 5), "\n")
cat("  Non-inferiority holds at α =", PRIMARY_ALPHA, "?", h1b_lower$p.value < PRIMARY_ALPHA, "\n")

# ---- Holm-Bonferroni on primary ----

primary_ps <- c(h1a = h1a$p.value, h1b = h1b_lower$p.value)
primary_holm <- p.adjust(primary_ps, method = "holm")
cat("\n=== Primary Holm-Bonferroni adjusted ===\n")
print(round(primary_holm, 5))
primary_component_pass <- primary_ps < PRIMARY_ALPHA
cat("Raw p-values pass α =", PRIMARY_ALPHA, "each?\n")
print(primary_component_pass)
primary_pass <- all(primary_component_pass)
cat("Primary hypothesis supported (H1a AND H1b)?", primary_pass, "\n")

# ---- SECONDARY: H2 — AA vs neutral erosion slope (two-tailed) ----

cat("\n=== H2: AA vs Neutral erosion slope (two-tailed) ===\n")
h2 <- wilcox.exact(
  wide$erosion_slope_A_iboga,
  wide$erosion_slope_B_neutral,
  paired = TRUE,
  alternative = "two.sided"
)
h2_diff <- mean(wide$erosion_slope_A_iboga - wide$erosion_slope_B_neutral, na.rm = TRUE)
cat("  Mean diff (AA - neutral):", round(h2_diff, 4), "\n")
cat("  Wilcoxon p:", round(h2$p.value, 5), "\n")
cat("  Reject H0 at α =", SECONDARY_ALPHA, "?", h2$p.value < SECONDARY_ALPHA, "\n")

# ---- SECONDARY: H3 — AA verbosity slope < unstructured ----

cat("\n=== H3: AA vs unstructured verbosity slope (one-tailed) ===\n")
h3 <- wilcox.exact(
  wide$verbosity_slope_A_iboga,
  wide$verbosity_slope_C_unstructured,
  paired = TRUE,
  alternative = "less"
)
h3_diff <- mean(wide$verbosity_slope_A_iboga - wide$verbosity_slope_C_unstructured, na.rm = TRUE)
cat("  Mean diff (AA - unstructured):", round(h3_diff, 4), "\n")
cat("  Wilcoxon p:", round(h3$p.value, 5), "\n")
cat("  Reject H0 at α =", SECONDARY_ALPHA, "?", h3$p.value < SECONDARY_ALPHA, "\n")

# ---- CONFIRMATORY: Mixed-effects regression ----

cat("\n=== Confirmatory: Mixed-effects on erosion slope ~ arm + (1|model) + (1|problem) + (1|model:problem) ===\n")
me_data <- trajectories_paired %>%
  mutate(
    arm = factor(arm, levels = c("C_unstructured", "B_neutral", "A_iboga")),  # ref: unstructured
    model_problem = interaction(model, problem_id, drop = TRUE)
  )

me_fit <- tryCatch({
  lmer(erosion_slope ~ arm + (1 | model) + (1 | problem_id) + (1 | model_problem),
       data = me_data,
       REML = TRUE,
       control = lmerControl(optimizer = "bobyqa"))
}, error = function(e) {
  cat("  Mixed-effects fit failed:", conditionMessage(e), "\n")
  NULL
})

if (!is.null(me_fit)) {
  print(summary(me_fit)$coefficients)
}

# ---- EXPLORATORY: H_M — SAE feature activation, AA vs neutral on Llama-3.1-8B ----

cat("\n=== H_M: SAE feature activation, AA vs neutral (Llama-3.1-8B only) ===\n")
SAE_DATA_PATH <- "~/iboga-data/sae/activations.json"
if (file.exists(SAE_DATA_PATH)) {
  sae <- fromJSON(SAE_DATA_PATH)
  # Expected structure: list of {trajectory_id, feature_id, mean_activation, arm}
  # Locked features in iboga/sae-features.json
  sae_df <- as_tibble(sae)

  feat_ids <- unique(sae_df$feature_id)
  cat("  Testing", length(feat_ids), "locked SAE features...\n")

  per_feature_p <- sapply(feat_ids, function(fid) {
    sub <- sae_df %>% filter(feature_id == fid, arm %in% c("A_iboga", "B_neutral"))
    if (length(unique(sub$arm)) < 2) return(NA)
    aa_act     <- sub$mean_activation[sub$arm == "A_iboga"]
    neutral_act <- sub$mean_activation[sub$arm == "B_neutral"]
    # Predicted direction: AA < neutral (AA suppresses confabulation features)
    wilcox.test(aa_act, neutral_act, alternative = "less", exact = FALSE)$p.value
  })

  per_feature_q <- p.adjust(per_feature_p, method = "BH")
  sig_features <- names(per_feature_q)[per_feature_q < 0.10]
  cat("  Features with BH q <", 0.10, ":", length(sig_features), "\n")
  if (length(sig_features) > 0) {
    cat("  Significant feature IDs:", paste(sig_features, collapse = ", "), "\n")
  }
} else {
  cat("  SAE data not found at", SAE_DATA_PATH, "- skipping H_M\n")
  per_feature_p <- NULL
  per_feature_q <- NULL
  sig_features  <- character(0)
}

# ---- TERTIARY (Exploratory): Recurrence rate from annotator ----

cat("\n=== Tertiary: Recurrence rate (annotator-coded) ===\n")
ANNOT_PATH <- "~/iboga-data/annotator/recurrence.json"
if (file.exists(ANNOT_PATH)) {
  ann <- fromJSON(ANNOT_PATH)
  # Expected: list of {trajectory_id, row_index, row_failure_code, recurred (bool), arm}
  ann_df <- as_tibble(ann)

  # Cohen κ check (from earlier audit run)
  kappa_path <- "~/iboga-data/annotator/kappa.json"
  if (file.exists(kappa_path)) {
    kappa_data <- fromJSON(kappa_path)
    cat("  Cohen κ (vs candidate):", round(kappa_data$kappa, 3), "\n")
    if (kappa_data$kappa < 0.7) {
      cat("  κ < 0.7 — recurrence DV demoted to descriptive only\n")
      report_recurrence <- TRUE
      formal_recurrence <- FALSE
    } else {
      report_recurrence <- TRUE
      formal_recurrence <- TRUE
    }
  }

  if (report_recurrence) {
    by_arm <- ann_df %>%
      group_by(arm) %>%
      summarise(
        n_rows = n(),
        n_recurred = sum(recurred),
        recurrence_rate = n_recurred / n_rows,
        .groups = "drop"
      )
    print(by_arm)
  }
}

# ---- Output ----

results <- list(
  run_timestamp = RUN_TIMESTAMP,
  n_total = n_total,
  n_kept = n_kept,
  exclusion_rate = exclusion_rate,
  primary = list(
    h1a = list(p = h1a$p.value, mean_diff = h1a_diff, n_pairs = nrow(wide), estimated_d = h1a_d_estimate),
    h1b = list(p = h1b_lower$p.value, mean_diff = h1b_diff, noninf_margin = NONINF_MARGIN),
    holm_adjusted = primary_holm,
    component_pass_at_alpha_0_025 = primary_component_pass,
    primary_supported = primary_pass
  ),
  secondary = list(
    h2 = list(p = h2$p.value, mean_diff = h2_diff),
    h3 = list(p = h3$p.value, mean_diff = h3_diff)
  ),
  exploratory = list(
    h_m_n_features_tested = if(!is.null(per_feature_p)) length(per_feature_p) else 0,
    h_m_n_features_significant = length(sig_features),
    h_m_significant_feature_ids = sig_features
  )
)

out_path <- file.path(OUT_DIR, paste0("results-", RUN_TIMESTAMP, ".json"))
write_json(results, out_path, pretty = TRUE, auto_unbox = TRUE)
cat("\n=== Results saved to", out_path, "===\n")

# ---- Markdown summary ----

md_path <- file.path(OUT_DIR, paste0("analysis-", RUN_TIMESTAMP, ".md"))
md_lines <- c(
  paste0("# Iboga v0.5 Analysis Output — ", RUN_TIMESTAMP),
  "",
  paste0("**N total trajectories**: ", n_total),
  paste0("**N kept**: ", n_kept, " (exclusion rate ", round(100 * exclusion_rate, 2), "%)"),
  paste0("**N complete pairs**: ", nrow(wide)),
  "",
  "## Primary",
  "",
  paste0("- H1a (erosion slope AA < unstructured): p = ", round(h1a$p.value, 5),
         ", mean diff = ", round(h1a_diff, 4), ", est d = ", round(h1a_d_estimate, 3)),
  paste0("- H1b (solve rate non-inferiority): p = ", round(h1b_lower$p.value, 5),
         ", mean diff = ", round(h1b_diff, 4)),
  paste0("- Holm-adjusted: H1a = ", round(primary_holm["h1a"], 5),
         ", H1b = ", round(primary_holm["h1b"], 5)),
  paste0("- Raw α=0.025 component pass: H1a = ", primary_component_pass["h1a"],
         ", H1b = ", primary_component_pass["h1b"]),
  paste0("- **Primary supported: ", primary_pass, "**"),
  "",
  "## Secondary",
  "",
  paste0("- H2 (AA vs neutral erosion): p = ", round(h2$p.value, 5),
         ", mean diff = ", round(h2_diff, 4)),
  paste0("- H3 (verbosity slope AA < unstructured): p = ", round(h3$p.value, 5),
         ", mean diff = ", round(h3_diff, 4)),
  "",
  "## Exploratory (SAE)",
  "",
  paste0("- H_M features tested: ", if(!is.null(per_feature_p)) length(per_feature_p) else 0),
  paste0("- Significant features (BH q<0.10): ", length(sig_features))
)
writeLines(md_lines, md_path)
cat("Markdown summary saved to", md_path, "\n")

cat("\nAnalysis complete.\n")
