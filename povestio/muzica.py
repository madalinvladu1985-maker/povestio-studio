"""Muzica ambientala originala (pad cald + clopotei), generata din cod - fara licente."""
import numpy as np, wave


def _hz(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def genereaza(dur, sr=44100):
    N = int(sr * dur); t = np.arange(N) / sr; mix = np.zeros(N)

    def pad(midi, s, e, amp):
        i0, i1 = int(s * sr), min(N, int(e * sr))
        if i1 <= i0: return
        tt = np.arange(i1 - i0) / sr; f = _hz(midi)
        sig = sum(np.sin(2 * np.pi * f * d * tt + p) for d, p in ((1, 0), (1.003, 1.1), (0.997, 2.3)))
        sig = sig + 0.25 * np.sin(2 * np.pi * f * 2 * tt)
        en = np.minimum(1, tt / 1.6) * np.minimum(1, np.maximum(0, (tt[-1] - tt) / 2.2))
        mix[i0:i1] += sig * en * amp

    def bell(midi, s, amp):
        i0 = int(s * sr); L = min(N - i0, int(3.5 * sr))
        if L <= 0: return
        tt = np.arange(L) / sr; f = _hz(midi)
        sig = np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * f * 2.76 * tt) * np.exp(-tt * 3)
        mix[i0:i0 + L] += sig * np.exp(-tt * 1.6) * np.minimum(1, tt / 0.005) * amp

    prog = [[50, 57, 62, 66, 69], [47, 54, 59, 62, 66], [43, 50, 55, 59, 64, 66], [45, 52, 57, 61, 64, 62]]
    step = 6.0
    k = 0; s = 0.0
    while s < dur:
        for j, m in enumerate(prog[k % 4]):
            pad(m, s, min(dur, s + step + 0.5), 0.05 if j == 0 else 0.035)
        s += step; k += 1
    mel = [81, 78, 76, 78, 74, 71, 79, 78, 74, 76, 76, 78, 81, 74]
    s, j = 1.2, 0
    while s < dur - 1:
        bell(mel[j % len(mel)], s, 0.06); s += 1.3 + (j % 3) * 0.35; j += 1

    def comb(x, d, g):
        y = x.copy(); D = int(d * sr)
        for i in range(D, len(y), D):
            y[i:i + D] += g * y[i - D:i][: len(y[i:i + D])]
        return y
    wet = sum(comb(mix, d, g) for d, g in ((0.0297, 0.7), (0.0371, 0.68), (0.0411, 0.66), (0.0437, 0.64))) / 4
    mix = 0.65 * mix + 0.5 * wet
    mix *= np.minimum(1, t / 1.5) * np.minimum(1, np.maximum(0, (dur - t) / 2.0))
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.5
    return np.stack([mix, np.roll(mix, int(0.012 * sr))], axis=1)


def scrie_wav(path, st, sr=44100):
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())
