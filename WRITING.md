# OSSGolf Writing Guide

Every post on ossgolf.com and every README in an OSSGolf repo follows this guide. It grows as we edit: when a copy change teaches us a new rule, add the rule here with its before and after.

## The Voice

Write the way you would explain it out loud to a friend at the range. Short, technical, factual, in plain English.

Two writers to keep in mind are Paul Graham and Om Malik. Borrow their habits: simple words, one idea leading to the next, a personal story where there is one.

## Rules

### 1. Use plain spoken English

Read the sentence out loud. If nobody would say it that way, rewrite it.

| Before | After |
|---|---|
| Lowest cost. | This is the cheapest option. |
| Control happens over Bluetooth Low Energy | You control it over Bluetooth Low Energy |
| ...needs weight to keep the trainer planted. | ...needs weight so the trainer stays put. |
| ...have earned a place in my practice | ...are now part of my practice |

### 2. Things do not talk

Tags, signals, parts and code do not say, name, answer or announce. Describe what they do and what the reader learns from it.

| Before | After |
|---|---|
| The hop pattern says a hit happened, and the resting frame heard just before it says which club made it. | The hop pattern tells you the club was hit. The resting frame right before it tells you which club it was. |
| ...so one frame names the club. | ...so you only need to hear one frame to know which club it is. |
| It announces itself with one steady tone | When it wakes up, it plays one steady tone |
| A hit gets an answer within about 12 ms. | The tag reacts to a hit within about 12 ms. |
| ...a hit changes its tune | ...a hit changes what it sends |

### 3. Finish the thought

Clipped endings read like a riddle. Say who does what.

| Before | After |
|---|---|
| ...to time the hit. | ...to work out when the hit happened. |
| Foam balls are too light to feed. | Foam balls are too light to work in it. |
| ...ready to be carried to a phone | ...so you can port it to a phone |

### 4. Pick the common word

| Use | In place of |
|---|---|
| sends | emits |
| is filled in | populates |
| is different | stands apart |
| works for | applies |
| helps you feel | teaches the feel of |

### 5. Say what it is

State the fact. Leave out sentences whose job is to say what something is not ("not this, just that") and sentences that only add a negative.

### 6. No em dashes

Use a period, a comma or a colon.

### 7. Make it flow

Each sentence should lead to the next. A run of "We did X. We did Y." reads as start and stop, so join related steps and let one concept set up the following one.

Lay the post out in the order a reader needs it: why it matters, how it was done, what was found, how to try it.

### 8. Who is speaking

- Technical sections are written about the project, like a Hackaday write-up. Leave out "we" and "our".
- A personal story or a personal recommendation is written as "I". The OSSTagLab intro and the 3D printing notes are examples.
- Talking to the reader as "you" is fine.

### 9. Do more with less

Cut every sentence the post works without. When a screenshot, photo or clip shows it, use that and shorten the text around it.

### 10. Numbers and facts

- Check every claim against the source: the data, the project page or the code. If the math is in doubt, do the math.
- Keep the numbers the reader needs and drop the rest.
- Give units, and write "about" or "up to" when the number is a measurement or a ceiling.
- Name what was studied, such as the Arccos Gen 4 tags.
- When a project page and personal experience differ, say whose word it is.

## Format

- **Titles and headings:** Title Case. Small words stay lowercase (a, an, and, at, for, in, is, of, on, or, the, to, with) unless they come first or follow a colon. No period at the end.
- **Compound words:** written open, as on the rest of the site: open source, after hit signal, hard coded, 4 hole course.
- **Links:** link a project the first time it is named, link a technical term to its Wikipedia page, and end the post with a list of links to the repos or project pages.
- **Images:** every post has one image for the home page. Every image has a description of what it shows. A changed image gets a new file name (`-v2`). Photos and clips are published with location and camera data removed.
- **Credit:** name the author of any project that is not ours, and state its license.

## Before You Publish

1. Read it out loud once. Fix anything you would not say.
2. Search for: says, names, answers, announces, emits, populates, and the em dash.
3. Look for "we" and "our" in technical sections.
4. Check each number and each claim against its source.
5. Check that headings are in Title Case.
6. Look at the built page on localhost, then push and compare the live page.
