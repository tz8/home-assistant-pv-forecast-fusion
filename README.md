# Home Assistant PV Forecast Fusion

A Home Assistant custom integration that combines multiple PV forecast sensors into one explainable fused forecast.

## MVP

- configurable source slots
- per-source weight, bias factor and confidence
- fused sensors for today, tomorrow and remaining today
- weather pattern classification from intraday curves
- diagnostic attributes with raw source inputs

## Planned next steps

- presets for Solcast / Forecast.Solar / Open-Meteo
- minute offset per source
- historical calibration against actual production
- weather-class specific learning
