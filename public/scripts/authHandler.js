// scripts/authHandler.js の中身をこれに丸ごと置き換える

document.addEventListener('DOMContentLoaded', () => {

    // ▼▼▼ デバッグ用ログ ▼▼▼
    console.log('--- authHandler.js が実行されました ---');
    console.log('現在のページ:', window.location.pathname);

    const hash = window.location.hash.substring(1);
    if (!hash) {
        // ハッシュがない場合
        console.log('URLにハッシュ(#)が見つかりません。処理を終了します。');
        return;
    }

    // ハッシュがある場合
    console.log('URLハッシュが見つかりました:', hash);

    try {
        const params = new URLSearchParams(hash);
        const token = params.get('access_token');

        if (token) {
            console.log('★★★ トークンを発見！ localStorageに保存します。★★★');
            localStorage.setItem('access_token', token);
            history.replaceState(null, '', window.location.pathname);
            console.log('保存完了。URLをクリーンアップしました。');
        } else {
            console.error('エラー: ハッシュはありますが、access_token が見つかりません。');
        }
    } catch (error) {
        console.error('トークン処理中にエラー:', error);
    }
});