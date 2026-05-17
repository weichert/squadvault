# SquadVault Product Vision and Storytelling Architecture
## Governing Document v1.0

**Date:** 2026-05-16
**Author:** Steve Weichert (commissioner, sole developer)
**Status:** Governing -- all session briefs and implementation plans
         reference this document

---

## Core purpose

SquadVault exists to tell the true story of a fantasy league -- its
managers, its players, its history, and its moments -- in a voice that
feels native to that league.

Everything else -- the verifier, the Signal Scout, the Writer's Room,
the review surface, the data pipeline -- is infrastructure in service
of this purpose.

---

## What the product is

SquadVault is a deterministic storytelling engine. It uncovers real
stories from real data and renders them in a league-appropriate voice.
It does not predict. It does not optimize. It does not invent. It
reports what happened, finds what is meaningful in what happened, and
says so in a way the league will recognize as true.

The measure of success is not accuracy alone. It is recognition. A
manager reads a SquadVault recap and says: "Yes. That is exactly what
happened to me."

---

## The two audiences

### League audience (shared artifacts)
The collective story of the league in a given week, season, or era.
Who won. Who lost. What the standings mean. What the history shows.
What this season will be remembered for. Every manager reads this and
sees their place in the larger story.

### Personal audience (individual artifacts)
The story of a single manager's season -- their decisions, their
players, their results, their trajectory. This is the artifact that
speaks directly to one person: here is what you did, here is what it
cost, here is what it produced, here is how it compares to your own
history and to the league around you.

Both artifact types are required. Both are built from the same data
substrate. They differ in angle, scope, and voice calibration.

---

## The voice model

Voice is league-specific, not system-wide. The same underlying story
renders differently depending on the league's character.

League types and voice registers:
- Friends league: irreverent, sharp, personal, unmoderated
- Family league: warm, celebratory, inclusive, appropriate for all ages
- Office league: professional, witty, moderated, broadly safe
- Competitive league: analytical in tone, results-focused

Voice is a first-class configuration, not an afterthought. The Voice
Profile is set at the league level and governs every Writer's Room
output for that league.

The architectural separation must be maintained:
- The Research Team (Signal Scout) surfaces stories and angles.
  It is tone-agnostic. Facts are facts regardless of who is reading.
- The Writer's Room renders those stories through the Voice Profile.
  It does not invent angles. It does not create facts. It narrates
  what the Research Team found, in the voice the league has defined.

---

## The Research Team -- full scope

The Signal Scout operates across six data layers.

### Layer 1: Matchup outcomes (implemented)
Who won, who lost, margins, scores, streaks, standings.

### Layer 2: Transaction activity (partially implemented)
Waiver bids, free agent adds/drops, trades. Does not yet compute
acquisition value, trade outcomes, or roster construction arcs.

### Layer 3: Fantasy player performance (partially implemented)
Weekly scores for starters and bench. Does not yet compute:
- Acquisition cost vs points produced
- Start/sit decision outcomes and season-long patterns
- Player scoring arcs across a season
- Cross-season player history on a given roster
- The player who won or lost a specific matchup

### Layer 4: Manager identity (not implemented)
The patterns that define a manager across seasons:
- Draft style: aggressive, conservative, position-focused
- Waiver behavior: reactive vs proactive, bid size tendencies
- Trade frequency and counterparty patterns
- Lineup decision quality as a season-long metric
- Signature tendencies: what this manager always does

### Layer 5: League history (partially implemented)
Championship history query built 2026-05-16. Not yet:
- All-time scoring records
- Longest streaks in league history
- Era analysis across 16 seasons
- Records set and broken
- Generational comparisons

### Layer 6: Real-world player performance (not implemented)
NFL box score data, season stats, injury history, usage trends.
Transforms "McCaffrey scored 32 points" into the full story of
what he did on the field and what it meant for the managers who
rostered him.

Required additions:
- Weekly NFL box scores (yards, TDs, targets, carries, snaps)
- Season-to-date stats for rostered players
- Injury and availability history
- Usage trends: role expanding or contracting

---

## The Writer's Room -- full scope

Receives verified, structured story inputs from the Signal Scout
and renders them as narrative artifacts. Does not compute. Does not
infer. Does not fill gaps with invention.

Responsible for:
- Selecting which angles to lead with
- Constructing narrative arc within the artifact
- Applying the Voice Profile consistently
- Producing prose that is specific, earned, and recognizable

Not responsible for:
- Verifying facts
- Computing figures not provided in context
- Any specific numeric claim not present in Signal Scout output

---

## Artifact types -- full scope

### Currently implemented
- Weekly recap (shared, league-wide)
- Rivalry Chronicle (shared, two-franchise)

### Required additions

Personal weekly digest (individual, per manager)
  The manager's week: their decisions, their players, their result,
  their standing. Delivered to each manager individually.

Season retrospective (shared, league-wide)
  The full story of a completed season: the arc, the turning point,
  the champion's path, the what-ifs, the records set.

Manager profile (individual, per manager)
  The story of a manager across their full history in the league:
  their style, their record, their best and worst seasons, their
  signature moments.

Draft retrospective (shared, per season)
  Who won the draft in hindsight. The steals. The overpays. The
  players who justified or betrayed their prices.

Trade audit (shared, per season or all-time)
  Who won each trade, measured in actual points produced. The trade
  that changed a season.

League history compendium (shared, all-time)
  The authoritative record of 16+ seasons: champions, records, eras,
  defining moments.

