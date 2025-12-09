from sqlalchemy import (
    Column, BigInteger, String, DECIMAL, TIMESTAMP, Boolean, Text,
    Integer, ForeignKey, Index
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
    balance_ton = Column(DECIMAL(18, 9), default=0)
    referral_link = Column(String(255), unique=True, nullable=False, index=True)
    referred_by = Column(BigInteger, ForeignKey("users.id"), index=True)
    referral_rate = Column(DECIMAL(5, 2), default=50.00)
    referral_earnings_ton = Column(DECIMAL(18, 9), default=0)
    total_games_played = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)
    total_won_ton = Column(DECIMAL(18, 9), default=0)
    total_staked_ton = Column(DECIMAL(18, 9), default=0)
    total_rake_paid_ton = Column(DECIMAL(18, 9), default=0)
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


class Game(Base):
    __tablename__ = "games"

    id = Column(BigInteger, primary_key=True, index=True)
    game_type = Column(String(20), nullable=False)
    mode = Column(String(20), nullable=False)
    player1_id = Column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    player2_id = Column(BigInteger, ForeignKey("users.id"), index=True)
    player1_color = Column(String(10))
    stake_amount_ton = Column(DECIMAL(18, 9), default=0)
    currency = Column(String(10), default="TON")
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