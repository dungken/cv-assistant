"""Learning Path Optimizer — Tuần 12.

Two strategies plug into the `Solver` protocol from lp_benchmark.py:

- `GreedyStrategy`  — pseudocode from §2.2.2; cached ΔJ per skill; deterministic
                      tie-break by (jd_unlocked desc, trend desc-not-used-here, name asc).
- `DijkstraStrategy` — state-space search per §2.2.3; states are frozensets of
                      learned skills; pruning by budget + relevance + prereq.

The Tuần 13 DP solver will live alongside these as a third Solver.

Production default is Greedy (see §3.3.2). Dijkstra is exposed for benchmarking
and for the "lộ trình tối ưu" path-mode in the API.
"""
from __future__ import annotations

import heapq
import logging
import time
from dataclasses import dataclass
from typing import Optional

from services.skill_service.services.lp_benchmark import (
    JD, SolverResult, TestCase, _cost, _prereqs, candidates_for,
    expand_with_prereqs, jd_unlocked,
)
from services.skill_service.services.ontology import SkillOntology

logger = logging.getLogger(__name__)


# ─── Reasoning / explanation ──────────────────────────────────────────────────


@dataclass
class PathStep:
    order: int
    skill: str
    cost_weeks: int
    reason: str
    jd_unlocked_after_this: list[str]


@dataclass
class ExplainedPath:
    steps: list[PathStep]
    total_weeks: int
    jd_unlocked_count: int
    jd_unlocked_total: int
    algorithm: str


def explain_path(path: list[str], tc: TestCase, ontology: SkillOntology, algorithm: str) -> ExplainedPath:
    owned: set[str] = set(tc.S_user)
    steps: list[PathStep] = []
    prev_unlocked_ids: set[str] = {
        j.id for j in tc.JDs if set(j.required).issubset(owned)
    }
    for i, sk in enumerate(path, start=1):
        owned.add(sk)
        now_unlocked_ids = [j.id for j in tc.JDs if set(j.required).issubset(owned)]
        newly = [jd for jd in now_unlocked_ids if jd not in prev_unlocked_ids]
        reason = _reason_for_step(sk, newly, tc, ontology, _cost(sk, ontology))
        steps.append(PathStep(
            order=i, skill=sk, cost_weeks=_cost(sk, ontology),
            reason=reason, jd_unlocked_after_this=now_unlocked_ids,
        ))
        prev_unlocked_ids = set(now_unlocked_ids)

    return ExplainedPath(
        steps=steps,
        total_weeks=sum(s.cost_weeks for s in steps),
        jd_unlocked_count=len(prev_unlocked_ids),
        jd_unlocked_total=len(tc.JDs),
        algorithm=algorithm,
    )


def _better_step(cand: tuple, current: tuple) -> bool:
    """Tuple compare with mixed asc/desc fields:
    (roi, gain, cost, chain_len, name) — first two desc, last three asc.
    Returns True if `cand` strictly beats `current`.
    """
    c_roi, c_gain, c_cost, c_len, c_name = cand
    b_roi, b_gain, b_cost, b_len, b_name = current
    if c_roi != b_roi:
        return c_roi > b_roi
    if c_gain != b_gain:
        return c_gain > b_gain
    if c_cost != b_cost:
        return c_cost < b_cost
    if c_len != b_len:
        return c_len < b_len
    return c_name < b_name


def _reason_for_step(skill: str, newly_unlocked: list[str], tc: TestCase,
                     ontology: SkillOntology, cost: int) -> str:
    if newly_unlocked:
        roi = len(newly_unlocked) / max(cost, 1)
        return f"Mở khóa thêm {len(newly_unlocked)} JD (ROI {roi:.2f} JD/tuần)."
    return "Là prerequisite cho skill chính tiếp theo trong lộ trình."


# ─── Greedy ───────────────────────────────────────────────────────────────────


