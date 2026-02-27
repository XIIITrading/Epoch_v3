# 04 - Indicator Deep Dive: Three-Phase Analysis

Per-indicator breakdown across ramp-up (pre-entry), entry snapshot,
and post-trade (post-entry) phases. Direction-normalized where applicable.

## Three-Phase Progression (Continuous Indicators)

### Candle Range %

**Ramp-Up (pre-entry)** (bars -24 to -1): Winners avg=0.240915, Losers avg=0.223473, Delta=+0.017442
**Post-Trade (post-entry)** (bars 0 to 24): Winners avg=0.231153, Losers avg=0.223112, Delta=+0.008041

### Volume Delta (5-bar)
*Direction-normalized: positive = favorable for trade direction*

**Ramp-Up (pre-entry)** (bars -24 to -1): Winners avg=8586.326054, Losers avg=13050.893818, Delta=-4464.567763
**Post-Trade (post-entry)** (bars 0 to 24): Winners avg=29180.557987, Losers avg=-20495.473229, Delta=+49676.031216

### Vol Delta Normalized
*Direction-normalized: positive = favorable for trade direction*

**Ramp-Up (pre-entry)** (bars -24 to -1): Winners avg=0.051939, Losers avg=0.082044, Delta=-0.030105
**Post-Trade (post-entry)** (bars 0 to 24): Winners avg=0.350753, Losers avg=-0.284927, Delta=+0.635680

### Volume ROC

**Ramp-Up (pre-entry)** (bars -24 to -1): Winners avg=184.461822, Losers avg=160.424087, Delta=+24.037735
**Post-Trade (post-entry)** (bars 0 to 24): Winners avg=11.212475, Losers avg=20.081467, Delta=-8.868993

### SMA Spread %

**Ramp-Up (pre-entry)** (bars -24 to -1): Winners avg=0.177494, Losers avg=0.165265, Delta=+0.012229
**Post-Trade (post-entry)** (bars 0 to 24): Winners avg=0.196444, Losers avg=0.174574, Delta=+0.021870

### CVD Slope
*Direction-normalized: positive = favorable for trade direction*

**Ramp-Up (pre-entry)** (bars -24 to -1): Winners avg=0.012411, Losers avg=0.044110, Delta=-0.031699
**Post-Trade (post-entry)** (bars 0 to 24): Winners avg=0.100704, Losers avg=-0.063524, Delta=+0.164228

## Model x Direction Breakdown

Per-indicator win rate and average value by model and direction.

### Candle Range %

| Model | Direction | Trades | Win Rate | Avg Value |
|-------|-----------|--------|----------|-----------|
| EPCH1 | LONG | 35 | 45.7% | 0.4652 |
| EPCH1 | SHORT | 40 | 47.5% | 0.5017 |
| EPCH2 | LONG | 564 | 40.1% | 0.2521 |
| EPCH2 | SHORT | 476 | 51.1% | 0.3168 |
| EPCH3 | LONG | 61 | 49.2% | 0.4788 |
| EPCH3 | SHORT | 63 | 44.4% | 0.4708 |
| EPCH4 | LONG | 816 | 49.4% | 0.2419 |
| EPCH4 | SHORT | 680 | 53.4% | 0.2836 |

### Volume Delta (5-bar)

| Model | Direction | Trades | Win Rate | Avg Value |
|-------|-----------|--------|----------|-----------|
| EPCH1 | LONG | 35 | 45.7% | 98822.4737 |
| EPCH1 | SHORT | 40 | 47.5% | -126938.5653 |
| EPCH2 | LONG | 564 | 40.1% | 3083.9442 |
| EPCH2 | SHORT | 476 | 51.1% | 10678.4386 |
| EPCH3 | LONG | 61 | 49.2% | 128006.9966 |
| EPCH3 | SHORT | 63 | 44.4% | -126553.2965 |
| EPCH4 | LONG | 816 | 49.4% | 27173.8707 |
| EPCH4 | SHORT | 680 | 53.4% | 5485.7784 |

