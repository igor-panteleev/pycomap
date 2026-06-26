# Configuration

Parsing of the controller's `ConfigurationTable` (C.O. 24575) and bulk decode
of `ValuesAll` / `SetpointsAll` blobs. The [`Controller`](controller.md) calls
these internally — you only need them directly when working with raw blobs.

## Descriptions

::: pycomap.configuration.ValueDescription

::: pycomap.configuration.SetpointDescription

::: pycomap.configuration.ValueState

## Enums

::: pycomap.configuration.ValueCategory

::: pycomap.configuration.SetpointCategory

::: pycomap.configuration.NamesCategory

## Functions

::: pycomap.configuration.parse_configuration_table

::: pycomap.configuration.parse_names_heap

::: pycomap.configuration.decode_values_all

::: pycomap.configuration.decode_setpoints_all

::: pycomap.configuration.decode_states_all

::: pycomap.configuration.decode_history_snapshot