class GreedyStrategy:
    """ROI-based greedy from §2.2.2 with two extensions to handle real-shape JDs
    where no single skill unlocks a JD on its own:

    1. **Soft ROI fallback.** When no candidate has integer-JD gain > 0, switch
       to a fractional objective: ROI_soft = (sum of progress fractions across JDs
       still in reach within remaining budget) / chain_cost. A "progress fraction"
       is `1 / |R(j) \\ owned|` — i.e. the marginal contribution to filling one JD.

    2. **Reach filter.** Only consider candidates that actually appear in some JD
       still feasible with remaining_budget; skip skills that can't possibly help.

    Deterministic tie-break: (roi desc, gain desc, cost asc, chain_len asc, name asc).
    """

    name = "greedy"

    def solve(self, tc: TestCase, ontology: SkillOntology) -> SolverResult:
        start = time.perf_counter()

        owned: set[str] = set(tc.S_user)
        path: list[str] = []
        remaining = tc.budget
        all_cands = sorted(candidates_for(tc))  # alphabetical baseline tie-break

        while True:
            # Phase 1: try integer-gain ROI.
            best = self._best_step(
                tc, ontology, owned, remaining, all_cands, scoring="integer",
            )
            if best is None:
                # Phase 2: fall back to fractional progress (no single skill unlocks anything).
                best = self._best_step(
                    tc, ontology, owned, remaining, all_cands, scoring="fractional",
                )
            if best is None:
                break

            _, _, _, chain, chain_cost = best
            for sk in chain:
                owned.add(sk)
                path.append(sk)
            remaining -= chain_cost

        return SolverResult(
            path=path,
            total_cost=sum(_cost(s, ontology) for s in path),
            jd_unlocked=jd_unlocked(owned, tc.JDs),
            runtime_s=time.perf_counter() - start,
        )

    def _best_step(
        self, tc: TestCase, ontology: SkillOntology,
        owned: set[str], remaining: int, cands: list[str], scoring: str,
    ) -> Optional[tuple[float, float, str, list[str], int]]:
        """Return (roi, gain, name, chain, chain_cost) or None."""
        best: Optional[tuple[float, float, str, list[str], int]] = None
        base_unlocked = jd_unlocked(owned, tc.JDs)
        # JDs still in reach: those whose missing-skill cost (rough) ≤ remaining.
        feasible_jds = [j for j in tc.JDs if self._jd_feasible(j, owned, ontology, remaining)]
        if not feasible_jds:
            return None

        for v in cands:
            if v in owned:
                continue
            chain = expand_with_prereqs([v], owned, ontology)
            chain_cost = sum(_cost(s, ontology) for s in chain)
            if chain_cost == 0 or chain_cost > remaining:
                continue
            new_owned = owned | set(chain)

            if scoring == "integer":
                gain = jd_unlocked(new_owned, tc.JDs) - base_unlocked
                if gain <= 0:
                    continue
            else:  # fractional
                gain = self._fractional_progress(new_owned, owned, feasible_jds)
                if gain <= 0:
                    continue

            roi = gain / chain_cost
            # Tie-break: higher roi → higher gain → lower chain_cost → shorter chain → alpha-first name.
            # We compare with current best as a separate function to handle the
            # mixed asc/desc fields cleanly.
            if best is None or _better_step(
                (roi, gain, chain_cost, len(chain), v),
                (best[0], best[1], best[4], len(best[3]), best[2]),
            ):
                best = (roi, gain, v, chain, chain_cost)
        return best

    def _jd_feasible(self, jd: JD, owned: set[str], ontology: SkillOntology, remaining: int) -> bool:
        """Cheap feasibility test: cost to learn missing skills (without prereqs) ≤ remaining."""
        missing = [s for s in jd.required if s not in owned]
        rough_cost = sum(_cost(s, ontology) for s in missing)
        return rough_cost <= remaining

    def _fractional_progress(
        self, new_owned: set[str], old_owned: set[str], feasible_jds: list[JD],
    ) -> float:
        """Sum over still-feasible JDs of (missing_before − missing_after) / missing_before.
        Range [0, n_jds]; higher means we filled more of the gaps."""
        total = 0.0
        for jd in feasible_jds:
            req = set(jd.required)
            missing_before = len(req - old_owned)
            if missing_before == 0:
                continue  # already unlocked
            missing_after = len(req - new_owned)
            if missing_after < missing_before:
                total += (missing_before - missing_after) / missing_before
        return total


# ─── Dijkstra ─────────────────────────────────────────────────────────────────


