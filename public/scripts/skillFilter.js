document.addEventListener('DOMContentLoaded', () => {
    // APIのエンドポイント
    // nginx経由でアクセスするため相対パスを使用
    const API_BASE_URL = '/api/v1';

    // スキルをフェッチしてHTMLに描画する
    const loadSkills = async () => {
        const container = document.querySelector('.skill-filter');
        if (!container) return;

        try {
            const response = await fetch(`${API_BASE_URL}/skills`);
            if (!response.ok) {
                throw new Error('Failed to fetch skills');
            }

            const data = await response.json(); // { skills: [...] }

            // <h3>Skills</h3> の下にコンテナを追加
            const listContainer = document.createElement('div');
            listContainer.className = 'skill-checkbox-list';

            // スキルの数だけチェックボックスを生成
            data.skills.forEach(skill => {
                const label = document.createElement('label');
                label.innerHTML = `
                    <input type="checkbox" name="skill" value="${skill.id}">
                    ${escapeHTML(skill.name)}
                `;
                listContainer.appendChild(label);
            });

            container.appendChild(listContainer);

        } catch (error) {
            console.error('Error loading skills:', error);
            container.innerHTML += '<p>Error loading skills.</p>';
        }
    };

    // XSS防止用のシンプルなHTMLエスケープ
    const escapeHTML = (str) => {
        return str.replace(/[&<>"']/g, (match) => {
            const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
            return map[match];
        });
    };

    loadSkills();
});