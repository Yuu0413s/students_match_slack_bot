const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const cors = require('cors');
const app = express();
const PORT = 3001; // フロントエンド(3000)と被らないポート

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
    console.log(`検証リクエスト受信: ${email}`);

  // 特例：管理者テストアカウント
    if (email === "test_admin@test.com") {
    return res.json({ role: 'ADMIN', name: "テスト管理者" });
    }

  // seniorsテーブルから検索
  const sql = `SELECT * FROM seniors WHERE email = ?`;

    db.get(sql, [email], (err, row) => {
    if (err) {
        console.error(err);
        return res.status(500).json({ error: 'DBエラー' });
    }

    if (row) {
      // 見つかったら「SENPAI」として返す
      // ※row.name が無い場合は '名無し' になります
        return res.json({
            role: 'SENPAI',
            name: row.name || '名無し先輩'
        });
    } else {
      // 見つからない場合
        return res.status(401).json({ error: 'ユーザー未登録' });
    }
    });
});

app.listen(PORT, () => {
    console.log(`Backend Server running on http://localhost:${PORT}`);
});