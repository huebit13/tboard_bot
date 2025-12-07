import { useState, useEffect } from 'react'
import { X, Clock } from 'lucide-react'

const BOARD_SIZE = 8

const Checkers = ({ bet, onExit, onGameEnd }) => {
  const [board, setBoard] = useState([])
  const [selectedPiece, setSelectedPiece] = useState(null)
  const [validMoves, setValidMoves] = useState([])
  const [currentPlayer, setCurrentPlayer] = useState('red')
  const [myTime, setMyTime] = useState(600)
  const [opponentTime, setOpponentTime] = useState(600)
  const [multiCapturePiece, setMultiCapturePiece] = useState(null)

  useEffect(() => initializeBoard(), [])

  useEffect(() => {
    const timer = setInterval(() => {
      if (currentPlayer === 'red') {
        setMyTime(t => {
          if (t <= 1) { onGameEnd('lose', 0); return 0 }
          return t - 1
        })
      } else {
        setOpponentTime(t => {
          if (t <= 1) { onGameEnd('win', bet * 2); return 0 }
          return t - 1
        })
      }
    }, 1000)
    return () => clearInterval(timer)
  }, [currentPlayer])

  useEffect(() => {
    if (currentPlayer === 'black') setTimeout(makeAIMove, 500)
  }, [currentPlayer])

  const initializeBoard = () => {
    const newBoard = Array(BOARD_SIZE).fill(null).map(() => Array(BOARD_SIZE).fill(null))
    for (let r = 0; r < 3; r++)
      for (let c = 0; c < BOARD_SIZE; c++)
        if ((r + c) % 2 === 1) newBoard[r][c] = { color: 'black', isKing: false }

    for (let r = BOARD_SIZE - 3; r < BOARD_SIZE; r++)
      for (let c = 0; c < BOARD_SIZE; c++)
        if ((r + c) % 2 === 1) newBoard[r][c] = { color: 'red', isKing: false }

    setBoard(newBoard)
  }

  const handleSquareClick = (row, col) => {
    if (currentPlayer !== 'red') return
    const piece = board[row][col]

    if (multiCapturePiece) {
      const move = validMoves.find(m => m.row === row && m.col === col)
      if (move) movePiece(multiCapturePiece, move, true)
      return
    }

    if (selectedPiece) {
      const move = validMoves.find(m => m.row === row && m.col === col)
      if (move) movePiece(selectedPiece, move)
      else if (piece && piece.color === 'red') selectPiece(row, col)
      else { setSelectedPiece(null); setValidMoves([]) }
    } else if (piece && piece.color === 'red') selectPiece(row, col)
  }

  const selectPiece = (row, col) => {
    setSelectedPiece({ row, col })
    const moves = getValidMoves(row, col, board)
    setValidMoves(moves)
  }

  const getValidMoves = (row, col, currentBoard) => {
    const piece = currentBoard[row][col]
    if (!piece) return []

    const directions = [[-1,-1],[-1,1],[1,-1],[1,1]]
    const moves = []

    for (const [dr, dc] of directions) {
      if (piece.isKing) {
        let r = row + dr, c = col + dc
        while (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE) {
          if (!currentBoard[r][c]) { r += dr; c += dc; continue }
          if (currentBoard[r][c].color !== piece.color) {
            let jumpR = r + dr, jumpC = c + dc
            while (jumpR >= 0 && jumpR < BOARD_SIZE && jumpC >= 0 && jumpC < BOARD_SIZE && !currentBoard[jumpR][jumpC]) {
              moves.push({ row: jumpR, col: jumpC, isCapture: true, capturePos: { row: r, col: c } })
              jumpR += dr
              jumpC += dc
            }
            break
          } else break
        }
      } else {
        const jumpR = row + dr*2, jumpC = col + dc*2
        const midR = row + dr, midC = col + dc
        if (jumpR >= 0 && jumpR < BOARD_SIZE && jumpC >= 0 && jumpC < BOARD_SIZE) {
          const midPiece = currentBoard[midR][midC]
          if (midPiece && midPiece.color !== piece.color && !currentBoard[jumpR][jumpC])
            moves.push({ row: jumpR, col: jumpC, isCapture: true, capturePos: { row: midR, col: midC } })
        }
      }
    }

    if (moves.length > 0) return moves 

    for (const [dr, dc] of directions) {
      if (piece.isKing) {
        let r = row + dr, c = col + dc
        while (r >= 0 && r < BOARD_SIZE && c >= 0 && c < BOARD_SIZE && !currentBoard[r][c]) {
          moves.push({ row: r, col: c, isCapture: false })
          r += dr
          c += dc
        }
      } else {
        const dir = piece.color === 'red' ? -1 : 1  
        if (dr !== dir) continue 
        const newR = row + dr, newC = col + dc
        if (newR >= 0 && newR < BOARD_SIZE && newC >= 0 && newC < BOARD_SIZE && !currentBoard[newR][newC])
          moves.push({ row: newR, col: newC, isCapture: false })
      }
    }

    return moves
  }

  const movePiece = (from, to, isMultiCapture = false) => {
    const newBoard = board.map(r => r.map(c => c ? { ...c } : null))
    const piece = newBoard[from.row][from.col]

    newBoard[to.row][to.col] = piece
    newBoard[from.row][from.col] = null

    if (to.isCapture) newBoard[to.capturePos.row][to.capturePos.col] = null

    if (to.row === 0 && piece.color === 'red') piece.isKing = true
    if (to.row === BOARD_SIZE - 1 && piece.color === 'black') piece.isKing = true

    setBoard(newBoard)
    setSelectedPiece(null)
    setValidMoves([])

    if (to.isCapture) {
      const nextMoves = getValidMoves(to.row, to.col, newBoard).filter(m => m.isCapture)
      if (nextMoves.length > 0) {
        setMultiCapturePiece({ row: to.row, col: to.col })
        setValidMoves(nextMoves)
        return
      }
    }
    setMultiCapturePiece(null)

    if (checkWinCondition(newBoard, 'black')) { setTimeout(() => onGameEnd('win', bet * 2), 500); return }
    if (checkWinCondition(newBoard, 'red')) { setTimeout(() => onGameEnd('lose', 0), 500); return }

    setCurrentPlayer(currentPlayer === 'red' ? 'black' : 'red')
  }

  const makeAIMove = () => {
    const blackPieces = []
    for (let r = 0; r < BOARD_SIZE; r++)
      for (let c = 0; c < BOARD_SIZE; c++)
        if (board[r][c]?.color === 'black') {
          const moves = getValidMoves(r, c, board)
          if (moves.length > 0) blackPieces.push({ row: r, col: c, moves })
        }

    if (blackPieces.length === 0) { onGameEnd('win', bet * 2); return }

    const randomPiece = blackPieces[Math.floor(Math.random() * blackPieces.length)]
    const captureMoves = randomPiece.moves.filter(m => m.isCapture)
    const randomMove = (captureMoves.length > 0 ? captureMoves : randomPiece.moves)[Math.floor(Math.random() * (captureMoves.length > 0 ? captureMoves.length : randomPiece.moves.length))]

    movePiece({ row: randomPiece.row, col: randomPiece.col }, randomMove)
  }

  const checkWinCondition = (boardState, color) => {
    const hasPieces = boardState.some(row => row.some(p => p?.color === color))
    if (!hasPieces) return true
    const canMove = boardState.some((row, r) => row.some((p, c) => p?.color === color && getValidMoves(r, c, boardState).length > 0))
    return !canMove
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2,'0')}`
  }

  return (
    <div className="fixed inset-0 bg-slate-950 z-50 overflow-y-auto">
      <div className="bg-slate-950/95 backdrop-blur border-b border-slate-800">
        <div className="px-4 py-4 flex items-center justify-between">
          <button onClick={onExit} className="p-2 hover:bg-slate-800 rounded-lg transition-all">
            <X className="w-5 h-5" />
          </button>
          <div className="text-center">
            <h2 className="text-lg font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              International Checkers
            </h2>
            <p className="text-xs text-gray-400">{bet} TON</p>
          </div>
          <div className="w-10"></div>
        </div>
      </div>

      <div className="px-4 py-6 max-w-2xl mx-auto">
        {/* Players Info */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          <div className={`bg-slate-900 border-2 ${currentPlayer==='black'?'border-yellow-400':'border-slate-700'} rounded-xl p-4`}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-6 h-6 bg-black rounded-full border-2 border-gray-400"></div>
              <span className="font-semibold">Opponent</span>
            </div>
            <div className="flex items-center gap-2 text-yellow-400">
              <Clock className="w-4 h-4"/>
              <span className="font-bold">{formatTime(opponentTime)}</span>
            </div>
          </div>
          <div className={`bg-slate-900 border-2 ${currentPlayer==='red'?'border-yellow-400':'border-slate-700'} rounded-xl p-4`}>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-6 h-6 bg-red-500 rounded-full"></div>
              <span className="font-semibold">You</span>
            </div>
            <div className="flex items-center gap-2 text-yellow-400">
              <Clock className="w-4 h-4"/>
              <span className="font-bold">{formatTime(myTime)}</span>
            </div>
          </div>
        </div>

        {/* Board */}
        <div className="bg-slate-900 p-4 rounded-xl border-2 border-slate-700">
          <div className="grid grid-cols-8 gap-0 aspect-square">
            {board.map((row,rowIndex)=>row.map((piece,colIndex)=>{
              const isLight = (rowIndex+colIndex)%2===0
              const isSelected = selectedPiece && selectedPiece.row===rowIndex && selectedPiece.col===colIndex
              const isValidMove = validMoves.some(m=>m.row===rowIndex && m.col===colIndex)
              return (
                <div key={`${rowIndex}-${colIndex}`} onClick={()=>handleSquareClick(rowIndex,colIndex)}
                  className={`aspect-square flex items-center justify-center cursor-pointer transition-all
                    ${isLight?'bg-amber-100':'bg-amber-800'} ${isSelected?'ring-4 ring-cyan-400':''} ${isValidMove?'ring-4 ring-green-400':''}`}>
                  {piece && (
                    <div className={`w-3/4 h-3/4 rounded-full flex items-center justify-center font-bold text-white
                      ${piece.color==='red'?'bg-red-500':'bg-gray-900'} ${piece.isKing?'ring-4 ring-yellow-400':''}`}>
                      {piece.isKing && '♔'}
                    </div>
                  )}
                </div>
              )
            }))}
          </div>
        </div>

        <div className="text-center mt-4 text-gray-400 text-sm">
          {currentPlayer==='red'?'Your turn':'Opponent\'s turn'}
        </div>
      </div>
    </div>
  )
}

export default Checkers
