document.addEventListener("DOMContentLoaded", () => {
  // 1. タブのリンク要素と、コンテンツ要素を取得
  const tabs = document.querySelectorAll(".tabs a");
  const contentSections = document.querySelectorAll(".tab-content");

  // 2. すべてのタブにクリックイベントリスナーを設定
  tabs.forEach((tab) => {
    tab.addEventListener("click", (e) => {
      e.preventDefault(); // リンクのデフォルト動作（ページ遷移）を停止

      // クリックされたタブ名を取得 (例: "Overview", "Projects")
      const targetTabName = tab.textContent.trim();
      const targetContentId = targetTabName.toLowerCase() + "-content"; // "overview-content"

      // --- A. タブのアクティブ状態を切り替える ---

      // 現在アクティブなタブから active クラスを削除
      tabs.forEach((t) => t.classList.remove("active"));

      // クリックされたタブに active クラスを追加
      tab.classList.add("active");

      // --- B. コンテンツの表示/非表示を切り替える ---

      contentSections.forEach((content) => {
        // すべてのコンテンツを非表示にする
        content.classList.remove("active");
        content.classList.add("hidden");

        // クリックされたタブに対応するコンテンツのみを表示
        if (content.id === targetContentId) {
          content.classList.remove("hidden");
          content.classList.add("active");
        }
      });
    });
  });
});
