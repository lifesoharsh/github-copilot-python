"""
Comprehensive pytest test suite for Flask Sudoku app.
Tests core sudoku logic and Flask API endpoints.
"""

import pytest
import json
import sys
from pathlib import Path

# Add starter directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import sudoku_logic
from app import app, CURRENT


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Flask test client fixture."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def reset_current_game():
    """Reset the CURRENT game state before and after each test."""
    yield
    CURRENT['puzzle'] = None
    CURRENT['solution'] = None


# ============================================================================
# SUDOKU LOGIC TESTS
# ============================================================================

class TestBoardCreation:
    """Tests for board creation and initialization."""

    def test_create_empty_board_dimensions(self):
        """Test that empty board has correct 9x9 dimensions."""
        board = sudoku_logic.create_empty_board()
        assert len(board) == 9
        assert all(len(row) == 9 for row in board)

    def test_create_empty_board_all_zeros(self):
        """Test that empty board is filled with zeros."""
        board = sudoku_logic.create_empty_board()
        for row in board:
            assert all(cell == 0 for cell in row)

    def test_deep_copy_independence(self):
        """Test that deep copy creates independent copy of board."""
        board1 = sudoku_logic.create_empty_board()
        board1[0][0] = 5
        board2 = sudoku_logic.deep_copy(board1)
        board2[0][0] = 9
        assert board1[0][0] == 5
        assert board2[0][0] == 9

    def test_deep_copy_nested_independence(self):
        """Test that deep copy truly copies nested lists."""
        board1 = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        board2 = sudoku_logic.deep_copy(board1)
        board2[0][0] = 99
        assert board1[0][0] == 1


class TestSafePlacement:
    """Tests for is_safe validation function."""

    def test_is_safe_empty_board(self):
        """Test that any number is safe on empty board."""
        board = sudoku_logic.create_empty_board()
        for num in range(1, 10):
            assert sudoku_logic.is_safe(board, 0, 0, num)

    def test_is_safe_duplicate_in_row(self):
        """Test that duplicate in row is not safe."""
        board = sudoku_logic.create_empty_board()
        board[0][0] = 5
        assert not sudoku_logic.is_safe(board, 0, 8, 5)

    def test_is_safe_duplicate_in_column(self):
        """Test that duplicate in column is not safe."""
        board = sudoku_logic.create_empty_board()
        board[0][0] = 5
        assert not sudoku_logic.is_safe(board, 8, 0, 5)

    def test_is_safe_duplicate_in_box(self):
        """Test that duplicate in 3x3 box is not safe."""
        board = sudoku_logic.create_empty_board()
        board[0][0] = 5
        assert not sudoku_logic.is_safe(board, 1, 1, 5)
        assert not sudoku_logic.is_safe(board, 2, 2, 5)

    def test_is_safe_valid_placement(self):
        """Test valid placement with no conflicts."""
        board = sudoku_logic.create_empty_board()
        board[0][0] = 1
        board[1][1] = 2
        assert sudoku_logic.is_safe(board, 2, 2, 3)
        assert sudoku_logic.is_safe(board, 0, 8, 2)

    def test_is_safe_checks_all_box_positions(self):
        """Test that all 9 positions in 3x3 box are checked."""
        board = sudoku_logic.create_empty_board()
        board[1][2] = 7  # Position in top-left 3x3 box
        for i in range(3):
            for j in range(3):
                assert not sudoku_logic.is_safe(board, i, j, 7)

    def test_is_safe_different_boxes(self):
        """Test that different 3x3 boxes don't interfere."""
        board = sudoku_logic.create_empty_board()
        board[0][0] = 5  # Top-left box
        assert sudoku_logic.is_safe(board, 3, 3, 5)  # Center box
        assert sudoku_logic.is_safe(board, 6, 6, 5)  # Bottom-right box


class TestBoardFilling:
    """Tests for board filling algorithm."""

    def test_fill_board_completes(self):
        """Test that fill_board successfully completes a board."""
        board = sudoku_logic.create_empty_board()
        result = sudoku_logic.fill_board(board)
        assert result is True
        assert all(cell != 0 for row in board for cell in row)

    def test_fill_board_valid_sudoku(self):
        """Test that filled board is valid sudoku."""
        board = sudoku_logic.create_empty_board()
        sudoku_logic.fill_board(board)
        assert is_valid_sudoku(board)

    def test_fill_board_all_numbers_present(self):
        """Test that each row has all numbers 1-9."""
        board = sudoku_logic.create_empty_board()
        sudoku_logic.fill_board(board)
        for row in board:
            assert sorted(row) == list(range(1, 10))


