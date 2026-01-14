# Comments Configuration Guide

## How Comments Work

The bot supports **custom comments** for TikTok videos. When ordering comments, you can specify the exact text you want posted.

## Setting Up Comments

### 1. Comments File Location

Comments are stored in: `~/.smmfollows_bot/comments.txt`

### 2. Format

- **One comment per line**
- Each line will be used as a separate comment
- Empty lines are ignored
- Supports emojis and special characters

### Example `comments.txt`:

```
Great video! 🔥
Love this content!
Amazing work!
So good!
This is awesome!
Keep it up!
Best one yet!
Incredible!
Perfect!
Nice! 👏
```

### 3. How Many Comments Are Used?

- The bot orders the **minimum quantity** (10 comments minimum)
- It will use the **first N comments** from your file (where N = quantity ordered)
- If you have fewer comments than the quantity, it will reuse comments

### 4. When Comments Are Ordered

- Comments are ordered when views reach **2,000** (milestone-based)
- This happens automatically during the delivery process

## Customizing Comments

### Edit the Comments File

```bash
# Open the file in your editor
nano ~/.smmfollows_bot/comments.txt

# Or use any text editor
code ~/.smmfollows_bot/comments.txt
```

### Tips for Good Comments

1. **Keep them natural** - Sound like real users
2. **Vary the length** - Mix short and longer comments
3. **Use emojis sparingly** - Not every comment needs emojis
4. **Make them relevant** - Generic comments work, but context-specific ones are better
5. **Avoid spam patterns** - Don't repeat the same comment multiple times

### Example Comment Sets

**Generic/Positive:**
```
Great video!
Love this!
Amazing content!
So good!
This is awesome!
```

**Engagement-focused:**
```
What do you think?
I need more of this!
Can you make a tutorial?
This is exactly what I needed!
How did you do that?
```

**Emoji-heavy:**
```
🔥🔥🔥
This is fire! 🔥
Amazing! 👏
Love it! ❤️
So good! 😍
```

## API Parameter

The bot sends comments using the `comments` parameter in the API request:
- Format: One comment per line (newline-separated)
- Parameter name: `comments`
- Example: `"Great video!\nLove this!\nAmazing!"`

## Troubleshooting

### Comments not being used?

1. Check if the file exists: `ls ~/.smmfollows_bot/comments.txt`
2. Check file format (one per line)
3. Make sure you have at least 10 comments (minimum order)

### Want to use different comments per video?

Currently, all videos use the same comments file. To use different comments:
1. Edit `comments.txt` before starting a new video
2. Or create separate config files and swap them

### Comments file not found?

The bot will still order comments, but without custom text. The SMM panel may use default comments or random comments.

## Testing

To test if your comments are being loaded:

```bash
python -c "
from pathlib import Path
comments_file = Path.home() / '.smmfollows_bot' / 'comments.txt'
if comments_file.exists():
    with open(comments_file, 'r') as f:
        comments = [line.strip() for line in f.readlines() if line.strip()]
    print(f'Found {len(comments)} comments:')
    for i, c in enumerate(comments[:5], 1):
        print(f'  {i}. {c}')
else:
    print('Comments file not found')
"
```


