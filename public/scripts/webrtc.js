/**
 * WebRTC通話機能
 * 音声通話とビデオ通話をサポート
 */

// WebRTC設定
const rtcConfiguration = {
  iceServers: [
    { urls: "stun:stun.l.google.com:19302" },
    { urls: "stun:stun1.l.google.com:19302" },
    { urls: "stun:stun2.l.google.com:19302" },
  ],
};

// WebRTC接続
let peerConnection = null;
let localStream = null;
let remoteStream = null;
let signalingWebSocket = null;
let isVideoCall = true;
let isMuted = false;
let isVideoDisabled = false;
let isScreenSharing = false;
let screenStream = null;
let callStartTime = null;
let callDurationInterval = null;
let currentConversationId = null;
let currentPartnerId = null;
let currentPartnerName = null;
// ICE候補のキュー（ピア接続が作成される前に到着した候補を保存）
let pendingIceCandidates = [];

// WebRTCマネージャークラス
export class WebRTCManager {
  constructor() {
    this.setupEventListeners();
  }

  /**
   * イベントリスナーの設定
   */
  setupEventListeners() {
    // 通話終了ボタン
    document.getElementById("end-call")?.addEventListener("click", () => {
      this.endCall();
    });

    // マイクオン/オフ
    document.getElementById("toggle-audio")?.addEventListener("click", () => {
      this.toggleAudio();
    });

    // ビデオオン/オフ
    document.getElementById("toggle-video")?.addEventListener("click", () => {
      this.toggleVideo();
    });

    // 画面共有
    document
      .getElementById("toggle-screen-share")
      ?.addEventListener("click", () => {
        this.toggleScreenShare();
      });

    // 着信応答
    document.getElementById("accept-call")?.addEventListener("click", () => {
      this.acceptIncomingCall();
    });

    // 着信拒否
    document.getElementById("reject-call")?.addEventListener("click", () => {
      this.rejectIncomingCall();
    });
  }

  /**
   * 通話を開始（発信側）
   * @param {string} conversationId - 会話ID
   * @param {string} partnerId - 相手のユーザーID
   * @param {string} partnerName - 相手の名前
   * @param {boolean} video - ビデオ通話かどうか
   * @param {WebSocket} ws - シグナリング用WebSocket
   */
  async startCall(
    conversationId,
    partnerId,
    partnerName,
    video = true,
    ws = null
  ) {
    try {
      console.log("通話を開始します:", { conversationId, partnerId, video });

      isVideoCall = video;
      currentConversationId = conversationId;
      currentPartnerId = partnerId;
      currentPartnerName = partnerName;
      signalingWebSocket = ws;

      // メディアストリームを取得
      await this.getUserMedia(video);

      // 通話モーダルを表示
      this.showCallModal(partnerName, video);

      // ピア接続を作成
      await this.createPeerConnection();

      // Offerを作成して送信
      const offer = await peerConnection.createOffer({
        offerToReceiveAudio: true,
        offerToReceiveVideo: video,
      });

      await peerConnection.setLocalDescription(offer);

      // シグナリングサーバーにOfferを送信
      this.sendSignalingMessage({
        type: "offer",
        sdp: offer.sdp,
        conversation_id: conversationId,
        target_user_id: partnerId,
        is_video: video,
      });

      this.updateCallStatus("相手を呼び出し中...");
    } catch (error) {
      console.error("通話の開始に失敗しました:", error);
      alert(
        "通話の開始に失敗しました。カメラとマイクへのアクセスを許可してください。"
      );
      this.endCall();
    }
  }

  /**
   * 着信を受け入れる
   */
  async acceptIncomingCall() {
    try {
      console.log("着信を受け入れます");

      // 着信モーダルを非表示
      this.hideIncomingCallModal();

      // メディアストリームを取得
      await this.getUserMedia(isVideoCall);

      // 通話モーダルを表示
      this.showCallModal(currentPartnerName, isVideoCall);

      // ピア接続を作成
      await this.createPeerConnection();

      // Offerを処理してAnswerを作成
      await this.processOffer();

      this.updateCallStatus("接続中...");
    } catch (error) {
      console.error("着信の受け入れに失敗しました:", error);
      alert("着信の受け入れに失敗しました。");
      this.endCall();
    }
  }

