#!/usr/bin/env python3
"""
Create a comments configuration file and update the bot to use it
"""

import json
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

# Default comments (user can customize these)
DEFAULT_COMMENTS = [
    "Great video!",
    "Love this!",
    "Amazing content!",
    "So good!",
    "🔥🔥🔥",
    "This is awesome!",
    "Keep it up!",
    "Best one yet!",
    "Incredible!",
    "Perfect!"
]

def create_comments_config():
    """Create a comments configuration file"""
    config_dir = Path.home() / '.smmfollows_bot'
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / 'comments.txt'
    
    if not config_file.exists():
        # Create default comments file
        with open(config_file, 'w') as f:
            f.write('\n'.join(DEFAULT_COMMENTS))
        print(f"{Fore.GREEN}✓ Created comments file: {config_file}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}You can edit this file to customize your comments{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}Comments file already exists: {config_file}{Style.RESET_ALL}")
    
    # Show current comments
    with open(config_file, 'r') as f:
        comments = [line.strip() for line in f.readlines() if line.strip()]
    
    print(f"\n{Fore.CYAN}Current Comments ({len(comments)}):{Style.RESET_ALL}")
    for i, comment in enumerate(comments[:10], 1):
        print(f"  {i}. {comment}")
    if len(comments) > 10:
        print(f"  ... and {len(comments) - 10} more")
    
    return config_file, comments

if __name__ == "__main__":
    config_file, comments = create_comments_config()
    print(f"\n{Fore.YELLOW}Note: The bot will need to be updated to use these comments.{Style.RESET_ALL}")
    print(f"{Fore.CYAN}We'll need to test which API parameter name works.{Style.RESET_ALL}")


