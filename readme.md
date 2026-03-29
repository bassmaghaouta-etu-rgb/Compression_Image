# PixelOptimize — Système Multi‑Agents Intelligent pour l’Optimisation de la Compression d’Images

## Introduction

**PixelOptimize** est un système intelligent conçu pour optimiser la compression d'images en utilisant une **architecture multi‑agents** et l'intégration de **modèles de langage avancés (LLM)** comme **Groq**.

Le système analyse les caractéristiques des images, prend des décisions intelligentes concernant le **format** et la **qualité de compression optimaux**, applique les compressions, puis génère des **rapports détaillés de performance**.

---

# Architecture du Projet

Le projet se compose de deux parties principales :

## 1. Interface Utilisateur — `n8nstrm.py`

Application interactive développée avec **Streamlit** permettant :

* Téléchargement d'images
* Visualisation du pipeline de traitement
* Consultation des rapports de compression

## 2. Serveur Multi‑Agents — `server_groq.py`

Serveur **Flask API** qui :

* Héberge les agents intelligents
* Gère le traitement des images
* Intègre le modèle LLM Groq

### Agents Implémentés

* **Agent Analyste** → Analyse des caractéristiques de l'image
* **Agent Décideur** → Choix du format optimal via LLM
* **Agent Comparateur** → Decision finale
* **Agent Exécuteur** → Application de la compression
* **Agent Rapporteur** → Génération des rapports détaillés

---

# Fonctionnalités

## Optimisation Intelligente

Utilisation d'agents IA et de LLM pour déterminer :

* Format optimal
* Qualité optimale
* Type de compression

## Formats Supportés

* JPEG
* PNG
* WebP
* AVIF
* HEIF *(via pillow‑heif)*

## Analyse Avancée

Calcul des métriques :

* SSIM
* PSNR
* MSE
* Taux de compression (τ%)

## Interface Interactive

Application Streamlit conviviale et intuitive.

## Rapports Automatiques

Génération de rapports détaillés incluant :

* Analyse initiale
* Décisions IA
* Résultats de compression
* Métriques de performance

---

# Portabilité et Prérequis

PixelOptimize nécessite une configuration préalable.

## Prérequis

### 1. Python

* Python 3.x requis

### 2. Dépendances Python

Installer les dépendances :

```bash
pip install -r requirements.txt
```

### 3. Serveur Flask

Le serveur doit être lancé sur :

```
http://127.0.0.1:5000
```


### 4. n8n

Webhook utilisé :

```
http://localhost:5678/webhook/compression-pipeline
```

Une instance **n8n locale** est requise pour le pipeline complet.

### 5. Tesseract OCR

PixelOptimize utilise **Tesseract OCR** pour l'analyse d'image.

Installation selon le système :

#### Windows

Télécharger depuis :

Tesseract-OCR GitHub

#### macOS

```bash
brew install tesseract
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt-get install tesseract-ocr
```

Configuration du chemin :

```python
import os
os.environ["TESSERACT_PATH"] = "/usr/local/bin/tesseract"
```

---

# Installation

## 1. Cloner le projet

```bash
git clone <repo-url>
cd PixelOptimize
```

## 2. Installer les dépendances

```bash
pip install -r requirements.txt
```

## 3. Installer Tesseract OCR

Voir section précédente.

## 4. Configurer n8n

* Installer n8n
* Lancer n8n
* Importer les workflows fournis

---

# Utilisation

## 1. Lancer le serveur Flask

```bash
python server_groq.py
```

Serveur disponible sur :

```
http://0.0.0.0:5000
```

---

## 2. Lancer l'application Streamlit

Dans un deuxième terminal :

```bash
streamlit run n8nstrm.py
```

Le navigateur s'ouvre automatiquement.

---

## 3. Utilisation de l'Interface

### Télécharger les Images

Uploader les images à optimiser.

### Visualiser le Pipeline

Suivre les étapes des agents :

* Analyse
* Décision
* Compression
* Rapport

### Consulter les Rapports

Accès aux métriques :

* Taille avant/après
* Qualité
* Ratio de compression
* Format choisi

---

# Dépannage

## Problèmes Courants

### ModuleNotFoundError

Installer les dépendances :

```bash
pip install -r requirements.txt
```

---

### TesseractNotFoundError

Vérifier :

* Installation de Tesseract
* Variable `TESSERACT_PATH`

---

### Problèmes Serveur Flask

Vérifier :

* Serveur lancé
* Port 5000 disponible

---

### Problèmes n8n

Vérifier :

* n8n actif
* Webhook configuré

---

### HEIF / AVIF non supporté

Installer :

```bash
pip install pillow-heif pillow-avif-plugin
```

---

# Difficultés Potentielles

* Configuration environnement
* Dépendances système
* Performance lente
* Configuration n8n
* Permissions fichiers

---

# Structure du Projet

```
PixelOptimize/
├── n8nstrm.py
├── server_groq.py
├── requirements.txt
├── PixelOptimize_Logo_2.png
├── users.json
├── database-projet/
└── rapports/
    ├── resume_global.json
    └── <nom_image>_rapport.json
```

---

# Technologies Utilisées

* Python
* Streamlit
* Flask
* Groq LLM
* n8n
* Tesseract OCR
* Pillow
* Scikit-image

---

# Auteurs

**Équipe 4**
Université Hassan II · FSTM

---



# PixelOptimize

Système Intelligent Multi‑Agents pour l’Optimisation de Compression d’Images

---