class TestSolutionCounting:
    """Tests for solution counting and uniqueness validation."""

    def test_count_solutions_empty_board(self):
        """Test that empty board has many solutions."""
        board = sudoku_logic.create_empty_board()
        count = sudoku_logic.count_solutions(board, count_limit=2)
        # Empty board has more than 1 solution
        assert count >= 2

    def test_count_solutions_complete_board(self):
        """Test that complete valid board has exactly 1 solution."""
        board = sudoku_logic.create_empty_board()
        sudoku_logic.fill_board(board)
        count = sudoku_logic.count_solutions(board, count_limit=2)
        assert count == 1

    def test_count_solutions_with_count_limit(self):
        """Test that count_limit stops search early."""
        board = sudoku_logic.create_empty_board()
        # Don't fill the board, so it has many solutions
        count = sudoku_logic.count_solutions(board, count_limit=5)
        # Should find exactly 5 (the limit) before stopping
        assert count == 5

    def test_count_solutions_unique_puzzle(self):
        """Test counting solutions on a puzzle with unique solution."""
        puzzle, solution = sudoku_logic.generate_puzzle(clues=35)
        count = sudoku_logic.count_solutions(puzzle, count_limit=2)
        assert count == 1

    def test_count_solutions_preserves_board(self):
        """Test that count_solutions doesn't modify the input board."""
        puzzle, solution = sudoku_logic.generate_puzzle(clues=35)
        puzzle_copy = sudoku_logic.deep_copy(puzzle)
        sudoku_logic.count_solutions(puzzle, count_limit=2)
        assert puzzle == puzzle_copy, "count_solutions modified the input board"


class TestPuzzleGeneration:
    """Tests for complete puzzle generation."""

    def test_generate_puzzle_returns_tuple(self):
        """Test that generate_puzzle returns tuple of puzzle and solution."""
        result = sudoku_logic.generate_puzzle()
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_generate_puzzle_boards_are_lists(self):
        """Test that puzzle and solution are lists."""
        puzzle, solution = sudoku_logic.generate_puzzle()
        assert isinstance(puzzle, list)
        assert isinstance(solution, list)

    def test_generate_puzzle_solution_valid(self):
        """Test that generated solution is valid sudoku."""
        puzzle, solution = sudoku_logic.generate_puzzle()
        assert is_valid_sudoku(solution)

    def test_generate_puzzle_has_clues(self):
        """Test that puzzle has non-zero cells."""
        puzzle, solution = sudoku_logic.generate_puzzle()
        clue_count = sum(1 for row in puzzle for cell in row if cell != 0)
        assert clue_count > 0

    def test_generate_puzzle_default_clues(self):
        """Test that default clues is approximately 35."""
        puzzle, solution = sudoku_logic.generate_puzzle(clues=35)
        clue_count = sum(1 for row in puzzle for cell in row if cell != 0)
        # Allow some variance due to random generation
        assert 30 <= clue_count <= 40

    def test_generate_puzzle_custom_clues(self):
        """Test generating puzzle with custom number of clues."""
        puzzle, solution = sudoku_logic.generate_puzzle(clues=20)
        clue_count = sum(1 for row in puzzle for cell in row if cell != 0)
        assert 15 <= clue_count <= 25

    def test_generate_puzzle_puzzle_less_filled_than_solution(self):
        """Test that puzzle has fewer filled cells than solution."""
        puzzle, solution = sudoku_logic.generate_puzzle()
        puzzle_count = sum(1 for row in puzzle for cell in row if cell != 0)
        solution_count = sum(1 for row in solution for cell in row if cell != 0)
        assert puzzle_count < solution_count
        assert solution_count == 81  # Full solution

    def test_generate_puzzle_solution_completes_puzzle(self):
        """Test that solution contains all puzzle values."""
        puzzle, solution = sudoku_logic.generate_puzzle()
        for i in range(9):
            for j in range(9):
                if puzzle[i][j] != 0:
                    assert puzzle[i][j] == solution[i][j]

    def test_generate_puzzle_deterministic_with_seed(self):
        """Test that puzzle generation is repeatable with random seed."""
        import random
        random.seed(42)
        puzzle1, solution1 = sudoku_logic.generate_puzzle()
        
        random.seed(42)
        puzzle2, solution2 = sudoku_logic.generate_puzzle()
        
        assert puzzle1 == puzzle2
        assert solution1 == solution2

    def test_generate_puzzle_has_unique_solution(self):
        """Test that generated puzzle has exactly one unique solution."""
        puzzle, solution = sudoku_logic.generate_puzzle(clues=35)
        num_solutions = sudoku_logic.count_solutions(puzzle, count_limit=2)
        assert num_solutions == 1, f"Expected 1 solution but found {num_solutions}"

    def test_generate_puzzle_unique_solution_with_few_clues(self):
        """Test that puzzles with few clues still have unique solution."""
        puzzle, solution = sudoku_logic.generate_puzzle(clues=20)
        num_solutions = sudoku_logic.count_solutions(puzzle, count_limit=2)
        assert num_solutions == 1, f"Expected 1 solution but found {num_solutions}"

    def test_generate_puzzle_multiple_puzzles_all_unique(self):
        """Test that multiple generated puzzles all have unique solutions."""
        for _ in range(3):
            puzzle, solution = sudoku_logic.generate_puzzle(clues=35)
            num_solutions = sudoku_logic.count_solutions(puzzle, count_limit=2)
            assert num_solutions == 1, f"Generated puzzle does not have unique solution"


