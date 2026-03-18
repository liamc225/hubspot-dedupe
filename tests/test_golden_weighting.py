from _golden.weighting import WeightedSignal, calculate_score


def test_calculate_score_caps_at_100() -> None:
    score, reasons = calculate_score(
        [
            WeightedSignal(name="one", points=80, matched=True),
            WeightedSignal(name="two", points=40, matched=True),
        ]
    )

    assert score == 100
    assert reasons == ["one", "two"]

