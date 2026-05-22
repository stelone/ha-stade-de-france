# Logo de l'intégration (Home Assistant brands)

Le logo affiché dans **Paramètres → Appareils et services** ne provient pas de ce
dépôt : Home Assistant le récupère sur le dépôt officiel
[`home-assistant/brands`](https://github.com/home-assistant/brands), servi via
`https://brands.home-assistant.io/`.

Les fichiers prêts à soumettre sont ici :

```
brands/custom_integrations/stade_de_france/
├── icon.png      # 256×256
└── icon@2x.png   # 512×512
```

## Soumettre le logo

1. Fork de `home-assistant/brands` sur GitHub.
2. Copie le dossier `custom_integrations/stade_de_france/` (ces deux PNG) à la
   racine du fork, au même chemin.
3. Ouvre une Pull Request. La CI vérifie : PNG, transparence, optimisation,
   image détourée (peu d'espace vide), domaine = `stade_de_france`
   (identique au `manifest.json`).
4. Une fois la PR **fusionnée**, le logo apparaît automatiquement dans HA
   (cache de quelques heures possible). Rien à changer dans l'intégration.

## Notes

- Le logo est **indépendant** de l'installation : tant que la PR n'est pas
  fusionnée, HA affiche l'icône par défaut. Impossible d'embarquer le logo
  directement dans le composant.
- `logo.png` / `logo@2x.png` (bandeau large) sont **optionnels** ; seuls les
  `icon*.png` sont nécessaires.
- L'icône fournie est un visuel **générique** (terrain + enceinte). N'utilise pas
  le logo déposé du Stade de France sans autorisation.