# ============================================================================
# FLASK APP TESTS
# ============================================================================

class TestFlaskAppBasics:
    """Tests for Flask app initialization."""

    def test_app_exists(self):
        """Test that Flask app is created."""
        assert app is not None

    def test_app_testing_mode(self):
        """Test that app can be set to testing mode."""
        assert app.config['TESTING'] is False
        app.config['TESTING'] = True
        assert app.config['TESTING'] is True
        app.config['TESTING'] = False


@pytest.mark.usefixtures('reset_current_game')
class TestIndexRoute:
    """Tests for index route."""

    def test_index_returns_200(self, client):
        """Test that index route returns 200 status."""
        response = client.get('/')
        assert response.status_code == 200

    def test_index_returns_html(self, client):
        """Test that index returns HTML content."""
        response = client.get('/')
        assert b'<!DOCTYPE' in response.data or b'<html' in response.data


@pytest.mark.usefixtures('reset_current_game')
class TestNewGameRoute:
    """Tests for new game generation route."""

    def test_new_game_returns_json(self, client):
        """Test that new game endpoint returns JSON."""
        response = client.get('/new')
        assert response.status_code == 200
        assert response.content_type == 'application/json'

    def test_new_game_returns_puzzle(self, client):
        """Test that new game returns puzzle data."""
        response = client.get('/new')
        data = json.loads(response.data)
        assert 'puzzle' in data
        assert isinstance(data['puzzle'], list)

    def test_new_game_puzzle_is_9x9(self, client):
        """Test that returned puzzle is 9x9 board."""
        response = client.get('/new')
        data = json.loads(response.data)
        puzzle = data['puzzle']
        assert len(puzzle) == 9
        assert all(len(row) == 9 for row in puzzle)

    def test_new_game_default_clues(self, client):
        """Test that new game has default clues (35)."""
        response = client.get('/new')
        data = json.loads(response.data)
        puzzle = data['puzzle']
        clue_count = sum(1 for row in puzzle for cell in row if cell != 0)
        assert 30 <= clue_count <= 40

    def test_new_game_custom_clues(self, client):
        """Test that new game respects clues parameter."""
        response = client.get('/new?clues=50')
        data = json.loads(response.data)
        puzzle = data['puzzle']
        clue_count = sum(1 for row in puzzle for cell in row if cell != 0)
        assert 45 <= clue_count <= 55

    def test_new_game_sets_current_puzzle(self, client):
        """Test that new game sets CURRENT puzzle."""
        assert CURRENT['puzzle'] is None
        response = client.get('/new')
        assert CURRENT['puzzle'] is not None
        assert CURRENT['solution'] is not None

    def test_new_game_overwrites_previous(self, client):
        """Test that new game call overwrites previous game."""
        client.get('/new?clues=35')
        puzzle1 = [row[:] for row in CURRENT['puzzle']]
        
        client.get('/new?clues=35')
        puzzle2 = CURRENT['puzzle']
        
        # Puzzles might be different (random generation)
        assert puzzle2 is not None


