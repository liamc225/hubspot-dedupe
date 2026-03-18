from dataclasses import dataclass


@dataclass(frozen=True)
class WeightedSignal:
    name: str
    points: int
    matched: bool


def calculate_score(signals: list[WeightedSignal]) -> tuple[int, list[str]]:
    score = 0
    matched_reasons: list[str] = []

    for signal in signals:
        if signal.matched:
            score += signal.points
            matched_reasons.append(signal.name)

    return min(score, 100), matched_reasons

