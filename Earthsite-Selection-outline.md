# Earth Site Selection Outline Plan

## Goal

When an Earth site is selected from the ranked list, known-site list, or map, make that one site visually distinct with a square outline centered on its existing circle marker. Keep current map recentering and selection behavior.

## Scope

- Update only the Earth selection behavior in `app/app.js` and its marker styling in `app/style.css`.
- Add a focused, dependency-free unit test in `tests/earth-selection.test.js`, using Node's built-in test runner.
- Do not change lunar-map behavior, scoring, Earth marker colors, map layers, data, or unrelated UI.
- Do not add a test framework or package dependency.

## Behavior and implementation

1. Keep one reference to the Earth selection outline, initially `null`. With no selected Earth site (including the initial page state), no outline is rendered.
2. Use a Leaflet marker with a transparent, fixed-size square `divIcon` and a green border so the outline appears square at all map zoom levels. Add only the CSS needed to remove Leaflet's default icon background/border and draw the outline. Make it non-interactive so the existing Earth circle markers continue to handle clicks and tooltips.
3. Update or create the outline from the existing `selectSite` flow so ranked rows, known-site rows, map clicks, and automatic first-result selection all stay in sync. Reuse and reposition the same outline on subsequent selections; do not accumulate outlines.
4. Treat a null position as clearing the selection: remove the outline from the map and reset its reference. No new deselection control is in scope.
5. Follow the existing `app.js` conventions: plain JavaScript, `const`/`let`, semicolons, Leaflet APIs, and the existing Earth-map state. Avoid unrelated refactoring or styling changes.

## Focused unit test

Use `node --test tests/earth-selection.test.js` with Node's built-in `node:test` and mocks for the small Leaflet surface used by the outline helper. Verify:

- No outline exists before a site is selected.
- Selecting a site adds one outline at that location.
- Selecting another site moves the same outline rather than adding another.
- Clearing the selection removes the outline and leaves no active outline.

The test should exercise the production helper from `app/app.js`, not a duplicate implementation.

## Verification

- Run the focused Node unit test.
- Review the diff to confirm only this plan, the Earth selection code/style, and its focused test are changed.
- Manually verify the Earth selection outline stays centered and unique while selecting ranked-list, known-site, and map results, and that existing lunar selection and Earth recentering remain unchanged.
