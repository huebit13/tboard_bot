import { Trophy, TrendingDown, Coins } from 'lucide-react'

const GameResultModal = ({ result, amount, onClose }) => {
  const isWin = result === 'win'

  return (
    <div className="fixed inset-0 bg-black/90 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div className="bg-slate-900 border-2 border-slate-700 rounded-2xl p-8 max-w-md w-full text-center relative overflow-hidden">
        {/* Background effects */}
        <div className={`absolute inset-0 opacity-10 ${isWin ? 'bg-gradient-to-br from-green-500 to-emerald-500' : 'bg-gradient-to-br from-red-500 to-rose-500'}`}></div>
        
        <div className="relative z-10">
          {/* Icon */}
          <div className={`w-24 h-24 rounded-full mx-auto mb-6 flex items-center justify-center ${
            isWin ? 'bg-green-500/20' : 'bg-red-500/20'
          }`}>
            {isWin ? (
              <Trophy className="w-12 h-12 text-green-400" />
            ) : (
              <TrendingDown className="w-12 h-12 text-red-400" />
            )}
          </div>

          {/* Title */}
          <h2 className={`text-4xl font-bold mb-4 ${
            isWin ? 'text-green-400' : 'text-red-400'
          }`}>
            {isWin ? '🎉 Victory!' : '💔 Defeat'}
          </h2>

          {/* Message */}
          <p className="text-gray-400 text-lg mb-6">
            {isWin ? 'Congratulations! You won the game!' : 'Better luck next time!'}
          </p>

          {/* Amount */}
          <div className="bg-slate-800 rounded-xl p-6 mb-6">
            <div className="flex items-center justify-center gap-3">
              <Coins className={`w-8 h-8 ${isWin ? 'text-yellow-400' : 'text-gray-400'}`} />
              <div>
                <div className={`text-3xl font-bold ${isWin ? 'text-green-400' : 'text-red-400'}`}>
                  {isWin ? '+' : ''}{amount.toFixed(2)} TON
                </div>
                <div className="text-sm text-gray-400">
                  {isWin ? 'Added to your balance' : 'Lost in this game'}
                </div>
              </div>
            </div>
          </div>

          {/* Buttons */}
          <div className="flex gap-3">
            <button
              onClick={onClose}
              className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-all ${
                isWin 
                  ? 'bg-gradient-to-r from-green-500 to-emerald-600 hover:shadow-lg hover:shadow-green-500/50' 
                  : 'bg-slate-800 hover:bg-slate-700'
              }`}
            >
              {isWin ? 'Claim Reward' : 'Back to Lobby'}
            </button>
          </div>

          {isWin && (
            <div className="mt-4 text-sm text-gray-400">
              Keep the winning streak going! 🔥
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default GameResultModal