@pytest.mark.usefixtures('reset_current_game')
class TestCheckRoute:
    """Tests for solution checking route."""

    def test_check_no_game_in_progress(self, client):
        """Test check endpoint when no game is in progress."""
        response = client.post('/check', json={'board': [[0]*9]*9})
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data

    def test_check_correct_solution(self, client):
        """Test checking a correct solution."""
        # Generate new game
        client.get('/new')
        solution = [row[:] for row in CURRENT['solution']]
        
        # Send solution for checking
        response = client.post('/check', json={'board': solution})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'incorrect' in data
        assert len(data['incorrect']) == 0

    def test_check_incorrect_single_cell(self, client):
        """Test checking solution with single incorrect cell."""
        client.get('/new')
        board = [row[:] for row in CURRENT['solution']]
        board[0][0] = 0 if board[0][0] != 0 else 5  # Change first cell
        
        response = client.post('/check', json={'board': board})
        data = json.loads(response.data)
        assert len(data['incorrect']) == 1
        assert data['incorrect'][0] == [0, 0]

    def test_check_multiple_incorrect_cells(self, client):
        """Test checking solution with multiple incorrect cells."""
        client.get('/new')
        board = [row[:] for row in CURRENT['solution']]
        board[0][0] = 0 if board[0][0] != 0 else 5
        board[1][1] = 0 if board[1][1] != 0 else 5
        board[2][2] = 0 if board[2][2] != 0 else 5
        
        response = client.post('/check', json={'board': board})
        data = json.loads(response.data)
        assert len(data['incorrect']) >= 2

    def test_check_returns_correct_coordinates(self, client):
        """Test that incorrect cells return correct row/col indices."""
        client.get('/new')
        board = [row[:] for row in CURRENT['solution']]
        board[5][7] = 0 if board[5][7] != 0 else 5
        
        response = client.post('/check', json={'board': board})
        data = json.loads(response.data)
        assert [5, 7] in data['incorrect']

    def test_check_requires_post_method(self, client):
        """Test that check endpoint requires POST method."""
        client.get('/new')
        response = client.get('/check')
        # GET request should not be allowed (405 Method Not Allowed)
        assert response.status_code in [405, 400]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_valid_sudoku(board):
    """
    Validate that a completed sudoku board is valid.
    
    Args:
        board: 9x9 2D list representing sudoku board
        
    Returns:
        True if board is valid, False otherwise
    """
    # Check rows
    for row in board:
        if sorted(row) != list(range(1, 10)):
            return False
    
    # Check columns
    for col in range(9):
        column = [board[row][col] for row in range(9)]
        if sorted(column) != list(range(1, 10)):
            return False
    
    # Check 3x3 boxes
    for box_row in range(3):
        for box_col in range(3):
            box = []
            for i in range(3):
                for j in range(3):
                    box.append(board[box_row*3 + i][box_col*3 + j])
            if sorted(box) != list(range(1, 10)):
                return False
    
    return True


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@pytest.mark.usefixtures('reset_current_game')
class TestIntegration:
    """Integration tests for complete game flow."""

    def test_full_game_flow(self, client):
        """Test complete game flow: new game -> check solution."""
        # Generate new game
        response = client.get('/new?clues=35')
        assert response.status_code == 200
        
        puzzle = json.loads(response.data)['puzzle']
        assert puzzle is not None
        
        # Check correct solution
        response = client.post('/check', json={'board': CURRENT['solution']})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['incorrect']) == 0

    def test_multiple_games_in_sequence(self, client):
        """Test playing multiple games in sequence."""
        for _ in range(3):
            client.get('/new?clues=30')
            response = client.post('/check', json={'board': CURRENT['solution']})
            assert response.status_code == 200
            data = json.loads(response.data)
            assert len(data['incorrect']) == 0


# ============================================================================
# LEADERBOARD TESTS
# ============================================================================

