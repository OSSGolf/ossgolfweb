# ossgolfweb

The OSSGolf website. A static blog for the open source golf projects, built with
[RSS Lobster](https://github.com/HectorZarate/rsslobster). Zero JavaScript output
except a tiny inline search, no trackers, no external requests.

Live projects it points to:

- [osstempo](https://github.com/OSSGolf/osstempo). ESP32 LED golf tempo trainer (firmware, web client, build docs).
- [osstempo-ios](https://github.com/OSSGolf/osstempo-ios). Native SwiftUI and CoreBluetooth iOS controller.
- [unofficial-r10-ios-sdk](https://github.com/OSSGolf/unofficial-r10-ios-sdk). Swift SDK for the Garmin R10 launch monitor.

## How it works

- `rsslobster.json` is the site config (title, tagline, style preset).
- `posts.json` is the content source of record for every post.
- `_site/` is the built output. Cloudflare serves this directory (build root `/_site`).
- Post images live in `_site/images/` and are referenced as `/images/<name>.png`.

## Local preview

```
rsslobster dev
```

## Add a post

```
rsslobster publish "$(cat body.md)" --type post --title "Title" --slug my-slug --tags "a,b,c"
rsslobster regenerate .
```

Commit the updated `posts.json` and `_site/`, then push. The Cloudflare build
deploys the new `_site/` automatically.

Licensed under [MIT](LICENSE).
