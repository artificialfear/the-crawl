# The Crawl

A dungeon-crawler game show where your to-do list is the dungeon. Sign in with Google; your save follows your account on any device.

- `index.html` is the whole app, built from a single source file.
- Saves live in Firebase (Firestore), one private save per Google account. Access rules are in `firestore.rules`.
- `firebase-config.js` identifies the Firebase project. It is not a secret.