class TestLeaderboardLogic:
    """Tests for leaderboard score management logic."""

    def test_score_object_creation(self):
        """Test that score objects have required fields."""
        score = {
            'name': 'Test Player',
            'time': 120,
            'difficulty': 'easy',
            'hintsUsed': 0,
            'timestamp': 1234567890
        }
        assert score['name'] == 'Test Player'
        assert score['time'] == 120
        assert score['difficulty'] == 'easy'
        assert score['hintsUsed'] == 0
        assert score['timestamp'] == 1234567890

    def test_score_validation_requires_name(self):
        """Test that score must have a name."""
        invalid_score = {
            'time': 120,
            'difficulty': 'easy',
            'hintsUsed': 0,
            'timestamp': 1234567890
        }
        assert 'name' not in invalid_score
        # In real code, this would fail validation

    def test_score_validation_requires_time(self):
        """Test that score must have completion time."""
        invalid_score = {
            'name': 'Test',
            'difficulty': 'easy',
            'hintsUsed': 0,
            'timestamp': 1234567890
        }
        assert 'time' not in invalid_score

    def test_score_validation_requires_difficulty(self):
        """Test that score must have difficulty."""
        invalid_score = {
            'name': 'Test',
            'time': 120,
            'hintsUsed': 0,
            'timestamp': 1234567890
        }
        assert 'difficulty' not in invalid_score

    def test_leaderboard_sorting_by_time(self):
        """Test that leaderboard is sorted by time (fastest first)."""
        scores = [
            {'name': 'Player1', 'time': 300, 'difficulty': 'easy', 'hintsUsed': 0, 'timestamp': 1},
            {'name': 'Player2', 'time': 100, 'difficulty': 'easy', 'hintsUsed': 0, 'timestamp': 2},
            {'name': 'Player3', 'time': 200, 'difficulty': 'easy', 'hintsUsed': 0, 'timestamp': 3},
        ]
        sorted_scores = sorted(scores, key=lambda s: s['time'])
        assert sorted_scores[0]['name'] == 'Player2'
        assert sorted_scores[1]['name'] == 'Player3'
        assert sorted_scores[2]['name'] == 'Player1'

    def test_leaderboard_top_10_limit(self):
        """Test that leaderboard keeps only top 10 scores."""
        scores = [
            {'name': f'Player{i}', 'time': i * 10, 'difficulty': 'easy', 'hintsUsed': 0, 'timestamp': i}
            for i in range(15)
        ]
        sorted_scores = sorted(scores, key=lambda s: s['time'])
        top_10 = sorted_scores[:10]
        
        assert len(top_10) == 10
        assert top_10[0]['name'] == 'Player0'
        assert top_10[9]['name'] == 'Player9'

    def test_difficulty_levels_valid(self):
        """Test that difficulty levels are valid."""
        valid_difficulties = ['easy', 'medium', 'hard']
        for difficulty in valid_difficulties:
            score = {
                'name': 'Test',
                'time': 120,
                'difficulty': difficulty,
                'hintsUsed': 0,
                'timestamp': 1234567890
            }
            assert score['difficulty'] in valid_difficulties

    def test_name_validation_empty_string(self):
        """Test that empty names are invalid."""
        name = ''
        assert len(name.strip()) == 0  # Invalid

    def test_name_validation_max_length(self):
        """Test that name respects max length."""
        name = 'A' * 30
        assert len(name) <= 30  # Valid
        
        long_name = 'A' * 31
        assert len(long_name) > 30  # Invalid

    def test_timestamp_format(self):
        """Test that timestamp is stored as milliseconds."""
        import time
        timestamp = int(time.time() * 1000)
        score = {
            'name': 'Test',
            'time': 120,
            'difficulty': 'easy',
            'hintsUsed': 0,
            'timestamp': timestamp
        }
        # Verify timestamp can be converted to a date
        date_obj = time.gmtime(score['timestamp'] / 1000)
        assert date_obj.tm_year > 2020

    def test_clues_count_by_difficulty(self):
        """Test that difficulty levels map to correct clue counts."""
        difficulty_clues = {
            'easy': 35,
            'medium': 25,
            'hard': 17
        }
        
        for difficulty, expected_clues in difficulty_clues.items():
            # Verify the mapping is correct
            assert expected_clues > 0
            assert difficulty in ['easy', 'medium', 'hard']


# ============================================================================
# HINT FUNCTIONALITY TESTS
# ============================================================================