### Vol Delta Normalized

| Model | Direction | Trades | Win Rate | Avg Value |
|-------|-----------|--------|----------|-----------|
| EPCH1 | LONG | 35 | 45.7% | 0.6507 |
| EPCH1 | SHORT | 40 | 47.5% | -1.1965 |
| EPCH2 | LONG | 564 | 40.1% | -0.2005 |
| EPCH2 | SHORT | 476 | 51.1% | -0.1801 |
| EPCH3 | LONG | 61 | 49.2% | 1.1132 |
| EPCH3 | SHORT | 63 | 44.4% | -1.2154 |
| EPCH4 | LONG | 816 | 49.4% | 0.1560 |
| EPCH4 | SHORT | 680 | 53.4% | -0.0394 |

### Volume ROC

| Model | Direction | Trades | Win Rate | Avg Value |
|-------|-----------|--------|----------|-----------|
| EPCH1 | LONG | 35 | 45.7% | 579.1901 |
| EPCH1 | SHORT | 40 | 47.5% | 329.3580 |
| EPCH2 | LONG | 564 | 40.1% | 396.1728 |
| EPCH2 | SHORT | 476 | 51.1% | 576.4619 |
| EPCH3 | LONG | 61 | 49.2% | 715.0421 |
| EPCH3 | SHORT | 63 | 44.4% | 56.8209 |
| EPCH4 | LONG | 816 | 49.4% | 207.7024 |
| EPCH4 | SHORT | 680 | 53.4% | 152.5721 |

### SMA Spread %

| Model | Direction | Trades | Win Rate | Avg Value |
|-------|-----------|--------|----------|-----------|
| EPCH1 | LONG | 35 | 45.7% | 0.2100 |
| EPCH1 | SHORT | 40 | 47.5% | 0.2175 |
| EPCH2 | LONG | 564 | 40.1% | 0.1555 |
| EPCH2 | SHORT | 476 | 51.1% | 0.2160 |
| EPCH3 | LONG | 61 | 49.2% | 0.1969 |
| EPCH3 | SHORT | 63 | 44.4% | 0.2972 |
| EPCH4 | LONG | 816 | 49.4% | 0.1606 |
| EPCH4 | SHORT | 680 | 53.4% | 0.2057 |

### CVD Slope

| Model | Direction | Trades | Win Rate | Avg Value |
|-------|-----------|--------|----------|-----------|
| EPCH1 | LONG | 35 | 45.7% | 0.0962 |
| EPCH1 | SHORT | 40 | 47.5% | -0.2139 |
| EPCH2 | LONG | 564 | 40.1% | -0.0353 |
| EPCH2 | SHORT | 476 | 51.1% | -0.0392 |
| EPCH3 | LONG | 61 | 49.2% | 0.1671 |
| EPCH3 | SHORT | 63 | 44.4% | -0.0696 |
| EPCH4 | LONG | 816 | 49.4% | 0.0572 |
| EPCH4 | SHORT | 680 | 53.4% | -0.0246 |

### SMA Configuration

| Model | Direction | Trades | Win Rate | Most Common |
|-------|-----------|--------|----------|-----------|
| EPCH1 | LONG | 35 | 45.7% | BULL |
| EPCH1 | SHORT | 40 | 47.5% | BEAR |
| EPCH2 | LONG | 564 | 40.1% | BEAR |
| EPCH2 | SHORT | 476 | 51.1% | BEAR |
| EPCH3 | LONG | 61 | 49.2% | BULL |
| EPCH3 | SHORT | 63 | 44.4% | BEAR |
| EPCH4 | LONG | 816 | 49.4% | BULL |
| EPCH4 | SHORT | 680 | 53.4% | BEAR |

### SMA Momentum

