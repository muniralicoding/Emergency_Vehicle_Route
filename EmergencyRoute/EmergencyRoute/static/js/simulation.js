/**
 * Emergency Vehicle Simulation & Web Audio Siren Synthesizer
 */

class AmbulanceSimulator {
    constructor() {
        this.isSimulating = false;
        this.animationTimer = null;
        this.currentStep = 0;
        this.totalSteps = 0;
        this.audioCtx = null;
        this.sirenOsc = null;
        this.sirenGain = null;
        this.sirenInterval = null;
        this.soundEnabled = false;
    }

    initAudio() {
        if (!this.audioCtx) {
            const AudioContext = window.AudioContext || window.webkitAudioContext;
            this.audioCtx = new AudioContext();
        }
        if (this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }
    }

    startSiren() {
        if (!this.soundEnabled) return;
        try {
            this.initAudio();
            if (this.sirenOsc) return;

            this.sirenOsc = this.audioCtx.createOscillator();
            this.sirenGain = this.audioCtx.createGain();

            this.sirenOsc.type = 'sawtooth';
            this.sirenGain.gain.setValueAtTime(0.04, this.audioCtx.currentTime); // gentle volume

            this.sirenOsc.connect(this.sirenGain);
            this.sirenGain.connect(this.audioCtx.destination);
            this.sirenOsc.start();

            // Alternating European / Emergency 2-tone siren (650 Hz <-> 900 Hz)
            let high = false;
            this.sirenInterval = setInterval(() => {
                if (!this.sirenOsc || !this.audioCtx) return;
                const freq = high ? 920 : 660;
                this.sirenOsc.frequency.setTargetAtTime(freq, this.audioCtx.currentTime, 0.08);
                high = !high;
            }, 350);
        } catch (e) {
            console.warn("Audio Context error:", e);
        }
    }

    stopSiren() {
        if (this.sirenInterval) {
            clearInterval(this.sirenInterval);
            this.sirenInterval = null;
        }
        if (this.sirenOsc) {
            try {
                this.sirenOsc.stop();
                this.sirenOsc.disconnect();
            } catch (e) {}
            this.sirenOsc = null;
        }
    }

    toggleSound() {
        this.soundEnabled = !this.soundEnabled;
        const soundBtn = document.getElementById("toggleSoundBtn");
        if (soundBtn) {
            soundBtn.innerHTML = this.soundEnabled 
                ? '<i class="fa-solid fa-volume-high text-emerald-400"></i>' 
                : '<i class="fa-solid fa-volume-xmark text-gray-400"></i>';
        }
        if (this.isSimulating) {
            if (this.soundEnabled) this.startSiren();
            else this.stopSiren();
        }
    }

    /**
     * Interpolates smooth points between two lat/lng coords
     */
    interpolatePath(latLngs, pointsPerSegment = 20) {
        const fullCoords = [];
        for (let i = 0; i < latLngs.length - 1; i++) {
            const p1 = latLngs[i];
            const p2 = latLngs[i + 1];
            for (let step = 0; step < pointsPerSegment; step++) {
                const ratio = step / pointsPerSegment;
                const lat = p1[0] + (p2[0] - p1[0]) * ratio;
                const lng = p1[1] + (p2[1] - p1[1]) * ratio;
                fullCoords.push([lat, lng]);
            }
        }
        if (latLngs.length > 0) {
            fullCoords.push(latLngs[latLngs.length - 1]);
        }
        return fullCoords;
    }

    startSimulation(pathCoords, onProgress, onFinish) {
        if (this.isSimulating) {
            this.stopSimulation();
        }
        if (!pathCoords || pathCoords.length < 2) return;

        this.isSimulating = true;
        this.startSiren();

        const smoothPoints = this.interpolatePath(pathCoords, 25);
        this.totalSteps = smoothPoints.length;
        this.currentStep = 0;

        const stepDurationMs = 45; // ~22 frames per second

        this.animationTimer = setInterval(() => {
            if (this.currentStep >= this.totalSteps) {
                this.stopSimulation();
                if (onFinish) onFinish();
                return;
            }

            const currentCoord = smoothPoints[this.currentStep];
            const percent = Math.round((this.currentStep / this.totalSteps) * 100);
            if (onProgress) {
                onProgress(currentCoord, percent, this.currentStep, this.totalSteps);
            }
            this.currentStep++;
        }, stepDurationMs);
    }

    stopSimulation() {
        this.isSimulating = false;
        if (this.animationTimer) {
            clearInterval(this.animationTimer);
            this.animationTimer = null;
        }
        this.stopSiren();
    }
}

window.ambulanceSim = new AmbulanceSimulator();
