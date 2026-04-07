# main.py
from store import DataFrameStore
from agent import run_query
from config import THREAD_ID
import os

def initialize():
    os.makedirs("plots", exist_ok=True)
    DataFrameStore.load()
    print("\n🤖 Aivee - Time Series Analysis Agent is Ready!\n")

def run_cli():
    print("Type 'exit' or 'quit' to stop.\n")
    while True:
        query = input("You: ").strip()
        if query.lower() in ["exit", "quit", "bye"]:
            print("👋 Goodbye!")
            break
        if not query:
            continue
        try:
            response = run_query(query, THREAD_ID)
            print(f"AI: {response}\n")
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")

if __name__ == "__main__":
    initialize()
    run_cli()