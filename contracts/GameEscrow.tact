// contracts/GameEscrow.tact
contract GameEscrow {

    const FEE_BPS: Int = 500; ;; 5%
    const BPS_DENOM: Int = 10_000;

    owner: Address;

    balances: map<Address, Int>;
    matches: map<Int, Match>;
    nextMatchId: Int;

    struct Match {
        player1: Address;
        player2: Address?;
        stake: Int;
        finished: Bool;
    }

    init(owner: Address) {
        self.owner = owner;
        self.nextMatchId = 0;
    }

    ;; =========================
    ;;  Create match (player A)
    ;; =========================
    receive("create_match") {
        require(msg.value > 0, "Stake required");

        let id = self.nextMatchId;
        self.nextMatchId += 1;

        self.matches[id] = Match{
            player1: msg.sender,
            player2: null(),
            stake: msg.value,
            finished: false
        };
    }

    ;; =========================
    ;;  Join match (player B)
    ;; =========================
    receive("join_match", matchId: Int) {
        let m = self.matches[matchId];
        require(m.finished == false, "Match finished");
        require(m.player2 == null(), "Already joined");
        require(msg.value == m.stake, "Invalid stake");

        m.player2 = msg.sender;
        self.matches[matchId] = m;
    }

    ;; =========================
    ;;  Finish match (backend)
    ;; =========================
    receive("finish_match", matchId: Int, winner: Address) {
        require(msg.sender == self.owner, "Only owner");

        let m = self.matches[matchId];
        require(m.finished == false, "Already finished");
        require(m.player2 != null(), "Match not ready");

        let total = m.stake * 2;
        let fee = total * FEE_BPS / BPS_DENOM;
        let reward = total - fee;

        self.balances[winner] += reward;
        send(self.owner, fee);

        m.finished = true;
        self.matches[matchId] = m;
    }

    ;; =========================
    ;;  Withdraw winnings
    ;; =========================
    receive("withdraw", amount: Int) {
        let bal = self.balances[msg.sender];
        require(amount > 0, "Invalid amount");
        require(bal >= amount, "Insufficient balance");

        self.balances[msg.sender] = bal - amount;
        send(msg.sender, amount);
    }

    ;; =========================
    ;;  Getter
    ;; =========================
    get fun balanceOf(addr: Address): Int {
        return self.balances[addr];
    }
}
