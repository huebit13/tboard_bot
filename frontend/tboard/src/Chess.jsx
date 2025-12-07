import { useState, useEffect } from "react"

const API = "http://localhost:8000"

const Chess = () => {
  const [board, setBoard] = useState([])
  const [state, setState] = useState(null)
  const [promotion, setPromotion] = useState(null)
  const [pendingMove, setPendingMove] = useState(null)
  const [selected, setSelected] = useState(null)

  const loadState = async () => {
    const r = await fetch(API + "/state")
    const data = await r.json()
    setState(data)
    setBoard(data.board)
  }

  const algebraic = (r, c) => {
    const files = "abcdefgh"
    return files[c] + (8 - r)
  }

  const sendMove = async (uci, promotionPiece = null) => {
    await fetch(API + "/move", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ uci, promotion: promotionPiece }),
    })

    await loadState()

    if (!state?.ended) {
      await fetch(API + "/ai_move", { method: "POST" })
      await loadState()
    }
  }


  const tryMove = (from, to) => {
    if (!from || !to || from === to) return
    const fromRank = parseInt(from[1])
    const needsPromotion =
      (fromRank === 7 && to[1] === "8") || (fromRank === 2 && to[1] === "1")
    const uci = from + to

    if (needsPromotion) {
      setPendingMove(uci)
      setPromotion(true)
      return
    }

    sendMove(uci)
  }

  const handleDrop = (e, r, c) => {
    e.preventDefault()
    const from = e.dataTransfer.getData("text/plain")
    const to = algebraic(r, c)
    tryMove(from, to)
  }

  const onPromotionSelect = async (piece) => {
    await sendMove(pendingMove, piece)
    setPromotion(null)
    setPendingMove(null)
  }

  const handleClick = (r, c) => {
    const sq = algebraic(r, c)
    if (!selected) {
      setSelected(sq)
    } else {
      tryMove(selected, sq)
      setSelected(null)
    }
  }

  useEffect(() => {
    loadState()
  }, [])

  const symbols = {
    white: { k: "♔", q: "♕", r: "♖", b: "♗", n: "♘", p: "♙" },
    black: { k: "♚", q: "♛", r: "♜", b: "♝", n: "♞", p: "♟" },
  }

  return (
    <div>
      {promotion && (
        <div style={{
          position: "absolute",
          top: 100,
          left: 100,
          background: "white",
          padding: 20,
          border: "2px solid black",
          display: "flex",
          gap: 10
        }}>
          <button onClick={() => onPromotionSelect("q")}>♛</button>
          <button onClick={() => onPromotionSelect("r")}>♜</button>
          <button onClick={() => onPromotionSelect("b")}>♝</button>
          <button onClick={() => onPromotionSelect("n")}>♞</button>
        </div>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(8, 60px)" }}>
        {board.map((row, r) =>
          row.map((cell, c) => {
            const sq = algebraic(r, c)
            const bg =
              sq === selected
                ? "#88f"
                : (r + c) % 2 === 0
                ? "#f0d9b5"
                : "#b58863"

            return (
              <div
                key={sq}
                onDrop={(e) => handleDrop(e, r, c)}
                onDragOver={(e) => e.preventDefault()}
                onClick={() => handleClick(r, c)}
                style={{
                  width: 60,
                  height: 60,
                  background: bg,
                  fontSize: 40,
                  display: "flex",
                  justifyContent: "center",
                  alignItems: "center"
                }}
              >
                {cell && (
                  <div
                    draggable
                    onDragStart={(e) =>
                      e.dataTransfer.setData("text/plain", sq)
                    }
                    style={{ cursor: "grab" }}
                  >
                    {symbols[cell.color][cell.type]}
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

export default Chess
