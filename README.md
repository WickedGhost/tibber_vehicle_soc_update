# tibber_vehicle_soc_update

Custom Home Assistant integration for updating a Tibber vehicle battery state of charge.

The integration exposes a Home Assistant service that can be called from an automation with a SoC value produced by an earlier step.

## Installation

### HACS

1. Add this repository to HACS as a custom repository of type `Integration`.
2. Install `Tibber Vehicle SoC Update` from HACS.
3. Restart Home Assistant.
4. Add the integration from Settings > Devices & Services.

### Manual

1. Copy `custom_components/tibber_vehicle_soc_update` into your Home Assistant `custom_components` directory.
2. Restart Home Assistant.
3. Add the integration from Settings > Devices & Services.

## HACS repository notes

- The repository is structured for HACS with the integration under `custom_components/tibber_vehicle_soc_update`.
- `hacs.json` is included at the repository root so HACS can recognize the repo as a custom integration.
- For normal HACS upgrades, publish versioned GitHub releases that match the `version` value in `custom_components/tibber_vehicle_soc_update/manifest.json`.

## Configuration

The config flow asks for:

- Friendly car name
- Tibber email
- Tibber password
- Tibber home ID
- Tibber vehicle ID

The friendly car name is used as the integration entry name in Home Assistant, so you do not have to identify the setup by raw `vehicle_id`.

## Service

Service name: `tibber_vehicle_soc_update.set_soc`

Fields:

- `config_entry_id` (required): choose the configured vehicle from the dropdown in the action editor
- `soc` (required): target battery percentage from 0 to 100

Calling the service updates the integration's stored current SoC so the last written value remains available internally.

In the visual action editor, the `config_entry_id` field is presented as a dropdown showing the friendly car names from your configured vehicles. In YAML mode, Home Assistant stores the selected value as the underlying config entry ID.

## Example automation

```yaml
alias: Update Tibber vehicle SoC
sequence:
  - service: tibber_vehicle_soc_update.set_soc
    data:
      config_entry_id: 0123456789abcdef0123456789abcdef
      soc: "{{ states('sensor.calculated_soc') | int }}"
```