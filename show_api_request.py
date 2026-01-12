#!/usr/bin/env python3
"""
Show exactly what the API request looks like for comment likes
"""

from colorama import Fore, Style, init

init(autoreset=True)

print(f"""
{Fore.CYAN}What the API Asks For (Comment Likes){Style.RESET_ALL}
{'='*60}

{Fore.YELLOW}Required Parameters:{Style.RESET_ALL}

1. {Fore.GREEN}key{Style.RESET_ALL}
   - Your API key
   - Example: '3327db2d9f02b8c241b200a40fe3d12d'

2. {Fore.GREEN}action{Style.RESET_ALL}
   - Must be 'add' (not 'order')
   - Example: 'add'

3. {Fore.GREEN}service{Style.RESET_ALL}
   - Service ID for comment likes
   - Example: '14718'

4. {Fore.GREEN}link{Style.RESET_ALL}
   - Your TikTok video URL
   - Example: 'https://www.tiktok.com/@user/video/1234567890'

5. {Fore.GREEN}quantity{Style.RESET_ALL}
   - Number of likes to order
   - Minimum: 50
   - Example: 50

6. {Fore.GREEN}username{Style.RESET_ALL}
   - TikTok username of the comment owner
   - WITHOUT the @ symbol
   - Example: 'the.clips.origins'

{'='*60}

{Fore.CYAN}Example API Request:{Style.RESET_ALL}

POST https://smmfollows.com/api/v2

Form Data:
  key: 3327db2d9f02b8c241b200a40fe3d12d
  action: add
  service: 14718
  link: https://www.tiktok.com/@the.clips.origins/video/7589415681972538631
  quantity: 50
  username: the.clips.origins

{'='*60}

{Fore.YELLOW}What This Means:{Style.RESET_ALL}

The API receives:
  ✓ Video URL → Knows which video
  ✓ Username → Knows which user's comment
  ✗ Comment ID → NOT provided
  ✗ Comment text → NOT provided
  ✗ Comment position → NOT provided

{Fore.RED}The Problem:{Style.RESET_ALL}
  If @the.clips.origins has MULTIPLE comments on the video,
  the API doesn't know which specific comment to like.

{Fore.CYAN}Solution:{Style.RESET_ALL}
  Make sure the username you provide has only ONE comment
  on the video. Best practice: Use YOUR OWN comment.

{'='*60}
""")


