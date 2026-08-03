# Bot Telegram — signaux 1xGames

Bot Python 3.10+ / Windows qui publie des photos avec légende dans un canal Telegram. Les colonnes sont tirées au hasard entre 1 et 5 : elles ne constituent pas une prédiction et ne garantissent aucun gain.

## Installation PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
notepad .env
python bot.py
```

Dans `.env`, renseigner le token obtenu auprès de BotFather et `CHANNEL_ID` (par exemple `@mon_canal`). Le bot doit être administrateur du canal avec le droit de publier. `TIMEZONE=Africa/Porto-Novo` est adapté à Cotonou. Si Windows signale un fuseau manquant : `pip install tzdata`.

Les images doivent être nommées exactement :

```text
assets/images/swamp_land.png
assets/images/kamikaze.png
assets/images/apple_of_fortune.png
assets/images/dragons_gold.png
assets/images/eastern_night.png
```

Le bot refuse de publier si une image manque. Utilisez uniquement des visuels dont vous détenez les droits.

## Planning

Le bot publie à T−7 minutes, et affiche T–T+5 : Swamp Land à :00, Kamikaze à :20, Apple of Fortune à :40, Dragon's Gold à :00 de l'heure impaire, Eastern Night à :30 de l'heure impaire. Les jobs se répètent toutes les 2 heures.

## Test sans envoyer

Dans `.env`, mettre `DRY_RUN=true`, puis lancer `python bot.py`. Les captions apparaissent dans PowerShell. Remettre `false` ensuite.

## Exécution en arrière-plan

Créer `run_background.ps1` :

```powershell
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Start-Process -FilePath "$root\venv\Scripts\pythonw.exe" `
  -ArgumentList "`"$root\bot.py`"" -WorkingDirectory $root
```

Lancer avec :

```powershell
powershell -ExecutionPolicy Bypass -File .\run_background.ps1
```

Pour démarrer automatiquement, créer une tâche :

```powershell
schtasks /Create /TN "1xGames Telegram Bot" /SC ONSTART /DELAY 0000:30 /TR "powershell.exe -ExecutionPolicy Bypass -File C:\chemin\run_background.ps1" /F
```

Pour diagnostiquer, lancer `python bot.py` au premier démarrage plutôt que `pythonw.exe`. Pour arrêter le processus en arrière-plan : `Get-Process pythonw | Stop-Process`.

## Notes

- Le script utilise `aiogram 3`, `APScheduler` et `zoneinfo`.
- Les erreurs d’API sont visibles dans les logs ; un superviseur Windows ou une tâche planifiée peut être utilisé pour relancer le bot.
- Vérifiez la conformité locale, les règles de Telegram et les obligations liées à la promotion de jeux d’argent avant diffusion.
