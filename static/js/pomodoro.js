class PomodoroTimer {
    constructor() {
        this.timeLeft = 25 * 60; // 25 minutes in seconds
        this.initialTime = 25 * 60;
        this.isRunning = false;
        this.timer = null;
        
        this.display = document.querySelector('.timer-display');
        this.startButton = document.getElementById('startTimer');
        this.resetButton = document.getElementById('resetTimer');
        this.modeButtons = document.querySelectorAll('.mode-button');
        
        this.initializeListeners();
        
        // Configurações de alarmes diferentes para pomodoro e break
        this.alarmSoundPomodoro = new Audio('/static/audio/alarm-work.mp3');
        this.alarmSoundBreak = new Audio('/static/audio/alarm-break.mp3');
        this.alarmSoundPomodoro.volume = 0.7;
        this.alarmSoundBreak.volume = 0.7;
        
        // Pré-carregar os sons
        this.alarmSoundPomodoro.load();
        this.alarmSoundBreak.load();
        
        // Adicionar estado do modo atual
        this.isBreakMode = false;
    }

    initializeListeners() {
        this.startButton.addEventListener('click', () => this.toggleTimer());
        this.resetButton.addEventListener('click', () => this.resetTimer());
        
        this.modeButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                this.modeButtons.forEach(btn => btn.classList.remove('active'));
                e.target.classList.add('active');
                this.setTime(parseInt(e.target.dataset.time));
            });
        });
    }

    toggleTimer() {
        if (this.isRunning) {
            this.pauseTimer();
            this.startButton.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M8,5.14V19.14L19,12.14L8,5.14Z"/></svg>';
        } else {
            this.startTimer();
            this.startButton.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M14,19H18V5H14M6,19H10V5H6V19Z"/></svg>';
        }
    }

    startTimer() {
        this.isRunning = true;
        this.timer = setInterval(() => {
            this.timeLeft--;
            this.updateDisplay();
            
            if (this.timeLeft <= 0) {
                this.timerComplete();
            }
        }, 1000);
    }

    pauseTimer() {
        this.isRunning = false;
        clearInterval(this.timer);
    }

    resetTimer() {
        this.pauseTimer();
        this.timeLeft = this.initialTime;
        this.updateDisplay();
        this.startButton.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M8,5.14V19.14L19,12.14L8,5.14Z"/></svg>';
    }

    setTime(minutes) {
        this.pauseTimer();
        this.initialTime = minutes * 60;
        this.timeLeft = this.initialTime;
        this.isBreakMode = minutes === 5; // Break mode se for 5 minutos
        this.updateDisplay();
    }

    updateDisplay() {
        const minutes = Math.floor(this.timeLeft / 60);
        const seconds = this.timeLeft % 60;
        this.display.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    timerComplete() {
        this.pauseTimer();
        this.resetTimer();
        
        // Melhor tratamento para tocar o som
        try {
            const alarm = this.isBreakMode ? this.alarmSoundBreak : this.alarmSoundPomodoro;
            
            // Reiniciar o áudio antes de tocar
            alarm.currentTime = 0;
            
            // Promessa para tocar o som
            const playPromise = alarm.play();
            
            if (playPromise !== undefined) {
                playPromise
                    .then(() => {
                        console.log('Áudio tocando com sucesso');
                    })
                    .catch(error => {
                        console.error('Erro ao tocar áudio:', error);
                        // Tentar tocar novamente após interação do usuário
                        document.addEventListener('click', () => {
                            alarm.play();
                        }, { once: true });
                    });
            }
        } catch (error) {
            console.error('Erro ao manipular áudio:', error);
        }
        
        // Mostrar notificação apropriada
        if (Notification.permission === 'granted') {
            new Notification('Pomodoro Timer', {
                body: this.isBreakMode ? 'Break time is up! Time to work!' : 'Work time is up! Time for a break!',
                icon: '/static/img/logo.png'
            });
        }
    }
}

// Inicializar o timer quando o documento estiver carregado
document.addEventListener('DOMContentLoaded', () => {
    const pomodoroTimer = new PomodoroTimer();
    
    // Solicitar permissão para notificações
    if (Notification.permission !== 'granted') {
        Notification.requestPermission();
    }
});
