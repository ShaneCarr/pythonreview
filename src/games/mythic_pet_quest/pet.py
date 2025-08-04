from dataclasses import dataclass

# data class: Auto-generates __init__, __repr__, __eq__,
@dataclass
class MythicPet:
    name: str
    hunger: int = 5
    energy: int = 5
    strength: int = 5

    def __post_init__(self):
        print(f"MythicPet: {self.name} enters world")

def main():
    mp = MythicPet("dragon")
    print(mp.name)
if __name__ == "__main__":
    main()



