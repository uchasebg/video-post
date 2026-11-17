---
name: video-post
description: "Write the text for a short video post (10–15 s) for Уча.се: a HOOK (the yellow banner that stays on top of the video), a VOICE OVER script (25–40 words, whose length sets the video length) and a DESCRIPTION (the caption that continues the voice over). Topics: calendar holidays, traditions, anniversaries of people and institutions, curious facts from school subjects. Written in Bulgarian first; on request a finished post is translated for eduboom (IT, RO, PL, ES, TR, AL, RS, GR, HU) as real-time-static-post does it. Also handles static card posts (Коледа, Нова година), which have a hook and a description but no voice over. Use when the user gives a topic or a date and asks for 'пост', 'видео пост', 'хук + войс оувър + описание', 'скрипт за видео', 'напиши ми текстовете за поста за този празник/личност/факт', or invokes /video-post. NOT for real-time news or memorial posts about a death (real-time-static-post), and NOT for paid ad creatives (ad-from-concept, ad-recreate, ad-translate)."
metadata:
  version: 1.0.0
---

# Video post (hook + voice over + description)

One short video, **10–15 seconds**. Three pieces of text:

| Piece | What it is | Where it lives |
|---|---|---|
| **Хук** | the text in the **yellow banner at the top of the video**, visible the whole time | on screen, silent |
| **Voice over** | what is spoken over the video. Its length *is* the video length | audio |
| **Описание** | the caption under the post: continues the voice over and tells the story in full | Facebook + Instagram |

The three are one chain with one job each: **the hook stops the scroll, the voice over opens a gap it
refuses to close, the description closes it and keeps opening new ones.** None of the three repeats
another one's sentence.

Language: **Bulgarian** (Уча.се). Translate only when the user explicitly asks for a given post — then
follow `style-guide.md` → Превод.

## Files (read them every run)

- `style-guide.md` — **the formula.** Lengths, the hook patterns, the voice over beats, the description
  structure, emoji, CTA, tone, the static-card variant and the translation standard.
- `examples.md` — all 12 reference posts the user supplied, the non-Bulgarian ones translated into
  Bulgarian, each with a note on what it teaches. Match this voice.
- `topic-bank.md` — the agreed topic bank. Check it when the user names a topic or asks what is next.
- `learnings.md` — **running log of the user's feedback and the decisions already taken.** Read before
  writing, append after every run.
- `scripts/post_sheet.py` — measuring and the tracking sheet (`measure`, `add`, `update`, `show`).

## Workflow

1. **Place the topic.** Look it up in `topic-bank.md`. Then decide which of the two kinds it is:

   - **Закотвена в дата** — holiday, birth/death date, anniversary of an event. Establish which day the
     post goes out and why that day. Compute the anniversary from today's real date and state the number
     in the description ("200 години от рождението", "61 години"). Get the arithmetic right — it is the
     most common silent error in this format.
   - **Без дата (evergreen)** — a curious fact that works any day: „Защо вилицата е смятана за
     сатанинско изобретение", „Защо през зимата от устата ни излиза облаче". **These need no occasion**
     (user, 2026-11-11). Years, centuries and dates still appear inside the description — they are
     the substance of the story — but nothing is built on "на този ден".

   Never invent an occasion for an evergreen topic. A forced anniversary weakens the post.

2. **Find the gap.** Before writing a single line, answer in one sentence: *what will the viewer not
   believe / not know / want to check?* That answer is the post. If the topic has no such twist, say so and
   propose the closest angle that does — a holiday with no surprise in it produces a hook like
   "Ден на народните будители", which is a title, not a hook (see `examples.md`).

