from pathlib import Path

from PIL import Image


def main():
    root = Path(__file__).resolve().parents[1]
    source = root / "frontend" / "src" / "assets" / "hero.png"
    output = root / "packaging" / "iconique.ico"

    image = Image.open(source).convert("RGBA")
    image.save(
        output,
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    main()
