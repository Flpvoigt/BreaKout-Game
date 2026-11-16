# Breakout Game

Um clone do clássico **Arkanoid/Breakout**, feito em Python com a biblioteca **Pygame**.

Projeto desenvolvido para o trabalho **AV2 - Linguagens** (Uniasselvi).

## Como jogar

```bash
pip install pygame numpy
python breakout.py
```

- **Setas (← →)** ou **A / D**: move a raquete
- **Espaço**: inicia o jogo a partir do menu
- A bola nasce grudada na raquete e só é lançada quando você se move pela primeira vez
- **R**: volta ao menu após Game Over ou Vitória

## Funcionalidades

- **Física de rebote baseada na posição do impacto**: o ângulo de saída da bola muda conforme o ponto em que ela toca a raquete.
- **Tijolos com vida variável**: tijolos mais próximos do topo quebram com 1 toque; conforme se aproximam da raquete, exigem até 3 toques (escurecem e ganham rachaduras visuais a cada batida que não quebra).
- **Power-ups** (caem aleatoriamente ao quebrar um tijolo):
  - `W` — raquete fica mais larga por um tempo
  - `M` — multiplica a bola em jogo (multi-ball)
  - `S` — deixa a(s) bola(s) mais lenta(s)
- **Sistema de níveis**: 5 fases com dificuldade progressiva (mais linhas de tijolos), transição "NÍVEL X COMPLETO!" entre elas.
- **Efeitos sonoros** gerados programaticamente (sem nenhum arquivo de áudio externo), via `numpy` + `pygame.sndarray`.
- **Efeitos visuais**: partículas ao quebrar tijolo, tremor de tela (screen shake), rastro de luz atrás da bola, menu com título pulsante.
- Placar, vidas, cronômetro de partida e contagem regressiva de cada power-up ativo.

## Requisitos

- Python 3.10+
- `pygame`
- `numpy` (usado só para gerar os efeitos sonoros; o jogo funciona normalmente sem som caso não esteja disponível)

## Estrutura do código

- **Classes**: `Paddle`, `Ball`, `Brick`, `Particle`, `PowerUp`
- **Áudio**: `init_audio()` / `play_sound()` — geram e tocam os efeitos sonoros
- **Funções de desenho**: `draw_menu`, `draw_pulsing_title`, `draw_powerup_timer`, `draw_end_message`, `draw_level_complete`
- **`main()`**: loop principal do jogo, com máquina de estados (`menu` / `playing`) e as flags de `game_over`, `won` e `transitioning` (entre níveis)
