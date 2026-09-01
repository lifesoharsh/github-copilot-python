// Client-side rendering and interaction for the Flask-backed Sudoku
const SIZE = 9;
const LEADERBOARD_KEY = 'sudokuLeaderboard';
const DARK_MODE_KEY = 'sudokuDarkMode';
const MAX_SCORES = 10;

// Difficulty configuration: difficulty -> clues count
const DIFFICULTY_CONFIG = {
  easy: 35,
  medium: 25,
  hard: 17
};

let puzzle = [];
let solution = [];
let currentDifficulty = 'easy';
let gameStartTime = null;
let timerInterval = null;
let hintsUsed = 0;
let darkModeEnabled = false;

// ============================================================================
// LEADERBOARD FUNCTIONS
// ============================================================================

/**
 * Load the leaderboard from localStorage.
 * Returns an array of score objects, sorted by time (best first).
 */
function loadLeaderboard() {
  try {
    const data = localStorage.getItem(LEADERBOARD_KEY);
    if (!data) return [];
    const scores = JSON.parse(data);
    // Ensure it's an array and has valid objects
    if (!Array.isArray(scores)) return [];
    return scores.filter(s => s.name && s.time !== undefined && s.difficulty && s.timestamp);
  } catch (e) {
    console.error('Error loading leaderboard:', e);
    return [];
  }
}

/**
 * Save the leaderboard to localStorage.
 */
function saveLeaderboard(scores) {
  try {
    localStorage.setItem(LEADERBOARD_KEY, JSON.stringify(scores));
  } catch (e) {
    console.error('Error saving leaderboard:', e);
  }
}

/**
 * Add a new score to the leaderboard and keep only top 10.
 * Score object format: {name, time, difficulty, hintsUsed, timestamp}
 */
function addScoreToLeaderboard(score) {
  if (!score.name || score.time === undefined || !score.difficulty) {
    console.error('Invalid score object:', score);
    return;
  }
  
  let scores = loadLeaderboard();
  scores.push(score);
  
  // Sort by time (ascending - lower is better)
  scores.sort((a, b) => a.time - b.time);
  
  // Keep only top 10
  scores = scores.slice(0, MAX_SCORES);
  
  saveLeaderboard(scores);
}

/**
 * Get the top 10 scores from localStorage.
 */
function getTop10Scores() {
  return loadLeaderboard().slice(0, MAX_SCORES);
}

/**
 * Display the leaderboard in the UI.
 */
function displayLeaderboard() {
  const scores = getTop10Scores();
  const tbody = document.getElementById('leaderboard-body');
  
  if (scores.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5">No scores yet. Complete a puzzle to appear here!</td></tr>';
    return;
  }
  
  tbody.innerHTML = scores.map((score, index) => {
    const date = new Date(score.timestamp).toLocaleDateString();
    const timeStr = formatTime(score.time);
    return `
      <tr>
        <td>${index + 1}</td>
        <td>${escapeHtml(score.name)}</td>
        <td>${timeStr}</td>
        <td>${score.difficulty}</td>
        <td>${date}</td>
      </tr>
    `;
  }).join('');
}

/**
 * Escape HTML to prevent XSS.
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

// ============================================================================
// TIMER FUNCTIONS
// ============================================================================

/**
 * Start the game timer.
 */
function startTimer() {
  gameStartTime = Date.now();
  timerInterval = setInterval(() => {
    if (gameStartTime) {
      const elapsed = Math.floor((Date.now() - gameStartTime) / 1000);
      document.getElementById('timer').innerText = formatTime(elapsed);
    }
  }, 1000);
}

/**
 * Stop the game timer and return elapsed time in seconds.
 */
function stopTimer() {
  clearInterval(timerInterval);
  timerInterval = null;
  if (gameStartTime) {
    return Math.floor((Date.now() - gameStartTime) / 1000);
  }
  return 0;
}

/**
 * Format time in seconds to MM:SS format.
 */
