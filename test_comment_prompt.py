#!/usr/bin/env python3
"""
Test the comment prompt functionality
"""

from colorama import Fore, Style, init

init(autoreset=True)

MINIMUMS = {'comments': 10}

print(f"\n{Fore.CYAN}{'='*60}")
print(f"{Fore.GREEN}🎯 MILESTONE REACHED: 2000 views")
print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
print(f"\n{Fore.YELLOW}It's time to order comments!{Style.RESET_ALL}")
print(f"{Fore.CYAN}Video: https://www.tiktok.com/@test/video/123{Style.RESET_ALL}")
print(f"\n{Fore.YELLOW}Please enter {MINIMUMS['comments']} comments (one per line):{Style.RESET_ALL}")
print(f"{Fore.CYAN}Press Enter after each comment. Type 'done' when finished.{Style.RESET_ALL}")
print(f"{Fore.CYAN}Or press Enter with empty line to finish.{Style.RESET_ALL}\n")

comments_list = []
for i in range(MINIMUMS['comments']):
    try:
        comment = input(f"{Fore.CYAN}Comment {i+1}/{MINIMUMS['comments']}: {Style.RESET_ALL}").strip()
        if comment.lower() == 'done':
            break
        if comment:
            comments_list.append(comment)
        elif len(comments_list) >= MINIMUMS['comments']:
            break
    except (EOFError, KeyboardInterrupt):
        print(f"\n{Fore.YELLOW}Input cancelled.{Style.RESET_ALL}")
        break

print(f"\n{Fore.GREEN}✓ You entered {len(comments_list)} comments:{Style.RESET_ALL}")
for i, comment in enumerate(comments_list, 1):
    print(f"  {i}. {comment}")


