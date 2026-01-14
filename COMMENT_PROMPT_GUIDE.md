# Comment Prompt Guide

## How It Works

When the bot reaches **2,000 views** (the milestone), it will **pause** and prompt you to enter comments interactively.

## The Prompt Process

### 1. Milestone Reached

When views reach 2,000, you'll see:

```
============================================================
🎯 MILESTONE REACHED: 2000 views
============================================================

It's time to order comments!
Video: https://www.tiktok.com/@the.clips.origins/video/...

Please enter 10 comments (one per line):
Press Enter after each comment. Type 'done' when finished.
Or press Enter with empty line to finish.

Comment 1/10: 
```

### 2. Enter Your Comments

Type each comment and press Enter:

```
Comment 1/10: This is amazing! 🔥
Comment 2/10: Love this content!
Comment 3/10: So good!
Comment 4/10: Keep it up!
Comment 5/10: Amazing work!
Comment 6/10: This is exactly what I needed!
Comment 7/10: Can you make more?
Comment 8/10: Perfect timing!
Comment 9/10: So inspiring!
Comment 10/10: Best one yet!
```

### 3. Finish Early

You can finish early by:
- Typing `done` and pressing Enter
- Pressing Enter with an empty line (after entering at least the minimum)

### 4. Review & Confirm

After entering comments, you'll see:

```
Comments to be posted:
  1. This is amazing! 🔥
  2. Love this content!
  3. So good!
  ...

Ordering 10 comments...
  ✓ Comments ordered! ID: 12345
  ✓ Comments saved to ~/.smmfollows_bot/comments.txt

Continuing with delivery plan...
```

## Tips

### Context Matters
- **Watch the video first** - The bot will pause, giving you time to check the video
- **Make comments relevant** - Since you know the context, make them specific
- **Vary the style** - Mix questions, statements, and reactions

### Good Comment Examples

**Engagement-focused:**
```
What do you think about this?
I need more content like this!
Can you make a tutorial?
This is exactly what I needed!
How did you do that?
```

**Reaction-focused:**
```
This is amazing! 🔥
Love this!
So good!
Perfect!
Incredible!
```

**Question-focused:**
```
What's your process?
Can you explain this?
How long did this take?
What inspired you?
Where can I learn more?
```

## What Happens Next

1. **Comments are ordered** - Sent to the SMM panel
2. **Comments are saved** - Stored in `~/.smmfollows_bot/comments.txt` for future reference
3. **Bot continues** - Delivery plan resumes automatically

## Troubleshooting

### Not enough comments entered?

If you enter fewer than 10 comments:
- The bot will try to fill from saved comments file
- If still not enough, it will skip the order (you can order manually later)

### Want to cancel?

Press `Ctrl+C` to cancel input. The bot will use comments entered so far (if minimum met).

### Comments not relevant anymore?

You can edit `~/.smmfollows_bot/comments.txt` before the milestone, but it's better to enter them fresh when prompted.

## Example Session

```
[12h 0m] Ordering 50 views...
  ✓ Order placed! ID: 1234
  Progress: 2000/4000 views, 70/125 likes

============================================================
🎯 MILESTONE REACHED: 2000 views
============================================================

It's time to order comments!
Video: https://www.tiktok.com/@the.clips.origins/video/7589415681972538631

Please enter 10 comments (one per line):
Press Enter after each comment. Type 'done' when finished.

Comment 1/10: This clip is fire! 🔥
Comment 2/10: Love the editing!
Comment 3/10: So smooth!
Comment 4/10: Can you make more like this?
Comment 5/10: Perfect timing!
Comment 6/10: This is exactly what I needed!
Comment 7/10: Amazing work!
Comment 8/10: Keep it up!
Comment 9/10: So inspiring!
Comment 10/10: Best one yet!

Comments to be posted:
  1. This clip is fire! 🔥
  2. Love the editing!
  3. So smooth!
  ...

Ordering 10 comments...
  ✓ Comments ordered! ID: 5678
  ✓ Comments saved to ~/.smmfollows_bot/comments.txt

Continuing with delivery plan...

[12h 18m] Ordering 50 views...
  ...
```

## Benefits

✅ **Context-aware** - You see the video before commenting  
✅ **Relevant** - Comments match the actual content  
✅ **Natural** - Looks more organic than generic comments  
✅ **Flexible** - Different comments for each video  


