#!/usr/bin/env python3
"""
Warhammer 40K Army Randomiser - CLI Version
Generates random 2000 point lists.
"""

from services.loader import load_factions
from services.generator import generate_army
from utils.formatters import format_army_plain_text


def main():
    factions = load_factions()
    if not factions:
        print("No faction files found in 'factions' directory.")
        return

    faction_names = sorted(factions.keys())

    print("\n" + "=" * 60)
    print("    WARHAMMER 40K ARMY RANDOMISER")
    print("=" * 60)

    while True:
        print("\nSelect a faction:")
        for i, name in enumerate(faction_names, 1):
            print(f"  {i:2}. {name}")
        print("   q. Quit")

        choice = input("\nEnter choice (number or 'q'): ").strip().lower()

        if choice == "q":
            print("Goodbye!")
            break

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(faction_names):
                faction_name = faction_names[idx]
                faction_data = factions[faction_name]

                while True:
                    inp = input(f"\nPress Enter to generate {faction_name} (or 'b' to go back): ").strip().lower()
                    if inp == "b":
                        break
                    army = generate_army(faction_data, 2000, faction_name=faction_name)
                    print("\n" + format_army_plain_text(faction_name, army))
            else:
                print("Invalid choice.")
        except ValueError:
            print("Invalid input. Enter a number or 'q'.")


if __name__ == "__main__":
    main()
