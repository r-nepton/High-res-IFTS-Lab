"""Public API limits to keep responses bounded."""

MAX_N_SIGMA = 8192
MIN_N_SIGMA = 128
MAX_N_STEPS = 8192
MIN_N_STEPS = 16
MAX_T_TOTAL_S = 864_000.0  # 10 days
MAX_TARGET_SNR = 1_000_000.0
