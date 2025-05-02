import os
import json
import time
import argparse
import dotenv
from typing import Dict, List, Optional
import sys

# Try to import OpenAI if available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Constants
NPC_DATA_FILE = "npc_data.json"
OPENAI_MODEL = "gpt-4o"  # Using gpt-4o as the latest model

class NPCChatSystem:
    def __init__(self):
        """Initialize the NPC chat system."""
        self.npcs = self._load_npcs()
        self.current_npc = None
        self.api_key = None
        self.conversation_history = []
        self.setup()

    def _load_npcs(self) -> List[Dict]:
        """Load NPC data from the JSON file."""
        try:
            with open(NPC_DATA_FILE, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: {NPC_DATA_FILE} not found. Creating a sample file.")
            sample_npcs = [
                {
                    "id": "merchant",
                    "name": "Gorn the Merchant",
                    "personality": "Shrewd, business-minded, but fair. Speaks with a slight accent.",
                    "role": "Town vendor who sells rare items and knows town gossip.",
                    "quest_instruction": "Can provide information about a rumored treasure in the nearby caves."
                },
                {
                    "id": "guard",
                    "name": "Captain Lyra",
                    "personality": "Stern, dutiful, but kind-hearted. Values order and justice.",
                    "role": "Captain of the town guard, responsible for security.",
                    "quest_instruction": "Might ask players to investigate strange occurrences in the forest."
                }
            ]
            with open(NPC_DATA_FILE, 'w') as file:
                json.dump(sample_npcs, file, indent=4)
            return sample_npcs

    def setup(self):
        """Set up the API provider and API key."""
        # Load environment variables from root .env
        dotenv.load_dotenv(dotenv.find_dotenv())
        if not OPENAI_AVAILABLE:
            print("OpenAI package not installed. Please install it with: pip install openai")
            sys.exit(1)
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            print("Error: OPENAI_API_KEY not found in .env. Please add it to your .env file.")
            sys.exit(1)

    def list_npcs(self):
        """Display all available NPCs."""
        print("\nAvailable NPCs:")
        for npc in self.npcs:
            print(f"ID: {npc['id']} - Name: {npc['name']}")

    def select_npc(self, npc_id: Optional[str] = None):
        """Select an NPC to chat with."""
        if npc_id is None:
            self.list_npcs()
            npc_id = input("\nEnter NPC ID to chat with: ")
        
        for npc in self.npcs:
            if npc['id'] == npc_id:
                self.current_npc = npc
                self.conversation_history = []
                print(f"\nYou are now chatting with {npc['name']}.")
                return True
        
        print(f"NPC with ID '{npc_id}' not found.")
        return False

    def _create_system_prompt(self) -> str:
        """Create a system prompt for the AI based on the current NPC."""
        npc = self.current_npc
        return (
            f"You are {npc['name']}, an NPC in a fantasy RPG game. "
            f"Personality: {npc['personality']} "
            f"Role: {npc['role']} "
            f"Quest: {npc['quest_instruction']} "
            f"Respond as this character would in the game, keeping responses relatively concise. "
            f"Never break character or reference that you are an AI."
        )

    def chat_with_huggingface(self, user_message: str) -> str:
        """Generate a response using the Hugging Face Inference API."""
        api_url = f"https://api-inference.huggingface.co/models/{HF_MODEL}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        # Format the conversation history
        system_prompt = self._create_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for entry in self.conversation_history:
            messages.append(entry)
        
        # Add the current message
        messages.append({"role": "user", "content": user_message})
        
        payload = {
            "inputs": messages,
            "parameters": {
                "max_new_tokens": 250,
                "temperature": 0.7,
                "stream": True
            }
        }
        
        try:
            print(f"\n{self.current_npc['name']}: ", end="", flush=True)
            response = requests.post(api_url, headers=headers, json=payload, stream=True)
            
            if response.status_code != 200:
                error_msg = f"Error: API call failed with status {response.status_code}"
                try:
                    error_data = response.json()
                    if 'error' in error_data:
                        error_msg += f" - {error_data['error']}"
                except:
                    pass
                print(error_msg)
                return "I'm sorry, I'm having trouble responding right now."
            
            full_response = ""
            for line in response.iter_lines():
                if line:
                    try:
                        chunk_data = json.loads(line.decode('utf-8'))
                        if 'generated_text' in chunk_data:
                            chunk = chunk_data['generated_text']
                            print(chunk, end="", flush=True)
                            full_response += chunk
                    except json.JSONDecodeError:
                        pass
            
            return full_response
        
        except Exception as e:
            print(f"\nError: {str(e)}")
            return "I'm sorry, I'm having trouble responding right now."

    def chat_with_openai(self, user_message: str) -> str:
        """Generate a response using the OpenAI API."""
        try:
            client = OpenAI(api_key=self.api_key)
            
            # Format the conversation history
            system_prompt = self._create_system_prompt()
            messages = [{"role": "system", "content": system_prompt}]
            
            # Add conversation history
            for entry in self.conversation_history:
                messages.append(entry)
            
            # Add the current message
            messages.append({"role": "user", "content": user_message})
            
            # Stream the response
            print(f"\n{self.current_npc['name']}: ", end="", flush=True)
            stream = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=250,
                stream=True
            )
            
            full_response = ""
            for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    print(content, end="", flush=True)
                    full_response += content
            
            return full_response
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            return "I'm sorry, I'm having trouble responding right now."

    def chat(self):
        """Main chat loop with the selected NPC."""
        if not self.current_npc:
            print("No NPC selected. Please select an NPC first.")
            return
        
        print("\n--- Chat Session Started ---")
        print(f"You are talking to {self.current_npc['name']}.")
        print("Type 'quit' to end the chat, or 'change' to select a different NPC.")
        
        # Initial greeting from NPC (customizable per-NPC via JSON 'greeting' field)
        greeting = self.current_npc.get(
            'greeting',
            "Hello there! How can I help you today?"
        )
        print(f"\n{self.current_npc['name']}: {greeting}")
        self.conversation_history.append({"role": "assistant", "content": greeting})
        
        while True:
            user_input = input("\nYou: ")
            
            # Exit commands
            cmd = user_input.strip().lower()
            if cmd in ('quit', 'exit'):
                print("Ending chat session.")
                break
            elif cmd == 'change':
                self.list_npcs()
                npc_id = input("\nEnter NPC ID to chat with: ")
                if self.select_npc(npc_id):
                    self.chat()  # Start a new chat with the selected NPC
                break
            
            # Add user message to history
            self.conversation_history.append({"role": "user", "content": user_input})
            
            # Generate response
            response = self.chat_with_openai(user_input)
            
            # Add assistant response to history
            self.conversation_history.append({"role": "assistant", "content": response})
            
            # Limit conversation history to last 10 exchanges to avoid token limits
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

def main():
    parser = argparse.ArgumentParser(description="NPC Chat System")
    parser.add_argument("--npc", help="NPC ID to start chatting with")
    args = parser.parse_args()
    
    npc_system = NPCChatSystem()
    
    if args.npc:
        if npc_system.select_npc(args.npc):
            npc_system.chat()
    else:
        npc_system.list_npcs()
        npc_id = input("\nEnter NPC ID to chat with: ")
        if npc_system.select_npc(npc_id):
            npc_system.chat()

if __name__ == "__main__":
    main()