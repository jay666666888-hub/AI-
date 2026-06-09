#!/usr/bin/env python3
"""
Calibration Governor - Anti-Reward-Hacking System
"""
import sys
import uuid
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

sys.path.insert(0, '/mnt/e/黑曜石/04_工作/AI开发生态系统/src')


class ConstraintType:
    ENTROPY_FLOOR = "entropy_floor"
    EXPLORATION_QUOTA = "exploration_quota"
    REWARD_CLIPPING = "reward_clipping"


@dataclass
class OutcomeRecord:
    timestamp: str
    task_id: str
    agent_id: str
    predicted_utility: float
    actual_outcome: float
    confidence: float


class CalibrationBuffer:
    def __init__(self, batch_size=20, min_buffer_size=10):
        self.batch_size = batch_size
        self.min_buffer_size = min_buffer_size
        self.buffer: List[OutcomeRecord] = []

    def record(self, task_id, agent_id, predicted, actual, confidence):
        self.buffer.append(OutcomeRecord(
            timestamp=datetime.now().isoformat(),
            task_id=task_id, agent_id=agent_id,
            predicted_utility=predicted, actual_outcome=actual,
            confidence=confidence
        ))

    def should_update(self):
        if len(self.buffer) < self.min_buffer_size:
            return False, f"Buffer too small: {len(self.buffer)}/{self.min_buffer_size}"
        if len(self.buffer) >= self.batch_size:
            return True, f"Batch size reached: {len(self.buffer)}/{self.batch_size}"
        if self.buffer:
            oldest = datetime.fromisoformat(self.buffer[0].timestamp)
            if datetime.now() - oldest > timedelta(hours=1):
                return True, "Time window exceeded"
        return False, f"Waiting: {len(self.buffer)}/{self.batch_size}"

    def get_batch(self):
        batch = self.buffer[:self.batch_size]
        self.buffer = self.buffer[self.batch_size:]
        return batch


class AntiConstraints:
    def __init__(self):
        self.entropy_floor = 0.3
        self.routing_diversity_floor = 0.4
        self.reward_clip_max = 1.0
        self.min_confidence = 0.3

    def check(self, agent_dist, predicted, confidence):
        results = []
        total = sum(agent_dist.values()) if agent_dist else 0
        
        # Entropy check
        if total > 0:
            entropy = 0.0
            for c in agent_dist.values():
                p = c / total
                if p > 0:
                    entropy -= p * (p ** 0.5)
            # Map to [0, 1] range - simplified formula can be negative
            entropy = max(0.0, min(1.0, entropy + 1.0))
            results.append({
                "constraint": "entropy_floor",
                "satisfied": entropy >= self.entropy_floor,
                "value": entropy,
                "threshold": self.entropy_floor
            })
            
            # Routing diversity
            max_ratio = max(agent_dist.values()) / total
            results.append({
                "constraint": "routing_diversity",
                "satisfied": max_ratio <= self.routing_diversity_floor,
                "value": max_ratio,
                "threshold": self.routing_diversity_floor
            })
        
        # Reward clipping
        results.append({
            "constraint": "reward_clipping",
            "satisfied": 0 <= predicted <= self.reward_clip_max,
            "value": predicted,
            "threshold": self.reward_clip_max
        })
        
        # Confidence
        results.append({
            "constraint": "confidence_threshold",
            "satisfied": confidence >= self.min_confidence,
            "value": confidence,
            "threshold": self.min_confidence
        })
        
        return results


