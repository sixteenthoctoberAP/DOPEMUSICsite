let currentAudio = null;

// Останавливает все аудио
function stopAllAudio() {
  document.querySelectorAll('audio').forEach(audio => {
    audio.pause();
    audio.currentTime = 0;
  });

  document.querySelectorAll('.play-btn').forEach(btn => {
    btn.classList.remove('active');
    btn.querySelector('.play-icon').style.display = 'inline-block';
    btn.querySelector('.pause-icon').style.display = 'none';
  });

  document.querySelectorAll('.progress-container').forEach(container => container.style.display = 'none');
  document.querySelectorAll('.progress-bar').forEach(bar => bar.style.width = '0%');
  document.querySelectorAll('.time').forEach(time => time.textContent = '0:00 / 0:00');
}

// Переключатель воспроизведения
function togglePlay(trackNumber, version) {
  const audio = document.getElementById(`track${trackNumber}-${version}`);
  const btn = event.currentTarget;
  const timeEl = btn.closest('.col-md-6').querySelector('.time');
  const progressBar = btn.closest('.col-md-6').querySelector('.progress-bar');
  const progressContainer = btn.closest('.col-md-6').querySelector('.progress-container');

  if (!audio) return;

  // Если уже играет — ставим на паузу
  if (!audio.paused) {
    audio.pause();
    btn.classList.remove('active');
    btn.querySelector('.play-icon').style.display = 'inline-block';
    btn.querySelector('.pause-icon').style.display = 'none';
    return;
  }

  // Останавливаем всё остальное
  stopAllAudio();

  // Включаем текущее
  audio.currentTime = 0;
  audio.play();
  btn.classList.add('active');
  btn.querySelector('.play-icon').style.display = 'none';
  btn.querySelector('.pause-icon').style.display = 'inline-block';
  progressContainer.style.display = 'block';

  currentAudio = { audio, progressBar, timeEl };
}

// Остановить все при клике вне
document.addEventListener('click', function(e) {
  const isClickInside = e.target.closest('.examples-block');
  if (!isClickInside && currentAudio) {
    stopAllAudio();
  }
});

// Обновление прогресса и времени
setInterval(() => {
  if (currentAudio && !currentAudio.audio.paused) {
    const duration = currentAudio.audio.duration || 0;
    const currentTime = currentAudio.audio.currentTime || 0;
    const percent = (currentTime / duration) * 100;

    currentAudio.progressBar.style.width = `${percent}%`;

    const formatTime = t => {
      const m = Math.floor(t / 60);
      const s = Math.floor(t % 60).toString().padStart(2, '0');
      return `${m}:${s}`;
    };

    currentAudio.timeEl.textContent = `${formatTime(currentTime)} / ${formatTime(duration)}`;
  }
}, 500);

// Обработка клика по прогресс-бару для перемотки
document.addEventListener('click', function(e) {
    const progressBarContainer = e.target.closest('.progress-container');
    if (!progressBarContainer || !currentAudio) return;

    const containerRect = progressBarContainer.getBoundingClientRect();
    const clickX = e.clientX - containerRect.left;
    const percent = clickX / progressBarContainer.offsetWidth;

    const duration = currentAudio.audio.duration;
    if (!isNaN(duration)) {
      currentAudio.audio.currentTime = percent * duration;
    }
  });