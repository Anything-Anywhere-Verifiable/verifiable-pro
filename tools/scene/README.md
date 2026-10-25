# Lead illustrations: the scene generator

Every news story on verifiable.pro opens with a lead image, usually a photo that `tools/photos.py` crops and grades ([CONTENT_GUIDE.md](../../CONTENT_GUIDE.md#photos)). A story that no suitable photo fits opens with a lead illustration instead: an isometric scene drawn in the same visual language as the home page hero. The scene is not painted by hand or by an image model. It is written as a short JSON spec of recognizable objects (a server rack, a pair of glasses, a certificate, a padlock) placed on a gray floor, and `tools/illustrate.py` draws it into a small, byte-deterministic SVG. Anyone can redraw every picture from the repository.

| Path | Contents |
| --- | --- |
| `tools/illustrate.py` | The command line: draw, check, draft, catalog |
| `tools/scene/iso.py` | Projection, elements, face shading, depth sorting |
| `tools/scene/svg.py` | Writes the SVG (merging runs of same-styled shapes); the shapes the occlusion check rasterizes |
| `tools/scene/palette.py` | The fixed light palette, the materials, the tints and the link colors |
| `tools/scene/kit.py` | Prop registry, parameter types, the builder props draw with |
| `tools/scene/props.py`, `props2.py` | The prop library |
| `tools/scene/figure.py`, `figure.json` | The person prop's figure, traced from the hero's own person (`tools/hero/person.py`) |
| `tools/scene/compose.py` | Spec validation, placement, ground, shadows, links, camera, and the composition and color checks |
| `tools/scene/catalog.svg` | Every prop and variant, labeled (`--catalog`) |
| `tests/test_illustrate.py` | Determinism, validation, composition, color rules, safety and `--check` |

## The file an article carries

`content/articles/<slug>/illustration.json`:

```json
{
  "kind": "illustration",
  "alt": {"en": "...", "zh": "..."},
  "caption": {"en": "Illustration: ...", "zh": "示意图：..."},
  "scene": { "...": "the spec described below" }
}
```

- **alt** says concretely what the picture shows, in one or two sentences in each language (at most about 320 characters in English and 140 in Chinese): the objects, their colors where color carries meaning, and how they are connected ("A dashed orange line with packets runs from a pair of smart glasses through a gateway lit in indigo into a glass enclosure holding a server rack"). It describes the picture, not the story. Write American English, as the rest of the site does: gray, color, center.
- **caption** opens with "Illustration:" / "示意图：" (CONTENT_GUIDE.md, "Lead images"; `--write`, `--check` and `tools/lint_content.py` all check it), says in one sentence what the scene stands for, and ends with what it does not depict ("It does not depict Meta's glasses, servers or ledger, and it does not show that the checks work as described."). Every part of the sentence must be in the picture: if the caption names a checker, draw one. The site adds the credit line; do not repeat it. Follow CONTENT_GUIDE.md: a vendor's design is "the design Meta describes", attestation never "proves" anything, and nothing is called verified.
- **scene** is this generator's input. The site never reads it; it only publishes the drawing and checks its digest.
- **svg_sha256** is the SHA-256 of `static/media/<slug>.svg`. Leave it out of a new spec and never edit it by hand: `--write` adds and updates it (it refuses a placeholder string), and the build fails when the drawing is missing or differs.

The Chinese texts are written for Chinese readers, not translated word for word: natural word order, full-width punctuation, a space between Chinese and Latin text, Latin names (Intel, SynthID) kept as they are. Before the specs are published, an editor checks each caption and alt text against the drawing.

## Adding or changing an illustration

Run these steps from the repository root. Drawing needs only Python 3; `--png` and `--thumb` also need Google Chrome (set `CHROME` to its path if it is not in the usual place).

1. **Write or edit the spec.** For a new picture, read the article (`en.md`) and decide the one idea the picture must carry: what the actors are, where the data goes, what is checked and by whom, and what fails. One idea, one focal object, three to six objects in all. Pick the focal object from the motif bank below, and check which focal props other stories already use (`--check` prints the tally). Write `content/articles/<slug>/illustration.json` as described above, with `alt` and `caption` in both languages and no `svg_sha256` yet; another article's spec is a quick starting point. To change a picture, edit the scene, `alt` or `caption` of its spec in place. Never edit `svg_sha256` or `static/media/<slug>.svg` by hand.
2. **Draft it and look.** Render the spec with the debug overlay, at full size and as thumbnails, into a scratch folder outside the repository:

   ```bash
   python3 tools/illustrate.py --spec content/articles/<slug>/illustration.json --png /tmp/draft.png --thumb /tmp/draft-thumb.png --debug
   ```

   `--spec` writes nothing in the repository. It accepts a whole illustration.json or a bare scene object, so a draft may also live anywhere (then add `--layers`, below). It prints the zoom, how much of the canvas the props cover, the focal object's size and center, any prop that is partly hidden, and the problems and warnings described under "Composition checks"; it writes the files even when there are problems (and exits with status 1). `--debug` draws the s/t grid with its numbers, each prop's footprint and id, the focal object's box and the middle zone its center must fall in. A partly hidden prop is printed as "photo 'video' shows 65% of itself (covered by photo 'image')". `--layers` names the article's layers (and topics) for the color check, such as `--layers outputs`; a spec saved beside its `en.md` reads them from there. `--thumb` writes the 240 × 160 thumbnail and, beside it, a 104 × 69 one (`draft-thumb-104.png`), the home rail's copy at most widths (it is 88 px wide from 960 to 1279 px).

   Look at all three PNGs. At 104 × 69 the focal object must still be recognizable and the picture must not look like the others. Fix every problem; fix a warning unless the covered link is the point. Repeat until it reads, then render once more without `--debug` for a last look.
3. **Draw and record it**, then check every picture as CI does:

   ```bash
   python3 tools/illustrate.py --write <slug>    # writes static/media/<slug>.svg and svg_sha256
   python3 tools/illustrate.py --check           # what CI runs: every drawing matches its spec and the rules
   ```

   `--write` refuses a spec with a problem, and rewrites the JSON when the digest changes, in a compact two-space layout that keeps each short object (an item, a link) on one line. `--check` also reports SVGs in `static/media/` that no spec draws.
4. **Check the texts.** `python3 tools/lint_content.py <slug>` checks the alt text and caption by the style, wording and Chinese typesetting rules of [CONTENT_GUIDE.md](../../CONTENT_GUIDE.md#lead-images); read its warnings and fix what applies.
5. **Build and look at the page.**

   ```bash
   python3 build.py --mode preview --out /tmp/vp-preview
   python3 -m http.server 8000 --directory /tmp/vp-preview   # then open http://localhost:8000/articles/<slug>/
   ```

   The build stops with `content error:` when a picture is missing or does not match its `svg_sha256`. Check the picture under the article's headline and its copy beside the story on the home page or Latest.
6. **Commit the spec and the picture together.** Redrawing a picture, or rewording its texts without changing a fact, is not a correction of the article, so it needs no `updated` date or `changes` entry; say in the commit message that it touches the illustration only. A caption that misstated a fact is a correction ([Corrections](../../CONTRIBUTING.md#corrections) in CONTRIBUTING.md).

## Coordinates

The scene uses the hero's projection: a point (s, t, h) lands at x = .894·(s + t), y = .447·(s − t) − h, scaled by 40 px per unit at zoom 1 (the camera then fits the props to the canvas). Units are grid units; a server rack is about 1.6 wide and 2.6 tall, a person 2.4 tall.

```
              back corner (low s, high t)
                     /\
       +t  ↗        /  \        the floor; light comes from the upper left
                   /    \
  left corner     /      \     right corner (high s, high t)
 (low s, low t)   \      /
                   \    /       +s  ↘
                    \  /
              front corner (high s, low t), nearest the viewer
```

Authors think in front, back, left and right; the grid does not. Use this table (a is a distance in grid units):

| To move a prop toward the picture's | change `at` by | u = s + t | v = s − t |
| --- | --- | --- | --- |
| front (bottom of the picture) | [+a, −a] | 0 | +2a |
| back (top) | [−a, +a] | 0 | −2a |
| left | [−a, −a] | −2a | 0 |
| right | [+a, +a] | +2a | 0 |

- **u = s + t** runs across the picture, left to right; **v = s − t** runs down it, back to front. Two props with similar u overlap on screen, and the one with larger v is in front. An item may give `at_uv: [u, v]` (or `[u, v, h]`) instead of `at`, if that is easier to think in.
- Every prop is drawn with its **front facing −t** (the lit, lower-left face). `facing` turns it by quarter turns: `left` (the default: front toward the lower left), `right` (front toward the lower right, in shade), `back-right`, `back-left` (front away from the viewer, rarely useful).
- `at` is the center of the prop's footprint, at the ground (h = 0 is the floor). A third number lifts the prop; `on` stands it on another prop.
- Each prop's size with its defaults is listed in the props reference below, as "(about W wide, D deep, H tall)": W along its front, D into it. Leave half a unit between footprints.

## The scene spec

```json
{
  "version": 1,
  "focal": "cvm",
  "items": [
    {"prop": "glasses", "id": "glasses", "at": [2.72, -2.82]},
    {"prop": "gate", "id": "check", "at": [0, -0.9], "w": 1.8, "h": 2.0, "tint": "tee"},
    {"prop": "certificate", "id": "report", "at": [3.6, -0.4], "tint": "tee", "w": 1.4, "h": 1.0},
    {"prop": "enclosure", "id": "cvm", "at": [-1.4, 0.7], "w": 2.6, "d": 2.1, "h": 3.1, "items": [
      {"prop": "server_rack", "id": "rack", "at": [-1.4, 0.7], "tint": "tee", "units": 6}]}
  ],
  "links": [
    {"from": "glasses", "to": "rack.lamp", "route": "via", "via": [[0.05, -0.9, 0.6]], "style": "dashed",
     "packets": [0.3, 0.8], "glow": true},
    {"from": "check", "to": "report", "style": "dotted", "color": "tee"}
  ]
}
```

The glasses stand in front of the gate and the rack behind it, on one line down the picture, so the data path runs straight through the middle of the gate's opening and the rack's lamp shows through it: anything behind a gate's pillars or lintel is hidden, so put what a path reaches where the opening frames it.

`items` is required, and `focal` is required for a published picture. Every key is checked: an unknown key, prop, tint, anchor or out-of-range value stops the draw with a message that names the item, such as `items[2] (gate 'check'): tint 'teal' is not available for gate (choose from neutral, tee, data, ...)`. Any object may also carry a `note` string, which is ignored.

### Top level

- `version`: optional; 1 when given.
- `focal`: the id of the one prop the picture is about (it may sit inside an enclosure). See "Composition checks".
- `backdrop`: `white` (default, as the hero), `mist` (#f3f5f7) or `tee` (a faint indigo wash). The picture is shown through `<img>`, so it keeps this light palette in dark mode too.
- `camera`: `zoom` is `"items"` (the default: the props fill the canvas with a 48 × 40 px margin, up to zoom 3, and the floor runs off the canvas), `"fit"` (the whole drawing, plate included, as a diamond on the backdrop) or a number (40 px per unit times the number; the draw fails if the drawing then runs off the canvas, and the message gives the largest zoom that fits). `pan` moves the drawing by [x, y] pixels.
- `ground`: see below. `items`: up to 40 props (aim for three to six). `links`: connectors between props.

### Ground

- `kind`: `plate` (default: a gray slab like the hero's plates), `tiles` (a plate with floor tiles), `desk` (a table top on legs) or `none` (props on the backdrop with their shadows only).
- `size`: `"auto"` (default) or `[width along s, depth along t]` centered on the origin. With the items camera and `size: "auto"`, a plate or tiles floor runs off the left, right and bottom edges of the canvas: its two back edges sit `margin` units (default 0.8) behind the props, and the backdrop shows only above them. With the fit camera, or a fixed size, the plate hugs the props and casts a soft shadow, as the hero's plates do.
- `tint`: `neutral`, `tee` (the indigo-tinted plate of the hero's two TEE layers) or `pcb` (circuit-board green); both are story tints (see Color).
- `thickness`: default 0.38.

A prop standing on the ground must stand on the plate; mark one that stands beside it with `"outside": true`. With the items camera the floor runs past it anyway, so `outside` matters only for the fit camera and fixed sizes.

### Items

Common keys of every item:

| Key | Meaning |
| --- | --- |
| `prop` | The prop's name (see the props reference below) |
| `id` | A name for links, `on` and `focal`: lower case letters, digits, `-` or `_` |
| `at` | `[s, t]` or `[s, t, h]`: the footprint's center, and its height above the floor |
| `at_uv` | Instead of `at`: `[u, v]` or `[u, v, h]`, with u = s + t across and v = s − t down |
| `on` | The id of an earlier item to stand on (its top, or its working surface for a desk, plate, book or conveyor) |
| `facing` | `left` (default), `right`, `back-right`, `back-left`; the person faces `back-right` only |
| `tint` | The color role (see Color), within the tints the prop allows |
| `scale` | Uniform size factor, 0.25 to 4 (default 1) |
| `shadow` | `false` to drop the prop's cast shadow |
| `outside` | `true` for a prop that stands off the plate |
| `allow_overlap` | `true` to accept that its box intersects another prop's (the draw order may then be wrong) |
| `allow_hidden` | `true` to accept that other props hide most of it (see Composition checks) |
| `items` | Only on `enclosure`: the props inside the glass, in the same coordinates |

Props whose boxes intersect are an error, because the painter's order of intersecting boxes is undefined; move them apart, or stand one `on` the other. Props inside an enclosure must fit inside its glass.

### Links

A link draws a connector between two props: data in transit, a binding, a check.

| Key | Meaning |
| --- | --- |
| `from`, `to` | An item id, `"id.anchor"`, or a point `[s, t, h]` (see "Where a link starts and ends") |
| `route` | `straight` (default: one segment), `floor` (an L along the floor, first along s, then t; `bend: "t"` reverses), `arc` (lifted by `lift`, default 1.5) or `via` (through the `via` points) |
| `via` | For `via`: a list of points `[s, t, h]` or anchors `"id.anchor"` |
| `style` | `solid`, `dashed`, `dotted` or `broken` (two stubs and a gap at `gap`, 0.1 to 0.9, default 0.5; the gap is at least half a unit wide) |
| `color` | `data` (orange, default), `tee` (indigo), `ink` (dark gray, for emphasis), `mute` (light gray, for secondary relations), or a layer hue (`models`, `outputs`, `agents`, `evaluations`, `institutions`). There is no cinnabar link |
| `packets` | Small cubes along the link: a count from 0 to 6, spread evenly, or a list of positions from 0.05 to 0.95 (`[0.3, 0.8]`) to keep them clear of other props |
| `glow` | A soft halo under the line (it counts as the picture's one glow) |
| `arrow` | An arrowhead at the `to` end |
| `width` | Line weight factor, 0.5 to 3. A link's weight grows with the zoom only up to zoom 2 (about 4 px at 1200 wide), so it stays a fine line |
| `layer` | `under` (under every prop; the default for a link that lies on the floor), `depth` (cut into short segments that are sorted with the props, so a line passes behind a nearer prop and in front of a farther one; the default for the others) or `over` (over every prop; rarely right) |

**Which route.** Use `straight` for almost every link between two props: on the floor it is one clean segment, in space one clean line. Use `floor` only for a trace that should follow the floor's grid, like the hero's traces along a plate's edges, and only when both legs run the same way across the picture (an L whose legs run toward the front and the back turns through an acute angle on screen and reads as a hook; the check warns). Use `arc` to reach a prop's top from another prop, over whatever lies between, and `via` for a path that must pass through a gate's opening or another point.

**Where a link starts and ends.**

- A link that names an item without an anchor uses the prop's *port* when it has one: a person's `phone`, a magnifier's handle `tip`, the glasses' `camera`, a gate's `through` (the floor in the middle of its opening), an interposer's `slot`. So a link to or from the person meets the phone in their hands, and a link to a magnifier meets the end of its handle, on the floor.
- On the floor, a link to an item (or its port, or `"id.base"`) stops where it meets that prop's outline on the screen, tucked a little under it; an enclosure is met at its glass. A link that runs behind a prop to reach it disappears behind it, as it should.
- In space (a straight or via link with a raised end), an item without a port is met where the line reaches its box.
- An arc to an item without a port ends on its `top`. An arc end on a prop's top is met straight from above: the line rises from it, or comes down onto it, over the last 0.6 units, so the arc clears the prop it lands on.
- A named anchor is met exactly. Every item has the anchors `base`, `top`, `center` and `front` (the middle of its front face after turning); props add their own, listed in the reference (for example `rack.lamp`, `ledger.new`, `seal.rim`, `gate.opening`). Start a link that leaves a flat prop's top at its rim (`seal.rim`), not its center, so its first dots do not walk across the prop.
- A dashed or dotted line keeps its rhythm where a prop cuts it in two.

## Color and meaning

The palette is the hero's light theme, fixed in `palette.py`. Color carries meaning, as on the hero, and the draw enforces the rules marked *checked*:

- **Grays** for everything by default: plates, devices, paper, buildings.
- **Indigo (`tee`)** only for TEEs, enclaves, attestation and the chain of evidence: a confidential VM's glass, a TEE-tinted chip, an attestation certificate.
- **Orange (`data`)** for the reader's data and the flow of data: links, packets, the reader's coat.
- **Cinnabar (`seal`)** for seals and signatures only. *Checked:* only `seal`, `stamp` and `certificate` take the seal tint; a document (`seal: "seal"`), a photo (`tag: "seal"`) and a book (`emblem: "seal"`) carry one by parameter; no link is cinnabar; and a picture holds at most two cinnabar marks.
- **Layer hues** (`models` blue, `outputs` pink, `agents` teal, `evaluations` violet, `institutions` brown) mark the layers a story is tagged with, as each hero plate's objects do. Use them on one or two objects, never on everything.
- **Story tints**, *checked* by `--write` and `--check` against the `layers` (and `topics`) in the article's `en.md`: a layer hue only when the story has that layer; `tee` only for a `runtime` story or one with the `confidential-computing` topic; `pcb` only for a `hardware` story. The check covers item tints, link colors, the ground's tint and materials. Watch the defaults: `bars`, `gauge` and `proof_tree` are violet, `book`, `gavel` and `scale` brown, `agent` and `tool` teal, `weights` and `neural_net` blue, and `ledger`, `gate`, `enclosure`, `padlock`, `shield`, `chain` and `zone` indigo.
- **One glow per picture**, *checked*: a link's `glow`, a packet's `glow`, a glowing agent core (`agent` with `glow`), and a TEE die (a `chip` with a bare enclave die, a `gpu` tinted tee) each count. A device's lamp is a small dot with no halo, in gray, the tint's lamp color or the warning yellow, never the data orange; a lamp drawn with a halo wider than 0.12 units counts as a glow.
- `dark` (near-black hardware) and `warn` (the warning sign's yellow) are for those objects only.

Gradients are limited to the plate tops and the shading of round solids.

## Composition checks

`--write` and `--check` refuse a picture with a problem; `--spec` lists them and still draws.

- **A focal object.** `focal` names it. Its box on the canvas must be at least 256 px tall (32% of the height), or 480 px wide for a flat object such as a chip or a map, and its center must fall in the middle 40% × 50% of the canvas (x 360 to 840, y 200 to 600). If it is too small, drop a prop or move the others closer, so the camera can come in; if it is off center, balance the other props around it.
- **No hidden props.** The draw rasterizes every prop in painter's order and refuses one that shows less than 40% of its own silhouette, naming the prop that covers it. Set `"allow_hidden": true` only when being hidden is the point. Glass, glows, shadows and lines do not hide anything; a prop standing `on` another does not count as hiding it.
- **Packets** are checked like props: one that shows less than 80% of itself is a problem, and one that comes within 6 px of a prop its link does not join is a warning (it seems to belong to that prop). Move them with `"packets": [positions]`.
- **Link ends.** A link whose start or end stops more than 10 px from the outline of the prop it names is a problem: it ends on empty floor. Name one of the prop's anchors (the message lists them), or move the props.
- **Covered links** are warnings: more than half of a link hidden behind props, or either end hidden behind a prop other than the one it ends at. A link that seems to start at the wrong prop usually has its end behind another one.
- **Link shapes** are warnings: a link that runs inside the prop it starts or ends at, away from that end (it seems to leave or enter through a side; an arc should end on the top); a floor route that doubles back on screen; and two links that cross away from their ends.
- **Motifs across the site.** `--check` prints how many pictures use each focal prop, and fails when one prop is the focal object of more than 5 pictures, or the magnifier of more than 4.

## Making a scene read

- **One focal object, large and central**, recognizable at 104 × 69. Three to six objects in all.
- **Tell the story with objects and one path.** Who holds the data, where it goes (an orange link), what checks it (indigo), what fails (a `broken` link, a `ghost` packet, a raised interposer, a `sign`).
- **Mind the overlaps on screen.** Tall props hide what is behind them (smaller v). Put tall props at the back, low props at the front, and keep props that should be seen together apart in u. The occlusion check and the `--debug` overlay show where this goes wrong.
- **No words, digits, logos or real brand marks** in the picture; small abstract marks (a padlock, a turnstile, a ring) are fine. No check marks. No crowds: at most one `person`.
- **The person** is the hero's own reader in the orange coat, traced from the home page. Use them for stories where anyone can check something; stand them at the front left facing into the scene. A link from them starts at the phone in their hands.
- **The magnifier** is for detector stories only, where detection itself is the subject (a watermark detector, a scanner of content), at most four pictures site-wide; never for a code, a rule or a law. For other checks use a `gate` (a check something passes through), a `math_block` turnstile (a checker), or two objects side by side with a link between them (a comparison).
- **Links stay quiet.** Data paths are orange; secondary relations (this certificate belongs to that model) are `mute` gray and dotted; `ink` is for the one relation the picture is about. Keep packets off other props, and links from crossing.
- **Look at all the renders.** If the 104 × 69 thumbnail does not show the focal object clearly, make it bigger or remove an object.

### Motif bank

Most stories share a layer with nine others, so vary the focal setup. Six or more per layer:

| Layer | Focal props and setups |
| --- | --- |
| Runtime and hardware (TEE) | a `chip` with an enclave (metal lid, or a bare indigo die); a `gpu` tinted tee (confidential GPU); an `enclosure` around a `server_rack` (a confidential VM); a `gate` tinted tee that data passes through (an attestation check); a `phone` or `glasses` sending a dashed packet path into an enclosure; `dimm` and `interposer` (memory attacks); a `server` with a lock inside an enclosure; a `certificate` tinted tee beside a `ledger` (an attestation report and a transparency log); a `map` with a `map_pin` on a `chip` (where a chip is) |
| Outputs | a `photo` with a `tag` or a seal (a provenance credential); a `camera` sending a picture to a `photo` with a seal (capture provenance); a `chain` with a `broken` link before a `photo` (a broken provenance chain); a `stamp` beside a `photo` (labeling); `photo` cards on a `conveyor` through a `gate` (a platform labeling uploads); a `neural_net` emitting a packet to a `document` with a seal (an output with a proof); a `photo` with the `magnifier` (a detector, and only a detector; counts toward the four) |
| Evaluations | `bars` or a `gauge` (scores and thresholds); a `proof_tree` with a `math_block` checker (formal proof); an `agent` inside an `enclosure` (a sandboxed test); a `screen` with a `log` and a `document` report (transcript review); a `scale` (a judgment); `nodes` with one highlighted (a multi-agent test); a `document` with a seal (an audit report) |
| Agents | an `agent` with `tool` tiles (tool calls); a `robot_arm` (acting in the world); `nodes` in a `chain` or `star` layout (a protocol); an `agent` in an `enclosure` (a sandbox); a `ledger` of actions (an action log); a `sign` beside an `agent` (an incident) |
| Models | `weights` with a `seal` on top (a signed model); a `neural_net` card; `crate`s on a `conveyor` through a `gate` (a model supply chain); `papers` beside `weights` (a model card, an SBOM); a `database` feeding `weights` (training data); `weights` inside an `enclosure` (a protected model) |
| Institutions | a `building` (a regulator); a `book` linked to what it governs (a code, a standard); a `scale` (a law, a balance); a `gavel` (enforcement); a `globe` (an international agreement); a `stamp` with a `certificate` (accreditation); a `map` with `map_pin`s (jurisdiction); a `crate` at a `gate` (export controls). Not the magnifier |

## Props

Sizes are in grid units. Each prop's look, with its defaults, is in [catalog.svg](catalog.svg); the variants of screen contents, photo marks and tags, icons, tints, links and grounds follow it. Redraw it with `python3 tools/illustrate.py --catalog tools/scene/catalog.svg`. The reference below is generated from the registry: after changing a prop, replace it with the output of `python3 tools/illustrate.py --props-md` (the tests check that the README holds that output exactly).

### Primitives

**`box`** (about 1 wide, 1 deep, 1 tall) A plain box, for anything the library lacks (a cabinet, a block, a step). Tints: any; default `neutral`.

- `w`: width along the front (x) (number 0.1 to 12, default 1)
- `d`: depth (y) (number 0.1 to 12, default 1)
- `h`: height (number 0.02 to 10, default 1)
- `material`: the solid's material, or `auto` to follow the tint (see Materials; default `auto`)
- `lip`: white highlight on the top's front edges (true or false, default true)

**`slab`** (about 2 wide, 1.4 deep, 0.1 tall) A thin slab: a tile, a tray, a board, a step. Tints: any; default `neutral`.

- `w`: width (x) (number 0.1 to 16, default 2)
- `d`: depth (y) (number 0.1 to 16, default 1.4)
- `h`: thickness (number 0.02 to 1, default 0.14)
- `material`: the solid's material, or `auto` to follow the tint (see Materials; default `auto`)
- `radius`: corner radius (rounded slabs have no lip) (number 0 to 1, default 0)

**`cylinder`** (about 1 wide, 1 deep, 1 tall) An upright cylinder: a drum, a post, a column, a token. Tints: any; default `neutral`.

- `r`: radius (number 0.05 to 5, default 0.5)
- `h`: height (number 0.02 to 10, default 1)
- `material`: the solid's material, or `auto` to follow the tint (see Materials; default `auto`)
- `rim`: a thin lighter rim around the top (true or false, default false)

**`sphere`** (about 0.8 wide, 0.8 deep, 0.8 tall) A ball resting on the ground (or floating, with a height in 'at'). Tints: any; default `neutral`.

- `r`: radius (number 0.05 to 4, default 0.4)
- `material`: the solid's material, or `auto` to follow the tint (see Materials; default `auto`)

**`panel`** (about 1.6 wide, 0.08 deep, 1.2 tall) A standing card or sign board with abstract content on its front. Tints: any; default `neutral`.

- `w`: width (number 0.2 to 8, default 1.6)
- `h`: height (number 0.2 to 6, default 1.2)
- `thickness`: thickness (number 0.02 to 0.6, default 0.08)
- `content`: what the front shows (one of blank, log, text, code, chart, line, timeline, image, lock, shield, wave, graph, chat, grid; default text)
- `material`: the solid's material, or `auto` to follow the tint (see Materials; default `paper`)
- `lift`: height of the card's bottom edge above its base (a floating card) (number 0 to 3, default 0)

**`sheet`** (about 1.4 wide, 1.8 deep, 0.03 tall) A flat sheet lying on the ground or on a desk: a page, a mat. Tints: any; default `neutral`.

- `w`: width (x) (number 0.2 to 10, default 1.4)
- `d`: depth (y) (number 0.2 to 10, default 1.8)
- `content`: what it shows (one of blank, log, text, code, chart, line, timeline, image, lock, shield, wave, graph, chat, grid; default text)
- `material`: the solid's material, or `auto` to follow the tint (see Materials; default `paper`)

**`screen`** (about 2.2 wide, 0.1 deep, 1.4 tall) A bare display panel, standing, with a dark bezel and light content. Tints: any; default `neutral`.

- `w`: width (number 0.4 to 8, default 2.2)
- `h`: height (number 0.3 to 6, default 1.4)
- `content`: what it shows (one of blank, log, text, code, chart, line, timeline, image, lock, shield, wave, graph, chat, grid; default log)
- `dark`: a dark screen with light content (true or false, default false)
- `lift`: bottom edge height (a floating screen) (number 0 to 4, default 0)

**`glass_box`** (about 2 wide, 1.6 deep, 1.4 tall) An empty glass case (to put things in glass use enclosure). Tints: `neutral`, `tee`, `data`, `agents`, `models`; default `tee`.

- `w`: width (number 0.3 to 12, default 2)
- `d`: depth (number 0.3 to 12, default 1.6)
- `h`: height (number 0.2 to 8, default 1.4)

### Structure

**`enclosure`** (about 4 wide, 3 deep, 2.4 tall) A glass enclosure around a group of props (an enclave, a sandbox, a TEE). Put the props inside it in its own 'items' list; they must fit inside the glass. Tints: `tee`, `neutral`, `data`, `agents`, `models`; default `tee`. Holds its own `items`.

- `w`: width (x) (number 0.5 to 16, default 4)
- `d`: depth (y) (number 0.5 to 16, default 3)
- `h`: height (number 0.3 to 10, default 2.4)
- `wash`: a tinted floor inside the glass (true or false, default true)

**`plate`** (about 4 wide, 3 deep, 0.2 tall) A raised platform on the ground, like the hero's plates (a second level, a TEE base). Tints: `neutral`, `tee`, `dark`; default `neutral`.

- `w`: width (x) (number 0.5 to 16, default 4)
- `d`: depth (y) (number 0.5 to 16, default 3)
- `h`: thickness (number 0.05 to 2, default 0.25)

**`zone`** (about 4 wide, 3 deep, 0 tall) A painted area on the floor with a dashed edge: a boundary, a region, a trust zone. Tints: `tee`, `data`, `neutral`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `tee`. Drawn flat on the floor, under the shadows.

- `w`: width (x) (number 0.4 to 20, default 4)
- `d`: depth (y) (number 0.4 to 20, default 3)
- `dashed`: a dashed edge (else solid) (true or false, default true)
- `fill`: a light wash inside (true or false, default true)

### Hardware

**`chip`** (about 2 wide, 2 deep, 0.3 tall) A processor package on a green substrate, with a metal lid or a bare die; enclave marks the protected region in indigo. Tints: `neutral`, `tee`, `data`, `dark`; default `neutral`. Anchors: `die`.

- `size`: side of the substrate (number 0.6 to 6, default 2)
- `lid`: a metal lid or a bare die (one of metal, die; default metal)
- `enclave`: an indigo die and a dashed boundary: a TEE inside the chip (true or false, default false)
- `lock`: a small padlock mark on the lid (true or false, default false)
- `pins`: gold contacts along two edges (true or false, default true)
- `boundary`: with enclave: the dashed indigo ring on the substrate (true or false, default true)

**`gpu`** (about 2.6 wide, 2.6 deep, 0.4 tall) An accelerator package as on the hero: a die ringed by memory (HBM) stacks on an interposer. Tint tee draws the confidential-computing boundary. Tints: `neutral`, `tee`, `data`, `dark`; default `neutral`. Anchors: `die`.

- `size`: side of the substrate (number 1 to 6, default 2.6)
- `hbm`: memory stacks (as a string) (one of 2, 4, 6; default 4)

**`gpu_card`** (about 3.2 wide, 0.4 deep, 1.2 tall) A graphics card standing on its edge: shroud, two fans, gold fingers. Tints: `neutral`, `tee`, `dark`; default `dark`.

- `length`: length (x) (number 1.6 to 6, default 3.2)

**`dimm`** (about 2.9 wide, 0.8 deep, 0.8 tall) Memory modules (DIMMs) standing in their slots, in a row from front to back. Tints: `neutral`; default `neutral`. Anchors: `front`.

- `count`: how many modules (integer 1 to 6, default 2)
- `slot`: draw the slots (true or false, default true)
- `length`: module length (x) (number 1.2 to 4, default 2.6)
- `spacing`: distance between modules (y) (number 0.3 to 1.5, default 0.55)

**`interposer`** (about 2.9 wide, 2.2 deep, 1.4 tall) A memory interposer: a module raised high on a gray adapter board in its slot, with a ribbon cable from the adapter to a small controller box (a DDRop-style probe). Tints: `dark`, `data`, `neutral`; default `dark`. Anchors: `adapter`, `device`, `module`, `slot`.

- `length`: module length (x) (number 1.2 to 4, default 2.6)
- `cable`: cable length to the box (toward the front) (number 0.5 to 4, default 1.2)
- `lamp`: a small yellow lamp on the controller box (true or false, default true)

**`server_rack`** (about 1.6 wide, 1.3 deep, 2.6 tall) A rack cabinet with stacked servers and their lamps. Tint tee: indigo lamps and trim, for confidential computing. Tints: `neutral`, `tee`, `data`, `dark`; default `neutral`. Anchors: `front`, `lamp`.

- `units`: servers in the rack (integer 2 to 10, default 6)
- `w`: width (number 1 to 3, default 1.6)
- `d`: depth (number 0.8 to 3, default 1.3)

**`server`** (about 3 wide, 1.6 deep, 0.5 tall) One server lying flat: a wide chassis with drive bays and lamps on its front. Tints: `neutral`, `tee`, `data`, `dark`; default `neutral`. Anchors: `front`.

- `w`: width (x) (number 1.2 to 6, default 3)
- `d`: depth (number 0.8 to 4, default 1.6)
- `lock`: a small indigo padlock on the front (true or false, default false)

**`database`** (about 1.6 wide, 1.6 deep, 1.1 tall) A database: stacked discs, as on the hero's model layer. Tints: `neutral`, `tee`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `neutral`. Anchors: `top`.

- `tiers`: discs (integer 1 to 5, default 3)
- `r`: radius (number 0.3 to 2, default 0.8)

**`cloud`** (about 2.3 wide, 0.4 deep, 1.5 tall) A cloud, standing like a cut-out with some depth: a cloud service. Use a height in 'at' to float it. Tints: `neutral`, `tee`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `neutral`. Anchors: `center`.

- `w`: width (number 1 to 6, default 2.6)

### Devices

**`monitor`** (about 2.6 wide, 0.6 deep, 2.1 tall) A desktop monitor on a stand, with abstract content on its screen. Tints: any; default `neutral`. Anchors: `screen`.

- `w`: screen width (number 1.2 to 6, default 2.6)
- `h`: screen height (number 0.8 to 4, default 1.65)
- `content`: what the screen shows (one of blank, log, text, code, chart, line, timeline, image, lock, shield, wave, graph, chat, grid; default chart)
- `dark`: a dark screen (true or false, default false)

**`laptop`** (about 2.2 wide, 1.8 deep, 1.4 tall) An open laptop, its screen tilted back. Tints: any; default `neutral`. Anchors: `screen`.

- `w`: width (number 1 to 4, default 2.2)
- `content`: what the screen shows (one of blank, log, text, code, chart, line, timeline, image, lock, shield, wave, graph, chat, grid; default code)
- `dark`: a dark screen (true or false, default false)

**`phone`** (about 0.8 wide, 0.1 deep, 1.5 tall) A smartphone standing upright, its screen toward the front. Tints: any; default `neutral`. Anchors: `screen`.

- `content`: what the screen shows (one of blank, log, text, code, chart, line, timeline, image, lock, shield, wave, graph, chat, grid; default chat)
- `h`: height (number 0.6 to 3, default 1.5)
- `dark`: a dark screen (true or false, default false)

**`glasses`** (about 1.7 wide, 1.2 deep, 0.6 tall) Smart glasses resting on their frame and temples, lenses toward the front, with a small camera at one hinge. Tint tee tints the lenses indigo. Tints: `neutral`, `tee`, `data`, `dark`; default `neutral`. Anchors: `camera`, `lens`.

- `w`: frame width (number 1 to 4, default 1.7)

**`packet`** (about 0.3 wide, 0.3 deep, 0.3 tall) A small data packet (a cube), for data in transit; ghost draws a dashed outline only (data that went missing). Links can also carry packets. Tints: `data`, `tee`, `neutral`; default `data`.

- `size`: edge (number 0.1 to 1, default 0.3)
- `glow`: a soft glow (true or false, default false)
- `ghost`: only a dashed outline: a lost or dropped packet (true or false, default false)

### Documents

**`document`** (about 1.2 wide, 0.06 deep, 1.6 tall) A page with lines of writing (never words), standing or lying, with an optional seal or signature: a report, a policy, a paper. Tints: `neutral`, `tee`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `neutral`. Anchors: `seal`.

- `pose`: standing on its edge or lying flat (one of standing, lying; default standing)
- `w`: width (number 0.5 to 3, default 1.25)
- `h`: height (length when lying) (number 0.6 to 4, default 1.65)
- `header`: a colored bar at the top (the tint's accent) (true or false, default true)
- `seal`: seal: cinnabar seal; tee: indigo ring (an attestation); ring: tint ring (one of none, seal, tee, ring; default none)
- `signature`: a signature stroke at the bottom (true or false, default false)
- `lines`: lines of writing (integer 0 to 10, default 6)

**`papers`** (about 1.4 wide, 1.8 deep, 0.2 tall) A small stack of pages lying flat, the top one written on. Tints: `neutral`, `tee`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `neutral`.

- `count`: pages (integer 2 to 8, default 4)
- `w`: width (number 0.6 to 3, default 1.3)
- `d`: length (number 0.6 to 3, default 1.7)

**`certificate`** (about 2.1 wide, 0.09 deep, 1.4 tall) A certificate or credential card standing on its edge, with a border, lines and a ribboned seal. Tint seal: a cinnabar seal; tee: an indigo attestation seal; other tints: a seal in that tint. Tints: `seal`, `tee`, `neutral`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `seal`. Anchors: `seal`.

- `w`: width (number 1 to 4, default 2.1)
- `h`: height (number 0.7 to 3, default 1.45)

**`book`** (about 1.5 wide, 1.9 deep, 0.3 tall) A closed book lying flat (a rule book, a code of practice, a standard), optionally with a ribbon and an emblem on the cover. Tints: `neutral`, `tee`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `institutions`.

- `w`: width (number 0.6 to 3, default 1.5)
- `d`: length (number 0.8 to 3, default 1.9)
- `thick`: thickness (number 0.1 to 1, default 0.32)
- `emblem`: the mark on the cover (seal: a cinnabar seal) (one of none, ring, seal, bars, lock; default bars)
- `ribbon`: a ribbon bookmark in the cover's dark shade (true or false, default true)

**`ledger`** (about 4 wide, 0.8 deep, 1 tall) An append-only log: blocks joined in a row (or stacked), the newest one in the tint, for a transparency log or a public ledger. Tints: `tee`, `data`, `neutral`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `tee`. Anchors: `first`, `new`.

- `count`: blocks (integer 2 to 7, default 4)
- `layout`: a row along x or a stack (one of row, stack; default row)
- `size`: block size (number 0.3 to 1.5, default 0.75)
- `pending`: the newest block floats just above its place (being added) (true or false, default true)

### Security

**`seal`** (about 0.9 wide, 0.9 deep, 0.1 tall) A wax seal (a signature, an attestation): a disc lying flat, or standing upright. Tints: `seal`, `tee`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `seal`. Anchors: `rim`.

- `r`: radius (number 0.15 to 1.5, default 0.45)
- `pose`: lying flat or standing on its edge (one of lying, standing; default lying)

**`padlock`** (about 1 wide, 0.4 deep, 1.1 tall) A padlock standing, keyhole toward the front; open lifts the shackle. Tints: `tee`, `neutral`, `data`, `dark`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `tee`. Anchors: `center`.

- `size`: body width (number 0.3 to 3, default 1)
- `open`: the shackle lifted out (true or false, default false)

**`key`** (about 1.6 wide, 0.6 deep, 0.1 tall) A key lying flat on the ground, its bow toward the back-left. Tints: `neutral`, `tee`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `neutral`.

- `size`: length (number 0.5 to 4, default 1.6)

**`shield`** (about 1.3 wide, 0.3 deep, 1.6 tall) A shield standing upright with an emblem: protection, a security claim. Tints: `tee`, `neutral`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `tee`.

- `size`: width (number 0.4 to 3, default 1.3)
- `emblem`: the mark on the shield (one of none, lock, keyhole, chip, bars; default lock)

**`stamp`** (about 1.7 wide, 0.9 deep, 1.2 tall) A rubber stamp with a knob handle, and optionally its fresh impression beside it: signing, approval, certification. Tints: `seal`, `tee`, `data`, `neutral`; default `seal`.

- `size`: scale factor (number 0.5 to 2.5, default 1)
- `impression`: a stamped ring on the ground beside it (true or false, default true)

### Analysis

**`magnifier`** (about 1.7 wide, 0.2 deep, 2.2 tall) A magnifying glass standing on the tip of its handle, the lens upright: detection, inspection. reveal draws what the lens finds (a hidden watermark). Use it only where detection itself is the story. Tints: `neutral`, `tee`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `neutral`. Anchors: `lens`, `tip`.

- `r`: lens radius (number 0.3 to 2, default 0.62)
- `height`: lens center above the base; 0 rests the handle's tip on the base (the center then sits at about 2.1 r); a larger value lengthens the handle down to the base, up to 3 r, then the glass floats (number 0 to 5, default 0)
- `turn`: turn the lens about the upright, in degrees (+ turns its face toward the lower right) (number -60 to 60, default 0)
- `reveal`: what shows inside the lens (one of none, wave, dots, grid, mark; default none)

**`scale`** (about 1.8 wide, 1.8 deep, 2 tall) A balance scale as on the hero's top plate: a white column on a round foot, a thin beam and two bowl pans hanging from it, drawn in the tint's line color: weighing, judgment, oversight, a law. Tints: `neutral`, `institutions`, `tee`, `data`, `evaluations`; default `institutions`.

- `tilt`: beam tilt: -1 left pan down, 1 right pan down (number -1 to 1, default 0)
- `size`: overall scale factor (number 0.5 to 3, default 1)

**`gauge`** (about 1.4 wide, 0.3 deep, 1 tall) A dial standing upright with a needle and a filled arc: a score, a threshold, a benchmark. Tints: `neutral`, `tee`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `evaluations`.

- `value`: needle position 0 to 1 (number 0 to 1, default 0.7)
- `size`: dial width (number 0.6 to 3, default 1.4)

**`bars`** (about 2.2 wide, 0.4 deep, 1.9 tall) A 3D bar chart standing on the ground: results, scores, measurements. Tints: `neutral`, `tee`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `evaluations`. Anchors: `top`.

- `heights`: bar heights, left to right (list of 2 to 8 numbers, each 0.1 to 5; default [0.8, 1.3, 1, 1.9])
- `highlight`: index of the bar in the tint (-1: the tallest) (integer -1 to 7, default -1)
- `bar`: bar width (number 0.15 to 1, default 0.42)

### Media

**`photo`** (about 2.2 wide, 0.1 deep, 1.6 tall) A picture standing on its edge: a landscape, a portrait, a video frame or a sound clip. mark overlays a faint watermark pattern; tag hangs a provenance tag or a seal on its corner. Tints: `neutral`, `outputs`, `tee`, `data`, `models`, `agents`, `evaluations`, `institutions`; default `neutral`. Anchors: `picture`.

- `w`: width (number 0.8 to 5, default 2.2)
- `h`: height (number 0.6 to 4, default 1.6)
- `content`: what the picture shows (one of landscape, portrait, video, audio, text; default landscape)
- `mark`: a faint watermark pattern over the picture (one of none, wave, dots; default none)
- `tag`: tag: a label tag; seal: a small cinnabar seal (indigo with tint tee); pin: a round badge (one of none, tag, seal, pin; default none)

**`camera`** (about 1.3 wide, 1 deep, 1.1 tall) A camera with its lens toward the front: capture, a photo's origin. Tints: `neutral`, `tee`, `data`, `outputs`; default `neutral`. Anchors: `lens`.

- `size`: body width (number 0.5 to 3, default 1.3)

### Institutions

**`building`** (about 4 wide, 2.8 deep, 3 tall) A public building with columns and a pediment: a government, a regulator, a court, a standards body. Tints: `neutral`, `models`, `outputs`, `agents`, `evaluations`, `institutions`, `tee`; default `neutral`. Anchors: `door`, `top`.

- `w`: width (number 2 to 7, default 3.6)
- `d`: depth (number 1.4 to 5, default 2.4)
- `columns`: columns (integer 3 to 9, default 5)
- `emblem`: a round emblem in the pediment (the tint's accent) (true or false, default true)

**`gavel`** (about 1.8 wide, 1.1 deep, 0.6 tall) A judge's gavel resting on its square sound block: a ruling, enforcement. Tints: `neutral`, `institutions`; default `institutions`.

- `size`: scale factor (number 0.5 to 3, default 1)

### Agents

**`agent`** (about 1.2 wide, 1.2 deep, 1.2 tall) An AI agent: a glass cube with a core (a sphere, a cube or a face). Tint agents: teal as on the hero; tee: indigo, an agent in an enclave; neutral: plain glass. Tints: `agents`, `tee`, `data`, `neutral`, `models`; default `agents`. Anchors: `core`.

- `size`: cube edge (number 0.5 to 3, default 1.2)
- `core`: the core (one of sphere, cube, face; default sphere)
- `glow`: a soft glow around the core (a picture keeps one glow) (true or false, default false)

**`robot_arm`** (about 1.2 wide, 1.6 deep, 2.1 tall) An industrial robot arm on a round base: an agent acting in the world, automation. Tints: `neutral`, `agents`, `data`, `tee`; default `neutral`. Anchors: `gripper`.

- `reach`: scale factor (number 0.6 to 2, default 1)

**`tool`** (about 0.9 wide, 0.2 deep, 0.9 tall) A tool an agent calls, as a standing tile with an icon (as on the hero's agent layer). Tints: `agents`, `neutral`, `tee`, `data`, `models`, `outputs`, `evaluations`, `institutions`; default `agents`.

- `icon`: the icon (one of gear, terminal, globe, wrench, search, doc, database, mail; default gear)
- `size`: tile width (number 0.4 to 2, default 0.9)

**`nodes`** (about 3.4 wide, 2.5 deep, 0.5 tall) A small network: spheres joined by lines, standing on the ground (agents talking, a protocol, a mesh). The highlighted node takes the tint. Tints: `neutral`, `tee`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `agents`. Anchors: `hub`.

- `layout`: how the nodes are joined (one of mesh, ring, star, chain; default mesh)
- `count`: nodes (integer 3 to 8, default 5)
- `w`: width (x) (number 1 to 8, default 3)
- `d`: depth (y) (number 0.6 to 8, default 2.2)
- `post`: a short post under each node (number 0 to 0.15, default 0)
- `highlight`: index of the node in the tint (-1: none) (integer -1 to 7, default 0)

### Models

**`neural_net`** (about 2.2 wide, 0.1 deep, 1.5 tall) A model as a standing card of layered nodes and connections, as on the hero's model layer. Tints: `models`, `neutral`, `tee`, `data`, `outputs`, `agents`, `evaluations`, `institutions`; default `models`.

- `columns`: nodes in each column of the network, left to right (`layers` is accepted as its older name) (list of 2 to 5 numbers, each 1 to 6; default [3, 4, 2])
- `w`: card width (number 1 to 5, default 2.2)
- `h`: card height (number 0.8 to 4, default 1.5)

**`weights`** (about 1.4 wide, 1.4 deep, 1.4 tall) Model weights as a block: a cube whose faces carry a regular grid of cells shaded like a matrix of values, two of them in the tint's strong shade (a model file, a checkpoint). Tints: `models`, `neutral`, `tee`, `data`, `outputs`, `agents`, `evaluations`, `institutions`; default `models`.

- `size`: edge (number 0.5 to 3, default 1.4)

### Proofs

**`proof_tree`** (about 2.7 wide, 1.2 deep, 2.5 tall) Building blocks stacked as a stepped pyramid, many lemmas at the bottom and one theorem at the top: a formal proof, verified building blocks. The top block takes the tint. Tints: `evaluations`, `tee`, `data`, `neutral`, `models`, `institutions`; default `evaluations`. Anchors: `top`.

- `levels`: rows of blocks (the bottom row has this many) (integer 2 to 5, default 4)
- `block`: block edge (number 0.3 to 1.2, default 0.62)

**`math_block`** (about 1 wide, 1 deep, 1 tall) A block with an abstract mark on its front (a turnstile, brackets, an equals sign, a lambda, a sum): a formula, a lemma, a statement. Tints: `neutral`, `evaluations`, `tee`, `data`, `models`; default `neutral`.

- `size`: edge (number 0.4 to 2.5, default 1)
- `mark`: the mark (one of turnstile, brackets, equals, lambda, sum, arrow; default turnstile)

### Location

**`map`** (about 3.2 wide, 2.4 deep, 0.06 tall) A map tile lying on the ground: land, roads, a river and a border. Tints: `neutral`, `tee`, `data`; default `neutral`.

- `w`: width (x) (number 1 to 10, default 3.2)
- `d`: depth (y) (number 1 to 10, default 2.4)
- `border`: a dashed border line across the map (true or false, default true)

**`map_pin`** (about 0.9 wide, 0.6 deep, 1.5 tall) A location pin standing on its point: where something is (a chip, a server, a user). Tints: `data`, `tee`, `neutral`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `data`. Anchors: `tip`.

- `size`: pin width (number 0.3 to 2, default 0.9)

**`satellite`** (about 3.5 wide, 0.7 deep, 1 tall) A satellite with two solar wings and a dish, floating (give it a height in 'at'): positioning, location checks, remote sensing. Tints: `neutral`, `tee`, `data`; default `neutral`.

- `size`: scale factor (number 0.5 to 2.5, default 1)

**`globe`** (about 1.6 wide, 1.6 deep, 1.9 tall) A globe on a small stand: a shaded sphere with meridians on its lit side: international, global standards, worldwide. Tints: `neutral`, `tee`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `neutral`.

- `r`: radius (number 0.3 to 2, default 0.8)

### Supply chain

**`crate`** (about 1.3 wide, 1.3 deep, 1.2 tall) A shipping crate with slats and a label: a shipment, the supply chain, an export. Tints: `neutral`, `tee`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `neutral`.

- `size`: edge (number 0.5 to 3, default 1.3)
- `label`: a label on the front in the tint (true or false, default true)

**`chain`** (about 3.1 wide, 0.4 deep, 0.5 tall) A chain of solid links lying along x, alternately standing and lying, whole or broken: a chain of evidence, of custody, of trust. broken opens the chain after that link. Tints: `tee`, `neutral`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `tee`.

- `links`: links (integer 2 to 9, default 5)
- `broken`: the link after which the chain is open (-1: whole) (integer -1 to 8, default -1)
- `size`: link length (number 0.4 to 2, default 0.8)

**`gate`** (about 3 wide, 0.5 deep, 2.8 tall) A gateway of two pillars and a lintel, with an optional scanning field between them: a checkpoint, a border, an access check. Tints: `neutral`, `tee`, `data`, `models`, `outputs`, `agents`, `evaluations`, `institutions`; default `tee`. Anchors: `opening`, `through`.

- `w`: inner width (number 1 to 6, default 2.2)
- `h`: inner height (number 1 to 6, default 2.4)
- `field`: a glowing scanning field (true or false, default true)

**`sign`** (about 1.2 wide, 0.1 deep, 2 tall) A warning sign on a post: a triangle with an exclamation mark (no words): a risk, an attack, a caution. Tints: `warn`, `data`, `neutral`; default `warn`.

- `size`: scale factor (number 0.5 to 2.5, default 1)

**`conveyor`** (about 4 wide, 1.2 deep, 0.7 tall) A conveyor belt on legs: a pipeline, a processing line. Put props on it with 'on'. Tints: `neutral`, `tee`, `data`; default `neutral`. Anchors: `end`, `start`.

- `length`: length (x) (number 1.5 to 12, default 4)
- `width`: belt width (number 0.6 to 3, default 1.2)

### People

**`person`** (about 0.5 wide, 0.4 deep, 2.3 tall) The reader from the home page hero: one person seen from behind in the orange coat, reading a phone held in both hands (the hero's own figure, traced by tools/scene/figure.py). They face up and to the right (facing back-right, the only facing), so stand them at the front left, looking into the scene. No faces, no crowds: at most one per picture. Tints: `data`, `neutral`, `tee`; default `data`. Anchors: `head`, `phone`.

- `height`: height (number 1.4 to 3.5, default 2.4)

**`desk`** (about 3.2 wide, 1.8 deep, 1.1 tall) A desk on four legs; place things on it with 'on'. Tints: `neutral`; default `neutral`.

- `w`: width (x) (number 1.2 to 8, default 3.2)
- `d`: depth (y) (number 0.8 to 4, default 1.8)
- `h`: height (number 0.5 to 2, default 1.1)

## Materials

`box`, `slab`, `cylinder` and `sphere` take a `material`: `plate`, `tplate` (TEE plate), `metal`, `paper`, `soft`, `steel`, `dark`, `ink`, `int` (interposer gray), `hbm`, `die`, `pcb`, `gold`, `kraft` (cardboard), `tee`, `teelight`, `data`, `datalight`, and each layer hue in a strong and a light form (`models`, `modelslight`, `outputs`, …). `auto` (the default) follows the tint. Every material has a top, a lit front-left and a shaded front-right color; faces in other directions are shaded between them. Layer, `tee` and `pcb` materials count as story tints; there is no cinnabar material.

## How it works

- `compose.py` validates the spec, builds each prop in its own coordinates, turns, scales and places it, routes the links, frames the camera and sizes the floor.
- A prop is a set of parts (convex solids with decorations on their faces). Props are drawn in painter's order by a topological sort of their 3D boxes (a box is behind another if they are separated along s, t or h toward the viewer), then each prop's parts the same way. That is why intersecting props are refused.
- A link in the `depth` layer is cut into segments about 0.25 units long, each with a thin box, sorted with the props; consecutive segments are drawn as one path, and a path that resumes after a prop carries a `stroke-dashoffset`, so its dashes keep their rhythm. Where a segment's box meets a prop's box, the prop's own parts decide the order.
- The camera frames the props' screen bounds; with the items camera the floor is then widened in plan until it covers the canvas's two bottom corners.
- The composition checks rasterize each prop's visible faces, and each link's packets, in painter's order into an owner buffer a quarter of the canvas's size (standard library point-in-polygon spans), and sample each link every 0.1 units. A floor link is trimmed against its props' outlines drawn at zoom 1 before the camera is chosen, since an outline's shape does not change with the zoom.
- Every prop except the person, a zone and glass gets a hairline outline in the hero's plate-edge gray (#c3c9d0): its opaque faces, stroked 2.4 px wide in one path just before the prop is drawn, so the prop covers the inner half and 1.2 px shows around it. White and paper props thereby keep their edges against the white backdrop and the light floor. A convex part (a box, a cylinder) is stroked as its hull, which keeps the path short.
- The painter's sort breaks ties on depths rounded to 1e-6 and then on the input order, never on raw floating-point order, so another platform's math library cannot reorder the drawing.
- Faces turned away from the viewer are culled, and a face's color follows its normal against the light from the upper left, so a prop turned with `facing` is shaded correctly.
- Shadows are each part's footprint pushed toward the lower right, blurred and drawn in one group under every prop, plus small contact shadows where a thin part touches the floor (a magnifier's handle, the person's feet).
- The person is not modeled here: `figure.py` traces the hero's own figure from `tools/hero/person.py` into `figure.json` (`python3 tools/scene/figure.py --write`; the tests run `--check`), and the prop places those paths at its feet.
- Output is one `<svg>` 1200 × 800 with a `<defs>` block (gradients and blur filters with fixed ids), a background rect and paths. There are no scripts, no `<foreignObject>`, no text, no external references. Numbers are rounded to four places and printed with one decimal, so the same spec gives the same bytes on any platform; the pictures are about 9 to 27 KB, most of them 12 to 20 KB.

## Adding a prop

Add a function to `props.py` or `props2.py` with the `@prop` decorator: a name, a group, a one-sentence description, the tints it allows, and its parameters (`num`, `integer`, `flag`, `choice`, `nums`). Draw in local coordinates (x along the front, y into the depth, the front at −y, z up, footprint centered on the origin) with the builder: `b.box`, `b.cbox`, `b.cyl`, `b.sphere`, `b.obox` (an oriented box), `b.extrude` (a 2D shape on a plane with depth), and decorations on a face plane (`front_plane`, `right_plane`, `top_plane`, then `plane.shape`, `plane.line`, `tline` for a line of "writing"). Keep parts from intersecting each other, set `b.anchors` for useful link points, `b.surface` if things can stand on it, and `b.contacts` for a thin part that touches the floor. Draw a device's small light as a dot without a halo (a `Glow(..., lamp=True)` wider than 0.12 units counts toward the one glow), set `b.port` to the anchor a link should reach when it names the prop alone (for a prop that is mostly empty space, such as a magnifier), set `b.outline = False` for a prop that must not get the hairline outline, and paint cinnabar only for the seal marks `compose._seal_marks` counts. To rename a parameter, keep the old name working with `aliases={"old": "new"}` in `@prop`. Then regenerate the props reference above (`--props-md`), redraw the catalog, look at it, and run `python3 -m unittest tests.test_illustrate`.
