import cmd
import copy
import dataclasses
import enum
import operator
import sys


# Pieces. Not using an Enum to save typing.
X = 'X'
O = 'O'
E = ' '  # Empty


# Scores. Not using an Enum to implement minmax easily.
class Score:
  X_WIN = 1
  O_WIN = -1
  DRAW = 0
  NON_TERMINAL = None


@dataclasses.dataclass
class Board:
  state: list[list[str]]
  score: int = 0


@dataclasses.dataclass
class Move:
  row: int
  column: int
  piece: str


@dataclasses.dataclass
class BoardWithMove:
  board: Board
  move: Move


def is_board_full(board: Board) -> bool:
  return not (
      board.state[0][0] == E
      or board.state[0][1] == E
      or board.state[0][2] == E
      or board.state[1][0] == E
      or board.state[1][1] == E
      or board.state[1][2] == E
      or board.state[2][0] == E
      or board.state[2][1] == E
      or board.state[2][2] == E
  )


def evaluate(board: Board) -> int | None:
  indices_to_check = [
      # Three rows.
      ((0, 0), (0, 1), (0, 2)),
      ((1, 0), (1, 1), (1, 2)),
      ((2, 0), (2, 1), (2, 2)),
      # Three columns.
      ((0, 0), (1, 0), (2, 0)),
      ((0, 1), (1, 1), (2, 1)),
      ((0, 2), (1, 2), (2, 2)),
      # Diagnal.
      ((0, 0), (1, 1), (2, 2)),
      ((0, 2), (1, 1), (2, 0)),
  ]

  for indices in indices_to_check:
    if (
        board.state[indices[0][0]][indices[0][1]]
        == board.state[indices[1][0]][indices[1][1]]
        and board.state[indices[0][0]][indices[0][1]]
        == board.state[indices[2][0]][indices[2][1]]
    ):
      if board.state[indices[0][0]][indices[0][1]] == X:
        return Score.X_WIN
      elif board.state[indices[0][0]][indices[0][1]] == O:
        return Score.O_WIN

  if is_board_full(board):
    return Score.DRAW
  else:
    return Score.NON_TERMINAL


def generate_all_possible_next_boards_with_move(
    board: Board, side_piece: str
) -> list[BoardWithMove]:
  next_boards_with_move = []
  for i in range(3):
    for j in range(3):
      if board.state[i][j] == E:
        new_board = Board(state=copy.deepcopy(board.state))
        new_board.state[i][j] = side_piece
        move = Move(row=i, column=j, piece=side_piece)
        next_boards_with_move.append(BoardWithMove(board=new_board, move=move))

  return next_boards_with_move


def pick_best_move(next_boards_with_move, comparator) -> tuple[int, Move]:
  # TODO: Randomize the pick the move with the same score to make the game more
  # interesting.
  first_next = next_boards_with_move[0]
  backup_score = first_next.board.score
  move = first_next.move
  for board_with_move in next_boards_with_move[1:]:
    if comparator(board_with_move.board.score, backup_score):
      backup_score = board_with_move.board.score
      move = board_with_move.move

  return (backup_score, move)


# Standard minmax algorithm.
# X tries to achieve high score, O tries to achieve low score.
def generate_move(board: Board, side_piece: str) -> tuple[Move, int]:
  assert evaluate(board) == Score.NON_TERMINAL
  assert side_piece == X or side_piece == O

  next_boards_with_move = generate_all_possible_next_boards_with_move(
      board, side_piece
  )

  for board_with_move in next_boards_with_move:
    result = evaluate(board_with_move.board)
    if result == Score.X_WIN:
      board_with_move.board.score = Score.X_WIN
    elif result == Score.O_WIN:
      board_with_move.board.score = Score.O_WIN
    elif result == Score.DRAW:
      board_with_move.board.score = Score.DRAW
    else:  # NON_TERMINAL
      # Populate the score for the next board by calling this function
      # recursively. Returned 'move' is discarded.
      if side_piece == X:
        move, score = generate_move(board_with_move.board, O)
        board_with_move.board.score = score
      else:
        move, score = generate_move(board_with_move.board, X)
        board_with_move.board.score = score

  if side_piece == X:
    board.score, move = pick_best_move(next_boards_with_move, operator.gt)
  else:  # O
    board.score, move = pick_best_move(next_boards_with_move, operator.lt)

  return move, board.score


class TicTacToeShell(cmd.Cmd):

  def __init__(self):
    super().__init__()

    self.board = Board(
        state=[
            [E, E, E],
            [E, E, E],
            [E, E, E],
        ],
    )

    # X always goes first, O follows.
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] == 'human'):
      self.human_piece = X
      self.computer_piece = O
    elif len(sys.argv) == 2 and sys.argv[1] == 'computer':
      self.human_piece = O
      self.computer_piece = X
      move, score = generate_move(self.board, self.computer_piece)
      self.board.state[move.row][move.column] = move.piece
      print("\n\nComputer's move:", move.row, move.column)
    else:
      print('Invalid command line.')
      sys.exit(1)

    self.print_board()
    self.prompt_for_move()

  def do_quit(self, arg):
    """Quit the game."""
    return True

  def do_EOF(self, arg):
    """Quit the game."""
    return True

  def do_print(self, arg):
    """Print the board."""
    self.print_board()

  def prompt_for_move(self):
    print(
        'It is your turn to move. Please input a pair of numbers for row and'
        ' column.\n'
    )

  def default(self, arg):
    """Human plays one move."""
    num1, num2 = tuple(map(int, arg.split()))
    if not (num1 == 0 or num1 == 1 or num1 == 2):
      print('Invalid input, num1 must be 0, 1 or 2')
      return
    if not (num2 == 0 or num2 == 1 or num2 == 2):
      print('Invalid input, num2 must be 0, 1 or 2')
      return

    move = Move(row=num1, column=num2, piece=self.human_piece)
    if self.board.state[move.row][move.column] != E:
      print('Invalid input, space is not empty.')
      return

    self.board.state[move.row][move.column] = move.piece
    self.print_board()

    result = evaluate(self.board)
    if result == Score.X_WIN:
      print('X win!')
      return True
    elif result == Score.O_WIN:
      print('O win!')
      return True
    elif result == Score.DRAW:
      print('Draw!')
      return True

    # Computer move.
    move, score = generate_move(self.board, self.computer_piece)
    self.board.state[move.row][move.column] = move.piece
    print("\nComputer's move:", move.row, move.column)
    self.print_board()

    result = evaluate(self.board)
    if result == Score.X_WIN:
      print('X win!')
      return True
    elif result == Score.O_WIN:
      print('O win!')
      return True
    elif result == Score.DRAW:
      print('Draw!')
      return True

    self.prompt_for_move()

  def print_board(self):
    print(self.board.state[0])
    print(self.board.state[1])
    print(self.board.state[2])
    print('Human:', self.human_piece)
    print('Computer:', self.computer_piece)


if __name__ == '__main__':
  print(
      'Welcome to Tic Tac Toe shell. Type two numbers separated by space to'
      ' specify the move. Type help or ? to list commands.\n'
  )
  TicTacToeShell().cmdloop()
