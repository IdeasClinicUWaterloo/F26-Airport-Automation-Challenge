# Stretch Goals

Pick these up **only once the core solution runs end to end and puts something on a
map**. A working simple tracker demos far better than a half-built sophisticated one,
and every item here is optional.

Times assume you already have the core working and are a first- or second-year
student who hasn't seen the material before. They're honest, not encouraging.

Each tier is self-contained — you don't need Tier 1 to attempt Tier 2.

---

## Tier 1 — an hour or two each, no new maths

These need nothing you don't already have. Good value: each one visibly improves the
demo, and any of them is a real answer to a judging criterion.

### Measure your accuracy — do this one first

`advanced/measure_accuracy.py` runs your tracker against a flight whose true track
is known and prints how far off it was. It needs no wiring; point it at your code
and run it.

*Why it matters:* it converts "our tracker works" into "our tracker holds 1.5 km
typical error and rejects position spikes above 50 km". It's also how you tell
whether any other item on this list actually helped, rather than guessing.

*Effort:* an hour to understand, zero to wire in.

### Grade the anomaly trust instead of using one constant

`ANOMALY_TRUST` is already wired through `tracker.update()`, but it's a flat number:
every flagged message is discounted by the same amount. Make it scale with how far
over the line the message landed, so one barely past the threshold is nudged down
slightly while a wild one is dropped entirely.

*Why it matters:* right now a 40 km surprise and a 400 km surprise are treated
identically, and only one of those is plausibly a real manoeuvre.

*Where to look:* `advanced/ekf.py`, in `update()` — it does this with two tiers, a
soft one and a hard gate.

### Track staleness

`tracker.predict()` will coast forward forever. Real systems refuse to: past some
number of minutes with no message, the track is stale and should say so rather than
quietly reporting a confident-looking position that's an extrapolation.

*Why it matters:* it's a genuine safety property, and it's the gap called out in the
main challenge README's regulatory section. Cheap to build, easy to explain to a judge.

*What you need:* one more knob and one more field in `get_state()`.

### Heading versus route geometry

Compare reported heading against the bearing to the next waypoint. If an aircraft
claims to be heading for a waypoint that's 90° off its nose, one of the two is wrong.

*Why it matters:* catches a class of error the position checks miss entirely — the
position is fine, the intent doesn't match it.

*What you need:* `find_bearing()` is already in `dead_reckoning.py`, and
`_has_passed()` in `message_parser.py` already does the "is it behind us" angle
comparison you'd reuse. Add a check alongside the other four.

### Sanity-check the reported ETA

`waypoint_report` messages carry an ETA that the core solution deliberately ignores
in favour of computing its own. Compare the two: if the reported ETA implies a speed
wildly different from the tracked one, flag it.

*What you need:* `_estimate_eta()` in `message_parser.py` already computes the
distance and speed you'd compare against. Work out the speed the reported ETA
implies, and flag it if the two differ by more than about a factor of two.

---

## Tier 2 — half a day each, some new ideas

Real scope. Attempt one, not several.

### Separate uncertainty per quantity

Right now one number covers position, and altitude/speed/heading are blended with
that same fraction. Give each its own uncertainty and its own drift rate. Altitude
during a climb is much less predictable than ground speed at cruise, and a single
number can't express that.

*Time:* 2–3 hours. *New maths:* none, just four copies of what's there.

*Why it's worth it:* it's the honest halfway house to a real filter, and it makes the
next item much less of a leap.

### Multi-hypothesis route tracking

When a route update contradicts history, the core solution accepts it and flags the
contradiction. The alternative is to keep both explanations alive with weights,
adjust the weights as messages support or contradict each one, and report the
strongest.

*Time:* 3–5 hours. *New ideas:* weights and normalization; not hard individually, but
there's a lot of bookkeeping and it's fiddly to debug.

*Where to look:* `advanced/hypothesis.py` gives you the `RouteHypothesis` class (92
lines, self-contained). The wiring is deliberately not provided — `advanced/README.md`
lists the five steps.

*Warning:* this changes the shape of your state everywhere, since "the route"
becomes "the current best route" — `get_state`, the ETA, the map, the waypoint
progress. That ripple is most of the work, not the new file.

### Reroute suggestion with graph search

Treat the waypoints as a graph weighted by distance and run Dijkstra or A\* to find a
path around a blocked waypoint (a storm cell, a restricted zone).

*Time:* 2–4 hours if you've seen Dijkstra, considerably more if not.

*Where to look:* `advanced/path_planning.py` — 93 lines and the most self-contained
thing in that folder. It doesn't touch the tracker at all, which makes it a safe
addition late on.

*Note:* the supplied nav data lists waypoints but no airways between them, so
`advanced/path_planning.py` treats every waypoint as connected to every other. Real
routing is constrained to published airways. Saying so out loud is worth marks.

---

## Tier 3 — read, don't build

### A real Extended Kalman Filter

Uncertainty as a 6×6 covariance matrix instead of one number, propagated through the
motion model's Jacobian, with chi-square gating on the innovation.

*Prerequisites, honestly:* covariance matrices, Jacobian linearization, chi-square
distributions with degrees of freedom, and eigendecomposition for the confidence
ellipse. Third-year material and up.

*The real obstacle isn't writing it, it's debugging it.* `PROCESS_NOISE` and
`MEASUREMENT_NOISE` are variances, not distances, so when the filter diverges you
can't reason about them the way you can about `DRIFT_PER_MINUTE_KM = 1.0` meaning
"a kilometre a minute". Knowing which of the six terms is wrong is intuition that
takes weeks. Teams that start here typically have no working demo at the end.

*It does work, though.* `advanced/ekf.py` is a drop-in replacement for `tracker.py`
— one changed import — and on the accuracy harness its median error is 0.02 km
against the simple tracker's 1.50 km. Swap it in and compare before deciding whether
that difference is worth a day of your hackathon.

### Build your own simulator

`advanced/simulator.py` already generates a known-truth flight for the accuracy
harness, so you don't need to write one. But if you want to understand the technique,
it's the most reusable thing in this challenge: any system that estimates something
can be tested by simulating a case where you know the answer.

*A cheap version worth writing yourself:* fly a straight line between two waypoints
at constant speed, sample it every few minutes, add a little random noise to each
sample, and feed those in as `state` messages. Maybe 40 lines, and you'll have built
your own answer key.

*Where to look:* `advanced/simulator.py` for the full version, and
`advanced/measure_accuracy.py` for how the scoring is done.
