# Changelog

## Fork 0.5.1.1

Changes in this fork compared with upstream
[uccae/Ambilight-Sync-for-Home-Assistant](https://github.com/uccae/Ambilight-Sync-for-Home-Assistant) 0.5.1.

### Defaults
- New presets poll the TV at 4 Hz and update lights at 3 Hz (upstream: 15 Hz each), with a 0.5 s transition and change threshold 12. Existing presets keep their stored values.

### TV off / unreachable
- If the TV is unreachable or reports standby for 15 s, the lights are restored to their state from before the sync started and polling slows to every 5 s.
- The sync resumes on its own once Ambilight colors come back, with upstream's soft hand-off.
- Stopping the sync after that no longer overwrites changes made to the lights in the meantime.
- New `waiting_for_tv` attribute on the sync switch and in the diagnostics.

### White and on/off lights
- Lights that only support color temperature also get a white temperature that follows the scene (warm for red, cool for blue, within the light's range). Upstream sends them brightness only.
- Frames that don't change what a light can show are not sent; identical commands are never repeated.

### Packaging and quality
- `ha-philipsjs>=3.2.5` instead of an exact pin, so the integration follows Home Assistant's library updates; config-entry-only `CONFIG_SCHEMA` for hassfest.
- Unit and behavior tests (`pytest`), lint, hassfest and HACS validation in GitHub Actions.

# Upstream changelog

## 0.5.1

- Recover the Philips client after repeated empty responses or connection failures.
- Treat missing frames as errors, while accepting valid black frames.
- Run bounded diagnostics independently of color polling and require confirmed TV power before warning.
- Retry unconfirmed diagnostics without flooding and close diagnostic clients on cancellation.

## 0.5.0

### Added

- Optional Ambient engine inside the existing integration, with X/Y/Z room positioning, TV orientation and four light characters: Natural, Matte, Reflective and Atmospheric. Classic remains the default.
- Shared physical room geometry across presets, with saved alternatives when migrating conflicting layouts.
- Continuous accent identification of a selected room light. Clicking empty space clears the selection and restores synchronization or the previous light state.
- Temporary per-light participation controls, independent of presets.
- JSON configuration export/import with validation and a change preview; TV credentials are excluded.
- Room Undo/Redo and capability-aware copying of light settings.

### Improved

- Preset handoffs retain common light workers and avoid an intermediate full stop.
- Responsive layout, card spacing, menus, dialogs and touch controls in both themes.
- Shared Chromatic-style Discard / Apply changes surface.
- TV screen diagonal in inches, with the existing aspect ratio preserved.
- Automatic room preview updates and bundled Google Material Symbols for Undo/Redo.

### Fixed

- Dismissed error messages stay hidden until the error changes or clears and occurs again.
- Virtual TV glow turns off with synchronization, including when an old preview response arrives later.
- Room selection can be cleared without changing coordinates or saving a draft.
- Selected-light identification ends on deselection, navigation, connection loss or lease expiry.

### Distribution and compatibility

- Standard `custom_components/ambilight_sync/` repository layout for HACS.
- Integration metadata, local brand icons and HACS/hassfest validation workflow.
- Existing pairings, presets, manual zone weights and per-light overrides are retained. Ambient is opt-in.
- No new mandatory runtime dependency. The existing polling and command transport remain in use.

Validation covers the interface and selected-light command/cleanup contracts. Physical TV and light behavior varies by device; no new end-to-end hardware certification is claimed.

## 0.4.1

- Refreshed sidebar UI and TV color previews.
