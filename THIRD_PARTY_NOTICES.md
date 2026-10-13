# Third-party notices

## vibe-knowledge-film

This project incorporates and modifies the rendering engine, project generator,
and selected method documentation from
[`Dave-cc/vibe-knowledge-film`](https://github.com/Dave-cc/vibe-knowledge-film),
revision `8c24001c4de15834425c1a58f0d1f15fe76e884f`.

Those files are distributed under the MIT License contained in [`LICENSE`](LICENSE).

The following upstream material is intentionally excluded because the upstream
license does not grant republication rights to the referenced film content:

- `references/analysis.md`
- the filled reference-film briefs in `references/prompts.md`
- reference-film subtitles and shot descriptions in `references/visualization.md`
- `examples/stim_B`, `examples/info_C`, and all upstream example media

## ChatTTS

ChatTTS is an optional local preview dependency. Its code is AGPL-3.0-or-later,
and the official released model is CC BY-NC 4.0. The official model must not be
used for monetized Douyin videos or other commercial output. It is not bundled
in this repository and is downloaded only when a user explicitly installs it.

The project blocks ChatTTS when a production manifest declares
`usage: commercial`. This check does not replace review of the upstream license.

## Fonts and FFmpeg

Font license texts retained in `engine/fonts/` apply to fonts downloaded by the
upstream font helper. FFmpeg is an external runtime and is not redistributed by
this repository.