function formatTime(seconds) {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Reset the timer display.
 */
function resetTimer() {
  document.getElementById('timer').innerText = '0:00';
  gameStartTime = null;
}

// ============================================================================
// DIFFICULTY FUNCTIONS
// ============================================================================

/**
 * Set the currently selected difficulty.
 */
function setDifficulty(difficulty) {
  if (!DIFFICULTY_CONFIG[difficulty]) {
    console.error('Invalid difficulty:', difficulty);
    return;
  }
  
  currentDifficulty = difficulty;
  
  // Update button states and aria-pressed attributes
  document.querySelectorAll('.difficulty-btn').forEach(btn => {
    const isActive = btn.dataset.difficulty === difficulty;
    btn.classList.toggle('active', isActive);
    btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
  });
}

/**
 * Get the clues count for the current difficulty.
 */
function getCluesForDifficulty() {
  return DIFFICULTY_CONFIG[currentDifficulty];
}

// ============================================================================
// BOARD FUNCTIONS
// ============================================================================

function createBoardElement() {
  const boardDiv = document.getElementById('sudoku-board');
  boardDiv.innerHTML = '';
  for (let i = 0; i < SIZE; i++) {
    const rowDiv = document.createElement('div');
    rowDiv.className = 'sudoku-row';
    for (let j = 0; j < SIZE; j++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.maxLength = 1;
      
      // Calculate which 3x3 subgrid this cell belongs to
      const boxRow = Math.floor(i / 3);
      const boxCol = Math.floor(j / 3);
      const boxNum = boxRow * 3 + boxCol;
      const isOddBox = boxNum % 2 === 0; // Boxes 0, 2, 4, 6, 8 are odd
      
      input.className = 'sudoku-cell' + (isOddBox ? ' box-odd' : ' box-even');
      input.dataset.row = i;
      input.dataset.col = j;
      input.addEventListener('input', (e) => {
        const val = e.target.value.replace(/[^1-9]/g, '');
        e.target.value = val;
      });
      rowDiv.appendChild(input);
    }
    boardDiv.appendChild(rowDiv);
  }
}

function renderPuzzle(puz) {
  puzzle = puz;
  createBoardElement();
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  for (let i = 0; i < SIZE; i++) {
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = puzzle[i][j];
      const inp = inputs[idx];
      if (val !== 0) {
        inp.value = val;
        inp.disabled = true;
        inp.className += ' prefilled';
      } else {
        inp.value = '';
        inp.disabled = false;
      }
    }
  }
}

async function newGame() {
  stopTimer();
  resetTimer();
  hintsUsed = 0;
  
  const clues = getCluesForDifficulty();
  const res = await fetch(`/new?clues=${clues}`);
  const data = await res.json();
  puzzle = data.puzzle;
  solution = data.solution;
  renderPuzzle(puzzle);
  document.getElementById('message').innerText = '';
  startTimer();
}

function getHint() {
  /**
   * Fill one empty cell with the correct value from the solution.
   * The cell becomes locked so the player cannot modify it.
   * Increments the hint counter.
   */
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  
  // Find all empty, non-prefilled, non-hinted cells
  const emptyCells = [];
  for (let i = 0; i < SIZE; i++) {
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const inp = inputs[idx];
      // Cell is empty if it has no value and is not disabled (prefilled or hinted)
      if (inp.value === '' && !inp.disabled) {
        emptyCells.push({ row: i, col: j, input: inp });
      }
    }
  }
  
  if (emptyCells.length === 0) {
    document.getElementById('message').innerText = 'No more hints available!';
    document.getElementById('message').style.color = '#ff9800';
    return;
  }
  
  // Choose a random empty cell
  const cell = emptyCells[Math.floor(Math.random() * emptyCells.length)];
  const correctValue = solution[cell.row][cell.col];
  
  // Fill the cell with the correct value
  cell.input.value = correctValue;
  
  // Lock the cell
  cell.input.disabled = true;
  cell.input.classList.add('hinted');
  
  // Increment hint counter
  hintsUsed++;
  
  // Show feedback
  document.getElementById('message').innerText = `Hint used (${hintsUsed})`;
  document.getElementById('message').style.color = '#1976d2';
}

// ============================================================================
// DARK MODE FUNCTIONS
// ============================================================================

/**
 * Load dark mode preference from localStorage.
 */
function loadDarkModePreference() {
  try {
    const stored = localStorage.getItem(DARK_MODE_KEY);
    return stored === 'true';
  } catch (e) {
    console.error('Error loading dark mode preference:', e);
    return false;
  }
}

/**
 * Save dark mode preference to localStorage.
 */
function saveDarkModePreference(enabled) {
  try {
    localStorage.setItem(DARK_MODE_KEY, enabled ? 'true' : 'false');
  } catch (e) {
    console.error('Error saving dark mode preference:', e);
  }
}

