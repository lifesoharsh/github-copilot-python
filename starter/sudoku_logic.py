import copy
import random

SIZE = 9
EMPTY = 0

def deep_copy(board):
    return copy.deepcopy(board)

def create_empty_board():
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]

def is_safe(board, row, col, num):
    # Check row and column
    for x in range(SIZE):
        if board[row][x] == num or board[x][col] == num:
            return False
    # Check 3x3 box
    start_row = row - row % 3
    start_col = col - col % 3
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    return True

def fill_board(board):
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                possible = list(range(1, SIZE + 1))
                random.shuffle(possible)
                for candidate in possible:
                    if is_safe(board, row, col, candidate):
                        board[row][col] = candidate
                        if fill_board(board):
                            return True
                        board[row][col] = EMPTY
                return False
    return True

def _solve_for_counting(board, solutions, count_limit):
    """
    Internal backtracking solver that counts solutions.
    Stops early once count_limit solutions are found.
    
    Args:
        board: 9x9 2D list representing the sudoku board
        solutions: List to accumulate found solutions
        count_limit: Maximum number of solutions to find before stopping
        
    Returns:
        True if should continue searching, False if count_limit reached
    """
    # If we've found enough solutions, stop searching
    if len(solutions) >= count_limit:
        return False
    
    # Find next empty cell
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                # Try each digit 1-9
                for num in range(1, SIZE + 1):
                    if is_safe(board, row, col, num):
                        board[row][col] = num
                        # Recursively search
                        if not _solve_for_counting(board, solutions, count_limit):
                            board[row][col] = EMPTY
                            return False
                        board[row][col] = EMPTY
                return True
    
    # No empty cells found - we have a complete solution
    solutions.append(deep_copy(board))
    return len(solutions) < count_limit

def count_solutions(board, count_limit=2):
    """
    Count the number of solutions for a given Sudoku puzzle.
    
    This uses backtracking to find all possible solutions. To improve
    performance, it stops searching after finding count_limit solutions.
    This is useful to verify that a puzzle has exactly one unique solution.
    
    Args:
        board: 9x9 2D list representing the sudoku puzzle (with some empty cells)
        count_limit: Maximum solutions to find before stopping (default: 2)
                    Use count_limit=2 to just check if puzzle is unique
                    
    Returns:
        Integer count of solutions found (up to count_limit)
        
    Example:
        puzzle = [...]  # Some puzzle with empty cells
        num_solutions = count_solutions(puzzle, count_limit=2)
        if num_solutions == 1:
            print("Puzzle has unique solution")
        elif num_solutions > 1:
            print("Puzzle has multiple solutions")
    """
    board_copy = deep_copy(board)
    solutions = []
    _solve_for_counting(board_copy, solutions, count_limit)
    return len(solutions)

def remove_cells(board, clues):
    """
    Remove cells from a completed board to create a puzzle.
    
    This function attempts to remove cells while ensuring the resulting
    puzzle has exactly one unique solution. Uses multiple passes with
    different cell orderings to reliably reach the target clue count.
    
    Args:
        board: 9x9 2D list representing a completed sudoku board
        clues: Target number of clues (filled cells) to leave
    """
    cells_to_remove = SIZE * SIZE - clues
    removed = 0
    max_passes = 10  # Maximum number of removal passes
    pass_num = 0
    
    while removed < cells_to_remove and pass_num < max_passes:
        # Get list of all cell positions and shuffle for randomness
        positions = [(r, c) for r in range(SIZE) for c in range(SIZE)]
        random.shuffle(positions)
        
        pass_removed = 0
        for row, col in positions:
            if removed >= cells_to_remove:
                break
                
            if board[row][col] != EMPTY:
                # Try removing this cell
                backup = board[row][col]
                board[row][col] = EMPTY
                
                # Check if puzzle still has unique solution
                if count_solutions(board, count_limit=2) == 1:
                    # Puzzle still valid with unique solution, keep it removed
                    removed += 1
                    pass_removed += 1
                else:
                    # Removing this cell creates multiple solutions, restore it
                    board[row][col] = backup
        
        # If we didn't remove any cells in this pass, no progress possible
        if pass_removed == 0:
            break
        
        pass_num += 1

def generate_puzzle(clues=35):
    """
    Generate a valid Sudoku puzzle with exactly one unique solution.
    
    Args:
        clues: Target number of filled cells in the puzzle (default: 35)
               Higher clues = easier puzzle; lower clues = harder puzzle
               Actual clues may be slightly less if removing more cells
               would create multiple solutions.
               
    Returns:
        Tuple of (puzzle, solution) where:
        - puzzle: 9x9 board with some cells filled, rest empty (0)
        - solution: 9x9 completed board (the answer)
        
    Both are guaranteed to be valid Sudoku boards, and the puzzle
    is guaranteed to have exactly one unique solution.
    """
    board = create_empty_board()
    fill_board(board)
    solution = deep_copy(board)
    remove_cells(board, clues)
    puzzle = deep_copy(board)
    return puzzle, solution