Player spotlight (shared, triggered by performance)
  When a real player materially affects multiple rosters, a
  player-focused artifact telling their story and its fantasy
  consequences.

---

## The data pipeline -- required additions

### Immediate (existing DB data, no new ingest)
1. Trade outcome computation
   Points produced by both sides after trade date. Who won. By how
   much. When the outcome became clear.

2. Acquisition value computation
   Points produced per dollar spent. Season-to-date and final totals.

3. Start/sit decision quality
   From WEEKLY_MATCHUP_RESULT optimal vs actual. Points left on bench
   per manager across the season. Lineup decision quality ranking.

4. Manager style fingerprinting
   From 16 seasons of draft, FAAB, and transaction history.
   Characterize each manager's approach as a structured profile.

5. League history record book
   All-time scoring, streak, and championship records.
   Full record book computable from existing data.

6. Season arc computation
   Turning points, momentum shifts, the week a season changed.

### Near-term (schema addition, no new source)
7. Injury tracking
   Record when players miss games. Join against fantasy scores to
   compute injury impact on roster outcomes.

### Medium-term (new data source required)
8. NFL box score ingest
   Weekly real-world player stats joined against fantasy roster data.

9. Player usage trends
   Snap counts, target shares, carry distribution.

### Long-term (evaluate feasibility)
10. League communication data
    Message board or group chat commentary. Opt-in. High storytelling
    value when available.

---

## The scope boundary

Inside the boundary:
- Retrospective evaluation: what happened, what it cost, what it produced
- Historical records: what has been true across the league's history
- Pattern description: what a manager tends to do, based on what they
  have done
- Outcome reporting: who won a trade, whose draft produced most

Outside the boundary (permanently):
- Prediction: what will happen
- Optimization: what a manager should do
- Recommendation: who to start, who to pick up, who to trade
- Engagement loops designed to drive return visits
- Analytics dashboards without narrative purpose

The test: does it report what happened, or does it suggest what to do?
If the latter, it stays out.

Retrospective performance evaluation is inside the boundary. It
describes the past accurately. It does not prescribe the future.

---

## Implementation sequencing

Arc 1: Data integrity (immediate -- in progress)
  Fix fabrication problem. Extend verifier. Constrain Writer's Room.
  Build commissioner review surface with claim annotation.
  Reference: session_brief_commissioner_review_arc.md

Arc 2: Fantasy player performance layer (next)
  Fully utilize WEEKLY_PLAYER_SCORE and WEEKLY_MATCHUP_RESULT.
  Compute acquisition value, start/sit quality, player arcs.
  Build Signal Scout detectors for these story types.

Arc 3: Manager identity and league history (following)
  Characterize each manager from 16 seasons of decisions.
  Build league history record book.
  Design manager profile and league history artifact types.

Arc 4: Trade and draft retrospective (following)
  Build trade outcome computation.
  Build draft retrospective artifact type.
  Retroactively evaluate all trades and drafts in DB.

Arc 5: Real-world player performance ingest (medium-term)
  Design schema for NFL box score data.
  Evaluate MFL API coverage.
  Build ingest pipeline.
  Extend Signal Scout to join fantasy and real-world performance.

Arc 6: Personal artifacts (following Arc 5)
  Design and build personal weekly digest.
  Design and build manager profile artifact.
  Establish per-manager distribution pipeline.

Arc 7: UI/UX commissioner surface (long-term)
  Design proper review and approval interface.
  Built on terminal tooling foundation from Arc 1.
  Extend to manager-facing distribution surface.

---

## What success looks like

A manager receives a SquadVault artifact and reads it from start to
finish. They recognize every claim as true. They feel the system
understood not just what happened, but what it meant. They share it
with the league without being asked.

A new manager joins and reads the league history compendium. They
understand the weight of the competition they are entering. They know
who the legends are, what the records mean, and what kind of league
this is.

A manager who has played for 15 years reads their manager profile and
finds it accurate. It captures their style, their history, their best
moments, and their worst. It reads like something written by someone
who watched every season. It was not. It was derived entirely from data.

That is the product.

---

## Governing principle: league average as baseline

Individual performance is most meaningful in context. League average
is the baseline that makes every personal metric legible.

Without context: "You left 23 points on your bench per week."
With context: "You left 23 points on your bench per week. The league
average was 18. Your lineup decisions were the costliest in the league
this season -- an estimated 3 additional wins with average decision
quality."

The same data. Completely different meaning.

This principle applies to every personal metric the system surfaces:

- Points scored vs league average
- Points allowed vs league average
- Bench points left vs league average (lineup decision quality)
- FAAB efficiency (points per dollar) vs league average
- Auction efficiency (points per dollar) vs league average
- Start/sit decision accuracy vs league average
- Trade outcome value vs league average
- Acquisition timing vs league average (who moves first)

League average comparison works in both directions. Underperformance
is a story. Outperformance is equally a story. Both deserve to be told
with the same specificity.

Percentile framing is encouraged where it adds clarity. "Your lineup
decisions placed you in the bottom 20% of the league" is more legible
than a raw bench points figure. Both the number and the percentile
should be available.

Historical league average comparison is also valid. "Your FAAB
efficiency this season (9.1 points per dollar) was the highest in
league history. The previous record was 8.3, set by Miller in 2019."
That is a fact. It is reportable.

Implementation note: league average figures must be computed at the
data layer and passed to the Writer's Room as verified context.
They are not to be synthesized or estimated by the Writer's Room.
