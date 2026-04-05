#!/usr/bin/env python3
import os

env_path = r"c:\Users\Devansh\OneDrive\Desktop\voltwise\.env"
print(f"Reading from: {env_path}")
print(f"File exists: {os.path.exists(env_path)}")

if os.path.exists(env_path):
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"\nTotal lines in file: {len(lines)}")
    api_keys = []
    
    for i, line in enumerate(lines, 1):
        line = line.strip()
        print(f"Line {i}: {line[:60] if line else '(empty)'}")
        if line and line.startswith("GEMINI_API_KEY="):
            key = line.split("=", 1)[1].strip()
            if key:
                api_keys.append(key)
                print(f"  ✅ Found key #{len(api_keys)}: {key[:30]}...")
    
    print(f"\nTotal API keys found: {len(api_keys)}")
