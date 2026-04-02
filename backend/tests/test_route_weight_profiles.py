from app.core.routing_profiles import routing_profiles_config


def test_mode_multipliers_are_strongly_separated():
    assert routing_profiles_config.safe_risk_multiplier > routing_profiles_config.balanced_risk_multiplier
    assert routing_profiles_config.night_base_risk_multiplier >= routing_profiles_config.safe_risk_multiplier
