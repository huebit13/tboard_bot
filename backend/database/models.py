from sqlalchemy import (
    Column, BigInteger, String, DECIMAL, TIMESTAMP, Boolean, Text,
    Integer, ForeignKey, Index, Date
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    ton_wallet_address = Column(String(48), unique=True, index=True)
    wallet_connected_at = Column(TIMESTAMP)
    
    # Балансы
    balance_ton = Column(DECIMAL(18, 9), default=0)
    balance_coins = Column(DECIMAL(18, 2), default=0)  # ✅ НОВОЕ: внутренняя валюта
    
    # Реферальная система
    referral_link = Column(String(255), unique=True, nullable=False, index=True)
    referred_by = Column(BigInteger, ForeignKey("users.id"), index=True)
    referral_rate = Column(DECIMAL(5, 2), default=40.00)
    referral_earnings_ton = Column(DECIMAL(18, 9), default=0)
    
    # Статистика игр
    total_games_played = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    
    # Статистика по TON
    total_won_ton = Column(DECIMAL(18, 9), default=0)
    total_staked_ton = Column(DECIMAL(18, 9), default=0)
    total_rake_paid_ton = Column(DECIMAL(18, 9), default=0)
    
    # ✅ НОВОЕ: Статистика по коинам
    total_won_coins = Column(DECIMAL(18, 2), default=0)
    total_staked_coins = Column(DECIMAL(18, 2), default=0)
    
    # Системные поля
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    last_active_at = Column(TIMESTAMP)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(Text)
    language = Column(String(10), default="ru")
    settings_json = Column(JSONB)

    # Relationships
    referrer = relationship("User", remote_side=[id], backref="referrals")
    games_as_player1 = relationship("Game", foreign_keys="Game.player1_id", back_populates="player1")
    games_as_player2 = relationship("Game", foreign_keys="Game.player2_id", back_populates="player2")
    games_won = relationship("Game", foreign_keys="Game.winner_id", back_populates="winner")
    
    referrals_made = relationship(
        "Referral",
        foreign_keys="Referral.referrer_id",
        back_populates="referrer"
    )
    referred_by_relation = relationship(
        "Referral",
        foreign_keys="Referral.referred_id",
        back_populates="referred"
    )
    
    # ✅ НОВОЕ: связи для внутренней валюты
    coin_transactions = relationship("CoinTransaction", back_populates="user")
    daily_rewards = relationship("DailyReward", back_populates="user")


class Game(Base):
    __tablename__ = "games"

    id = Column(BigInteger, primary_key=True, index=True)
    game_type = Column(String(20), nullable=False)
    mode = Column(String(20), nullable=False)
    player1_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    player2_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    player1_color = Column(String(10))
    
    # ✅ ИЗМЕНЕНО: поддержка обеих валют
    stake_amount_ton = Column(DECIMAL(18, 9), default=0)
    stake_amount_coins = Column(DECIMAL(18, 2), default=0)  # ✅ НОВОЕ
    currency = Column(String(10), default="TON")  # "TON" или "COINS"
    
    winner_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    result = Column(String(20))
    rake_amount = Column(DECIMAL(18, 9), default=0)
    escrow_tx_hash = Column(String(100), index=True)
    game_state_json = Column(JSONB)
    final_state_json = Column(JSONB)
    move_count = Column(Integer, default=0)
    duration_seconds = Column(Integer)
    started_at = Column(TIMESTAMP)
    finished_at = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    tournament_id = Column(BigInteger)
    is_ranked = Column(Boolean, default=True)
    inline_message_id = Column(String(255))
    chat_id = Column(BigInteger)

    # Relationships
    player1 = relationship("User", foreign_keys=[player1_id], back_populates="games_as_player1")
    player2 = relationship("User", foreign_keys=[player2_id], back_populates="games_as_player2")
    winner = relationship("User", foreign_keys=[winner_id], back_populates="games_won")

    # Composite index
    __table_args__ = (
        Index('idx_games_type_result', 'game_type', 'result'),
    )


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(BigInteger, primary_key=True, index=True)
    referrer_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    referred_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    referral_link_used = Column(String(255))
    referred_at = Column(TIMESTAMP, server_default=func.now())
    first_game_at = Column(TIMESTAMP)
    first_stake_at = Column(TIMESTAMP)
    total_earned_from_referee_ton = Column(DECIMAL(18, 9), default=0)
    is_active = Column(Boolean, default=True, index=True)

    # Relationships
    referrer = relationship("User", foreign_keys=[referrer_id], back_populates="referrals_made")
    referred = relationship("User", foreign_keys=[referred_id], back_populates="referred_by_relation")

    # Unique constraint
    __table_args__ = (
        Index('idx_referrals_active', 'referrer_id', 'is_active'),
    )


class Lobby(Base):
    __tablename__ = "lobbies"

    id = Column(Integer, primary_key=True, index=True)
    game_type = Column(String(20), nullable=False)
    
    # ✅ ИЗМЕНЕНО: поддержка обеих валют
    stake = Column(DECIMAL(18, 9), nullable=False)  # Универсальное поле
    currency = Column(String(10), default="TON")  # ✅ НОВОЕ: "TON" или "COINS"
    
    password_hash = Column(String(128), nullable=True)
    creator_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    joiner_id = Column(BigInteger, ForeignKey("users.id"), nullable=True, index=True)
    status = Column(String(20), default="waiting")
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    expires_at = Column(TIMESTAMP)

    # Relationships
    creator = relationship("User", foreign_keys=[creator_id])
    joiner = relationship("User", foreign_keys=[joiner_id])


# ✅ НОВАЯ ТАБЛИЦА: История транзакций внутренней валюты
class CoinTransaction(Base):
    __tablename__ = "coin_transactions"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(DECIMAL(18, 2), nullable=False)
    transaction_type = Column(String(50), nullable=False, index=True)
    # Типы: 'game_win', 'game_stake', 'daily_bonus', 'referral_bonus', 'admin_gift'
    related_game_id = Column(BigInteger, ForeignKey("games.id"), nullable=True)
    description = Column(Text)
    balance_before = Column(DECIMAL(18, 2), nullable=False)
    balance_after = Column(DECIMAL(18, 2), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="coin_transactions")
    game = relationship("Game")


# ✅ НОВАЯ ТАБЛИЦА: Ежедневные награды
class DailyReward(Base):
    __tablename__ = "daily_rewards"

    id = Column(BigInteger, primary_key=True, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    reward_date = Column(Date, nullable=False, index=True)
    coins_earned = Column(DECIMAL(18, 2), nullable=False)
    streak_days = Column(Integer, default=1)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="daily_rewards")

    __table_args__ = (
        Index('idx_daily_rewards_user_date', 'user_id', 'reward_date', unique=True),
    )