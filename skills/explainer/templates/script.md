---
id: {{id}}
lang: {{lang}}
title: {{title}}
voice: female
template: {{template}}   # midnight | paper | blueprint | chalk — see `cli.py templates`
# theme: {accent: "#e4572e"}   # optional brand colors on top of the template
sources:
  - Where the facts in this episode come from
---

## Cover {#cover}

```screen
type: cover
kicker: Series name · Episode 1
title: {{title}}
sub: One sentence on what the viewer will learn
```

- First narration line — it is read aloud and shown as a subtitle.
- Second line. Keep each line to one idea.

## The idea in three parts {#overview}

```screen
type: cards
title: Three things to know
cards:
  - {tag: "1", title: First part, sub: A short explanation, at: 0}
  - {tag: "2", title: Second part, sub: A short explanation, at: 1}
  - {tag: "3", title: Third part, sub: A short explanation, at: 2}
```

- The first part is about this.
- The second part is about that.
- And the third part ties them together.

## Recap {#closing}

```screen
type: closing
items:
  - First part
  - Second part
  - Third part
next: Next episode title
```

- That's the whole idea in three parts.
- Next time, we'll go one level deeper.
