"""Print every piece, grouped by difficulty class.

Run from the project root:  PYTHONPATH=src python3 -m extetris
"""
from . import geometry as g
from .pieces import DIFFICULTY_CLASSES


def main():
    for cls in DIFFICULTY_CLASSES:
        infos = cls.catalogue()
        unit = "hole" if cls.SPAWN_HOLES == 1 else "holes"
        print(f"=== {cls.__name__}  ({cls.SPAWN_HOLES} {unit} at spawn, "
              f"{len(infos)} piece{'' if len(infos) == 1 else 's'}) ===")
        for n, info in enumerate(infos, start=1):
            ties = len(info.spawn_turns)
            print(f"\n#{n} {info.name}   box {info.box_size}, touching "
                  f"{info.touching}{', has mirror twin' if info.chiral else ''}"
                  f"{f', {ties} possible spawn turns' if ties > 1 else ''}")
            print(g.render(info.spawn_turns[0]))
        print()


if __name__ == "__main__":
    main()