class CalibrationCurve:
    def __init__(self, num_buckets=10):
        self.num_buckets = num_buckets
        self.buckets: Dict[int, List] = defaultdict(list)

    def add(self, predicted, actual):
        bucket_idx = min(int(predicted * self.num_buckets), self.num_buckets - 1)
        self.buckets[bucket_idx].append((predicted, actual))

    def compute_curve(self):
        points = []
        for bucket_idx in range(self.num_buckets):
            if bucket_idx not in self.buckets:
                continue
            pts = self.buckets[bucket_idx]
            mean_pred = statistics.mean(p for p, a in pts)
            mean_actual = statistics.mean(a for p, a in pts)
            points.append({
                "bucket": bucket_idx / self.num_buckets,
                "mean_predicted": mean_pred,
                "mean_actual": mean_actual,
                "count": len(pts)
            })
        return points

    def compute_ece(self):
        points = self.compute_curve()
        if not points:
            return 0.0
        total = sum(p["count"] for p in points)
        ece = 0.0
        for p in points:
            weight = p["count"] / total
            ece += weight * abs(p["mean_predicted"] - p["mean_actual"])
        return ece

    def is_well_calibrated(self, threshold=0.1):
        ece = self.compute_ece()
        return ece < threshold, ece


class RewardDriftDetector:
    def __init__(self, lookback_days=7):
        self.lookback_days = lookback_days
        self.history = []

    def record(self, date, mean_utility):
        self.history.append({"date": date, "mean_utility": mean_utility})
        cutoff = datetime.now() - timedelta(days=self.lookback_days)
        self.history = [h for h in self.history if datetime.fromisoformat(h["date"]) > cutoff]

    def detect(self):
        if len(self.history) < 2:
            return {"has_drift": False, "direction": "unknown", "magnitude": 0.0}
        
        baselines = [h["mean_utility"] for h in self.history]
        current, oldest = baselines[-1], baselines[0]
        drift_magnitude = abs(current - oldest)
        slope = (baselines[-1] - baselines[0]) / (len(baselines) - 1) if len(baselines) > 1 else 0
        
        return {
            "has_drift": drift_magnitude > 0.1,
            "direction": "increasing" if slope > 0.02 else "decreasing" if slope < -0.02 else "stable",
            "magnitude": drift_magnitude,
            "current_baseline": current
        }


class GovernancePressureMonitor:
    def __init__(self, window_size=100):
        self.window_size = window_size
        self.decisions = []

    def record(self, decision):
        self.decisions.append({"decision": decision, "timestamp": datetime.now().isoformat()})
        if len(self.decisions) > self.window_size:
            self.decisions = self.decisions[-self.window_size:]

    def get_status(self):
        if len(self.decisions) < 10:
            return {"status": "unknown", "block_rate": 0.0}
        
        blocked = sum(1 for d in self.decisions if d["decision"] == "blocked")
        block_rate = blocked / len(self.decisions)
        
        status = "optimal"
        if block_rate > 0.5:
            status = "too_restrictive"
        elif block_rate < 0.05:
            status = "too_permissive"
        
        return {"status": status, "block_rate": block_rate, "total": len(self.decisions)}


class CalibrationGovernor:
    def __init__(self):
        self.buffer = CalibrationBuffer()
        self.constraints = AntiConstraints()
        self.calibration_curve = CalibrationCurve()
        self.reward_drift = RewardDriftDetector()
        self.governance = GovernancePressureMonitor()
        self.weights = {"utility": 1.0, "routing": 1.0, "governance": 1.0}
        self.total_updates = 0
        self.blocked_updates = 0

    def record(self, task_id, agent_id, predicted, actual, confidence):
        self.buffer.record(task_id, agent_id, predicted, actual, confidence)
        self.calibration_curve.add(predicted, actual)
        self.governance.record("approved")

    def compute_update(self):
        should_update, reason = self.buffer.should_update()
        if not should_update:
            return None

        batch = self.buffer.get_batch()
        if not batch:
            return None

        agent_dist = Counter(r.agent_id for r in batch)
        constraint_results = self.constraints.check(
            dict(agent_dist), batch[0].predicted_utility, batch[0].confidence
        )

        blocked = [r for r in constraint_results if not r["satisfied"]]
        if blocked:
            self.blocked_updates += 1
            return {"blocked": True, "reasons": [str(b) for b in blocked]}

        confidences = [r.confidence for r in batch]
        actuals = [r.actual_outcome for r in batch]
        
        avg_conf = statistics.mean(confidences)
        stability = max(0.0, 1.0 - statistics.stdev(actuals)) if len(actuals) > 1 else 1.0
        learning_rate = 0.1 * avg_conf * stability
        
        errors = [r.predicted_utility - r.actual_outcome for r in batch]
        mean_error = statistics.mean(errors)
        
        self.weights["utility"] *= (1.0 - learning_rate * mean_error)
        self.total_updates += 1
        
        return {
            "blocked": False,
            "confidence": avg_conf,
            "stability": stability,
            "learning_rate": learning_rate,
            "adjustments": self.weights.copy()
        }

    def get_status(self):
        is_calibrated, ece = self.calibration_curve.is_well_calibrated(threshold=0.1)
        return {
            "calibration": {"is_calibrated": is_calibrated, "ece": ece},
            "drift": self.reward_drift.detect(),
            "governance": self.governance.get_status(),
            "buffer_size": len(self.buffer.buffer),
            "weights": self.weights,
            "updates": {"total": self.total_updates, "blocked": self.blocked_updates}
        }


