# AutoFlip 🚘

Site gratuit de détection d'opportunités automobiles.

## Installation
Activer GitHub Pages dans Settings > Pages > Deploy from a branch > main / root.

## Collecte
Le workflow GitHub Actions est programmé toutes les 30 minutes. Il ne collecte que des flux JSON HTTPS autorisés. Dans Settings > Secrets and variables > Actions > Variables, créer AUTOFLIP_FEED_URLS avec les URL des flux autorisés séparées par des virgules.

Format : {"listings":[{"id":"1","title":"Clio","price":3000,"resale_estimate":4200,"source":"Partenaire","url":"https://example.com/1"}]}

Sans flux configuré, le site affiche trois annonces fictives. Aucune extraction automatique de Leboncoin ou La Centrale n'est activée. Les estimations de revente sont fournies par le flux et non par une IA. Les marges ne comprennent que les frais saisis.
