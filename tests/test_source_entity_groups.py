from custom_components.pv_forecast_fusion.source_entity_groups import (
    aggregate_curve_values,
    aggregate_numeric_values,
    expand_entity_group,
)


def test_expand_entity_group_autofills_multiple_forecast_solar_entities():
    resolved = expand_entity_group(
        today_entities="sensor.energy_production_today, sensor.energy_production_today_2",
        tomorrow_entities="",
        remaining_entities="",
        attributes_by_today_entity={},
        configured_source_type="forecast_solar",
    )

    assert [item.today_entity for item in resolved.items] == [
        "sensor.energy_production_today",
        "sensor.energy_production_today_2",
    ]
    assert [item.tomorrow_entity for item in resolved.items] == [
        "sensor.energy_production_tomorrow",
        "sensor.energy_production_tomorrow_2",
    ]
    assert [item.remaining_entity for item in resolved.items] == [
        "sensor.energy_production_today_remaining",
        "sensor.energy_production_today_remaining_2",
    ]


def test_expand_entity_group_pairs_explicit_tomorrow_and_remaining_lists_by_position():
    resolved = expand_entity_group(
        today_entities="sensor.a_today, sensor.b_today",
        tomorrow_entities="sensor.a_tomorrow, sensor.b_tomorrow",
        remaining_entities="sensor.a_remaining, sensor.b_remaining",
        attributes_by_today_entity={},
        configured_source_type="manual",
    )

    assert [item.tomorrow_entity for item in resolved.items] == ["sensor.a_tomorrow", "sensor.b_tomorrow"]
    assert [item.remaining_entity for item in resolved.items] == ["sensor.a_remaining", "sensor.b_remaining"]


def test_expand_entity_group_preserves_blank_placeholders_for_positional_mapping():
    resolved = expand_entity_group(
        today_entities="sensor.a_today, sensor.b_today, sensor.c_today",
        tomorrow_entities="sensor.a_tomorrow, , sensor.c_tomorrow",
        remaining_entities="sensor.a_remaining, , sensor.c_remaining",
        attributes_by_today_entity={},
        configured_source_type="manual",
    )

    assert [item.tomorrow_entity for item in resolved.items] == [
        "sensor.a_tomorrow",
        None,
        "sensor.c_tomorrow",
    ]
    assert [item.remaining_entity for item in resolved.items] == [
        "sensor.a_remaining",
        None,
        "sensor.c_remaining",
    ]


def test_aggregate_numeric_values_sums_available_values_only():
    assert aggregate_numeric_values([11.063, None, 9.999]) == 21.062
    assert aggregate_numeric_values([None, None]) is None


def test_aggregate_curve_values_sums_curves_elementwise():
    combined = aggregate_curve_values([
        [1.0, 2.0, 3.0],
        [0.5, 1.5],
        [],
    ])

    assert combined == [1.5, 3.5, 3.0]
