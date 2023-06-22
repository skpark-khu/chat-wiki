const progressBar = document.getElementsByClassName('progress-bar')[0];
const maxProgress = 100; // 최대 진행도 (100%)
const incrementAmount = 0.1; // 진행도 증가량

let currentProgress = 0;

setInterval(() => {
    const computedStyle = getComputedStyle(progressBar);
    const width = parseFloat(computedStyle.getPropertyValue('--width')) || 0;

    if (currentProgress >= maxProgress) {
        // 진행도가 최대치에 도달한 경우 초기화
        currentProgress = 0;
        progressBar.style.setProperty('--width', currentProgress);
    } else {
        // 진행도를 증가시키고 스타일에 반영
        currentProgress += incrementAmount;
        progressBar.style.setProperty('--width', currentProgress);
    }
}, 5);