import { useState, useEffect } from 'react'
import { Trophy, X, Clock, Zap } from 'lucide-react'

const RockPaperScissors = ({ bet, onExit, onGameEnd }) => {
  const [myScore, setMyScore] = useState(0)
  const [opponentScore, setOpponentScore] = useState(0)
  const [myChoice, setMyChoice] = useState(null)
  const [opponentChoice, setOpponentChoice] = useState(null)
  const [timeLeft, setTimeLeft] = useState(30)
  const [roundResult, setRoundResult] = useState(null)
  const [isChoosing, setIsChoosing] = useState(true)
  const [showResult, setShowResult] = useState(false)

  const choices = [
    { id: 'rock', emoji: '✊', name: 'Rock' },
    { id: 'paper', emoji: '✋', name: 'Paper' },
    { id: 'scissors', emoji: '✌️', name: 'Scissors' }
  ]

  useEffect(() => {
    if (isChoosing && timeLeft > 0) {
      const timer = setTimeout(() => setTimeLeft(timeLeft - 1), 1000)
      return () => clearTimeout(timer)
    } else if (timeLeft === 0 && !myChoice) {
      // Auto choose random if time runs out
      handleChoice(choices[Math.floor(Math.random() * 3)].id)
    }
  }, [timeLeft, isChoosing, myChoice])

  const handleChoice = (choiceId) => {
    if (!isChoosing) return
    
    setMyChoice(choiceId)
    setIsChoosing(false)
    
    // Simulate opponent choice
    setTimeout(() => {
      const opponentChoiceId = choices[Math.floor(Math.random() * 3)].id
      setOpponentChoice(opponentChoiceId)
      
      // Determine winner
      const result = determineWinner(choiceId, opponentChoiceId)
      setRoundResult(result)
      
      if (result === 'win') {
        const newScore = myScore + 1
        setMyScore(newScore)
        if (newScore === 3) {
          setTimeout(() => onGameEnd('win', bet * 2), 2000)
        }
      } else if (result === 'lose') {
        const newScore = opponentScore + 1
        setOpponentScore(newScore)
        if (newScore === 3) {
          setTimeout(() => onGameEnd('lose', 0), 2000)
        }
      }
      
      // Reset for next round
      if (myScore < 2 && opponentScore < 2) {
        setTimeout(() => {
          setMyChoice(null)
          setOpponentChoice(null)
          setRoundResult(null)
          setIsChoosing(true)
          setTimeLeft(30)
        }, 3000)
      }
    }, 1000)
  }

  const determineWinner = (my, opponent) => {
    if (my === opponent) return 'draw'
    if (
      (my === 'rock' && opponent === 'scissors') ||
      (my === 'paper' && opponent === 'rock') ||
      (my === 'scissors' && opponent === 'paper')
    ) {
      return 'win'
    }
    return 'lose'
  }

  const getChoiceData = (choiceId) => {
    return choices.find(c => c.id === choiceId)
  }

  return (
    <div className="fixed inset-0 bg-slate-950 z-50 overflow-hidden">
      {/* Header */}
      <div className="bg-slate-950/95 backdrop-blur border-b border-slate-800">
        <div className="px-4 py-4 flex items-center justify-between">
          <button
            onClick={onExit}
            className="p-2 hover:bg-slate-800 rounded-lg transition-all"
          >
            <X className="w-5 h-5" />
          </button>
          <div className="text-center">
            <h2 className="text-lg font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              Rock Paper Scissors
            </h2>
            <p className="text-xs text-gray-400">First to 3 wins • {bet} TON</p>
          </div>
          <div className="w-10"></div>
        </div>
      </div>

      {/* Score Board */}
      <div className="px-4 py-6">
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-3 gap-4 mb-6">
            {/* My Score */}
            <div className="bg-slate-900 border-2 border-cyan-500 rounded-xl p-4 text-center">
              <div className="text-sm text-gray-400 mb-2">You</div>
              <div className="text-4xl font-bold text-cyan-400">{myScore}</div>
            </div>

            {/* Timer */}
            <div className="bg-slate-900 border-2 border-slate-700 rounded-xl p-4 text-center">
              <Clock className="w-6 h-6 text-yellow-400 mx-auto mb-2" />
              <div className="text-3xl font-bold text-yellow-400">{timeLeft}s</div>
            </div>

            {/* Opponent Score */}
            <div className="bg-slate-900 border-2 border-red-500 rounded-xl p-4 text-center">
              <div className="text-sm text-gray-400 mb-2">Opponent</div>
              <div className="text-4xl font-bold text-red-400">{opponentScore}</div>
            </div>
          </div>

          {/* Round Result */}
          {roundResult && (
            <div className="text-center mb-6">
              <div className={`text-2xl font-bold mb-2 ${
                roundResult === 'win' ? 'text-green-400' : 
                roundResult === 'lose' ? 'text-red-400' : 'text-yellow-400'
              }`}>
                {roundResult === 'win' ? '🎉 You Win!' : 
                 roundResult === 'lose' ? '😢 You Lose!' : '🤝 Draw!'}
              </div>
            </div>
          )}

          {/* Choices Display */}
          <div className="grid grid-cols-2 gap-8 mb-8">
            {/* My Choice */}
            <div className="text-center">
              <div className="text-sm text-gray-400 mb-3">Your Choice</div>
              <div className="bg-slate-900 border-2 border-cyan-500/50 rounded-2xl p-8">
                {myChoice ? (
                  <div>
                    <div className="text-7xl mb-2">{getChoiceData(myChoice).emoji}</div>
                    <div className="text-lg font-semibold text-cyan-400">
                      {getChoiceData(myChoice).name}
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="text-7xl mb-2">❓</div>
                    <div className="text-lg text-gray-500">Waiting...</div>
                  </div>
                )}
              </div>
            </div>

            {/* Opponent Choice */}
            <div className="text-center">
              <div className="text-sm text-gray-400 mb-3">Opponent's Choice</div>
              <div className="bg-slate-900 border-2 border-red-500/50 rounded-2xl p-8">
                {opponentChoice ? (
                  <div>
                    <div className="text-7xl mb-2">{getChoiceData(opponentChoice).emoji}</div>
                    <div className="text-lg font-semibold text-red-400">
                      {getChoiceData(opponentChoice).name}
                    </div>
                  </div>
                ) : (
                  <div>
                    <div className="text-7xl mb-2">❓</div>
                    <div className="text-lg text-gray-500">Waiting...</div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Choice Buttons */}
          {isChoosing && !myChoice && (
            <div className="grid grid-cols-3 gap-4">
              {choices.map((choice) => (
                <button
                  key={choice.id}
                  onClick={() => handleChoice(choice.id)}
                  className="bg-slate-900 border-2 border-slate-700 hover:border-cyan-500 rounded-xl p-6 transition-all transform hover:scale-105 group"
                >
                  <div className="text-6xl mb-3">{choice.emoji}</div>
                  <div className="text-lg font-semibold group-hover:text-cyan-400 transition-colors">
                    {choice.name}
                  </div>
                </button>
              ))}
            </div>
          )}

          {myChoice && !roundResult && (
            <div className="text-center">
              <div className="inline-flex items-center gap-2 bg-slate-900 px-6 py-3 rounded-lg">
                <Zap className="w-5 h-5 text-yellow-400 animate-pulse" />
                <span className="text-gray-400">Waiting for opponent...</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default RockPaperScissors