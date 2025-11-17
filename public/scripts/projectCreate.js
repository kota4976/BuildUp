document.addEventListener('DOMContentLoaded', () => {

    // --- 要素の取得 ---
    const createProjectBtn = document.querySelector('.create-project-btn');
    const modal = document.getElementById('create-project-modal');
    const closeBtn = modal.querySelector('.close-btn');
    const form = document.getElementById('create-project-form');
    const skillsContainer = document.getElementById('skills-container');
    const addSkillBtn = document.getElementById('add-skill-btn');
    const formError = document.getElementById('form-error');

    // --- モーダル表示 ---
    createProjectBtn.addEventListener('click', () => {
        modal.style.display = 'block';
    });

    // --- モーダル非表示 (3パターン) ---
    // 1. 閉じるボタン
    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });
    // 2. モーダル外のクリック
    window.addEventListener('click', (e) => {
        if (e.target == modal) {
            modal.style.display = 'none';
        }
    });
    // 3. Escapeキー
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            modal.style.display = 'none';
        }
    });


    // --- スキル入力欄の動的追加 ---
    addSkillBtn.addEventListener('click', () => {
        const skillRow = document.createElement('div');
        skillRow.className = 'skill-input-row';
        skillRow.innerHTML = `
            <input type="number" class="skill-id" placeholder="Skill ID" required>
            <input type="number" class="skill-level" placeholder="Level (1-5)" min="1" max="5" required>
            <button type="button" class="remove-skill-btn">Remove</button>
        `;
        skillsContainer.appendChild(skillRow);
    });

    // --- スキル入力欄の削除 (イベント移譲) ---
    skillsContainer.addEventListener('click', (e) => {
        if (e.target.classList.contains('remove-skill-btn')) {
            e.target.parentElement.remove();
        }
    });


    // --- フォーム送信処理 ---
    form.addEventListener('submit', async (e) => {
        e.preventDefault(); // デフォルトのフォーム送信をキャンセル
        formError.style.display = 'none'; // エラーメッセージを隠す

        // 1. フォームからデータを取得
        const title = document.getElementById('project-title').value;
        const description = document.getElementById('project-description').value;

        // 2. スキルデータを取得
        const required_skills = [];
        const skillRows = skillsContainer.querySelectorAll('.skill-input-row');

        for (const row of skillRows) {
            const skill_id = parseInt(row.querySelector('.skill-id').value, 10);
            const required_level = parseInt(row.querySelector('.skill-level').value, 10);

            if (!skill_id || !required_level || required_level < 1 || required_level > 5) {
                formError.textContent = 'Invalid skill data. Please check Skill ID and Level (1-5).';
                formError.style.display = 'block';
                return; // 送信中断
            }
            required_skills.push({ skill_id, required_level });
        }

        if (required_skills.length === 0) {
            formError.textContent = 'At least one skill is required.';
            formError.style.display = 'block';
            return; // 送信中断
        }

        // 3. APIリクエストのペイロードを作成
        const payload = {
            title,
            description,
            required_skills
        };

        // 4. 認証トークンを取得 (ログイン機能が実装されている前提)
        //    (トークンは localStorage や httpOnly cookie から取得)
        const token = localStorage.getItem('access_token');
        if (!token) {
            formError.textContent = 'You must be logged in to create a project.';
            formError.style.display = 'block';
            return;
        }

        // 5. APIにPOSTリクエストを送信
        try {
            // ★★ 注意: エンドポイントのパスは実際のものに合わせてください
            //    (例: /api/v1/projects)
            const API_BASE_URL = 'http://localhost:8080/api/v1';

            // ▼▼▼ fetchのURLを修正 ▼▼▼
            const response = await fetch(`http://localhost:8080/api/v1/projects`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(payload)
            });

            if (response.status === 201) {
                // 成功
                alert('Project created successfully!');
                modal.style.display = 'none'; // モーダルを閉じる
                form.reset(); // フォームをリセット
                skillsContainer.innerHTML = ''; // スキル欄を空にする
                // ここでプロジェクト一覧を再読み込みする関数を呼ぶと尚良い
                // location.reload(); // (一番簡単な方法)
            } else {
                // 失敗
                const errorData = await response.json();
                formError.textContent = `Error: ${errorData.detail || response.statusText}`;
                formError.style.display = 'block';
            }
        } catch (error) {
            console.error('Error creating project:', error);
            formError.textContent = 'An unexpected error occurred. Please try again.';
            formError.style.display = 'block';
        }
    });
});