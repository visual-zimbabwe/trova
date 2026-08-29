// OmaTrova Soundtrack Audio Player & Waveform Visualizer

const AudioVisualizer = {
  audio: null,
  audioCtx: null,
  analyser: null,
  source: null,
  animId: null,
  canvas: null,
  ctx: null,

  init(canvasElement) {
    this.canvas = canvasElement;
    if (this.canvas) {
      this.ctx = this.canvas.getContext('2d');
    }
  },

  playTrack(previewUrl, trackName) {
    if (this.audio) {
      this.audio.pause();
      if (this.animId) cancelAnimationFrame(this.animId);
    }

    if (!previewUrl) return;

    this.audio = new Audio(previewUrl);
    this.audio.crossOrigin = 'anonymous';

    try {
      if (!this.audioCtx) {
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (this.audioCtx.state === 'suspended') {
        this.audioCtx.resume();
      }

      this.analyser = this.audioCtx.createAnalyser();
      this.analyser.fftSize = 64;
      this.source = this.audioCtx.createMediaElementSource(this.audio);
      this.source.connect(this.analyser);
      this.analyser.connect(this.audioCtx.destination);
    } catch (e) {
      // Audio context might fail on some cross-origin streams, fallback to plain play
    }

    this.audio.play();
    this.startVisualization();
  },

  stop() {
    if (this.audio) {
      this.audio.pause();
      this.audio = null;
    }
    if (this.animId) {
      cancelAnimationFrame(this.animId);
    }
    if (this.ctx && this.canvas) {
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
  },

  startVisualization() {
    if (!this.canvas || !this.ctx || !this.analyser) return;

    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    const canvas = this.canvas;
    const ctx = this.ctx;

    const draw = () => {
      this.animId = requestAnimationFrame(draw);
      this.analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const accentColor = getComputedStyle(document.documentElement).getPropertyValue('--om-accent').trim() || '#4a9a68';
      const barWidth = (canvas.width / bufferLength) * 1.5;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height;
        ctx.fillStyle = accentColor;
        ctx.fillRect(x, canvas.height - barHeight, barWidth - 2, barHeight);
        x += barWidth;
      }
    };

    draw();
  }
};