if __name__ == "__main__":
    print("CALIBRATION GOVERNOR - Anti-Reward-Hacking System")
    print("=" * 60)

    governor = CalibrationGovernor()

    print("\n[1] Recording predictions and outcomes...")
    scenarios = [
        (0.8, 0.75, 0.9, "planner"),
        (0.7, 0.65, 0.8, "coder"),
        (0.9, 0.62, 0.7, "reviewer"),
        (0.6, 0.55, 0.85, "tester"),
        (0.75, 0.78, 0.95, "planner"),
        (0.65, 0.60, 0.75, "coder"),
        (0.85, 0.80, 0.9, "reviewer"),
        (0.7, 0.72, 0.88, "tester"),
        (0.8, 0.76, 0.92, "planner"),
        (0.75, 0.68, 0.78, "coder"),
        (0.9, 0.85, 0.95, "reviewer"),
        (0.6, 0.58, 0.82, "tester"),
        (0.95, 0.50, 0.6, "deployer"),
        (0.88, 0.45, 0.55, "deployer"),
        (0.92, 0.52, 0.58, "deployer"),
        (0.85, 0.78, 0.88, "planner"),
        (0.72, 0.70, 0.85, "coder"),
        (0.78, 0.75, 0.90, "reviewer"),
        (0.68, 0.65, 0.80, "tester"),
        (0.82, 0.80, 0.92, "deployer"),
    ]

    for predicted, actual, confidence, agent in scenarios:
        governor.record(str(uuid.uuid4())[:8], agent, predicted, actual, confidence)

    print(f"  Recorded {len(scenarios)} scenarios")

    print("\n[2] Computing update...")
    update = governor.compute_update()
    if update:
        if update.get("blocked"):
            print(f"  BLOCKED: {update['reasons']}")
        else:
            print(f"  Confidence: {update['confidence']:.2f}")
            print(f"  Stability: {update['stability']:.2f}")
            print(f"  Weights: {update['adjustments']}")
    else:
        print("  Buffer not ready")

    print("\n[3] Status Report:")
    status = governor.get_status()
    print(f"  Calibration: is_calibrated={status['calibration']['is_calibrated']}, ECE={status['calibration']['ece']:.3f}")
    print(f"  Drift: {status['drift']}")
    print(f"  Governance: status={status['governance']['status']}, block_rate={status['governance']['block_rate']:.1%}")
    print(f"  Buffer: {status['buffer_size']} samples")
    print(f"  Updates: total={status['updates']['total']}, blocked={status['updates']['blocked']}")

    print("\n[4] Calibration Curve:")
    curve = governor.calibration_curve.compute_curve()
    for p in curve:
        print(f"  Bucket {p['bucket']:.1f}: pred={p['mean_predicted']:.2f}, actual={p['mean_actual']:.2f}, n={p['count']}")

    print("=" * 60)
