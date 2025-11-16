class BuildUpHeader extends HTMLElement {
    constructor() {
        super();
        // シャドウDOMを作成し、スタイルとHTMLを完全にカプセル化（隔離）します
        this.attachShadow({ mode: 'open' });
        
        // ユーザー提供のHTMLとCSSを統合し、テンプレートを設定します
        this.shadowRoot.innerHTML = `
            <style>
                /* --- CSS: コンポーネントの見た目を定義 --- */
                :host {
                    display: block;
                    position: sticky; /* スクロールしても固定 */
                    top: 0;
                    z-index: 1000;
                }
                
                .navbar {
                    background-color: #ffffff;
                    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
                    /* ヘッダーの中央寄せを容易にするために、display: flexを追加 */
                    display: flex; 
                    justify-content: center;
                    padding: 15px 40px;
                }

                .navbar-container {
                    max-width: 1200px;
                    width: 100%; /* 幅を確実に取る */
                    margin: 0 auto;
                    display: flex;
                    /* 今回は右側に要素がないため、左寄せにするか、justify-contentを調整 */
                    justify-content: flex-start; 
                    align-items: center;
                }

                .nav-left {
                    display: flex;
                    align-items: center;
                }

                .logo {
                    text-decoration: none;
                    margin-right: 30px;
                }
                        
                /* ロゴ画像用のCSS */
                .logo-img { 
                    /* ユーザー指定の画像サイズに設定 */
                    height: 35px; 
                    width: auto;
                    display: block;
                }

                .nav-menu {
                    /* ロゴとメニューの間隔 */
                    margin-left: 40px; 
                    display: flex;
                    gap: 30px; /* メニュー項目間のスペース */
                }
                
                .nav-link {
                    text-decoration: none;
                    color: #555;
                    font-weight: 500;
                    font-size: 0.95rem; /* 15.2px */
                    padding: 5px 0;
                    transition: color 0.3s ease;
                }
                
                .nav-link:hover {
                    color: #007bff;
                    border-bottom: 2px solid #007bff; /* ホバーエフェクトを追加 */
                }
                
                /* --- レスポンシブ対応 (モバイル向け) --- */
                /* 右側にボタンがないため、nav-menuを非表示にする閾値を調整 */
                @media (max-width: 600px) {
                     .navbar {
                        padding: 15px 20px;
                    }
                    .nav-menu {
                        /* モバイルではメニューを非表示に */
                        display: none;
                    }
                    .navbar-container {
                        /* 右寄せにするためにスペースを空ける */
                        justify-content: space-between; 
                    }
                    /* モバイル用トグルボタン（存在しないが将来のために）*/
                     .menu-toggle {
                        display: block; 
                        background: none;
                        border: none;
                        font-size: 24px;
                        cursor: pointer;
                        color: #555;
                        padding: 0;
                    }
                }

            </style>

            <!-- HTML構造 (nav-left部分のみ) -->
            <header class="navbar">
                <div class="navbar-container">
                    <div class="nav-left">
                        <a href="/public/index.html" class="logo">
                            <!-- 💡 画像パスは、親ドキュメントからの相対パス -->
                            <img src="images/BuildUp-logo.jpg" alt="BuildUp Logo" class="logo-img">
                        </a>
                        <nav class="nav-menu">
                            <a href="/public/projectReserch.html" class="nav-link">プロジェクト</a>
                            <a href="/public/chat.html" class="nav-link">メッセージ</a>
                            <a href="#" class="nav-link">応募管理</a>
                        </nav>
                    </div>
                    <!-- モバイル用トグルボタン (将来的拡張のため設置) -->
                    <button class="menu-toggle" style="display: none;"><i class="fas fa-bars"></i></button>
                </div>
            </header>
        `;
    }
}

// 💡 カスタム要素として登録: HTMLで <build-up-header> と呼び出せるようになります
customElements.define('build-up-header', BuildUpHeader);