class DijkstraStrategy:
    """State-space Dijkstra over skill subsets.

    State = frozenset of skills owned. Edges add one candidate skill (with its
    prereqs auto-expanded). We expand states in order of total cost and keep
    the best (jd_unlocked, lowest cost) seen.
    """

    name = "dijkstra"

    def __init__(self, max_states: int = 50_000):
        self.max_states = max_states

    def solve(self, tc: TestCase, ontology: SkillOntology) -> SolverResult:
        start = time.perf_counter()
        owned0 = frozenset(tc.S_user)
        cands = candidates_for(tc)
        if not cands:
            return SolverResult(path=[], total_cost=0,
                                jd_unlocked=jd_unlocked(set(owned0), tc.JDs),
                                runtime_s=time.perf_counter() - start)

        best_jd0 = jd_unlocked(set(owned0), tc.JDs)
        best: tuple[int, int, frozenset, tuple] = (best_jd0, 0, owned0, ())
        # (jd_unlocked, -cost_inverted_for_min, state, path_tuple)
        # We'll track (jd_unlocked desc, cost asc, lex(path)) for determinism.

        visited: dict[frozenset, int] = {owned0: 0}
        heap: list = []
        # Tuple in heap: (total_cost, tiebreak_seq, state, path_tuple)
        counter = 0
        heapq.heappush(heap, (0, counter, owned0, ()))
        states_expanded = 0

        while heap and states_expanded < self.max_states:
            cost, _, state, path_t = heapq.heappop(heap)
            if cost > visited.get(state, cost):
                continue
            states_expanded += 1

            j_unlocked = jd_unlocked(set(state), tc.JDs)
            cand_key = (j_unlocked, -cost)
            best_key = (best[0], -best[1])
            if cand_key > best_key or (cand_key == best_key and path_t < best[3]):
                best = (j_unlocked, cost, state, path_t)

            # Expand: try adding each candidate skill (with prereqs).
            for v in cands:
                if v in state:
                    continue
                chain = expand_with_prereqs([v], set(state), ontology)
                chain_cost = sum(_cost(s, ontology) for s in chain)
                if chain_cost == 0:
                    continue
                new_cost = cost + chain_cost
                if new_cost > tc.budget:
                    continue
                new_state = state | frozenset(chain)
                if new_cost >= visited.get(new_state, new_cost + 1):
                    continue
                visited[new_state] = new_cost
                counter += 1
                heapq.heappush(
                    heap,
                    (new_cost, counter, new_state, path_t + tuple(chain)),
                )

        if states_expanded >= self.max_states:
            logger.warning("Dijkstra hit max_states=%d for tc=%s", self.max_states, tc.test_id)

        path = list(best[3])
        return SolverResult(
            path=path,
            total_cost=best[1],
            jd_unlocked=best[0],
            runtime_s=time.perf_counter() - start,
        )


# ─── Dynamic Programming (Tuần 13) ────────────────────────────────────────────


