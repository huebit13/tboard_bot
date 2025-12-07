import { useState, useEffect } from 'react'
import { X, Clock } from 'lucide-react'

const Chess = ({ bet, onExit, onGameEnd }) => {
  const [board, setBoard] = useState([])
  const [selectedPiece, setSelectedPiece] = useState(null)
  const [validMoves, setValidMoves] = useState([])
  const [currentPlayer, setCurrentPlayer] = useState('white')
  const [myTime, setMyTime] = useState(600)
  const [opponentTime, setOpponentTime] = useState(600)
  const [capturedPieces, setCapturedPieces] = useState({ white: [], black: [] })

  const pieceSymbols = {
    white: { king: '♔', queen: '♕', rook: '♖', bishop: '♗', knight: '♘', pawn: '♙' },
    black: { king: '♚', queen: '♛', rook: '♜', bishop: '♝', knight: '♞', pawn: '♟' }
  }

  useEffect(() => {
    initializeBoard()
  }, [])

  useEffect(() => {
    const timer = setInterval(() => {
      if (currentPlayer === 'white' && myTime > 0) {
        setMyTime(myTime - 1)
        if (myTime === 1) {
          onGameEnd('lose', 0)
        }
      } else if (currentPlayer === 'black' && opponentTime > 0) {
        setOpponentTime(opponentTime - 1)
        if (opponentTime === 1) {
          onGameEnd('win', bet * 2)
        }
      }
    }, 1000)
    return () => clearInterval(timer)
  }, [currentPlayer, myTime, opponentTime])

  useEffect(() => {
    if (currentPlayer === 'black') {
      setTimeout(() => makeAIMove(), 1000)
    }
  }, [currentPlayer])

  const initializeBoard = () => {
    const newBoard = [
      // Black pieces
      [
        { type: 'rook', color: 'black' }, { type: 'knight', color: 'black' },
        { type: 'bishop', color: 'black' }, { type: 'queen', color: 'black' },
        { type: 'king', color: 'black' }, { type: 'bishop', color: 'black' },
        { type: 'knight', color: 'black' }, { type: 'rook', color: 'black' }
      ],
      Array(8).fill(null).map(() => ({ type: 'pawn', color: 'black' })),
      Array(8).fill(null),
      Array(8).fill(null),
      Array(8).fill(null),
      Array(8).fill(null),
      Array(8).fill(null).map(() => ({ type: 'pawn', color: 'white' })),
      // White pieces
      [
        { type: 'rook', color: 'white' }, { type: 'knight', color: 'white' },
        { type: 'bishop', color: 'white' }, { type: 'queen', color: 'white' },
        { type: 'king', color: 'white' }, { type: 'bishop', color: 'white' },
        { type: 'knight', color: 'white' }, { type: 'rook', color: 'white' }
      ]
    ]
    setBoard(newBoard)
  }

  const handleSquareClick = (row, col) => {
    if (currentPlayer !== 'white') return

    const piece = board[row][col]

    if (selectedPiece) {
      const isValidMove = validMoves.some(m => m.row === row && m.col === col)
      if (isValidMove) {
        movePiece(selectedPiece, { row, col })
      } else if (piece && piece.color === 'white') {
        selectPiece(row, col)
      } else {
        setSelectedPiece(null)
        setValidMoves([])
      }
    } else if (piece && piece.color === 'white') {
      selectPiece(row, col)
    }
  }

  const selectPiece = (row, col) => {
    setSelectedPiece({ row, col })
    const moves = getValidMoves(row, col)
    setValidMoves(moves)
  }

  const getValidMoves = (row, col) => {
    const piece = board[row][col]
    if (!piece) return []

    const moves = []

    switch (piece.type) {
      case 'pawn':
        const direction = piece.color === 'white' ? -1 : 1
        const startRow = piece.color === 'white' ? 6 : 1
        
        // Forward move
        if (!board[row + direction]?.[col]) {
          moves.push({ row: row + direction, col })
          // Double move from start
          if (row === startRow && !board[row + direction * 2]?.[col]) {
            moves.push({ row: row + direction * 2, col })
          }
        }
        
        // Captures
        [-1, 1].forEach(dc => {
          const target = board[row + direction]?.[col + dc]
          if (target && target.color !== piece.color) {
            moves.push({ row: row + direction, col: col + dc })
          }
        })
        break

      case 'rook':
        [[0, 1], [0, -1], [1, 0], [-1, 0]].forEach(([dr, dc]) => {
          addLineMoves(row, col, dr, dc, moves, piece)
        })
        break

      case 'knight':
        [[-2, -1], [-2, 1], [-1, -2], [-1, 2], [1, -2], [1, 2], [2, -1], [2, 1]].forEach(([dr, dc]) => {
          const newRow = row + dr
          const newCol = col + dc
          if (newRow >= 0 && newRow < 8 && newCol >= 0 && newCol < 8) {
            const target = board[newRow]?.[newCol]
            if (!target || target.color !== piece.color) {
              moves.push({ row: newRow, col: newCol })
            }
          }
        })
        break

      case 'bishop':
        [[1, 1], [1, -1], [-1, 1], [-1, -1]].forEach(([dr, dc]) => {
          addLineMoves(row, col, dr, dc, moves, piece)
        })
        break

      case 'queen':
        [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [1, -1], [-1, 1], [-1, -1]].forEach(([dr, dc]) => {
          addLineMoves(row, col, dr, dc, moves, piece)
        })
        break

      case 'king':
        [[0, 1], [0, -1], [1, 0], [-1, 0], [1, 1], [1, -1], [-1, 1], [-1, -1]].forEach(([dr, dc]) => {
          const newRow = row + dr
          const newCol = col + dc
          if (newRow >= 0 && newRow < 8 && newCol >= 0 && newCol < 8) {
            const target = board[newRow]?.[newCol]
            if (!target || target.color !== piece.color) {
              moves.push({ row: newRow, col: newCol })
            }
          }
        })
        break
    }

    return moves
  }

  const addLineMoves = (row, col, dr, dc, moves, piece) => {
    let newRow = row + dr
    let newCol = col + dc
    
    while (newRow >= 0 && newRow < 8 && newCol >= 0 && newCol < 8) {
      const target = board[newRow]?.[newCol]
      if (!target) {
        moves.push({ row: newRow, col: newCol })
      } else {
        if (target.color !== piece.color) {
          moves.push({ row: newRow, col: newCol })
        }
        break
      }
      newRow += dr
      newCol += dc
    }
  }

  const movePiece = (from, to) => {
    const newBoard = board.map(row => [...row])
    const piece = newBoard[from.row][from.col]
    const capturedPiece = newBoard[to.row][to.col]
    
    if (capturedPiece) {
      setCapturedPieces(prev => ({
        ...prev,
        [piece.color]: [...prev[piece.color], capturedPiece]
      }))
      
      if (capturedPiece.type === 'king') {
        setTimeout(() => onGameEnd('win', bet * 2), 1000)
        return
      }
    }

    newBoard[to.row][to.col] = piece
    newBoard[from.row][from.col] = null

    setBoard(newBoard)
    setSelectedPiece(null)
    setValidMoves([])
    setCurrentPlayer('black')
  }

  const makeAIMove = () => {
    const blackPieces = []
    for (let row = 0; row < 8; row++) {
      for (let col = 0; col < 8; col++) {
        if (board[row][col] && board[row][col].color === 'black') {
          const moves = getValidMoves(row, col)
          if (moves.length > 0) {
            blackPieces.push({ row, col, moves })
          }
        }
      }
    }

    if (blackPieces.length === 0) {
      onGameEnd('win', bet * 2)
      return
    }

    const randomPiece = blackPieces[Math.floor(Math.random() * blackPieces.length)]
    const randomMove = randomPiece.moves[Math.floor(Math.random() * randomPiece.moves.length)]

    const newBoard = board.map(row => [...row])
    const piece = newBoard[randomPiece.row][randomPiece.col]
    const capturedPiece = newBoard[randomMove.row][randomMove.col]
    
    if (capturedPiece) {
      setCapturedPieces(prev => ({
        ...prev,
        black: [...prev.black, capturedPiece]
      }))
      
      if (capturedPiece.type === 'king') {
        setTimeout(() => onGameEnd('lose', 0), 1000)
        return
      }
    }

    newBoard[randomMove.row][randomMove.col] = piece
    newBoard[randomPiece.row][randomPiece.col] = null

    setBoard(newBoard)
    setCurrentPlayer('white')
  }

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
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
              Chess
            </h2>
            <p className="text-xs text-gray-400">{bet} TON</p>
          </div>
          <div className="w-10"></div>
        </div>
      </div>

      <div className="px-4 py-6 max-w-4xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* Left sidebar - Captured pieces */}
          <div className="lg:col-span-2">
            <div className="bg-slate-900 rounded-xl p-3 border-2 border-slate-700">
              <div className="text-xs text-gray-400 mb-2">Captured</div>
              <div className="flex flex-wrap gap-1">
                {capturedPieces.white.map((piece, i) => (
                  <span key={i} className="text-xl">{pieceSymbols.white[piece.type]}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Center - Board */}
          <div className="lg:col-span-8">
            {/* Opponent info */}
            <div className={`bg-slate-900 border-2 ${currentPlayer === 'black' ? 'border-yellow-400' : 'border-slate-700'} rounded-xl p-3 mb-4 flex items-center justify-between`}>
              <span className="font-semibold">Opponent (Black)</span>
              <div className="flex items-center gap-2 text-yellow-400">
                <Clock className="w-4 h-4" />
                <span className="font-bold">{formatTime(opponentTime)}</span>
              </div>
            </div>

            {/* Chess board */}
            <div className="bg-slate-900 p-4 rounded-xl border-2 border-slate-700">
              <div className="grid grid-cols-8 gap-0 aspect-square">
                {board.map((row, rowIndex) => 
                  row.map((piece, colIndex) => {
                    const isLight = (rowIndex + colIndex) % 2 === 0
                    const isSelected = selectedPiece && selectedPiece.row === rowIndex && selectedPiece.col === colIndex
                    const isValidMove = validMoves.some(m => m.row === rowIndex && m.col === colIndex)
                    
                    return (
                      <div
                        key={`${rowIndex}-${colIndex}`}
                        onClick={() => handleSquareClick(rowIndex, colIndex)}
                        className={`
                          aspect-square flex items-center justify-center cursor-pointer transition-all text-4xl
                          ${isLight ? 'bg-amber-100' : 'bg-amber-800'}
                          ${isSelected ? 'ring-4 ring-cyan-400 ring-inset' : ''}
                          ${isValidMove ? 'ring-4 ring-green-400 ring-inset' : ''}
                        `}
                      >
                        {piece && pieceSymbols[piece.color][piece.type]}
                      </div>
                    )
                  })
                )}
              </div>
            </div>

            {/* Player info */}
            <div className={`bg-slate-900 border-2 ${currentPlayer === 'white' ? 'border-yellow-400' : 'border-slate-700'} rounded-xl p-3 mt-4 flex items-center justify-between`}>
              <span className="font-semibold">You (White)</span>
              <div className="flex items-center gap-2 text-yellow-400">
                <Clock className="w-4 h-4" />
                <span className="font-bold">{formatTime(myTime)}</span>
              </div>
            </div>
          </div>

          {/* Right sidebar - Captured pieces */}
          <div className="lg:col-span-2">
            <div className="bg-slate-900 rounded-xl p-3 border-2 border-slate-700">
              <div className="text-xs text-gray-400 mb-2">Captured</div>
              <div className="flex flex-wrap gap-1">
                {capturedPieces.black.map((piece, i) => (
                  <span key={i} className="text-xl">{pieceSymbols.black[piece.type]}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        <div className="text-center mt-4 text-gray-400 text-sm">
          {currentPlayer === 'white' ? 'Your turn' : 'Opponent\'s turn'}
        </div>
      </div>
    </div>
  )
}

export default Chess