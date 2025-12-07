from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import chess
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Move(BaseModel):
    uci: str
    promotion: str | None = None

class Game:
    def __init__(self):
        self.board = chess.Board()
        self.history = [self.board.fen()]
        self.captured = {"white": [], "black": []}
        self.ended = False
        self.result = None

    def board_array(self):
        arr = []
        for r in range(8):
            row = []
            for c in range(8):
                sq = chess.square(c, 7 - r)
                p = self.board.piece_at(sq)
                if p:
                    row.append({"type": p.symbol().lower(), "color": "white" if p.color else "black"})
                else:
                    row.append(None)
            arr.append(row)
        return arr

    def push_move(self, uci, promotion):
        move = chess.Move.from_uci(uci)
        if promotion:
            move.promotion = {
                "q": chess.QUEEN,
                "r": chess.ROOK,
                "b": chess.BISHOP,
                "n": chess.KNIGHT
            }[promotion]
        if move not in self.board.legal_moves:
            raise ValueError("Illegal move")
        if self.board.is_capture(move):
            captured = self.board.piece_at(move.to_square)
            if captured:
                self.captured["white" if captured.color else "black"].append(captured.symbol())
        self.board.push(move)
        self.history.append(self.board.fen())
        self.check_end()

    def check_end(self):
        if self.board.is_checkmate():
            loser = "white" if self.board.turn else "black"
            winner = "black" if loser == "white" else "white"
            self.ended = True
            self.result = {"winner": winner, "loser": loser, "reason": "checkmate"}
            return
        if self.board.is_stalemate():
            loser = "white" if self.board.turn else "black"
            winner = "black" if loser == "white" else "white"
            self.ended = True
            self.result = {"winner": winner, "loser": loser, "reason": "stalemate"}
            return

GAME = Game()

@app.get("/state")
def get_state():
    return {
        "board": GAME.board_array(),
        "currentPlayer": "white" if GAME.board.turn else "black",
        "captured": GAME.captured,
        "ended": GAME.ended,
        "result": GAME.result,
        "fen": GAME.board.fen(),
    }

@app.get("/legal_moves")
def legal_moves(from_sq: str):
    try:
        sq = chess.parse_square(from_sq)
    except:
        return []
    return [m.uci() for m in GAME.board.legal_moves if m.from_square == sq]

@app.post("/move")
def move(m: Move):
    try:
        GAME.push_move(m.uci, m.promotion)
    except Exception as e:
        raise HTTPException(400, str(e))
    return get_state()

@app.post("/ai_move")
def ai_move():
    if GAME.ended:
        return get_state()
    moves = list(GAME.board.legal_moves)
    if not moves:
        GAME.check_end()
        return get_state()
    move = random.choice(moves)
    GAME.push_move(move.uci(), None)
    return get_state()

@app.post("/reset")
def reset():
    global GAME
    GAME = Game()
    return get_state()
