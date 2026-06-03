# Home Assistant PV Forecast Fusion

A Home Assistant custom integration that combines multiple PV forecast sensors into one explainable fused forecast.

## MVP

- configurable source slots
- auto-detection and auto-mapping for Solcast, Forecast.Solar and Open-Meteo/Solar production forecast entities
- per-source weight, bias factor and confidence
- fused sensors for today, tomorrow and remaining today
- weather pattern classification from intraday curves
- diagnostic attributes with raw source inputs and preset resolution info

## Planned next steps

- source type selector and provider-specific defaults in the config flow UI
- minute offset per source
- historical calibration against actual production
- weather-class specific learning
