"""
Fix Problematic Filenames

Renames Python files with commas or hyphens in their names
to use underscores instead (valid Python module names).
"""

from pathlib import Path
import shutil


def fix_filename(file_path: Path) -> Path:
    """Fix filename by replacing commas and hyphens with underscores"""
    name = file_path.name
    new_name = name.replace(",", "").replace(" ", "_").replace("-", "_")

    # Remove multiple underscores
    while "__" in new_name:
        new_name = new_name.replace("__", "_")

    if new_name != name:
        new_path = file_path.parent / new_name
        print(f"Renaming: {file_path.name}")
        print(f"      -> {new_name}")
        shutil.move(str(file_path), str(new_path))
        return new_path
    return file_path


def main():
    base_path = Path(__file__).parent.parent
    src_path = base_path / "src" / "superstandard"

    # Find all Python files with commas or hyphens
    count = 0
    for py_file in src_path.rglob("*.py"):
        if "," in py_file.name or "-" in py_file.stem:  # stem = name without extension
            fix_filename(py_file)
            count += 1

    print(f"\nFixed {count} filenames")


if __name__ == "__main__":
    main()