3. **Fact-check. Non-negotiable.** These topics are full of comfortable myths — Coca-Cola and the red suit,
   folk etymologies, "the first ever" claims. WebSearch 3–6 queries, WebFetch 3–4 independent credible
   sources, and prefer official ones (museum, institute, archive, BNT, Smithsonian).
   - A fact is stated only if **2 independent reliable sources** confirm it.
   - **Three degrees, in this order of preference** (user rule, 2026-11-11): (1) confirmed by two opened
     reliable sources → state it; (2) uncertain but the story needs it → **hedge** ("според някои
     източници", "смята се", "вероятно", "по описанието на музея", "според преданието") or attribute it
     to whoever makes the claim ("производителят я рекламира като…"); (3) uncertain and it adds nothing →
     **drop the precise detail**. Often it is enough to remove the number or the adjective and keep the
     sentence ("реклами с Дядо Коледа" instead of "с ЧЕРВЕН Дядо Коледа").
   - **Separate folklore from fact.** A legend is introduced as a legend ("Според преданието…"), never as
     history. The examples do this well — follow them.
   - Never invent a "first", a year, a number or a quote.
   - **A source you did not open is not a source** (user challenge, 2026-11-11). A search-engine summary
     points you where to look; it is not evidence. If WebFetch returns 402/403/404, find the fact
     elsewhere or drop it — never list that link among the sources. Record in `sources` which links were
     opened directly and which failed.
   - **For claims about images, check the printing technique, not just the description.** Nast's
     "Merry Old Santa Claus" (1881) is described everywhere as a red-suited Santa, but Harper's Weekly
     printed in black and white and the original is a black-and-white wood engraving; the colour versions
     online are later. The same trap caught the White Rock ads.
   - Keep the sources; show them to the user as markdown links at the end.

4. **Write, in this order: voice over → hook → description.** The voice over sets the gap, so it comes
   first; the hook is then written so it does not duplicate it, and the description is written to answer it.
   Follow `style-guide.md` to the letter.

5. **Measure before showing.** Run:
   `python "%USERPROFILE%\.claude\skills\video-post\scripts\post_sheet.py" measure <post.json>`
   It prints hook words/characters, voice over words and the estimated seconds, and the description
   character count (UTF-16, emoji = 2) and paragraph count. Rewrite anything out of range — do not show the
   user a voice over that runs 25 seconds.

6. **Deliver as a table.** The user wants the finished post in a table. Give, in the chat:
   - a markdown table `Хук | Voice over | Описание` with the voice over in full and the description in
     full (paragraphs separated by `<br><br>` inside the cell);
   - the same description below the table as plain text with real blank lines, for copying;
   - the measurements (VO: n думи ≈ n сек; описание: n знака);
   - **2 alternative hooks** (they also go into the sheet, in `alt_hooks` — user, 2026-11-11);
   - a short fact-check note: what is confirmed, what is hedged, what was left out and why;
   - the sources as markdown links.

7. **After approval, log it.** Write the JSON to the scratchpad and run:
   `python "%USERPROFILE%\.claude\skills\video-post\scripts\post_sheet.py" add <post.json>`
   The script saves and closes the workbook if it is open in Excel, writes, and reopens it — never ask the
   user to close the file. Those two steps are Windows-only and are skipped on other platforms.

   **Where the sheet lives.** The script resolves it at run time, so no path is hardcoded: it uses
   `$VIDEO_POSTS_SHEET` if that is set, otherwise the nearest `content` folder at or above the working
   directory, giving `content/video-posts/video-posts.xlsx`, and it creates the file on the first write.
   If the sheet belongs somewhere else on this machine, set `VIDEO_POSTS_SHEET` rather than editing the
   script.

   `content\hook+vo+description.xlsx` is the user's original reference corpus: **read it, never write to
   it.** On another machine it may simply be absent — that is fine. Its whole content is already in
   `examples.md`, which is the file to rely on.

   **Where there is no local filesystem, Python or Excel** (claude.ai in the browser, for example):
   skip the sheet entirely and do not mention it. Steps 1–6 are the whole job there. Deliver the table
   in the chat as described in step 6 and say the post is ready to be copied into the tracking sheet —
   never ask the user to install anything.

8. **Translation, only on request.** BG approved → translate per `style-guide.md` → Превод. Save with
   `update <n>` into the translation columns.

9. **Learn.** Every time the user corrects something, approves a variant or states a new rule, append a
   dated entry to `learnings.md`: what they said, the rule it implies, one short example. If the rule is
   general, fold it into `style-guide.md` too. Add every approved post to `examples.md`.

## Open questions to raise with the user

Ask again at the start of a session when they have not been answered (user asked to be reminded,
2026-11-11):

1. **Performance data** — views / retention / reactions per post. Until this exists, every rule in
   `style-guide.md` is derived from the shape of the examples, not from what measurably worked.
2. **1–2 finished videos**, or a description of the format (stock footage, animation, talking head). This
   sets the real speaking pace and so the real word count per second.
3. Whether the topic bank should be kept and extended inside `topic-bank.md`.

## Answering the user

Reply in Bulgarian, professionally and briefly. The chat carries the post, the measurements, the
alternatives, the fact-check note and the sources — nothing else.
