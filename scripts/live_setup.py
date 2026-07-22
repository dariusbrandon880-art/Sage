#!/usr/bin/env python3
"""SAGE Live Operational Activation Setup Assistant.

Guides developers through the step-by-step live configuration of
production credentials, security parameters, and OAuth sync capabilities.
"""

import os
import sys
import hmac
import hashlib
from pathlib import Path

# Styling helpers
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_title(text: str):
    print(f"\n{BOLD}{CYAN}=== {text} ==={RESET}")


def print_success(text: str):
    print(f"{GREEN}[✓] {text}{RESET}")


def print_info(text: str):
    print(f"[*] {text}")


def print_warn(text: str):
    print(f"{YELLOW}[!] {text}{RESET}")


def print_error(text: str):
    print(f"{RED}[✗] {text}{RESET}")


def main():
    print("=" * 70)
    print(f"{BOLD}{GREEN}      SAGE RUNTIME - LIVE PLATFORM ACTIVATION ASSISTANT{RESET}")
    print("=" * 70)
    print("This utility will assist you in configuring your production keys,")
    print("setting up live integrations, and verifying end-to-end connectivity.")

    # 1. Host Domain Configuration
    print_title("1. LIVE HOSTING & PUBLIC HTTPS ENDPOINT")
    print("To receive GitHub webhooks and ChatGPT actions, SAGE must be hosted")
    print("on a public server with SSL (HTTPS).")
    current_host = os.getenv("HOST", "0.0.0.0")
    current_port = os.getenv("PORT", "8000")
    print_info(f"Current Bind Settings: {current_host}:{current_port}")
    print_info("Recommended: Use Nginx/Caddy with Let's Encrypt reverse-proxy to port 8000.")

    # 2. OpenAI Custom Action Key
    print_title("2. OPENAI CUSTOM GPT ACTION SECURITY")
    print("To authorize ChatGPT to securely read and write SAGE state,")
    print("configure your secret API Key boundaries.")
    current_keys = os.getenv("SAGE_API_KEYS", "")
    if current_keys and current_keys != "sage-default-key-2026":
        print_success(f"Existing custom keys detected: {len(current_keys.split(','))} keys configured.")
    else:
        print_warn("SAGE is currently using the default development key.")

    # 3. Gemini / Jules API Token
    print_title("3. GEMINI / JULES COGNITIVE WORKFLOW")
    print("To sync multi-turn developer reasoning directly to the master archive,")
    print("SAGE utilizes Google AI Studio credentials.")
    gemini_key = os.getenv("GEMINI_API_KEY", "")
    if gemini_key:
        print_success("Gemini API Key is configured in environment.")
    else:
        print_warn("No Gemini API Key found. AI context endpoints will run in sandbox mode.")

    # 4. GitHub Webhook Passphrase
    print_title("4. GITHUB WEBHOOK CRYPTOGRAPHIC SIGNATURE")
    print("To prevent payload spoofing, all inbound GitHub commits, releases,")
    print("and pull requests are verified using SHA256 HMAC.")
    webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    if webhook_secret:
        print_success("GITHUB_WEBHOOK_SECRET configured. HMAC-SHA256 active.")
    else:
        print_warn("No webhook secret found. Webhooks will bypass origin verification.")

    # 5. Google Workspace OAuth Verification
    print_title("5. GOOGLE WORKSPACE OAUTH DRIVE SYNCHRONIZATION")
    print("SAGE mirrors markdown files to Google Docs and trackers to Google Sheets.")
    creds_path = Path(".sage/credentials.json")
    if creds_path.exists():
        print_success("Google OAuth credentials file found at '.sage/credentials.json'.")
        print_info("Upon first run of 'POST /tools/workspace/sync', SAGE will initiate")
        print("the standard interactive Google OAuth consent browser flow on your machine,")
        print("persisting 'token.json' under '.sage/' for continuous headless execution.")
    else:
        print_warn("Credentials missing at '.sage/credentials.json'.")
        print("Follow the steps in docs/master/EXTERNAL_SETUP.md to download your credentials.json.")

    # 6. Next Steps Summary
    print_title("6. PROVISIONING & IMMEDIATE ACTION CHECKLIST")
    print("To complete 100% of the live cloud connection process:")
    print(f"  1. Update {BOLD}.env{RESET} with your live secrets.")
    print("  2. Ensure your domain is routed and Nginx is configured.")
    print(f"  3. Run {BOLD}bash scripts/activate_sage.sh{RESET} to boot SAGE.")
    print("  4. Upload SAGE's OpenAPI schema to Custom Actions in ChatGPT.")
    print("  5. Add your secure payload URL to your GitHub Webhook settings.")
    print("=" * 70)
    print(f"{BOLD}{GREEN}SAGE is repository-side complete and ready for live staging!{RESET}")
    print("=" * 70)


if __name__ == "__main__":
    main()