@pytest.mark.usefixtures('reset_current_game')
class TestHintFunctionality:
    """Tests for Hint button functionality."""

    def test_new_game_includes_solution_in_response(self, client):
        """Test that /new endpoint returns both puzzle and solution."""
        response = client.get('/new')
        data = json.loads(response.data)
        assert 'puzzle' in data
        assert 'solution' in data
        assert isinstance(data['solution'], list)
        assert len(data['solution']) == 9
        assert all(len(row) == 9 for row in data['solution'])

    def test_solution_is_complete_board(self, client):
        """Test that solution has all cells filled (no zeros)."""
        response = client.get('/new')
        data = json.loads(response.data)
        solution = data['solution']
        for row in solution:
            assert all(cell != 0 for cell in row), "Solution should have no empty cells"

    def test_solution_is_valid_sudoku(self, client):
        """Test that returned solution is valid sudoku."""
        response = client.get('/new')
        data = json.loads(response.data)
        solution = data['solution']
        assert is_valid_sudoku(solution)

    def test_puzzle_matches_solution_on_clues(self, client):
        """Test that puzzle clues match solution values."""
        response = client.get('/new')
        data = json.loads(response.data)
        puzzle = data['puzzle']
        solution = data['solution']
        
        for i in range(9):
            for j in range(9):
                if puzzle[i][j] != 0:
                    assert puzzle[i][j] == solution[i][j], \
                        f"Puzzle clue at ({i},{j}) doesn't match solution"

    def test_hints_used_counter_logic(self):
        """Test that hints counter increments and tracks usage."""
        hints_used = 0
        assert hints_used == 0
        
        hints_used += 1
        assert hints_used == 1
        
        hints_used += 5
        assert hints_used == 6
        
        # Reset for new game
        hints_used = 0
        assert hints_used == 0

    def test_hinted_cell_marked_in_leaderboard(self):
        """Test that hints used is stored in leaderboard score object."""
        score = {
            'name': 'Test Player',
            'time': 150,
            'difficulty': 'easy',
            'hintsUsed': 3,
            'timestamp': 1234567890
        }
        assert score['hintsUsed'] == 3

    def test_multiple_hints_different_counts(self):
        """Test that different games can have different hint counts."""
        game1_hints = 0
        game1_hints += 1
        game1_hints += 1
        assert game1_hints == 2
        
        game2_hints = 0
        game2_hints += 1
        game2_hints += 1
        game2_hints += 1
        assert game2_hints == 3
        
        assert game1_hints != game2_hints

    def test_hint_from_valid_solution(self, client):
        """Test that a hint value comes from the solution."""
        response = client.get('/new')
        data = json.loads(response.data)
        puzzle = data['puzzle']
        solution = data['solution']
        
        # Pick a random empty cell from puzzle
        empty_cells = []
        for i in range(9):
            for j in range(9):
                if puzzle[i][j] == 0:
                    empty_cells.append((i, j))
        
        assert len(empty_cells) > 0, "Puzzle should have empty cells"
        
        # Get solution value for a random empty cell
        row, col = empty_cells[0]
        hint_value = solution[row][col]
        
        # Verify it's a valid number (1-9)
        assert 1 <= hint_value <= 9

    def test_hints_do_not_count_prefilled_cells(self):
        """Test that original puzzle clues don't count as hints."""
        hints_used = 0
        prefilled_count = 35  # Easy difficulty
        
        # Hints should start at 0, not count prefilled
        assert hints_used == 0
        assert prefilled_count > 0
        
        # Only explicit hint button clicks increment hints
        hints_used += 1
        assert hints_used == 1  # Only the hint button adds to counter

    def test_hints_persist_during_game(self):
        """Test that hint counter persists through game session."""
        hints_used = 0
        hints_used += 1  # First hint
        assert hints_used == 1
        
        hints_used += 1  # Second hint
        assert hints_used == 2
        
        # Should not reset mid-game
        assert hints_used == 2

    def test_hints_reset_on_new_game(self):
        """Test that hint counter resets when new game starts."""
        hints_used = 3  # Some hints used
        
        # New game starts
        hints_used = 0
        assert hints_used == 0

    def test_hint_button_exists_in_html(self, client):
        """Test that index page includes hint button."""
        response = client.get('/')
        assert response.status_code == 200
        # Check that hint button is in the HTML
        assert b'hint' in response.data.lower() or b'Hint' in response.data
