# Buyback-10 Strategie - Detaillierte Erklärung

## Überblick

Die Buyback-10 Strategie ist eine trendfolgende Handelsstrategie, die auf einem gleitenden 200-Tage-Durchschnitt (MA200) basiert. Sie kombiniert klassische Moving-Average-Signale mit einer automatischen Rückkauf-Logik nach 10 Tagen.

## Strategie-Regeln

### 1. Basis-Signal: MA200 (Moving Average 200)
- Der MA200 ist der Durchschnitt der letzten 200 Schlusskurse
- Er zeigt den langfristigen Trend an

### 2. Verkauf-Signal
**Verkaufen**, wenn:
- Der Schlusskurs **unter** den MA200 fällt (Cross below)
- Signal wird am Schlusskurs erkannt
- Verkauf erfolgt am **Eröffnungskurs des nächsten Tages**

### 3. Wartezeit nach Verkauf
- Nach dem Verkauf beginnt eine **10-Tage-Wartezeit**
- Es werden **Handelstage** gezählt (keine Wochenenden/Feiertage)

### 4. Rückkauf-Signale
**Zurückkaufen**, wenn eine dieser Bedingungen erfüllt ist:

**Option A - Vorzeitiger Rückkauf:**
- Der Schlusskurs steigt **über** den MA200 (Cross above)
- → Sofortiger Kauf (wartet nicht die 10 Tage ab)

**Option B - Automatischer Rückkauf:**
- 10 Handelstage sind vergangen
- → Automatischer Kauf, **auch wenn** der Preis noch unter MA200 ist

## Wichtig: Lookahead-Bias Vermeidung

Die Strategie vermeidet unrealistische Annahmen:

- **Signal-Erkennung**: Verwendet den **Schlusskurs** (Close) des Tages
- **Ausführung**: Handel findet am **Eröffnungskurs** (Open) des **nächsten Tages** statt

**Warum?** In der Realität siehst du das Signal am Ende des Tages, kannst aber erst am nächsten Morgen handeln.

## Konkretes Beispiel

### Szenario: Verkauf und 10-Tage-Wartezeit

**Ausgangssituation:** 
- Du bist investiert (100 Aktien von SPY)
- Startkapital: $10,000

| Tag | Datum | Schlusskurs | MA200 | Event | days_since_sell | Position | Aktion | Kontostand |
|-----|-------|-------------|-------|-------|-----------------|----------|--------|------------|
| 0 | 5. Jan | $425 | $425 | Invested | - | Long (100 Aktien) | - | ~$42,500 |
| **1** | **6. Jan** | **$420** | **$425** | **Cross Below!** | 0 | Long → Cash | **Verkaufe** am 7. Jan zu $418 (Open) | **$41,800** |
| 2 | 7. Jan | $418 | $424 | Below MA | 1 | Cash | Warte (1/10) | $41,800 |
| 3 | 8. Jan | $415 | $423 | Below MA | 2 | Cash | Warte (2/10) | $41,800 |
| 4 | 9. Jan | $410 | $422 | Below MA | 3 | Cash | Warte (3/10) | $41,800 |
| 5 | 10. Jan | $412 | $421 | Below MA | 4 | Cash | Warte (4/10) | $41,800 |
| 6 | 13. Jan | $408 | $420 | Below MA | 5 | Cash | Warte (5/10) | $41,800 |
| 7 | 14. Jan | $405 | $419 | Below MA | 6 | Cash | Warte (6/10) | $41,800 |
| 8 | 15. Jan | $407 | $418 | Below MA | 7 | Cash | Warte (7/10) | $41,800 |
| 9 | 16. Jan | $410 | $417 | Below MA | 8 | Cash | Warte (8/10) | $41,800 |
| 10 | 17. Jan | $412 | $416 | Below MA | 9 | Cash | Warte (9/10) | $41,800 |
| **11** | **20. Jan** | **$415** | **$415** | **10 Tage vorbei!** | **10** | **Cash → Long** | **Kaufe** am 21. Jan zu $417 (Open) | 100 Aktien @ $417 |

### Erklärung der Schlüsseltage:

**Tag 1 (6. Januar):**
- Schlusskurs $420 < MA200 $425 → **Cross Below** Signal!
- Signal wird erkannt, aber noch keine Aktion

