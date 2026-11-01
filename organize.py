import subprocess
import shutil
from pathlib import Path
from datetime import datetime, date

REPO_ROOT = Path(__file__).resolve().parent
START_DATE = date(2026, 11, 1)

SUPPORTED_EXTENSIONS = (".py", ".java", ".cpp", ".js")


def get_git_history():
    command = [
        "git",
        "log",
        "--all",
        "--date=iso-strict",
        "--format=COMMIT_DATE:%ad",
        "--name-only",
    ]

    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    history = []
    commit_date = None

    for line in result.stdout.splitlines():
        line = line.strip()

        if line.startswith("COMMIT_DATE:"):
            timestamp = line.removeprefix("COMMIT_DATE:")
            commit_date = datetime.fromisoformat(timestamp).date()

        elif (
            line
            and commit_date
            and line.endswith(SUPPORTED_EXTENSIONS)
        ):
            history.append((commit_date, line))

    return history


def get_problem_dates():
    problem_dates = {}

    for commit_date, file_path in get_git_history():
        relative_path = Path(file_path)

        # Ignore solutions already inside day folders.
        if not relative_path.parts:
            continue

        if relative_path.parts[0].startswith("Day"):
            continue

        # Each problem is expected to have its own folder.
        if len(relative_path.parts) < 2:
            continue

        problem_folder = relative_path.parts[0]

        if problem_folder not in problem_dates:
            problem_dates[problem_folder] = commit_date
        else:
            problem_dates[problem_folder] = min(
                problem_dates[problem_folder],
                commit_date,
            )

    return problem_dates


def main():
    if not (REPO_ROOT / ".git").exists():
        print("Error: Run this script from inside your Git repository.")
        return

    problem_dates = get_problem_dates()

    if not problem_dates:
        print("No problem folders found in Git history.")
        return

    planned_moves = []

    for problem_name, solved_date in sorted(problem_dates.items()):
        source = REPO_ROOT / problem_name

        # Only move folders that currently exist at the repository root.
        if not source.is_dir():
            continue

        if solved_date < START_DATE:
            print(f"Skipping {problem_name}: date is before START_DATE.")
            continue

        day_number = (solved_date - START_DATE).days + 1
        day_folder = f"Day{day_number:02d}"

        destination_parent = REPO_ROOT / day_folder
        destination = destination_parent / problem_name

        if destination.exists():
            print(f"Skipping {problem_name}: destination already exists.")
            continue

        planned_moves.append((source, destination))

    if not planned_moves:
        print("No folders need to be moved.")
        return

    print("\n=== PLANNED MOVES ===\n")

    for source, destination in planned_moves:
        print(f"{source.name} -> {destination.parent.name}/{destination.name}")

    confirmation = input(
        "\nType YES to move these folders, or anything else to cancel: "
    ).strip()

    if confirmation != "YES":
        print("Cancelled. No folders were moved.")
        return

    moved = []

    try:
        for source, destination in planned_moves:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            moved.append((source, destination))

    except Exception as error:
        print(f"\nError while moving folders: {error}")
        print("Attempting to restore folders already moved...")

        for source, destination in reversed(moved):
            try:
                if destination.exists() and not source.exists():
                    shutil.move(str(destination), str(source))
            except Exception as rollback_error:
                print(f"Could not restore {source.name}: {rollback_error}")

        return

    print("\nOrganization complete.")

    for _, destination in moved:
        print(f"Moved to: {destination.relative_to(REPO_ROOT)}")

    print("\nReview the changes with: git status")


if __name__ == "__main__":
    main()