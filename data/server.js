const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const app = express();
const PORT = 3001;

// ミドルウェア設定
app.use(cors());
app.use(express.json());

// データベース接続
const db = new sqlite3.Database('./muds_matching.db', (err) => {
    if (err) {
        console.error('DB接続エラー:', err.message);
    } else {
        console.log('muds_matching.db に接続しました');
    }
});

// ログイン検証用API
app.post('/api/verify-user', (req, res) => {
    const { email } = req.body;

  // 管理者テストアカウントの特例（必要であればサーバー側でも定義）
    if (email === "y.shibata0820@gmail.com") {
    return res.json({ role: 'ADMIN', name: "テスト管理者" });
    }

  // seniorsテーブルからメールアドレスで検索
  const sql = `SELECT * FROM seniors WHERE email = ?`;

    db.get(sql, [email], (err, row) => {
        if (err) {
            console.error(err);
        return res.status(500).json({ error: 'DBエラー' });
    }

    if (row) {
      // ユーザーが見つかった場合
        return res.json({
            role: 'SENIOR',
            name: row.name || '名無し先輩'
        });
    } else {
      // 見つからなかった場合
        return res.status(401).json({ error: 'ユーザーが登録されていません' });
    }
    });
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});