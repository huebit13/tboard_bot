import { useState, useEffect, useRef } from 'react'
import { Wallet, Share2, Users, Trophy, Gamepad2, Coins, X, Check, Zap, Sparkles, Search, Clock, Copy, TrendingUp, TrendingDown, ArrowLeft, Gift } from 'lucide-react'

import { useTonWallet } from './hooks/useTonWallet'
import { RefreshCw } from 'lucide-react'

// Import game components (create these files in your src folder)
import RockPaperScissors from './RockPaperScissors'
import Checkers from './Checkers'
import Chess from './Chess'
import GameResultModal from './GameResultModal'

const TBoardApp = () => {
  const [scrollY, setScrollY] = useState(0)
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 })
  // TON Wallet
  const { 
    address, 
    formattedAddress, 
    balance, 
    loading: balanceLoading,
    isConnected, 
    connect, 
    disconnect,
    refreshBalance 
  } = useTonWallet()
  const [showGameSelect, setShowGameSelect] = useState(false)
  const [showBetSelect, setShowBetSelect] = useState(false)
  const [selectedGame, setSelectedGame] = useState(null)
  const [selectedBet, setSelectedBet] = useState(null)
  const [showMatchmaking, setShowMatchmaking] = useState(false)
  const [showShareModal, setShowShareModal] = useState(false)
  const [showProfileModal, setShowProfileModal] = useState(false)
  const [activeGame, setActiveGame] = useState(null)
  const [gameResult, setGameResult] = useState(null)
  const [userProfile, setUserProfile] = useState({
    name: 'CryptoPlayer',
    avatar: '👤'
  })
  const [referralStats, setReferralStats] = useState({
    referrals: 12,
    earned: 24.5,
    link: 't.me/tboard_bot?start=ref_USER123'
  })
  const [userStats, setUserStats] = useState({
    gamesPlayed: 47,
    winRate: 68,
    totalEarned: 156.8,
    gameHistory: [
      { id: 1, game: 'dice', bet: 10, result: 'win', amount: 20, date: '2 hours ago' },
      { id: 2, game: 'coin', bet: 5, result: 'loss', amount: -5, date: '5 hours ago' },
      { id: 3, game: 'rps', bet: 25, result: 'win', amount: 50, date: '1 day ago' },
      { id: 4, game: 'roulette', bet: 50, result: 'win', amount: 100, date: '1 day ago' },
      { id: 5, game: 'dice', bet: 10, result: 'loss', amount: -10, date: '2 days ago' }
    ]
  })

  const games = [
    { id: 'rps', name: 'Rock Paper Scissors', icon: '✊', color: 'cyan' },
    { id: 'checkers', name: 'Checkers', icon: '🎯', color: 'purple' },
    { id: 'chess', name: 'Chess', icon: '♟️', color: 'blue' },
    { id: 'dice', name: 'Dice Battle', icon: '🎲', color: 'green' }
  ]

  const betAmounts = [
    { value: 0.05, label: '0.05 TON' },
    { value: 0.1, label: '0.1 TON' },
    { value: 0.5, label: '0.5 TON' },
    { value: 1, label: '1 TON' },
    { value: 5, label: '5 TON' },
    { value: 10, label: '10 TON' }
  ]

  const [activeLobby, setActiveLobby] = useState([
    { id: 1, game: 'rps', bet: 5, player: 'CryptoKing', avatar: '👑', time: '2m' },
    { id: 2, game: 'chess', bet: 10, player: 'MoonBoy', avatar: '🌙', time: '5m' },
    { id: 3, game: 'checkers', bet: 1, player: 'DiamondHands', avatar: '💎', time: '1m' },
    { id: 4, game: 'dice', bet: 25, player: 'WhaleAlert', avatar: '🐋', time: '3m' }
  ])





  const handleCreateGame = () => {
    setShowGameSelect(true)
  }

  const handleGameSelect = (game) => {
    setSelectedGame(game)
    setShowGameSelect(false)
    setShowBetSelect(true)
  }

  const handleBetSelect = (bet) => {
    setSelectedBet(bet)
    setShowBetSelect(false)
    setShowMatchmaking(true)
    
    // Simulate finding match and starting game after 2 seconds
    setTimeout(() => {
      setShowMatchmaking(false)
      setActiveGame({
        gameType: selectedGame.id,
        bet: bet.value
      })
    }, 2000)
  }

  const handleGameEnd = (result, amount) => {
    setGameResult({ result, amount })
    setActiveGame(null)
    
    // Update balance
    if (result === 'win') {
      setBalance(balance + amount)
    } else {
      setBalance(balance - amount)
    }
  }

  const handleCloseResult = () => {
    setGameResult(null)
    setSelectedGame(null)
    setSelectedBet(null)
  }

  const handleExitGame = () => {
    if (window.confirm('Are you sure you want to exit the game? You will lose your bet.')) {
      setActiveGame(null)
      setSelectedGame(null)
      setSelectedBet(null)
    }
  }

  const handleShare = () => {
    setShowShareModal(true)
  }

  const handleProfileClick = () => {
    setShowProfileModal(true)
  }

  const handleCopyLink = () => {
    navigator.clipboard.writeText(referralStats.link)
    alert('Referral link copied!')
  }

  const handleDisconnectWallet = async () => {
    await disconnect()
    setShowProfileModal(false)
  }

  const handleCopyAddress = () => {
    navigator.clipboard.writeText(address)
    alert('Address copied!')
  }

  // Welcome Screen
  if (!isConnected) {
    return (
      <div className="bg-slate-950 text-white min-h-screen font-sans overflow-hidden relative flex items-center justify-center">
        <style dangerouslySetInnerHTML={{__html: `
          @keyframes pulse-glow { 0%, 100% { box-shadow: 0 0 20px rgba(6, 182, 212, 0.5); } 50% { box-shadow: 0 0 40px rgba(6, 182, 212, 0.8); } }
          .animate-pulse-glow { animation: pulse-glow 2s ease-in-out infinite; }
        `}} />

        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-20 left-20 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
          <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl"></div>
        </div>

        <div className="relative z-10 max-w-md mx-auto px-6 text-center">
          <div className="mb-8 flex justify-center">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center animate-pulse-glow">
              <Trophy className="w-12 h-12 text-white" />
            </div>
          </div>

          <h1 className="text-5xl font-bold bg-gradient-to-r from-cyan-400 via-blue-500 to-purple-600 bg-clip-text text-transparent mb-4">
            TBoard
          </h1>
          
          <p className="text-xl text-gray-400 mb-8">
            Challenge players in exciting mini-games and win TON rewards
          </p>

          <div className="bg-slate-900/50 backdrop-blur border border-cyan-500/30 rounded-xl p-6 mb-8">
            <div className="flex items-start gap-4 text-left mb-4">
              <Gamepad2 className="w-6 h-6 text-cyan-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-cyan-400 mb-1">Multiple Games</h3>
                <p className="text-sm text-gray-400">Choose from Dice, Coin Flip, RPS and more</p>
              </div>
            </div>
            <div className="flex items-start gap-4 text-left mb-4">
              <Zap className="w-6 h-6 text-blue-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-blue-400 mb-1">Instant Matches</h3>
                <p className="text-sm text-gray-400">Quick matchmaking with real players</p>
              </div>
            </div>
            <div className="flex items-start gap-4 text-left">
              <Coins className="w-6 h-6 text-purple-400 flex-shrink-0 mt-1" />
              <div>
                <h3 className="font-semibold text-purple-400 mb-1">Real Rewards</h3>
                <p className="text-sm text-gray-400">Win TON crypto in every game</p>
              </div>
            </div>
          </div>

          <button
            onClick={connect}
            onMouseEnter={() => setIsHovering(true)}
            onMouseLeave={() => setIsHovering(false)}
            className="w-full group relative px-8 py-4 rounded-xl font-bold text-lg overflow-hidden bg-gradient-to-r from-cyan-500 to-blue-600 hover:shadow-2xl hover:shadow-cyan-500/50 transition-all transform hover:scale-105 mb-4"
          >
            <span className="relative z-10 flex items-center justify-center gap-3">
              <Wallet className="w-6 h-6" />
              Connect Wallet
            </span>
            <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity"></div>
          </button>

          <p className="text-xs text-gray-500">
            Connect your TON wallet to start playing
          </p>
        </div>
      </div>
    )
  }

  const getGameData = (gameId) => {
    return games.find(g => g.id === gameId)
  }

  // Render active game
  if (activeGame) {
    const { gameType, bet } = activeGame
    
    if (gameType === 'rps') {
      return <RockPaperScissors bet={bet} onExit={handleExitGame} onGameEnd={handleGameEnd} />
    } else if (gameType === 'checkers') {
      return <Checkers bet={bet} onExit={handleExitGame} onGameEnd={handleGameEnd} />
    } else if (gameType === 'chess') {
      return <Chess bet={bet} onExit={handleExitGame} onGameEnd={handleGameEnd} />
    }
  }

  // Main Lobby Screen
  return (
    <div className="bg-slate-950 text-white min-h-screen font-sans overflow-x-hidden relative">
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes pulse-glow { 0%, 100% { box-shadow: 0 0 20px rgba(6, 182, 212, 0.5); } 50% { box-shadow: 0 0 40px rgba(6, 182, 212, 0.8); } }
        .animate-pulse-glow { animation: pulse-glow 2s ease-in-out infinite; }
      `}} />

      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute top-20 left-20 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 w-80 h-80 bg-purple-500/10 rounded-full blur-3xl"></div>
      </div>

      {/* Header */}
      <header className="relative z-10 border-b border-slate-800 bg-slate-950/80 backdrop-blur">
        <div className="px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div 
              onClick={handleProfileClick}
              className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-xl cursor-pointer hover:scale-110 transition-transform"
            >
              {userProfile.avatar}
            </div>
            <button
              onClick={handleShare}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-all flex items-center gap-2"
            >
              <Share2 className="w-4 h-4" />
              <span className="text-sm font-semibold">Share</span>
            </button>
          </div>

          <div 
            className="flex items-center gap-2 bg-slate-800 px-4 py-2 rounded-lg group cursor-pointer" 
            onClick={refreshBalance}
          >
            <Coins className="w-5 h-5 text-yellow-400" />
            <span className="font-bold text-lg">
              {balanceLoading ? '...' : balance.toFixed(2)}
            </span>
            <span className="text-gray-400 text-sm">TON</span>
            <RefreshCw className="w-4 h-4 text-gray-400 group-hover:text-cyan-400 group-hover:rotate-180 transition-all" />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="relative z-10 px-4 py-6 max-w-4xl mx-auto">
        <div className="mb-6">
          <h2 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent mb-2">
            Active Lobby
          </h2>
          <p className="text-gray-400">Join a game or create your own challenge</p>
        </div>

        {/* Create Game Button */}
        <button
          onClick={handleCreateGame}
          className="w-full group relative px-6 py-4 rounded-xl font-bold overflow-hidden bg-gradient-to-r from-cyan-500 to-blue-600 hover:shadow-xl hover:shadow-cyan-500/50 transition-all transform hover:scale-105 mb-6"
        >
          <span className="relative z-10 flex items-center justify-center gap-3 text-lg">
            <Gamepad2 className="w-6 h-6" />
            Create Game
          </span>
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-purple-600 opacity-0 group-hover:opacity-100 transition-opacity"></div>
        </button>

        {/* Active Games List */}
        <div className="space-y-4">
          {activeLobby.map((lobby) => {
            const gameData = getGameData(lobby.game)
            return (
              <div
                key={lobby.id}
                className="group bg-slate-900 border-2 border-slate-700 hover:border-cyan-500 rounded-xl p-4 transition-all transform hover:scale-102"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="text-4xl">{gameData.icon}</div>
                    <div>
                      <h3 className="font-bold text-lg">{gameData.name}</h3>
                      <div className="flex items-center gap-2 text-sm text-gray-400">
                        <span className="flex items-center gap-1">
                          <span className="text-xl">{lobby.avatar}</span>
                          {lobby.player}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {lobby.time}
                        </span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <div className="text-2xl font-bold text-yellow-400">{lobby.bet}</div>
                      <div className="text-xs text-gray-400">TON</div>
                    </div>
                    <button className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-600 rounded-lg font-semibold hover:shadow-lg hover:shadow-green-500/50 transition-all">
                      Join
                    </button>
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        {activeLobby.length === 0 && (
          <div className="text-center py-12">
            <Users className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">No active games</p>
            <p className="text-gray-500 text-sm">Be the first to create a challenge!</p>
          </div>
        )}
      </div>

      {/* Game Select Modal */}
      {showGameSelect && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border-2 border-cyan-500 rounded-2xl p-6 max-w-md w-full relative">
            <button
              onClick={() => setShowGameSelect(false)}
              className="absolute top-4 right-4 p-2 hover:bg-slate-800 rounded-lg transition-all"
            >
              <X className="w-5 h-5" />
            </button>

            <h2 className="text-2xl font-bold mb-6 bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
              Choose Your Game
            </h2>

            <div className="grid grid-cols-2 gap-4">
              {games.map((game) => (
                <button
                  key={game.id}
                  onClick={() => handleGameSelect(game)}
                  className="group bg-slate-800 hover:bg-slate-700 border-2 border-slate-700 hover:border-cyan-500 rounded-xl p-6 transition-all transform hover:scale-105"
                >
                  <div className="text-5xl mb-3">{game.icon}</div>
                  <h3 className="font-bold text-sm">{game.name}</h3>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Bet Select Modal */}
      {showBetSelect && selectedGame && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border-2 border-cyan-500 rounded-2xl p-6 max-w-md w-full relative">
            <button
              onClick={() => {
                setShowBetSelect(false)
                setSelectedGame(null)
              }}
              className="absolute top-4 right-4 p-2 hover:bg-slate-800 rounded-lg transition-all"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="text-center mb-6">
              <div className="text-6xl mb-3">{selectedGame.icon}</div>
              <h2 className="text-2xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                {selectedGame.name}
              </h2>
              <p className="text-gray-400 mt-2">Select your bet amount</p>
              <div className="mt-3 bg-slate-800 rounded-lg px-4 py-2 inline-flex items-center gap-2">
                <span className="text-sm text-gray-400">Your balance:</span>
                <span className="font-bold text-yellow-400">{balance.toFixed(2)} TON</span>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-3">
              {betAmounts.map((bet) => {
                const canAfford = balance >= bet.value
                return (
                  <button
                    key={bet.value}
                    onClick={() => canAfford && handleBetSelect(bet)}
                    disabled={!canAfford}
                    className={`group border-2 rounded-xl p-4 transition-all transform ${
                      canAfford 
                        ? 'bg-slate-800 hover:bg-slate-700 border-slate-700 hover:border-yellow-500 hover:scale-105 cursor-pointer' 
                        : 'bg-slate-900 border-slate-800 opacity-50 cursor-not-allowed'
                    }`}
                  >
                    <div className={`text-2xl font-bold mb-1 ${canAfford ? 'text-yellow-400' : 'text-gray-600'}`}>
                      {bet.value}
                    </div>
                    <div className="text-xs text-gray-400">TON</div>
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Matchmaking Modal */}
      {showMatchmaking && selectedGame && selectedBet && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border-2 border-cyan-500 rounded-2xl p-8 max-w-md w-full text-center relative">
            <button
              onClick={() => {
                setShowMatchmaking(false)
                setSelectedGame(null)
                setSelectedBet(null)
              }}
              className="absolute top-4 right-4 p-2 hover:bg-slate-800 rounded-lg transition-all"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="mb-6">
              <div className="text-6xl mb-4 animate-pulse">{selectedGame.icon}</div>
              <h2 className="text-2xl font-bold mb-2">{selectedGame.name}</h2>
              <div className="inline-flex items-center gap-2 bg-yellow-500/20 px-4 py-2 rounded-full">
                <Coins className="w-5 h-5 text-yellow-400" />
                <span className="text-xl font-bold text-yellow-400">{selectedBet.value} TON</span>
              </div>
            </div>

            <div className="mb-6">
              <Search className="w-16 h-16 text-cyan-400 mx-auto mb-4 animate-pulse" />
              <h3 className="text-xl font-bold mb-2 bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                Searching for opponent...
              </h3>
              <p className="text-gray-400">Finding a worthy challenger</p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => {
                  setShowMatchmaking(false)
                  setSelectedGame(null)
                  setSelectedBet(null)
                }}
                className="flex-1 px-6 py-3 bg-slate-800 hover:bg-slate-700 rounded-lg font-semibold transition-all"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Share Modal - Full Screen */}
      {showShareModal && (
        <div className="fixed inset-0 bg-slate-950 z-50 overflow-y-auto">
          <div className="min-h-screen">
            {/* Header */}
            <div className="sticky top-0 bg-slate-950/95 backdrop-blur border-b border-slate-800 z-10">
              <div className="px-4 py-4 flex items-center gap-4">
                <button
                  onClick={() => setShowShareModal(false)}
                  className="p-2 hover:bg-slate-800 rounded-lg transition-all"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
                <h2 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                  Invite Friends
                </h2>
              </div>
            </div>

            {/* Content */}
            <div className="px-4 py-6 max-w-2xl mx-auto">
              {/* Stats Cards */}
              <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-slate-900 border-2 border-cyan-500/30 rounded-xl p-4">
                  <Users className="w-8 h-8 text-cyan-400 mb-2" />
                  <div className="text-2xl font-bold text-cyan-400">{referralStats.referrals}</div>
                  <div className="text-sm text-gray-400">Friends Invited</div>
                </div>
                <div className="bg-slate-900 border-2 border-yellow-500/30 rounded-xl p-4">
                  <Gift className="w-8 h-8 text-yellow-400 mb-2" />
                  <div className="text-2xl font-bold text-yellow-400">{referralStats.earned} TON</div>
                  <div className="text-sm text-gray-400">Total Earned</div>
                </div>
              </div>

              {/* Referral Link */}
              <div className="bg-slate-900 border-2 border-slate-700 rounded-xl p-6 mb-6">
                <h3 className="font-bold text-lg mb-2">Your Referral Link</h3>
                <p className="text-sm text-gray-400 mb-4">Share this link with friends to earn rewards</p>
                
                <div className="bg-slate-800 rounded-lg p-4 mb-4 break-all">
                  <code className="text-cyan-400 text-sm">{referralStats.link}</code>
                </div>

                <button
                  onClick={handleCopyLink}
                  className="w-full px-6 py-3 bg-gradient-to-r from-cyan-500 to-blue-600 rounded-lg font-semibold hover:shadow-lg hover:shadow-cyan-500/50 transition-all flex items-center justify-center gap-2"
                >
                  <Copy className="w-5 h-5" />
                  Copy Link
                </button>
              </div>

              {/* Rewards Info */}
              <div className="bg-slate-900 border-2 border-purple-500/30 rounded-xl p-6">
                <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-purple-400" />
                  Referral Rewards
                </h3>
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-cyan-500/20 flex items-center justify-center flex-shrink-0">
                      <Check className="w-4 h-4 text-cyan-400" />
                    </div>
                    <div>
                      <div className="font-semibold text-cyan-400">Friend joins</div>
                      <div className="text-sm text-gray-400">Get 2 TON bonus instantly</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-500/20 flex items-center justify-center flex-shrink-0">
                      <Check className="w-4 h-4 text-blue-400" />
                    </div>
                    <div>
                      <div className="font-semibold text-blue-400">Friend plays first game</div>
                      <div className="text-sm text-gray-400">Get 10% of their bet amount</div>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-purple-500/20 flex items-center justify-center flex-shrink-0">
                      <Check className="w-4 h-4 text-purple-400" />
                    </div>
                    <div>
                      <div className="font-semibold text-purple-400">Lifetime earnings</div>
                      <div className="text-sm text-gray-400">Get 5% from all friend's games forever</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Profile Modal - Full Screen */}
      {showProfileModal && (
        <div className="fixed inset-0 bg-slate-950 z-50 overflow-y-auto">
          <div className="min-h-screen">
            {/* Header */}
            <div className="sticky top-0 bg-slate-950/95 backdrop-blur border-b border-slate-800 z-10">
              <div className="px-4 py-4 flex items-center gap-4">
                <button
                  onClick={() => setShowProfileModal(false)}
                  className="p-2 hover:bg-slate-800 rounded-lg transition-all"
                >
                  <ArrowLeft className="w-5 h-5" />
                </button>
                <h2 className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
                  Profile
                </h2>
              </div>
            </div>

            {/* Content */}
            <div className="px-4 py-6 max-w-2xl mx-auto">
              {/* User Info */}
              <div className="bg-slate-900 border-2 border-cyan-500/30 rounded-xl p-6 mb-6 text-center">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-cyan-500 to-blue-600 flex items-center justify-center text-4xl mx-auto mb-4">
                  {userProfile.avatar}
                </div>
                <h3 className="text-2xl font-bold mb-2">{userProfile.name}</h3>
                <div className="flex items-center justify-center gap-2 bg-slate-800 px-4 py-2 rounded-lg mb-4 max-w-xs mx-auto">
                  <Wallet className="w-4 h-4 text-cyan-400" />
                  <span className="text-sm text-gray-400">{formattedAddress}</span>
                  <button
                    onClick={handleCopyAddress}
                    className="p-1 hover:bg-slate-700 rounded transition-all"
                  >
                    <Copy className="w-3 h-3" />
                  </button>
                </div>
                <div className="flex items-center justify-center gap-2">
                  <Coins className="w-5 h-5 text-yellow-400" />
                  <span className="text-xl font-bold">{balance.toFixed(2)} TON</span>
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="bg-slate-900 border-2 border-slate-700 rounded-xl p-4 text-center">
                  <Gamepad2 className="w-6 h-6 text-cyan-400 mx-auto mb-2" />
                  <div className="text-xl font-bold">{userStats.gamesPlayed}</div>
                  <div className="text-xs text-gray-400">Games</div>
                </div>
                <div className="bg-slate-900 border-2 border-slate-700 rounded-xl p-4 text-center">
                  <Trophy className="w-6 h-6 text-yellow-400 mx-auto mb-2" />
                  <div className="text-xl font-bold">{userStats.winRate}%</div>
                  <div className="text-xs text-gray-400">Win Rate</div>
                </div>
                <div className="bg-slate-900 border-2 border-slate-700 rounded-xl p-4 text-center">
                  <Coins className="w-6 h-6 text-green-400 mx-auto mb-2" />
                  <div className="text-xl font-bold">{userStats.totalEarned}</div>
                  <div className="text-xs text-gray-400">Earned</div>
                </div>
              </div>

              {/* Game History */}
              <div className="bg-slate-900 border-2 border-slate-700 rounded-xl p-6 mb-6">
                <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-cyan-400" />
                  Recent Games
                </h3>
                <div className="space-y-3">
                  {userStats.gameHistory.map((game) => {
                    const gameData = getGameData(game.game)
                    return (
                      <div key={game.id} className="flex items-center justify-between bg-slate-800 rounded-lg p-3">
                        <div className="flex items-center gap-3">
                          <div className="text-2xl">{gameData.icon}</div>
                          <div>
                            <div className="font-semibold text-sm">{gameData.name}</div>
                            <div className="text-xs text-gray-400">{game.date}</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm text-gray-400">Bet: {game.bet} TON</div>
                          <div className={`font-bold flex items-center gap-1 justify-end ${game.result === 'win' ? 'text-green-400' : 'text-red-400'}`}>
                            {game.result === 'win' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                            {game.amount > 0 ? '+' : ''}{game.amount} TON
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Disconnect Button */}
              <button
                onClick={handleDisconnectWallet}
                className="w-full px-6 py-3 bg-red-500/20 border-2 border-red-500 text-red-400 rounded-lg font-semibold hover:bg-red-500/30 transition-all"
              >
                Disconnect Wallet
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Game Result Modal */}
      {gameResult && (
        <GameResultModal 
          result={gameResult.result}
          amount={gameResult.amount}
          onClose={handleCloseResult}
        />
      )}
    </div>
  )
}

export default TBoardApp