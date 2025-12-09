-- ============================================
-- Users table
-- ============================================
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    ton_wallet_address VARCHAR(48) UNIQUE,
    wallet_connected_at TIMESTAMP,
    balance_ton DECIMAL(18,9) DEFAULT 0,
    referral_link VARCHAR(255) UNIQUE NOT NULL,
    referred_by BIGINT REFERENCES users(id),
    referral_rate DECIMAL(5,2) DEFAULT 50.00,
    referral_earnings_ton DECIMAL(18,9) DEFAULT 0,
    total_games_played INT DEFAULT 0,
    total_wins INT DEFAULT 0,
    total_losses INT DEFAULT 0,
    total_won_ton DECIMAL(18,9) DEFAULT 0,
    total_staked_ton DECIMAL(18,9) DEFAULT 0,
    total_rake_paid_ton DECIMAL(18,9) DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_active_at TIMESTAMP,
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    language VARCHAR(10) DEFAULT 'ru',
    settings_json JSONB
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_wallet ON users(ton_wallet_address);
CREATE INDEX idx_users_referral_link ON users(referral_link);
CREATE INDEX idx_users_referred_by ON users(referred_by);

-- ============================================
-- Games table
-- ============================================
CREATE TABLE games (
    id BIGSERIAL PRIMARY KEY,
    game_type VARCHAR(20) NOT NULL,
    mode VARCHAR(20) NOT NULL,
    player1_id BIGINT NOT NULL REFERENCES users(id),
    player2_id BIGINT REFERENCES users(id),
    player1_color VARCHAR(10),
    stake_amount_ton DECIMAL(18,9) DEFAULT 0,
    currency VARCHAR(10) DEFAULT 'TON',
    winner_id BIGINT REFERENCES users(id),
    result VARCHAR(20),
    rake_amount DECIMAL(18,9) DEFAULT 0,
    escrow_tx_hash VARCHAR(100),
    game_state_json JSONB,
    final_state_json JSONB,
    move_count INT DEFAULT 0,
    duration_seconds INT,
    started_at TIMESTAMP,
    finished_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    tournament_id BIGINT,
    is_ranked BOOLEAN DEFAULT TRUE,
    inline_message_id VARCHAR(255),
    chat_id BIGINT
);

CREATE INDEX idx_games_player1 ON games(player1_id);
CREATE INDEX idx_games_player2 ON games(player2_id);
CREATE INDEX idx_games_type_result ON games(game_type, result);
CREATE INDEX idx_games_created_at ON games(created_at);
CREATE INDEX idx_games_escrow_tx ON games(escrow_tx_hash);

-- ============================================
-- Referrals table
-- ============================================
CREATE TABLE referrals (
    id BIGSERIAL PRIMARY KEY,
    referrer_id BIGINT NOT NULL REFERENCES users(id),
    referred_id BIGINT NOT NULL REFERENCES users(id),
    referral_link_used VARCHAR(255),
    referred_at TIMESTAMP DEFAULT NOW(),
    first_game_at TIMESTAMP,
    first_stake_at TIMESTAMP,
    total_earned_from_referee_ton DECIMAL(18,9) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(referrer_id, referred_id)
);

CREATE INDEX idx_referrals_referrer ON referrals(referrer_id);
CREATE INDEX idx_referrals_referred ON referrals(referred_id);
CREATE INDEX idx_referrals_active ON referrals(referrer_id, is_active);