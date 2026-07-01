from app.agents import filter_agent, trust_agent
from app.core.schemas import Product


def make_product(**kwargs) -> Product:
    defaults = dict(title="boAt Rockerz 255 Pro+", brand="boAt", position=1, price=999.0, rating=4.1, reviews_count=45231)
    defaults.update(kwargs)
    return Product(**defaults)


def test_filter_agent_scores_and_sorts_by_match():
    p1 = make_product(asin="A1", title="Gaming Bluetooth Earbuds Low Latency", position=3,
                       specs={"latency": "low"})
    p2 = make_product(asin="A2", title="Basic Wired Earphones", position=1, specs={})
    ranked = filter_agent.run([p1, p2], priority_specs=["latency"])
    assert ranked[0].asin == "A1"
    assert ranked[0].match_score == 1.0
    assert ranked[1].match_score == 0.0


def test_filter_agent_no_specs_falls_back_to_serp_position():
    p1 = make_product(asin="A1", position=2)
    p2 = make_product(asin="A2", position=1)
    ranked = filter_agent.run([p1, p2], priority_specs=[])
    assert [p.asin for p in ranked] == ["A2", "A1"]


def test_trust_agent_scores_reasonable_range():
    p = make_product(rating=4.5, reviews_count=10000)
    reviews = [{"verified_purchase": True}] * 8 + [{"verified_purchase": False}] * 2
    scored = trust_agent.run(p, reviews)
    assert 0 <= scored.trust_score <= 100
    assert scored.kept_pct is not None
    assert "Highly Trusted" in scored.badges


def test_trust_agent_flags_low_review_volume():
    p = make_product(rating=4.0, reviews_count=5)
    scored = trust_agent.run(p, [])
    assert "Limited Review Data" in scored.badges
