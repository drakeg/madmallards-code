# Mad Mallards Code — visual design system

## Direction and decision

**Approved direction:** The user selected concept 1, a bold green mallard mascot with a coding terminal and coral CODE lettering. This product is **Mad Mallards Code**. Its parent company is **Mad Mallard Solutions** (singular Mallard), *not* Mad Mallards Adventures. The production SVG in this repository is a scalable, hand-authored adaptation of that selected concept, not a pixel-identical export of the initial generated concept image. The company attribution appears in the mark and login page.

## Color roles

- Workspace shell: `#042924` and `#0c292d` (deep mallard green)
- Primary content: `#152332` (ink) on `#ffffff` or `#f4f7f8`
- Primary action: `#036a59` (forest teal), text white; coral `#ff7660` for expressive accents
- Positive/local marker: `#60ead3` (aqua mint) on dark green
- Secondary body: `#58697c` (slate)
- Dividers: `#dce5e9`
- Focus ring: `#1d8f73` on light backgrounds

Color is meaningful, not the only means of conveying state. Buttons have text labels and messages use content labels. Color contrast should be reviewed in automated and human interaction checks; a complete WCAG audit has not been performed.

## Typography and components

Use the user device's system sans-serif stack (`Inter` if installed, then system fallbacks); there are no bundled font files or external licensed font dependencies. Code and file previews use system monospace. Preserve Bootstrap 5.3.3 for layout and form behavior; bespoke CSS tokens control identity. No React or paid UI library is introduced. The mobile sidebar uses explicit toggle state and keyboard escape; content widgets keep preexisting IDs for app compatibility.

## Layout and motion

Desktop: fixed-height command bar, scrolling repository rail, spacious work area, conversation-first content, anchored prompt composer. Mobile: collapsed repository rail, single-column prompt suggestions, reachable controls, responsive model select. Transitions are minimal and disabled under `prefers-reduced-motion`.

## Assets and provenance

Original production SVG assets now live in `app/static/brand/mad-mallards-code-logo.svg` and `app/static/brand/favicon.svg`. They are adapted from the user's chosen mascot concept and explicitly credit **Mad Mallard Solutions**. The logo and favicon are self-contained, vector-scalable, and available to the public login screen, while authenticated application CSS and APIs remain access-controlled. No external fonts or paid assets are bundled. Bootstrap 5.3.3 CSS is served locally under `app/static/vendor/bootstrap/` with its MIT license.

### Vendored Bootstrap checksum

Upstream CSS: `https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css`

SHA-256: `3c8f27e6009ccfd710a905e6dcf12d0ee3c6f2ac7da05b0572d3e0d12e736fc8`

License: `app/static/vendor/bootstrap/LICENSE` (MIT, Bootstrap Authors).

## Logo usage

Use the wide logo on the signed-in command bar and welcome screen, and the compact mallard-terminal emblem as the favicon. Preserve the product/company distinction: `Mad Mallards Code` is the product; `Mad Mallard Solutions` owns it. Do not substitute `Mad Mallards Adventures` in this project. Keep alt text for screen readers, with the mascot purely decorative where already described in the accessible link label. Do not use the full logo as a tiny square favicon.
