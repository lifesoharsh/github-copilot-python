# Project Instructions for Copilot

## Project
- This project is a Sudoku game being refactored from legacy Python code.
- The application generates and validates 9x9 Sudoku puzzles.
- Each generated puzzle must have exactly one unique solution.
- The application includes difficulty selection, timer, hints, solution checking, Top 10 leaderboard persistence, and dark mode.

## Tech Stack
- Backend: Python 3 with Flask
- Frontend: HTML, vanilla JavaScript, CSS
- Testing: pytest
- Browser persistence: localStorage

## Code Conventions
- Use clear, descriptive function and variable names.
- Keep functions focused on one responsibility.
- Preserve existing public APIs unless a requirement explicitly requires a change.
- Handle invalid input gracefully.
- Add or update tests when changing application behavior.
- Keep frontend logic in main.js and styling in styles.css.
- Keep Sudoku logic in sudoku_logic.py and Flask routes in app.py.

## Sudoku Rules
- Represent the board as a 9x9 list of lists.
- Use 0 to represent an empty cell.
- A valid Sudoku must contain digits 1-9 without duplicates in any row, column, or 3x3 subgrid.
- Puzzle generation must ensure exactly one valid solution using backtracking-based solution counting.
- Do not rely on assumptions about a particular generated puzzle layout.

## Feature Rules
- Difficulty levels control the number of prefilled cells.
- Hints must fill a correct empty cell and lock that cell.
- Incorrect user entries should receive immediate feedback when checked.
- The timer tracks the current game duration and stops when the puzzle is completed.
- Top 10 scores must persist between browser sessions using localStorage.
- Leaderboard entries contain player name, completion time, difficulty, and hints used.
- Dark mode must update the complete UI.

## What NOT to Do
- Do not introduce unnecessary frameworks or libraries.
- Do not use jQuery.
- Do not remove existing functionality when adding a feature.
- Do not change Sudoku rules to make tests pass.
- Do not add unrelated features.
- Do not hard-code a specific puzzle layout.