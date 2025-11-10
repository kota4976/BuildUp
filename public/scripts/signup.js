// ----------------------------------------------------------------
// フォーム検証と処理のロジック (デモ用)
// ----------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('signup-form');
    const submitBtn = document.getElementById('submit-btn');
    const emailInput = document.getElementById('email');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm-password');
    const termsCheckbox = document.getElementById('terms');
    
    // パスワードの一致、利用規約、および必須フィールドのチェックをリアルタイムで行う関数
    function validateForm() {
        const passwordsMatch = passwordInput.value === confirmPasswordInput.value && passwordInput.value.length >= 8;
        const termsAgreed = termsCheckbox.checked;
        const emailValid = emailInput.value.trim() !== '';

        if (passwordsMatch && termsAgreed && emailValid) {
            submitBtn.disabled = false;
        } else {
            submitBtn.disabled = true;
        }
    }
    
    // 入力/変更イベントにバリデーションを適用
    emailInput.addEventListener('input', validateForm);
    passwordInput.addEventListener('input', validateForm);
    confirmPasswordInput.addEventListener('input', validateForm);
    termsCheckbox.addEventListener('change', validateForm);

    // 初期ロード時のバリデーション
    validateForm(); 

    // フォーム送信時の処理 (実際にはAPIコールが行われます)
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        if (submitBtn.disabled) {
            console.error("入力内容を確認してください。");
            alertUserMessage('すべての項目を正しく入力し、利用規約に同意してください。', 'error');
            return;
        }
        
        // デモ用: 成功メッセージをログに表示
        console.log('サインアップデータ:', {
            name: document.getElementById('name').value,
            email: document.getElementById('email').value,
            password: passwordInput.value
        });

        // 成功したことをユーザーに伝えるフィードバックを表示
        alertUserMessage('アカウントが正常に作成されました！', 'success');
        
        // 実際にはここでページ遷移やAPIコールを行う
    });

    // カスタムアラート表示関数 (alert()の代わり)
    function alertUserMessage(message, type) {
        const existingAlert = document.querySelector('.custom-alert');
        if (existingAlert) existingAlert.remove();

        const alertDiv = document.createElement('div');
        alertDiv.className = `custom-alert fixed top-5 left-1/2 transform -translate-x-1/2 p-4 rounded-lg shadow-xl text-sm font-medium z-50 opacity-0 transition-all duration-300`;
        alertDiv.textContent = message;

        if (type === 'success') {
            alertDiv.classList.add('bg-green-100', 'text-green-800', 'border', 'border-green-300');
        } else if (type === 'error') {
            alertDiv.classList.add('bg-red-100', 'text-red-800', 'border', 'border-red-300');
        } else {
             alertDiv.classList.add('bg-yellow-100', 'text-yellow-800', 'border', 'border-yellow-300');
        }
        
        document.body.appendChild(alertDiv);
        
        // フェードイン
        setTimeout(() => alertDiv.classList.add('opacity-100', 'scale-100'), 10);

        // 3秒後にフェードアウト
        setTimeout(() => {
            alertDiv.classList.remove('opacity-100', 'scale-100');
            alertDiv.classList.add('opacity-0', 'scale-90');
            setTimeout(() => alertDiv.remove(), 300); // アニメーション後に削除
        }, 3000);
    }
    
    // ソーシャルログインボタンのクリックイベント (デモ用)
    document.getElementById('github-login-btn').addEventListener('click', (e) => {
        e.preventDefault();
        alertUserMessage(`GitHubでのサインアップ処理を開始します... (デモ)`, 'info');
    });
});