  /**
   * 着信を拒否
   */
  rejectIncomingCall() {
    console.log("着信を拒否しました");

    // 拒否メッセージを送信
    this.sendSignalingMessage({
      type: "reject",
      conversation_id: currentConversationId,
      target_user_id: currentPartnerId,
    });

    // モーダルを非表示
    this.hideIncomingCallModal();

    // 状態をリセット
    this.resetState();
  }

  /**
   * 通話を終了
   */
  endCall() {
    console.log("通話を終了します");

    // 終了メッセージを送信
    if (
      signalingWebSocket &&
      signalingWebSocket.readyState === WebSocket.OPEN
    ) {
      this.sendSignalingMessage({
        type: "end",
        conversation_id: currentConversationId,
        target_user_id: currentPartnerId,
      });
    }

    // ストリームとピア接続をクリーンアップ
    this.cleanup();

    // モーダルを非表示
    this.hideCallModal();
    this.hideIncomingCallModal();

    // 状態をリセット
    this.resetState();
  }

  /**
   * ユーザーメディアを取得
   * @param {boolean} video - ビデオを取得するかどうか
   */
  async getUserMedia(video) {
    const constraints = {
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
      video: video
        ? {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: "user",
          }
        : false,
    };

    localStream = await navigator.mediaDevices.getUserMedia(constraints);

    // ローカルビデオに表示
    const localVideo = document.getElementById("local-video");
    if (localVideo) {
      localVideo.srcObject = localStream;
    }

    console.log("メディアストリームを取得しました:", localStream.getTracks());
  }

  /**
   * ピア接続を作成
   */
  async createPeerConnection() {
    // 既存のピア接続がある場合はクリーンアップ
    if (peerConnection) {
      peerConnection.close();
      peerConnection = null;
    }

    peerConnection = new RTCPeerConnection(rtcConfiguration);

    // ローカルストリームをピア接続に追加
    if (localStream) {
      localStream.getTracks().forEach((track) => {
        peerConnection.addTrack(track, localStream);
      });
    }

    // ICE候補のイベントハンドラー
    peerConnection.onicecandidate = (event) => {
      if (event.candidate) {
        console.log("ICE候補を送信:", event.candidate);
        this.sendSignalingMessage({
          type: "ice-candidate",
          candidate: event.candidate.toJSON(),
          conversation_id: currentConversationId,
          target_user_id: currentPartnerId,
        });
      }
    };

    // リモートストリームのイベントハンドラー
    peerConnection.ontrack = (event) => {
      console.log("リモートトラックを受信:", event.streams);

      if (!remoteStream) {
        remoteStream = new MediaStream();
        const remoteVideo = document.getElementById("remote-video");
        if (remoteVideo) {
          remoteVideo.srcObject = remoteStream;
        }
      }

      event.streams[0].getTracks().forEach((track) => {
        remoteStream.addTrack(track);
      });

      this.updateCallStatus("通話中");
      this.startCallDuration();
    };

    // 接続状態の変更
    peerConnection.oniceconnectionstatechange = () => {
      console.log("ICE接続状態:", peerConnection.iceConnectionState);

      if (peerConnection.iceConnectionState === "connected") {
        this.updateCallStatus("通話中");
        this.startCallDuration();
      } else if (peerConnection.iceConnectionState === "disconnected") {
        this.updateCallStatus("接続が切断されました");
      } else if (peerConnection.iceConnectionState === "failed") {
        this.updateCallStatus("接続に失敗しました");
        setTimeout(() => this.endCall(), 3000);
      }
    };

    console.log("ピア接続を作成しました");
  }

  /**
   * シグナリングメッセージを受信
   * @param {Object} data - シグナリングメッセージ
   */
  async handleSignalingMessage(data) {
    console.log("シグナリングメッセージを受信:", data);

    try {
      switch (data.type) {
        case "offer":
          await this.handleOffer(data);
          break;

        case "answer":
          await this.handleAnswer(data);
          break;

        case "ice-candidate":
          await this.handleIceCandidate(data);
          break;

        case "reject":
          this.handleReject(data);
          break;

        case "end":
          this.handleEnd(data);
          break;

        default:
          console.warn("不明なシグナリングメッセージタイプ:", data.type);
      }
    } catch (error) {
      console.error("シグナリングメッセージの処理に失敗しました:", error);
    }
  }

