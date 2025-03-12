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

        // Atualiza a inicialização do som ambiente
        this.ambientSound = new Audio('/static/audio/rain.wav');
        this.ambientSound.loop = true;
        this.ambientButton = document.createElement('button');
        this.ambientButton.className = 'ambient-sound-button';
        this.ambientButton.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16"><path fill="currentColor" d="M12,3V12.26C11.5,12.09 11,12 10.5,12C8.56,12 7,13.56 7,15.5C7,17.44 8.56,19 10.5,19C12.44,19 14,17.44 14,15.5V6H18V3H12Z" /></svg>';
        
        document.querySelector('.timer-controls').appendChild(this.ambientButton);
        
        this.isAmbientPlaying = false;
        this.ambientButton.addEventListener('click', () => this.toggleAmbientSound());
        
        // Pré-carrega o som ambiente
        this.ambientSound.load();
        this.ambientSound.volume = 0.5; // Volume reduzido para 50%

        this.startTime = null; // Adiciona controle do tempo inicial
        this.timerType = 'work'; // Tipo padrão é work
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
        this.startTime = new Date(); // Registra o tempo inicial
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
        if (this.isRunning && this.startTime) {
            this.isRunning = false;
            clearInterval(this.timer);
            this.logPomodoroSession(false); // Registra sessão pausada
        }
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
        this.logPomodoroSession(true); // Registra sessão completa
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

    logPomodoroSession(completed) {
        if (!this.startTime) return;
        
        const endTime = new Date();
        const duration = Math.round((this.initialTime - this.timeLeft)); // Tempo decorrido em segundos

        fetch('/api/pomodoro/log', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                start_time: this.startTime.toISOString(),
                end_time: endTime.toISOString(),
                duration: duration,
                timer_type: this.timerType,
                completed: completed
            })
        })
        .then(response => response.json())
        .then(data => {
            if (!data.success) {
                console.error('Error logging pomodoro session:', data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });

        this.startTime = null; // Reset startTime
    }

    toggleAmbientSound() {
        try {
            if (this.isAmbientPlaying) {
                this.ambientSound.pause();
                this.ambientButton.classList.remove('active');
            } else {
                const playPromise = this.ambientSound.play();
                
                if (playPromise !== undefined) {
                    playPromise
                        .then(() => {
                            this.ambientButton.classList.add('active');
                        })
                        .catch(error => {
                            console.error('Erro ao tocar som ambiente:', error);
                        });
                }
            }
            this.isAmbientPlaying = !this.isAmbientPlaying;
        } catch (error) {
            console.error('Erro ao manipular som ambiente:', error);
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