class DPStrategy:
    """0/1-knapsack-style DP over candidate skills per §2.2.4.

    State table best[i][b] holds the max JD-unlock count achievable using a
    subset of candidates[:i] with total cost ≤ b. Because the unlock count is
    *not* separable across items (a JD only counts when *all* its required
    skills are owned), we also keep `track[i][b]` — the actual best subset at
    that cell — so the recurrence can re-evaluate `count_JDs_covered` against
    the real candidate subset rather than treating each gain as independent.

    Candidates are pre-expanded with their REQUIRES closure so any chosen item
    already drags in its prereqs (matching what Greedy/Dijkstra do via
    `expand_with_prereqs`). The "item cost" is therefore the cost of the whole
    closure for skills currently outside `S_user`.

    Trade-off accepted: O(n · B · |J|) wall-clock with n ≤ ~30, B ≤ 25, |J| ≤
    ~20 fits comfortably under 1s. For larger n this collapses to brute force.
    """

    name = "dp"

    def __init__(self, max_candidates: int = 30, brute_force_threshold: int = 20):
        """`brute_force_threshold`: when |candidates| ≤ this, exhaustively search
        all 2^n subsets — required because the unlock-count objective is not
        separable per item, so single-cell DP can prune away necessary
        intermediate subsets. For n > threshold and ≤ max_candidates, we use
        the bitmask DP with the cell-level dominance approximation accepting
        ~few-percent suboptimality (still much better than Greedy as a baseline).
        """
        self.max_candidates = max_candidates
        self.brute_force_threshold = brute_force_threshold

    def solve(self, tc: TestCase, ontology: SkillOntology) -> SolverResult:
        start = time.perf_counter()
        owned0 = set(tc.S_user)
        # 1. Build the candidate list, each with its REQUIRES closure + total cost.
        raw_cands = candidates_for(tc)
        if len(raw_cands) > self.max_candidates:
            logger.warning(
                "DP refusing %d candidates (max=%d) for tc=%s; falling back to greedy",
                len(raw_cands), self.max_candidates, tc.test_id,
            )
            return GreedyStrategy().solve(tc, ontology)
        if len(raw_cands) <= self.brute_force_threshold:
            # Exact via exhaustive subset enumeration — handles non-separable objective.
            from services.skill_service.services.lp_benchmark import solve_brute_force
            return solve_brute_force(tc, ontology, max_candidates=self.brute_force_threshold)

        items: list[tuple[str, tuple[str, ...], int]] = []
        for v in raw_cands:
            chain = tuple(expand_with_prereqs([v], owned0, ontology))
            chain_cost = sum(_cost(s, ontology) for s in chain)
            if chain_cost == 0 or chain_cost > tc.budget:
                continue
            items.append((v, chain, chain_cost))

        n = len(items)
        B = tc.budget

        # best[i][b] = (jd_unlocked, total_cost, subset_tuple)
        # subset_tuple is the tuple of "chosen v" (in input order) — we re-derive
        # the owned-skill set from chains to evaluate gain.
        best: list[list[tuple[int, int, tuple[int, ...]]]] = [
            [(0, 0, ())] * (B + 1) for _ in range(n + 1)
        ]
        # Cache jd_unlocked for chosen subsets (encoded as bitmask of indices).
        cover_cache: dict[int, int] = {}

        def coverage_of(mask: int) -> int:
            cached = cover_cache.get(mask)
            if cached is not None:
                return cached
            owned = set(owned0)
            m = mask
            i = 0
            while m:
                if m & 1:
                    owned.update(items[i][1])
                m >>= 1
                i += 1
            cnt = jd_unlocked(owned, tc.JDs)
            cover_cache[mask] = cnt
            return cnt

        for i in range(1, n + 1):
            v_idx = i - 1
            _, _, c = items[v_idx]
            for b in range(B + 1):
                # Don't take v_i
                best[i][b] = best[i - 1][b]
                # Take v_i
                if b >= c:
                    prev_jd, prev_cost, prev_subset = best[i - 1][b - c]
                    new_subset = prev_subset + (v_idx,)
                    new_mask = 0
                    for idx in new_subset:
                        new_mask |= 1 << idx
                    new_jd = coverage_of(new_mask)
                    new_cost = prev_cost + c
                    cur_jd, cur_cost, cur_subset = best[i][b]
                    # Tie-break: more JDs is the primary objective. When tied,
                    # we prefer the *larger* subset to preserve investment
                    # options for later rows (avoids the empty-prefix trap that
                    # would prevent combinations like {FastAPI, PostgreSQL,
                    # Docker} from ever forming when no single skill unlocks a
                    # JD). After larger-subset, prefer lower cost then lex order
                    # for determinism.
                    if (new_jd, len(new_subset), -new_cost, new_subset) > (
                        cur_jd, len(cur_subset), -cur_cost, cur_subset
                    ):
                        best[i][b] = (new_jd, new_cost, new_subset)
                # Early termination: if we've covered all JDs, no benefit from continuing this row.
                if best[i][b][0] == len(tc.JDs):
                    # propagate to remaining b cells
                    for b2 in range(b + 1, B + 1):
                        if best[i][b2][0] < best[i][b][0]:
                            best[i][b2] = best[i][b]

        final_jd, _, final_subset = best[n][B]

        # Prune: the tie-break favors larger subsets to avoid the empty-prefix
        # trap, so the raw DP output may include skills that don't contribute
        # to coverage. Drop any skill (and its private prereqs) whose removal
        # does not reduce the unlock count. This keeps DP at the JD-optimum
        # while restoring cost-minimality among optima.
        chosen = list(final_subset)
        changed = True
        while changed:
            changed = False
            for k in range(len(chosen) - 1, -1, -1):
                trial = chosen[:k] + chosen[k + 1:]
                trial_mask = 0
                for idx in trial:
                    trial_mask |= 1 << idx
                if coverage_of(trial_mask) >= final_jd:
                    chosen = trial
                    changed = True
                    break

        # Materialize the actual learning order (with prereq chains, dedup).
        path: list[str] = []
        seen_skill: set[str] = set(owned0)
        for idx in chosen:
            for sk in items[idx][1]:
                if sk not in seen_skill:
                    path.append(sk)
                    seen_skill.add(sk)
        final_cost = sum(_cost(s, ontology) for s in path)

        return SolverResult(
            path=path,
            total_cost=final_cost,
            jd_unlocked=final_jd,
            runtime_s=time.perf_counter() - start,
        )


# ─── Public optimizer (strategy registry) ─────────────────────────────────────


_STRATEGIES = {
    "greedy": GreedyStrategy,
    "dijkstra": DijkstraStrategy,
    "dp": DPStrategy,
}


class LearningPathOptimizer:
    """Strategy-pattern façade matching §3.3.2."""

    def __init__(self, ontology: SkillOntology):
        self.ontology = ontology

    def optimize(self, tc: TestCase, algorithm: str = "greedy") -> tuple[SolverResult, ExplainedPath]:
        cls = _STRATEGIES.get(algorithm)
        if cls is None:
            raise ValueError(f"Unknown algorithm '{algorithm}'. Available: {sorted(_STRATEGIES)}")
        solver = cls()
        result = solver.solve(tc, self.ontology)
        explained = explain_path(result.path, tc, self.ontology, algorithm)
        return result, explained
