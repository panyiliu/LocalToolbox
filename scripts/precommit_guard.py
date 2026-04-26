import pathlib
import subprocess
import sys


BLOCKED_PATTERNS = (
    ".cursor/",
    "uidemo.html",
    "node_modules/",
    ".DS_Store",
    "Thumbs.db",
)


def get_staged_files() -> list[str]:
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        print("pre-commit guard: 无法读取暂存区文件", file=sys.stderr)
        return []
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def is_blocked(path_str: str) -> bool:
    normalized = path_str.replace("\\", "/")
    return any(pattern in normalized for pattern in BLOCKED_PATTERNS)


def main() -> int:
    staged_files = get_staged_files()
    blocked = [path for path in staged_files if is_blocked(path)]
    if blocked:
        print("pre-commit guard: 检测到不应提交的文件，请先移出暂存区：", file=sys.stderr)
        for file_path in blocked:
            print(f"  - {file_path}", file=sys.stderr)
        print("建议执行: git restore --staged <file>", file=sys.stderr)
        return 1

    print("pre-commit guard: staged files check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