**Tag 2 (7. Januar):**
- Order wird am **Eröffnungskurs** ausgeführt: Verkaufe zu $418
- Du hast jetzt $41,800 in Cash
- `days_since_sell` = 1 (Zähler startet)

**Tage 2-10:**
- Preis bleibt unter MA200
- Zähler läuft hoch: 1, 2, 3, ..., 9, 10
- Keine Aktion, nur warten

**Tag 11 (20. Januar):**
- `days_since_sell` = 10 → **Rückkauf-Bedingung erfüllt!**
- Preis ist immer noch unter MA200 ($415 < $415)
- Trotzdem: Automatischer Rückkauf

**Tag 12 (21. Januar):**
- Kaufe 100 Aktien zum **Eröffnungskurs** von $417
- Du bist wieder investiert

## Alternative: Vorzeitiger Rückkauf

Was wäre, wenn der Preis vorher über den MA200 gestiegen wäre?

| Tag | Datum | Schlusskurs | MA200 | Event | days_since_sell | Position | Aktion |
|-----|-------|-------------|-------|-------|-----------------|----------|--------|
| ... | ... | ... | ... | ... | ... | ... | ... |
| 7 | 14. Jan | $405 | $419 | Below MA | 6 | Cash | Warte (6/10) |
| **8** | **15. Jan** | **$420** | **$418** | **Cross Above!** | **7** | **Cash → Long** | **Kaufe zurück** |

→ Bei Tag 8 würde sofort gekauft, da der Preis über MA200 steigt (Cross Above)  
→ Die 10-Tage-Wartezeit wird abgebrochen

## Code-Referenz

Die Logik findest du in `strategies/buyback.py`:

```python
# Zeilen 87-102: Kauf-Logik
if prev_pos == 0:  # Currently in cash
    # Buy if: cross above MA OR wait_days have passed since sell
    if cross_up == 1:
        current_pos = 1  # Vorzeitiger Rückkauf bei Cross Above
        days_since_sell = 0
    elif days_since_sell >= wait_days:  # Automatischer Rückkauf nach 10 Tagen
        current_pos = 1
        days_since_sell = 0
    else:
        current_pos = 0
        days_since_sell += 1  # Zähler erhöhen

# Zeilen 103-110: Verkauf-Logik
else:  # Currently long
    # Sell if cross below MA
    if cross_down == 1:
        current_pos = 0
        days_since_sell = 1  # Zähler starten
    else:
        current_pos = 1
        days_since_sell = 0
```

## Vorteile der Strategie

1. **Automatischer Wiedereinstieg**: Verpasst keine längeren Aufwärtsbewegungen
2. **Trendfolgend**: Verkauft bei Abwärtstrends (unter MA200)
3. **Zeitbasierte Sicherheit**: Kommt nach maximal 10 Tagen zurück in den Markt
4. **Flexibel**: Kann sofort zurückkaufen, wenn Preis über MA200 steigt

## Nachteile / Risiken

1. **Whipsaw**: Häufige Hin- und Her-Trades bei volatilen Märkten um MA200
2. **Garantierter Rückkauf**: Kauft nach 10 Tagen zurück, auch wenn Downtrend anhält
3. **Lag**: MA200 ist ein nachlaufender Indikator - reagiert verzögert
4. **Transaktionskosten**: Viele Trades können Gebühren summieren

## Parameter

- **Symbol**: Standard ist `SPY` (S&P 500 ETF)
- **MA Period**: Standard 200 Tage (konfigurierbar)
- **Wait Days**: Standard 10 Tage (konfigurierbar)
- **Initial Cash**: Standard $10,000

## Verwendung

```bash
python master.py --strategy buyback --symbol SPY --years 5
```

Oder im Code:

```python
from strategies.buyback import backtest_buyback

result = backtest_buyback(
    symbol="SPY",
    years=5,
    initial_cash=10_000,
    ma_period=200,
    wait_days=10
)

print(f"Total Return: {result.total_return * 100:.2f}%")
print(f"CAGR: {result.cagr * 100:.2f}%")
print(f"Max Drawdown: {result.max_drawdown * 100:.2f}%")
```
