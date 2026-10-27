# Changelog

Changes in this fork compared with upstream
[uccae/Ambilight-Sync-for-Home-Assistant](https://github.com/uccae/Ambilight-Sync-for-Home-Assistant) v0.4.1.

## 0.4.1.1

### Installation
- Integration moved to `custom_components/ambilight_sync/` so HACS can install it as a custom repository.

### Defaults
- New presets poll the TV at 4 Hz and update lights at 3 Hz (previously 15 Hz each), with a 0.5 s transition and change threshold 12. Existing presets keep their stored values.

### TV off / unreachable
- If the TV is unreachable or reports standby for 15 s, the lights are restored to their state from before the sync started and polling slows to every 5 s.
- The sync resumes on its own once Ambilight colors come back.
- Stopping the sync after that no longer overwrites changes made to the lights in the meantime.
- New `waiting_for_tv` attribute on the sync switch.

### White and on/off lights
- Lights without color support get matching commands: color temperature (warm for red scenes, cool for blue scenes, within the light's range) plus brightness, brightness only, or plain on/off.
- Frames that don't change what a light can show are not sent; identical commands are never repeated.

### Quality
- Unit and behavior tests (`pytest`), lint, hassfest and HACS validation in GitHub Actions.
