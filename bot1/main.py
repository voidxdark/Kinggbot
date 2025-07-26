import json
import time

def load_enemies():
    try:
        with open('shared/enemies.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def run_bot():
    while True:
        enemies = load_enemies()
        print("Enemies list:", enemies)
        time.sleep(5)

if __name__ == "__main__":
    run_bot()
