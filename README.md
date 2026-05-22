# Interférences — documentation

Carnet musique & écriture. HTML statique, CSS global partagé, hébergé sur GitHub Pages.

---

## Structure

```
interferences/
├── index.html            ← page principale : navigation + fetch des contenus
├── interferences.css     ← feuille de style globale (partagée par toutes les pages)
├── README.md
├── journal/
│   ├── YYYY-MM-DD-slug.html
│   └── ...
```

---

## Principes

- `index.html` est la page principale. Les entrées journal et les sections transversales y sont chargées à la volée via `fetch` — rien ne se recharge, tout reste sur une page.
- `interferences.css` est le seul fichier de style. Toute modification CSS se répercute sur l'ensemble du site.
- Tous les chemins sont **relatifs**. Le repo peut être renommé ou déplacé sans rien casser.

---

## Nommage des entrées journal

```
YYYY-MM-DD-slug.html
```

Exemples :
```
2026-03-20-daft-punk.html
2026-03-20-autechre.html
2026-02-26-eliane-radigue.html
```

La date en préfixe garantit l'ordre chronologique naturel dans le dossier. Plusieurs entrées à la même date sont possibles — le slug les distingue. Plusieurs entrées sur le même sujet à des dates différentes sont explicitement prévues.

---

## Workflow pour une nouvelle entrée journal

1. Produire l'entrée avec Claude dans le projet
2. Télécharger le fichier `YYYY-MM-DD-slug.html` et le placer dans `journal/`
3. Ajouter le bloc suivant dans `index.html`, en tête de la liste Journal (ordre chronologique inverse) :

```html
<div class="entry-toggle" data-src="journal/YYYY-MM-DD-slug.html">
  <span class="entry-date">JJ mois AAAA</span>
  <span class="entry-title">Titre de l'entrée</span>
  <span class="toggle-hint">↓ ouvrir</span>
</div>
<div class="entry-content"></div>
```

4. Pusher — GitHub Pages publie automatiquement.

---

## Workflow pour une mise à jour d'entrée journal existante

1. Fournir à Claude le fichier HTML de l'entrée concernée
2. Télécharger le fichier mis à jour
3. Remplacer le fichier dans `journal/`
4. Pusher — pas de modification de `index.html` nécessaire

---

## Workflow CSS

Toute modification du style se fait dans `interferences.css` uniquement.

---

## Conventions typographiques dans le HTML

| Élément | Classe CSS | Police | Usage |
|---|---|---|---|
| Corps de texte (voix auteur) | `.author-voice` | Playfair Display | Texte de l'auteur, formulations directes |
| Observations | `.observation` | DM Mono | Apports extérieurs, analyses |
| Citation de tiers | `<blockquote>` | Playfair Display italic | Citations d'artistes, d'interviewés |
| Date d'entrée | `.entry-date` | DM Mono | Méta |
| Titre d'entrée | `.entry-title` | DM Mono | Titres des entrées journal et sections |

Albums : `<em>Titre</em>`

Morceaux : entre guillemets dans le texte, sans balise spécifique.

Formulations de l'auteur : dans le texte, sans guillemets ajoutés par le HTML.

Observations : dans le texte, sans tiret long ajouté par le HTML.

Spécificité de `transmissions.html` : voix principale en `<p class="observation">`, citations de l'auteur en `<p class="author-voice"><em>« ... »</em></p>` (paragraphe seul) ou `<em>« ... »</em>` intégré dans un `<p class="observation">`.
