import json
from pathlib import Path


TEMPLATE = """VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({major}, {minor}, {patch}, {build}),
    prodvers=({major}, {minor}, {patch}, {build}),
    mask=0x3F,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904B0',
        [
          StringStruct('CompanyName', '{publisher}'),
          StringStruct('FileDescription', '{app_name} desktop application'),
          StringStruct('FileVersion', '{version}'),
          StringStruct('InternalName', '{app_name}'),
          StringStruct('OriginalFilename', '{app_name}.exe'),
          StringStruct('ProductName', '{app_name}'),
          StringStruct('ProductVersion', '{version}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def normalize_version(version: str):
    parts = [int(part) for part in version.split(".")]
    while len(parts) < 4:
        parts.append(0)
    return parts[:4]


def main():
    root = Path(__file__).resolve().parent
    metadata = json.loads((root / "version.json").read_text(encoding="utf-8"))
    major, minor, patch, build = normalize_version(metadata["version"])

    version_info = TEMPLATE.format(
        major=major,
        minor=minor,
        patch=patch,
        build=build,
        publisher=metadata["publisher"],
        app_name=metadata["app_name"],
        version=metadata["version"],
    )

    (root / "version_info.txt").write_text(version_info, encoding="utf-8")


if __name__ == "__main__":
    main()