  /**
   * Offerを処理（着信側）
   * @param {Object} data - Offerデータ
   */
  async handleOffer(data) {
    console.log("Offerを受信しました");

    // 状態を保存
    currentConversationId = data.conversation_id;
    currentPartnerId = data.sender_id;
    currentPartnerName = data.sender_name || "相手";
    isVideoCall = data.is_video || false;

    // WebSocket接続を取得（chat.jsから取得）
    // グローバル変数からWebSocketを取得
    if (typeof window.getCurrentWebSocket === "function") {
      signalingWebSocket = window.getCurrentWebSocket();
    }

    // 着信モーダルを表示
    this.showIncomingCallModal(currentPartnerName, isVideoCall);

    // Offerを保存（受け入れ時に使用）
    window._pendingOffer = data.sdp;

    // 既に到着しているICE候補をクリア（新しいOfferなので）
    pendingIceCandidates = [];
  }

  /**
   * 着信受け入れ後、Offerを設定してAnswerを作成
   */
  async processOffer() {
    if (!window._pendingOffer || !peerConnection) {
      console.error("ピア接続またはOfferがありません");
      return;
    }

    const offer = new RTCSessionDescription({
      type: "offer",
      sdp: window._pendingOffer,
    });

    await peerConnection.setRemoteDescription(offer);

    // キューに保存されているICE候補を処理
    if (pendingIceCandidates.length > 0) {
      console.log(
        `${pendingIceCandidates.length}個の保留中のICE候補を処理します`
      );
      for (const candidateData of pendingIceCandidates) {
        try {
          const candidate = new RTCIceCandidate(candidateData);
          await peerConnection.addIceCandidate(candidate);
        } catch (error) {
          console.error("保留中のICE候補の追加に失敗しました:", error);
        }
      }
      pendingIceCandidates = [];
    }

    const answer = await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);

    // Answerを送信
    this.sendSignalingMessage({
      type: "answer",
      sdp: answer.sdp,
      conversation_id: currentConversationId,
      target_user_id: currentPartnerId,
    });

    // Offerをクリア
    delete window._pendingOffer;

