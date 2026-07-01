# Source Context

This project builds on a case study by Vir Jain (IIT Madras), "Reducing Choice Overload on
Amazon," and its accompanying `amazonchoice.lovable.app` prototype.

## Problem statement (from the original deck)
> "Amazon shoppers struggle to confidently and quickly choose the right product when faced with
> thousands of similar options, which results in decision paralysis, wasted time, and reduced
> satisfaction."

## Key insights carried into this build
- More options ≠ better experience — clarity beats abundance
- Customers want a product that fits their needs (functional + emotional), not more options
- Users don't read hundreds of reviews; they rely on summarized trust signals (Airbnb case study)
- Intent-driven, personalized surfacing reduces overload better than generic filters (Netflix
  case study)

## What this repo adds beyond the original prototype
The original prototype re-ranks once after a manual spec pick. This system:
- Infers a starting spec priority automatically (IntentAgent) so the user isn't the one who has
  to make the first move — the prototype's manual "pick up to 3 specs" step is preserved as an
  override, not the only entry point
- Runs against **live** Amazon SERP data via SerpAPI instead of a static mock catalog
- Adds a visible agent reasoning trace, addressing "mistrust in platform" directly rather than
  just producing a different ranking
- Separates deterministic ranking math from LLM-generated explanations, so the system is fast and
  reproducible where it can be, and only "creative" where genuine language understanding is
  needed