/**
 * Apply or remove dark mode from the page.
 */
function applyDarkMode(enabled) {
  darkModeEnabled = enabled;
  const body = document.body;
  if (enabled) {
    body.classList.add('dark-mode');
  } else {
    body.classList.remove('dark-mode');
  }
  saveDarkModePreference(enabled);
}

/**
 * Toggle dark mode on/off.
 */
function toggleDarkMode() {
  applyDarkMode(!darkModeEnabled);
}

async function checkSolution() {
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  const board = [];
  for (let i = 0; i < SIZE; i++) {
    board[i] = [];
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = inputs[idx].value;
      board[i][j] = val ? parseInt(val, 10) : 0;
    }
  }
  const res = await fetch('/check', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({board})
  });
  const data = await res.json();
  const msg = document.getElementById('message');
  if (data.error) {
    msg.style.color = '#d32f2f';
    msg.innerText = data.error;
    return;
  }
  const incorrect = new Set(data.incorrect.map(x => x[0]*SIZE + x[1]));
  for (let idx = 0; idx < inputs.length; idx++) {
    const inp = inputs[idx];
    if (inp.disabled) continue;
    inp.className = 'sudoku-cell';
    if (incorrect.has(idx)) {
      inp.className = 'sudoku-cell incorrect';
    }
  }
  if (incorrect.size === 0) {
    msg.style.color = '#388e3c';
    msg.innerText = 'Congratulations! You solved it!';
    handleGameWon();
  } else {
    msg.style.color = '#d32f2f';
    msg.innerText = 'Some cells are incorrect.';
  }
}

// ============================================================================
// GAME COMPLETION FUNCTIONS
// ============================================================================

/**
 * Handle game completion - show name input modal.
 */
function handleGameWon() {
  stopTimer();
  const modal = document.getElementById('name-modal');
  const nameInput = document.getElementById('player-name');
  nameInput.value = '';
  modal.classList.remove('hidden');
  // Set focus to name input for accessibility
  setTimeout(() => nameInput.focus(), 100);
}

/**
 * Save the completed game score to leaderboard.
 */
function saveGameScore() {
  const nameInput = document.getElementById('player-name');
  const name = nameInput.value.trim();
  
  if (!name) {
    alert('Please enter your name');
    return;
  }
  
  if (name.length > 30) {
    alert('Name must be 30 characters or less');
    return;
  }
  
  const elapsedTime = Math.floor((Date.now() - gameStartTime) / 1000);
  const score = {
    name: name,
    time: elapsedTime,
    difficulty: currentDifficulty,
    hintsUsed: hintsUsed,
    timestamp: Date.now()
  };
  
  addScoreToLeaderboard(score);
  displayLeaderboard();
  
  closeNameModal();
}

/**
 * Close the name input modal.
 */
function closeNameModal() {
  const modal = document.getElementById('name-modal');
  modal.classList.add('hidden');
}

// ============================================================================
// INITIALIZATION
// ============================================================================

window.addEventListener('load', () => {
  // Load and apply dark mode preference
  const isDarkMode = loadDarkModePreference();
  applyDarkMode(isDarkMode);
  
  // Wire dark mode toggle button
  document.getElementById('dark-mode-toggle').addEventListener('click', toggleDarkMode);
  
  // Wire difficulty buttons
  document.querySelectorAll('.difficulty-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      setDifficulty(e.target.dataset.difficulty);
    });
  });
  
  // Wire game buttons
  document.getElementById('new-game').addEventListener('click', newGame);
  document.getElementById('hint-btn').addEventListener('click', getHint);
  document.getElementById('check-solution').addEventListener('click', checkSolution);
  
  // Wire modal buttons
  document.getElementById('save-score-btn').addEventListener('click', saveGameScore);
  document.getElementById('cancel-score-btn').addEventListener('click', closeNameModal);
  
  // Wire Enter key in name input
  document.getElementById('player-name').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
      saveGameScore();
    }
  });
  
  // Wire Escape key to close modal
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      const modal = document.getElementById('name-modal');
      if (!modal.classList.contains('hidden')) {
        closeNameModal();
      }
    }
  });
  
  // Load and display leaderboard
  displayLeaderboard();
  
  // Initialize with default difficulty and load first game
  setDifficulty('easy');
  newGame();
});