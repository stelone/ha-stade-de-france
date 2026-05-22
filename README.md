# Stade de France — Intégration Home Assistant

[![Ajouter le dépôt à HACS dans votre instance Home Assistant.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=stelone&repository=ha-stade-de-france&category=integration)

Suivez les événements à venir au **Stade de France** (concerts, rugby, football…)
dans Home Assistant et recevez une **notification 0 à 7 jours avant** chaque
événement.

Les données proviennent de la billetterie officielle
(`billets.stadefrance.com`, plateforme SecuTix). Il n'existe pas d'API publique
officielle : l'intégration **analyse la page des événements** (scraping). La mise
à jour a lieu toutes les 12 heures.

## Fonctionnalités

- 📆 **Calendrier** `calendar.*` listant tous les événements à venir.
- 🔔 **Notification intégrée** : l'intégration appelle elle-même le service
  `notify` de votre choix, X jours avant l'événement (configurable).
- 📊 **Capteurs** :
  - prochain événement (nom + attributs `start`, `type`, `availability`, `url`)
  - jours avant le prochain événement
  - nombre d'événements à venir
- ⏰ **Capteur binaire** « événement imminent » (ON si un événement est dans la
  fenêtre configurée), utile pour vos propres automatisations.

## Installation (HACS)

Le plus simple : cliquez sur le bouton **« Open your Home Assistant instance and
open a repository inside HACS »** en haut de cette page, puis installez et
redémarrez.

Sinon, manuellement dans HACS :

1. HACS → menu ⋮ → **Dépôts personnalisés**.
2. Ajoutez `https://github.com/stelone/ha-stade-de-france` (catégorie
   *Integration*).
3. Installez **Stade de France**, puis redémarrez Home Assistant.
4. **Paramètres → Appareils et services → Ajouter une intégration** →
   *Stade de France*.

### Installation manuelle

Copiez `custom_components/stade_de_france` dans le dossier `custom_components`
de votre configuration, puis redémarrez Home Assistant.

## Configuration

Après l'ajout, ouvrez les **Options** de l'intégration :

| Option | Description | Défaut |
| --- | --- | --- |
| Service de notification | Service `notify` appelé (ex. `notify.mobile_app_iphone`). Vide = aucun envoi. | — |
| Délai avant l'événement | Nombre de jours avant l'événement (0 = le jour même, max 7). | 2 |
| Heure de la notification | Heure d'envoi de la notification. | 09:00 |

La notification est envoyée une seule fois par événement (suivi persistant des
événements déjà notifiés, robuste aux redémarrages).

## Automatisation avancée (optionnel)

La notification intégrée suffit. Pour aller plus loin, vous pouvez utiliser le
capteur binaire ou le calendrier dans vos propres automatisations :

```yaml
automation:
  - alias: "Rappel événement Stade de France"
    trigger:
      - platform: state
        entity_id: binary_sensor.stade_de_france_event_upcoming
        to: "on"
    action:
      - service: notify.mobile_app_iphone
        data:
          title: "Stade de France"
          message: >-
            Prochain événement : {{ states('sensor.stade_de_france_next_event') }}
```

> Les `entity_id` ci-dessus correspondent aux identifiants par défaut ; ils
> peuvent différer selon la langue de votre instance. Vérifiez-les dans
> **Outils de développement → États**.

## Développement

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements_test.txt
pytest
```

- `tests/test_scraper.py` valide l'analyse HTML sur un échantillon réel figé
  (`tests/fixtures/events.html`) et s'exécute sans Home Assistant.
- `tests/integration/` valide le config flow, le notifier et la mise en place
  de bout en bout (nécessite `pytest-homeassistant-custom-component`).

## Limites

- Le scraping dépend de la structure HTML de SecuTix ; un changement de leur côté
  peut nécessiter une mise à jour de `scraper.py` (l'analyse est défensive et
  journalise les blocs non reconnus).
- Usage personnel, faible fréquence d'appel (toutes les 12 h).
