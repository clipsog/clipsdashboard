#!/usr/bin/env python3
"""
Continuous monitoring daemon - runs in background to monitor all videos
"""

import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

def run_monitor():
    """Run monitor and display status"""
    monitor_script = Path(__file__).parent / 'monitor_progress.py'
    result = subprocess.run(['python', str(monitor_script)], capture_output=True, text=True)
    return result.stdout

def main():
    print(f"""
    {Fore.CYAN}╔══════════════════════════════════════════════╗
    ║   Continuous Monitor (24/7)              ║
    ╚══════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    print(f"{Fore.YELLOW}Press Ctrl+C to stop{Style.RESET_ALL}\n")
    
    check_interval = 300  # Check every 5 minutes
    
    try:
        while True:
            # Clear screen and show timestamp
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"Status Check: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}{Style.RESET_ALL}\n")
            
            # Run monitor
            output = run_monitor()
            print(output)
            
            # Wait before next check
            print(f"\n{Fore.CYAN}Next check in {check_interval/60:.0f} minutes...{Style.RESET_ALL}")
            time.sleep(check_interval)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Monitoring stopped{Style.RESET_ALL}")

if __name__ == "__main__":
    main()


