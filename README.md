# ProjetS1S2

Jeu 2D en Python avec Pygame.

## Installation

```bash
pip install -r requirements.txt
```

## Lancement

```bash
python Main.py
```

## Contrôles

| Touche | Action |
|--------|--------|
| Flèches / ZQSD | Se déplacer |
| ESPACE | Attaquer |
| ESC | Menu |

## Fonctionnalités

- Mode solo
- Mode multijoueur (Host/Client)
- Système de combat
- Collisions avec les murs

## MàJ d'iana
### 20/03/26
Ce qui change :
- Ajout des GIFs :D
- Ajout des images, notamment le profil du joueur
- Play : Ajout du score et du timer
- Play : les mobs sont générés à intervalle aléatoire, 3 mobs max sur scène
- Play : pas de victoire au cours d'une partie, que Game Over
- Ajout de la page paramètre
- Ajout des paramètres 'Résolution de fenètre', 'Taille du texte' et 'Langue'

### 17-18/04/26
Ce qui change :
- Ajout des 3 autres joueurs pour le multi
    - Ajout d'une page lobby (en construction)
    - Ajout des images des 3 autres skins (3 autres joueurs) pendant la partie

- Ajout des images des 3 autres mobs, notamment la bactérie, le virus et le caillot
- Correction de lecture des animations des monstres (notamment les gifs "wasd") en cours...
- Modifications sur le profil pendant la partie (UI)
- Suppression du paramètre "taille du texte", il s'avère moche..

### 26/05/26
Ce qui change :
- màj du titre : désormais une image ! :D
- ajout des polices par doute de choix dsl
    - 'PixelOpertor' est désormais la police de corps par défaut
    - 'PressStart2P' reste pour les titres et les boutons
- correction de l'interface multijoueur
    - page lobby prête!
- ajout d'une indication "Chargement"
- màj langues
    - EN et FR sont désormais faciles à basculer :D
    - FR : suppression des accents pour la lisibilité avec 'PressStart2P'
- correction de l'interface de la page Paramètres
- ajout d'un paramètre "Disposition clavier" pour basculer entre ZQSD et WASD

- le joueur peut dash avec la touche MAJ !
- correction de l'interface en partie
- correction du cooldown
    auparavant 1s dans le jeu vaut 2s réelles bruv
- bazar de Chrom : ajout du bouton "Merci" pour quitter son shop :3