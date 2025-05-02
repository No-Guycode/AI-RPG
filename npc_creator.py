#!/usr/bin/env python3
import os
import sys
import json

NPC_DATA_FILE = "npc_data.json"

def load_npcs():
    try:
        with open(NPC_DATA_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_npcs(npcs):
    with open(NPC_DATA_FILE, 'w') as f:
        json.dump(npcs, f, indent=4)
    print(f"Saved {len(npcs)} NPC(s) to {NPC_DATA_FILE}.")

def create_npc(existing_ids):
    while True:
        npc_id = input("Enter NPC ID (or 'done' to finish): ").strip()
        if not npc_id:
            continue
        if npc_id.lower() == 'done':
            return None
        if npc_id in existing_ids:
            print(f"ID '{npc_id}' already exists. Choose another.")
            continue
        break
    name = input("Enter NPC Name: ").strip()
    personality = input("Enter personality description: ").strip()
    role = input("Enter role description: ").strip()
    quest_instruction = input("Enter quest instruction: ").strip()
    default_greet = "Hello there! How can I help you today?"
    greeting = input(f"Enter starting greeting (optional) [default: {default_greet}]: ").strip()

    npc = {
        "id": npc_id,
        "name": name,
        "personality": personality,
        "role": role,
        "quest_instruction": quest_instruction
    }
    if greeting:
        npc["greeting"] = greeting
    return npc

def main():
    print("=== NPC Creator ===")
    npcs = load_npcs()
    existing_ids = {npc.get('id') for npc in npcs if isinstance(npc, dict) and 'id' in npc}

    while True:
        new_npc = create_npc(existing_ids)
        if new_npc is None:
            break
        npcs.append(new_npc)
        existing_ids.add(new_npc['id'])
        print(f"Added NPC '{new_npc['id']}'.")

    save_npcs(npcs)

    # >>> FIXED: directly import and call chat.main() <<<
    print("\nLaunching NPC Chat…")
    import npc_chat
    npc_chat.main()

if __name__ == '__main__':
    main()
