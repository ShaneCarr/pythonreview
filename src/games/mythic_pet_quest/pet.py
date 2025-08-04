from dataclasses import dataclass

from magic.compat import none_magic

# python3 mythic_pet_quest/pet.py
# data class: Auto-generates __init__, __repr__, __eq__,
@dataclass
class MythicPet:
    name: str
    hunger: int = 5
    energy: int = 5
    strength: int = 5
    def __post_init__(self):
        print(f"MythicPet: {self.name} enters world")
    def status(self):
        print("todo status")
    def feed(self):
        print("todo feed")
    def rest(self):
        print("todo rest")
    def train(self):
        print("todo train")
def main():
    pet = MythicPet("dragon")
    print(pet.name)

    while True:
        pet.status()

        print("\nChoose an Action")
        print("1 Feed")
        print("2 Rest")
        print("3 Train")
        print("4 Quit game")

        choice = input("Enter your choice: ")
        if choice == "1":
            pet.feed()
        elif choice == "2":
            pet.rest()
        elif choice == "3":
            pet.train()
        elif choice == "4":
            break
        else:
            print("Invalid choice")
if __name__ == "__main__":
    main()