    console.log("Answerを送信しました");
  }

  /**
   * Answerを処理（発信側）
   * @param {Object} data - Answerデータ
   */
  async handleAnswer(data) {
    console.log("Answerを受信しました");

    if (!peerConnection) {
      console.error("ピア接続がありません");
      return;
    }

    const answer = new RTCSessionDescription({
      type: "answer",
      sdp: data.sdp,
    });

    await peerConnection.setRemoteDescription(answer);
    this.updateCallStatus("接続確立中...");
  }

  /**
   * ICE候補を処理
   * @param {Object} data - ICE候補データ
   */
  async handleIceCandidate(data) {
    console.log("ICE候補を受信しました");

    // ピア接続がまだ作成されていない場合、キューに保存
    if (!peerConnection) {
      console.log("ピア接続がまだ作成されていません。キューに保存します。");
      pendingIceCandidates.push(data.candidate);
      return;
    }

    try {
      const candidate = new RTCIceCandidate(data.candidate);
      await peerConnection.addIceCandidate(candidate);
      console.log("ICE候補を追加しました");
    } catch (error) {
      console.error("ICE候補の追加に失敗しました:", error);
    }
  }

  /**
   * 着信拒否を処理
   * @param {Object} data - 拒否データ
   */
  handleReject(data) {
    console.log("着信が拒否されました");
    alert("相手が通話を拒否しました。");
    this.endCall();
  }

  /**
   * 通話終了を処理
   * @param {Object} data - 終了データ
   */
  handleEnd(data) {
    console.log("相手が通話を終了しました");
    this.endCall();
  }

  /**
   * マイクのオン/オフを切り替え
   */
  toggleAudio() {
    if (!localStream) return;

    const audioTrack = localStream.getAudioTracks()[0];
    if (audioTrack) {
      audioTrack.enabled = !audioTrack.enabled;
      isMuted = !audioTrack.enabled;

      const button = document.getElementById("toggle-audio");
      if (isMuted) {
        button.classList.add("muted");
        button.querySelector("i").setAttribute("data-lucide", "mic-off");
      } else {
        button.classList.remove("muted");
        button.querySelector("i").setAttribute("data-lucide", "mic");
      }

      // アイコンを再初期化
      if (typeof lucide !== "undefined") {
        lucide.createIcons();
      }

      console.log("マイク:", isMuted ? "オフ" : "オン");
    }
  }

  /**
   * ビデオのオン/オフを切り替え
   */
  toggleVideo() {
    if (!localStream) return;

    const videoTrack = localStream.getVideoTracks()[0];
    if (videoTrack) {
      videoTrack.enabled = !videoTrack.enabled;
      isVideoDisabled = !videoTrack.enabled;

      const button = document.getElementById("toggle-video");
      if (isVideoDisabled) {
        button.classList.add("disabled");
        button.querySelector("i").setAttribute("data-lucide", "video-off");
      } else {
        button.classList.remove("disabled");
        button.querySelector("i").setAttribute("data-lucide", "video");
      }

      // アイコンを再初期化
      if (typeof lucide !== "undefined") {
        lucide.createIcons();
      }

      console.log("ビデオ:", isVideoDisabled ? "オフ" : "オン");
    }
  }

  /**
   * 画面共有の切り替え
   */
  async toggleScreenShare() {
    try {
      if (!isScreenSharing) {
        // 画面共有を開始
        screenStream = await navigator.mediaDevices.getDisplayMedia({
          video: {
            cursor: "always",
          },
          audio: false,
        });

        const screenTrack = screenStream.getVideoTracks()[0];

        // ピア接続のビデオトラックを置き換え
        const sender = peerConnection
          .getSenders()
          .find((s) => s.track?.kind === "video");
        if (sender) {
          sender.replaceTrack(screenTrack);
        }

        // 画面共有が停止されたときの処理
        screenTrack.onended = () => {
          this.stopScreenShare();
        };

        isScreenSharing = true;

        const button = document.getElementById("toggle-screen-share");
        button.classList.add("active");

        console.log("画面共有を開始しました");
      } else {
        this.stopScreenShare();
      }
    } catch (error) {
      console.error("画面共有の開始に失敗しました:", error);
      alert("画面共有の開始に失敗しました。");
    }
  }

  /**
   * 画面共有を停止
   */
  async stopScreenShare() {
    if (screenStream) {
      screenStream.getTracks().forEach((track) => track.stop());
      screenStream = null;
    }

    // 元のビデオトラックに戻す
    const videoTrack = localStream.getVideoTracks()[0];
    const sender = peerConnection
      .getSenders()
      .find((s) => s.track?.kind === "video");
    if (sender && videoTrack) {
      await sender.replaceTrack(videoTrack);
    }

    isScreenSharing = false;

    const button = document.getElementById("toggle-screen-share");
    button?.classList.remove("active");

    console.log("画面共有を停止しました");
  }

  /**
   * 通話時間のカウントを開始
   */
  startCallDuration() {
    if (callDurationInterval) return;

    callStartTime = Date.now();
    callDurationInterval = setInterval(() => {
      const duration = Math.floor((Date.now() - callStartTime) / 1000);
      const minutes = Math.floor(duration / 60)
        .toString()
        .padStart(2, "0");
      const seconds = (duration % 60).toString().padStart(2, "0");

      const durationElement = document.getElementById("call-duration");
      if (durationElement) {
        durationElement.textContent = `${minutes}:${seconds}`;
      }
    }, 1000);
  }

  /**
   * 通話時間のカウントを停止
   */
  stopCallDuration() {
    if (callDurationInterval) {
      clearInterval(callDurationInterval);
      callDurationInterval = null;
    }
    callStartTime = null;
  }

  /**
   * シグナリングメッセージを送信
   * @param {Object} message - 送信するメッセージ
   */
  sendSignalingMessage(message) {
    // WebSocket接続を再取得（グローバル変数から）
    if (
      !signalingWebSocket ||
      signalingWebSocket.readyState !== WebSocket.OPEN
    ) {
      if (typeof window.getCurrentWebSocket === "function") {
        signalingWebSocket = window.getCurrentWebSocket();
      }
    }

    if (
      signalingWebSocket &&
      signalingWebSocket.readyState === WebSocket.OPEN
    ) {
      signalingWebSocket.send(JSON.stringify(message));
      console.log("シグナリングメッセージを送信:", message);
    } else {
      console.error("WebSocket接続が開いていません", {
        hasWebSocket: !!signalingWebSocket,
        readyState: signalingWebSocket?.readyState,
        hasGlobalFunction: typeof window.getCurrentWebSocket === "function",
      });
    }
  }

  /**
   * 通話モーダルを表示
   * @param {string} partnerName - 相手の名前
   * @param {boolean} video - ビデオ通話かどうか
   */
  showCallModal(partnerName, video) {
    const modal = document.getElementById("call-modal");
    const partnerNameElement = document.getElementById("call-partner-name");

    if (modal) {
      modal.classList.add("show");
      if (!video) {
        modal.classList.add("audio-only");
      } else {
        modal.classList.remove("audio-only");
      }
    }

    if (partnerNameElement) {
      partnerNameElement.textContent = partnerName;
    }

    // アイコンを初期化
    if (typeof lucide !== "undefined") {
      lucide.createIcons();
    }
  }

  /**
   * 通話モーダルを非表示
   */
  hideCallModal() {
    const modal = document.getElementById("call-modal");
    if (modal) {
      modal.classList.remove("show");
      modal.classList.remove("audio-only");
    }
  }

  /**
   * 着信モーダルを表示
   * @param {string} callerName - 発信者の名前
   * @param {boolean} video - ビデオ通話かどうか
   */
  showIncomingCallModal(callerName, video) {
    const modal = document.getElementById("incoming-call-modal");
    const callerNameElement = document.getElementById("caller-name");
    const callTypeLabel = document.getElementById("call-type-label");

    if (modal) {
      modal.classList.add("show");
    }

    if (callerNameElement) {
      callerNameElement.textContent = callerName;
    }

    if (callTypeLabel) {
      callTypeLabel.textContent = video ? "ビデオ通話" : "音声通話";
    }

    // アイコンを初期化
    if (typeof lucide !== "undefined") {
      lucide.createIcons();
    }
  }

  /**
   * 着信モーダルを非表示
   */
  hideIncomingCallModal() {
    const modal = document.getElementById("incoming-call-modal");
    if (modal) {
      modal.classList.remove("show");
    }
  }

  /**
   * 通話ステータスを更新
   * @param {string} status - ステータステキスト
   */
  updateCallStatus(status) {
    const statusElement = document.getElementById("call-status");
    if (statusElement) {
      statusElement.textContent = status;
    }
    console.log("通話ステータス:", status);
  }

  /**
   * クリーンアップ
   */
  cleanup() {
    // ローカルストリームを停止
    if (localStream) {
      localStream.getTracks().forEach((track) => track.stop());
      localStream = null;
    }

    // 画面共有ストリームを停止
    if (screenStream) {
      screenStream.getTracks().forEach((track) => track.stop());
      screenStream = null;
    }

    // リモートストリームをクリア
    remoteStream = null;

    // ピア接続を閉じる
    if (peerConnection) {
      peerConnection.close();
      peerConnection = null;
    }

    // 通話時間のカウントを停止
    this.stopCallDuration();

    // ビデオ要素をクリア
    const localVideo = document.getElementById("local-video");
    const remoteVideo = document.getElementById("remote-video");

    if (localVideo) {
      localVideo.srcObject = null;
    }

    if (remoteVideo) {
      remoteVideo.srcObject = null;
    }

    console.log("クリーンアップが完了しました");
  }

  /**
   * 状態をリセット
   */
  resetState() {
    currentConversationId = null;
    currentPartnerId = null;
    currentPartnerName = null;
    isVideoCall = true;
    isMuted = false;
    isVideoDisabled = false;
    isScreenSharing = false;
    pendingIceCandidates = [];
    window._pendingOffer = null;

    // ボタンの状態をリセット
    const audioButton = document.getElementById("toggle-audio");
    const videoButton = document.getElementById("toggle-video");
    const screenButton = document.getElementById("toggle-screen-share");

    if (audioButton) {
      audioButton.classList.remove("muted");
      audioButton.querySelector("i")?.setAttribute("data-lucide", "mic");
    }

    if (videoButton) {
      videoButton.classList.remove("disabled");
      videoButton.querySelector("i")?.setAttribute("data-lucide", "video");
    }

    if (screenButton) {
      screenButton.classList.remove("active");
    }

    // アイコンを再初期化
    if (typeof lucide !== "undefined") {
      lucide.createIcons();
    }
  }
}

// グローバルインスタンスをエクスポート
export const webrtcManager = new WebRTCManager();
