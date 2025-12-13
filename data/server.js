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

// ==========================================
// 認証・ユーザー判定 API
// ==========================================

// 1. ログイン検証用API
app.post('/api/verify-user', (req, res) => {
    const { email } = req.body;

    // 管理者テストアカウントの特例
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
                name: row.last_name ? `${row.last_name} ${row.first_name}` : '名無し先輩'
            });
        } else {
            // 見つからなかった場合
            return res.status(401).json({ error: 'ユーザーが登録されていません' });
        }
    });
});

// ==========================================
// 先輩 (Seniors) 関連 API
// ==========================================

// 2. 先輩個人データ取得用API
app.get('/api/seniors/:email', (req, res) => {
    const { email } = req.params;
    const sql = `SELECT * FROM seniors WHERE email = ?`;

    db.get(sql, [email], (err, row) => {
        if (err) {
            console.error(err);
            return res.status(500).json({ error: 'DBエラー' });
        }
        if (!row) {
            return res.status(404).json({ error: 'データが見つかりません' });
        }
        res.json(row);
    });
});

// 3. 全員取得用API（管理者用）
app.get('/api/seniors', (req, res) => {
    const sql = `SELECT * FROM seniors`;

    db.all(sql, [], (err, rows) => {
        if (err) {
            console.error(err);
            return res.status(500).json({ error: 'DBエラー' });
        }
        res.json(rows);
    });
});

// 4. 先輩データの更新用API (編集機能)
app.put('/api/seniors/:id', (req, res) => {
    const { id } = req.params;
    const {
        last_name, first_name, grade, department,
        internship_experience,
        availability_status
    } = req.body;

    const sql = `
        UPDATE seniors
        SET last_name = ?,
            first_name = ?,
            grade = ?,
            department = ?,
            internship_experience = ?,
            availability_status = ?
        WHERE id = ?
    `;

    db.run(sql, [
        last_name,
        first_name,
        grade,
        department,
        internship_experience,
        availability_status,
        id
    ], function(err) {
        if (err) {
            console.error(err);
            return res.status(500).json({ error: '更新失敗' });
        }
        res.json({ message: '更新成功', changes: this.changes });
    });
});

// ==========================================
// 後輩 (Juniors) 関連 API
// ==========================================

// 5. 後輩全員取得用API（管理者用）
app.get('/api/juniors', (req, res) => {
    const sql = `SELECT * FROM juniors`;

    db.all(sql, [], (err, rows) => {
        if (err) {
            console.error("後輩データ取得エラー:", err);
            return res.status(500).json({ error: 'DBエラー: 後輩データの取得に失敗しました' });
        }
        res.json(rows);
    });
});

// 6. 後輩データの更新用API
app.put('/api/juniors/:id', (req, res) => {
    const { id } = req.params;
    const {
        student_id,
        last_name,
        first_name,
        grade
    } = req.body;

    const sql = `
        UPDATE juniors
        SET student_id = ?,
            last_name = ?,
            first_name = ?,
            grade = ?
        WHERE id = ?
    `;

    db.run(sql, [
        student_id,
        last_name,
        first_name,
        grade,
        id
    ], function(err) {
        if (err) {
            console.error("後輩データ更新エラー:", err);
            return res.status(500).json({ error: '更新失敗' });
        }
        res.json({ message: '更新成功', changes: this.changes });
    });
});

// ==========================================
// サーバー起動
// ==========================================
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});