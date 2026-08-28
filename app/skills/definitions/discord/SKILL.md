# Discord Bot & Interaction Engineering

## Purpose
Build interactive, resilient Discord bots using discord.py 2.x.

## When to Use
Implementing Discord commands, embeds, modals, and message handlers.

## Workflow
1. Setup discord.ext.commands.Bot
2. Register slash commands (/api, /test, etc.)
3. Handle on_message for natural conversation
4. Format status updates with embeds.

## Best Practices
Always defer interactions before heavy operations. Never log bot tokens.

## Common Failures & Pitfalls
Interaction timeout (exceeding 3 seconds without defer), rate limit bans.

## Verification Checklist
- [ ] Interaction deferral active
- [ ] Channel permission checks
- [ ] Embeds formatted cleanly.
