---
name: narrated-vibe-knowledge-film
description: Create narrated Chinese knowledge videos in Night (abstract science) or Fable (behavioral story) style, including research, spoken script, storyboard, TTS timing, Canvas animation, subtitles, sound mix, commercial-license checks, 30-second preview, and numbered final MP4 delivery. Use when the user wants a Vibe knowledge film, narrated explainer, 夜曲/寓言知识短片, or a Douyin-ready knowledge video. Do not use for live-action editing or videos whose source assets lack publication rights.
---

# Narrated Vibe Knowledge Film

Create a comprehensible knowledge film whose narration, visible action, subtitle,
and sound all share one timeline. Deliver a project folder and a numbered MP4 in
`成品/`.

## Read before acting

- For any monetized, sponsored, client, or account-growth video, read
  [references/commercial-release.md](references/commercial-release.md).
- For the project file formats and commands, read
  [references/pipeline.md](references/pipeline.md).
- For shot design, read [references/storyboarding.md](references/storyboarding.md).
- For Canvas engine details, read [references/engine.md](references/engine.md)
  only when implementing or debugging animation.
- For visual styling, read [references/worlds.md](references/worlds.md) after
  choosing Night or Fable.

## Non-negotiable rules

1. Treat monetized Douyin publication as `usage: commercial`.
2. Use CosyVoice3 locally by default. Its code and official
   `Fun-CosyVoice3-0.5B-2512` weights are Apache-2.0, but the reference voice
   must be self-recorded or separately cleared for commercial use. Keep one
   rights-documented profile in `voices/narrator.json` and reuse it across
   films; do not request a new recording for every project.
3. Do not assume that an API, model, voice clone, image, font, music track, or
   sound effect permits commercial use. Record the source and license in
   `license-manifest.json` before final render.
4. Never clone a real person's voice without documented permission.
5. Do not reuse upstream reference-film subtitles, examples, images, or shot
   designs. Build every film from the user's topic and verified sources.
6. Generate narration before locking the final shot timings. Measure the real
   audio durations and derive subtitle and scene boundaries from them.
7. Keep a quiet background music bed present for the whole film. Narration is
   always the foreground. Use sparse instrumental textures without vocals,
   busy drums, harsh high frequencies, or dense competing melodies.
8. Every finished film must include `publish.md`: a ready-to-post Chinese
   introduction followed by one to five relevant hashtags. It should state the
   concrete dilemma or question, preserve the film's factual boundary, avoid
   spoiling the full explanation, and invite a specific comment or choice.

## Workflow

### 1. Establish the film

Write the audience, one-sentence claim, desired duration, usage, and the facts
that need verification. Choose one world:

- **C Night / 夜曲** for invisible mechanisms, science, mathematics, logic, or
  philosophy that can be demonstrated through small visual experiments.
- **B Fable / 寓言** for psychology and behavior explained through a recurring
  character, animal, or everyday scene.

When unsure, use Night. Fable requires more custom illustration work.

### 2. Design visible explanations

For every concept choose a recognizable object, process, scale, or scene. Make
the verb in the sentence happen on screen. Questions, definitions, citations,
and conclusions may use typography rather than forced illustration.

Create `facts.md`, `script.md`, and `storyboard.md`. Each storyboard row must
connect one spoken line to a visible subject, action, viewer takeaway, sound,
and source.

### 3. Build the narration

Use short spoken sentences. Normalize numbers, abbreviations, formulas, and
names before synthesis. Keep a pronunciation override file for unusual terms.

Generate one audio file per sentence. Reuse one documented voice throughout a
film. Retry only defective sentences. Do not concatenate the whole script and
hope that timing remains stable.

For commercial work, use `cosyvoice3`, `openai-compatible`, or another adapter
whose model and voice rights have been verified. CosyVoice3 must refuse a
project whose global reference profile is missing or whose `rights_confirmed`
value is not true. The default profile path is `voices/narrator.json` relative
to the skill root.

### 4. Lock the timeline

Run `scripts/build_timeline.py`. It measures each voice clip and writes
`timeline.json`, `subtitles.srt`, and `generated_subs.js`. Use those times in
the Canvas scenes. Let the picture react near the word or phrase it explains,
then hold long enough for comprehension.

### 5. Create and review the first 30 seconds

Build the hardest explanatory shot first, inspect full-resolution stills, then
render the opening clip. Check it with sound on and off:

- without subtitles, the subject and action are recognizable;
- narration, subtitle, and action express the same idea;
- the next shot never starts before the sentence finishes;
- sound effects and music do not mask speech;
- the hook shows a concrete event before naming the concept.

Fix visible or audible problems before extending the full film.

### 6. Render and mix

Render deterministic picture with `engine/render.py`. Export sound events, then
run `engine/audio.py <project> --wav-only` and use `scripts/mix_narration.py` to
mix narration, event sound, and optional BGM.
Speech is the reference layer. Always generate `audio/score.wav`; do not deliver
a narration-only film. Use the safe defaults in `mix_narration.py`: normalize
speech first, keep the generated score low, keep optional BGM lower still, and
duck all background layers smoothly whenever speech is present. During speech
pauses the bed may rise gently but must not jump in level. A dramatic hush means
very quiet background, not digital silence. Do not stretch narration merely to
fit a pre-existing animation.

Before delivery, listen to at least the opening, one dense explanatory section,
and the ending on ordinary speakers or headphones. If any word becomes harder
to understand, lower or simplify the background rather than boosting the whole
mix. Do not ask a novice user to choose dB, LUFS, compressor, or limiter values;
use the script defaults unless they explicitly request a different sound.

### 7. Commercial preflight and delivery

Write `publish.md` before preflight. Keep it concise and natural for Douyin.
Use no more than five `#话题`; never pad the list with unrelated trending tags.

Run `scripts/preflight_release.py`. Stop final delivery if any asset has a
missing source, unknown license, non-commercial restriction, or unapproved
voice identity.

Use `scripts/archive_final.py`. It copies the finished video and introduction
into the ignored `成品/` directory as `NNN_标题.mp4` and `NNN_标题_简介.txt`,
choosing the next available sequence number.

Report what was generated, the TTS provider and voice, source/license status,
verification performed, and any remaining limitation.

## Remotion decision

This skill intentionally keeps the upstream Canvas + Playwright + FFmpeg stack.
Read [references/remotion.md](references/remotion.md) before proposing a Remotion
migration or optional exporter.
