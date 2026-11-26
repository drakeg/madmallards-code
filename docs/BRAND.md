# Mad Mallards Code — visual design system

## Direction and decision

Current UI improvement uses the existing Mad Mallards Code product and its developer-workbench purpose. Direction selected provisionally during UI modernization: **quiet technical confidence**. This is not an approved or finalized corporate logo redesign; the typographic `M·` mark is a temporary interface signifier, rendered in CSS (no generated raster or copied imagery).

## Color roles

- Workspace shell: `#0e1724` (night ink), `#142337` (sidebar)
- Primary content: `#152332` (ink) on `#ffffff` or `#f4f7f8`
- Primary action: `#146e56` (deep green), text white
- Positive/local marker: `#b8f5d5` (mint) on night ink
- Secondary body: `#58697c` (slate)
- Dividers: `#dce5e9`
- Focus ring: `#1d8f73` on light backgrounds

Color is meaningful, not the only means of conveying state. Buttons have text labels and messages use content labels. Color contrast should be reviewed in automated and human interaction checks; a complete WCAG audit has not been performed.

## Typography and components

Use the user device's system sans-serif stack (`Inter` if installed, then system fallbacks); there are no bundled font files or external licensed font dependencies. Code and file previews use system monospace. Preserve Bootstrap 5.3.3 for layout and form behavior; bespoke CSS tokens control identity. No React or paid UI library is introduced. The mobile sidebar uses explicit toggle state and keyboard escape; content widgets keep preexisting IDs for app compatibility.

## Layout and motion

Desktop: fixed-height command bar, scrolling repository rail, spacious work area, conversation-first content, anchored prompt composer. Mobile: collapsed repository rail, single-column prompt suggestions, reachable controls, responsive model select. Transitions are minimal and disabled under `prefers-reduced-motion`.

## Assets and provenance

All UI styling and temporary CSS lettering are original repo-authored source. No external icons, screenshots, stock visuals, commercial assets, or fonts have been added. Bootstrap 5.3.3 CSS is bundled locally under `app/static/vendor/bootstrap/` with the upstream MIT license. No CDN request is needed for the workbench layout. Formal logo concept selection, favicon and reusable vector assets remain separate backlog tasks; none are represented as approved.

### Vendored Bootstrap checksum

Upstream CSS: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css`

SHA-256: `3c8f27e6009ccfd710a905e6dcf12d0ee3c6f2ac7da05b0572d3e0d12e736fc8`

License: `app/static/vendor/bootstrap/LICENSE` (MIT, Bootstrap Authors).
