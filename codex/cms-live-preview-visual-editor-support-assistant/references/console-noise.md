# Console output to ignore

Preview runs the customer's site in an iframe, with two applications exchanging postMessage. That
arrangement produces console output on healthy setups. Every entry below appears on integrations
that are working correctly.

Read a console log against this list **before** drawing any conclusion from it. Treating one of
these as the cause is a reliable way to lose an hour, and worse, to tell a customer their
integration is broken when it is not.

**If one of these is the only thing in the console, you have no console evidence — not evidence of a
problem.** Say so and move to the network tab.

## The list

### `NO_REQUEST_LISTENER_FOUND` / `No ack listener found`

Routine. It means a postMessage arrived with no registered listener, which happens normally during
load and teardown. Appears on working setups.

Never conclude anything from it on its own. It does not affect SSR content, and it is not evidence
that the handshake failed — check for the tracker POST instead.

### Third-party script errors from ad, consent, or personalisation tags

Expected. Those scripts key their targeting, delivery or storage off the top-level origin, which is
the Contentstack app when the site is framed. They see the iframe context rather than the real
site and behave differently.

Not a Contentstack request failure — the calls fire and fail at the third party's own delivery
stage. This is inherent to iframe rendering and has no product-side fix.

## Adding to this list

An entry earns a place here only if it appears on a **correctly working** integration. Something
that shows up only when a setup is broken is a diagnostic signal and belongs in a FAQ entry, not
here.

Each entry should say what the message actually means, so a reader can tell it apart from a
genuinely similar-looking error, and name the wrong conclusion people draw from it where there is a
common one.
