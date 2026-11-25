"""Efeitos sonoros gerados por codigo (sem nenhum arquivo de audio externo),
via numpy + pygame.sndarray."""
import sys
import pygame

try:
    import numpy as np
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "numpy"], check=False)
    try:
        import numpy as np
    except ImportError:
        np = None

sound_enabled = True
sound_volume = 0.7  # 0.0 a 1.0, ajustavel pelo menu de pausa
SOUNDS = {}
AUDIO_SAMPLE_RATE = 44100


def _gerar_tom(freq, duration_ms, volume=0.5, wave="sine", sample_rate=AUDIO_SAMPLE_RATE):
    """Gera um array numpy PCM16 mono curto com um tom simples (senoidal ou quadrada).
    So e chamada a partir de iniciar_audio() apos a checagem `if np is None: return`,
    entao o numpy sempre esta disponivel aqui - o assert so informa isso ao Pylance."""
    assert np is not None
    n_samples = max(1, int(sample_rate * duration_ms / 1000))
    t = np.linspace(0, duration_ms / 1000.0, n_samples, endpoint=False)
    if wave == "square":
        data = np.sign(np.sin(2 * np.pi * freq * t))
    else:
        data = np.sin(2 * np.pi * freq * t)
    # envelope de fade-in/out pra evitar "cliques" nas bordas
    fade = max(1, min(n_samples // 4, int(sample_rate * 0.005)))
    envelope = np.ones(n_samples)
    envelope[:fade] = np.linspace(0, 1, fade)
    envelope[-fade:] = np.linspace(1, 0, fade)
    data = data * envelope * volume
    return (data * 32767).astype(np.int16)


def _gerar_sequencia(notes):
    """Concatena varias notas (freq, duration_ms, volume, wave) num unico array."""
    assert np is not None
    pieces = [_gerar_tom(*note) for note in notes]
    return np.concatenate(pieces)


def _gerar_ruido(duration_ms, volume=0.5, sample_rate=AUDIO_SAMPLE_RATE):
    """Rajada de ruido branco (com o mesmo envelope de fade das notas) - usada
    pra crepitar como estatica/eletricidade, coisa que um tom puro nao faz."""
    assert np is not None
    n_samples = max(1, int(sample_rate * duration_ms / 1000))
    data = np.random.uniform(-1, 1, n_samples)
    fade = max(1, min(n_samples // 4, int(sample_rate * 0.005)))
    envelope = np.ones(n_samples)
    envelope[:fade] = np.linspace(0, 1, fade)
    envelope[-fade:] = np.linspace(1, 0, fade)
    data = data * envelope * volume
    return (data * 32767).astype(np.int16)


def iniciar_audio():
    """Inicializa o mixer e constroi cada efeito sonoro na hora, via numpy.
    Se nao houver numpy ou dispositivo de audio disponivel, desativa o som
    silenciosamente (o jogo continua funcionando sem efeitos sonoros)."""
    global sound_enabled
    if np is None:
        sound_enabled = False
        return
    try:
        pygame.mixer.quit()
        pygame.mixer.init(frequency=AUDIO_SAMPLE_RATE, size=-16, channels=1)
    except Exception:
        sound_enabled = False
        return
    try:
        SOUNDS["hit_paddle"] = pygame.sndarray.make_sound(_gerar_tom(220, 70, 0.45, "square"))
        SOUNDS["hit_wall"] = pygame.sndarray.make_sound(_gerar_tom(150, 60, 0.35, "sine"))
        SOUNDS["brick_hit"] = pygame.sndarray.make_sound(_gerar_tom(320, 70, 0.35, "sine"))
        SOUNDS["brick_destroy"] = pygame.sndarray.make_sound(_gerar_sequencia([
            (660, 50, 0.45, "square"), (990, 90, 0.5, "square"),
        ]))
        SOUNDS["powerup"] = pygame.sndarray.make_sound(_gerar_sequencia([
            (500, 60, 0.4, "sine"), (750, 100, 0.45, "sine"),
        ]))
        SOUNDS["lose_life"] = pygame.sndarray.make_sound(_gerar_sequencia([
            (400, 90, 0.4, "sine"), (240, 140, 0.4, "sine"),
        ]))
        SOUNDS["game_over"] = pygame.sndarray.make_sound(_gerar_sequencia([
            (300, 150, 0.45, "square"), (220, 150, 0.45, "square"), (150, 220, 0.5, "square"),
        ]))
        SOUNDS["victory"] = pygame.sndarray.make_sound(_gerar_sequencia([
            (523, 100, 0.45, "sine"), (659, 100, 0.45, "sine"), (784, 160, 0.5, "sine"),
        ]))
        SOUNDS["cannon_fire"] = pygame.sndarray.make_sound(_gerar_tom(200, 45, 0.3, "square"))
        SOUNDS["coin"] = pygame.sndarray.make_sound(_gerar_sequencia([
            (880, 40, 0.4, "sine"), (1175, 70, 0.45, "sine"),
        ]))
        SOUNDS["buy_life"] = pygame.sndarray.make_sound(_gerar_sequencia([
            (440, 80, 0.45, "sine"), (660, 80, 0.45, "sine"), (880, 120, 0.5, "sine"),
        ]))
        SOUNDS["raio_caindo"] = pygame.sndarray.make_sound(np.concatenate([
            _gerar_ruido(35, 0.25), _gerar_tom(1900, 25, 0.3, "square"),
            _gerar_ruido(35, 0.25), _gerar_tom(2300, 25, 0.3, "square"),
            _gerar_ruido(40, 0.25), _gerar_tom(1600, 30, 0.3, "square"),
        ]))
        SOUNDS["trovao"] = pygame.sndarray.make_sound(np.concatenate([
            _gerar_ruido(50, 0.4), _gerar_tom(90, 160, 0.55, "square"), _gerar_tom(60, 220, 0.5, "square"),
        ]))
    except Exception:
        sound_enabled = False


_last_played_ms = {}
SOUND_THROTTLE_MS = 40  # evita "cacho" de som quando varios eventos batem no mesmo frame


def tocar_som(name):
    if not sound_enabled or sound_volume <= 0:
        return
    now = pygame.time.get_ticks()
    if now - _last_played_ms.get(name, -SOUND_THROTTLE_MS) < SOUND_THROTTLE_MS:
        return
    snd = SOUNDS.get(name)
    if snd is not None:
        try:
            snd.set_volume(sound_volume)
            snd.play()
            _last_played_ms[name] = now
        except Exception:
            pass