| Model | Direction | Trades | Win Rate | Most Common |
|-------|-----------|--------|----------|-----------|
| EPCH1 | LONG | 35 | 45.7% | NARROWING |
| EPCH1 | SHORT | 40 | 47.5% | WIDENING |
| EPCH2 | LONG | 564 | 40.1% | WIDENING |
| EPCH2 | SHORT | 476 | 51.1% | WIDENING |
| EPCH3 | LONG | 61 | 49.2% | NARROWING |
| EPCH3 | SHORT | 63 | 44.4% | WIDENING |
| EPCH4 | LONG | 816 | 49.4% | WIDENING |
| EPCH4 | SHORT | 680 | 53.4% | NARROWING |

### Price Position

| Model | Direction | Trades | Win Rate | Most Common |
|-------|-----------|--------|----------|-----------|
| EPCH1 | LONG | 35 | 45.7% | ABOVE |
| EPCH1 | SHORT | 40 | 47.5% | BELOW |
| EPCH2 | LONG | 564 | 40.1% | BELOW |
| EPCH2 | SHORT | 476 | 51.1% | BELOW |
| EPCH3 | LONG | 61 | 49.2% | ABOVE |
| EPCH3 | SHORT | 63 | 44.4% | BELOW |
| EPCH4 | LONG | 816 | 49.4% | ABOVE |
| EPCH4 | SHORT | 680 | 53.4% | BELOW |

### M5 Structure

| Model | Direction | Trades | Win Rate | Most Common |
|-------|-----------|--------|----------|-----------|
| EPCH1 | LONG | 35 | 45.7% | BULL |
| EPCH1 | SHORT | 40 | 47.5% | BEAR |
| EPCH2 | LONG | 564 | 40.1% | BEAR |
| EPCH2 | SHORT | 476 | 51.1% | BEAR |
| EPCH3 | LONG | 61 | 49.2% | BEAR |
| EPCH3 | SHORT | 63 | 44.4% | BEAR |
| EPCH4 | LONG | 816 | 49.4% | BULL |
| EPCH4 | SHORT | 680 | 53.4% | BEAR |

### M15 Structure

| Model | Direction | Trades | Win Rate | Most Common |
|-------|-----------|--------|----------|-----------|
| EPCH1 | LONG | 35 | 45.7% | BEAR |
| EPCH1 | SHORT | 40 | 47.5% | BEAR |
| EPCH2 | LONG | 564 | 40.1% | BEAR |
| EPCH2 | SHORT | 476 | 51.1% | BEAR |
| EPCH3 | LONG | 61 | 49.2% | BEAR |
| EPCH3 | SHORT | 63 | 44.4% | BEAR |
| EPCH4 | LONG | 816 | 49.4% | BULL |
| EPCH4 | SHORT | 680 | 53.4% | BEAR |

### H1 Structure

| Model | Direction | Trades | Win Rate | Most Common |
|-------|-----------|--------|----------|-----------|
| EPCH1 | LONG | 35 | 45.7% | BULL |
| EPCH1 | SHORT | 40 | 47.5% | BEAR |
| EPCH2 | LONG | 564 | 40.1% | BEAR |
| EPCH2 | SHORT | 476 | 51.1% | BULL |
| EPCH3 | LONG | 61 | 49.2% | BEAR |
| EPCH3 | SHORT | 63 | 44.4% | BEAR |
| EPCH4 | LONG | 816 | 49.4% | BEAR |
| EPCH4 | SHORT | 680 | 53.4% | BEAR |

## Key Observations for AI Analysis

When analyzing deep dive data, consider:
1. **Strongest predictor**: Which single indicator has the most consistent winner/loser separation across all phases?
2. **Phase transitions**: Does any indicator 'flip' behavior between ramp-up and post-trade?
3. **Model-specific edges**: Do some models benefit more from certain indicators?
4. **Direction asymmetry**: After normalization, are LONGs and SHORTs equally predictable?
5. **Leading indicators**: Which indicators diverge earliest in the ramp-up phase?