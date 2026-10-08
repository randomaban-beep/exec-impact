"""Build 1-minute bars and trailing, prior-only estimators (Stage 3).

Sigma is close-to-close on 1m bars; empty minutes contribute a zero return.
Intra-bar realized vol is diagnostic only and is never used for impact or AC.
"""
