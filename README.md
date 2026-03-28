# 🕵️ Fake News Detection App

> A deep learning web app that classifies news articles as **real or fake** — with special focus on Kenyan news sources often missed by global models.

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.18-FF6F00?style=flat&logo=tensorflow&logoColor=white)](https://tensorflow.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Cloud-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Firebase](https://img.shields.io/badge/Firebase-Firestore-FFCA28?style=flat&logo=firebase&logoColor=black)](https://firebase.google.com)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=flat)](#license)
[![Status](https://img.shields.io/badge/Status-Live-22C55E?style=flat)]()

<!-- Replace the line below with your actual demo GIF -->
![App Demo](assets/demo.gif)

---

## 📑 Table of Contents

- [About the Project](#about-the-project)
- [Live Demo](#live-demo)
- [Key Features](#key-features)
- [Architecture & Tech Stack](#architecture--tech-stack)
- [Dataset](#dataset)
- [Model Performance](#model-performance)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## About the Project

Misinformation is a growing crisis, and in regions like Kenya, locally relevant news verification tools are almost nonexistent. Most fake news detection models are trained exclusively on Western news datasets, making them unreliable for Kenyan and East African news contexts.

This project addresses that gap by:

1. **Training a Bidirectional LSTM** on a merged dataset of 43,000+ articles spanning global and Kenyan sources
2. **Building a custom web scraper** that pulls real-time articles from Kenya's top news outlets
3. **Deploying a full-stack web app** with persistent user authentication and a clean, dark-themed UI

The result is a tool that anyone can use to paste a news article, get an instant prediction.

---

## 🚀 Live Demo

👉 **[Open the app on Streamlit Cloud](https://donlstm.streamlit.app)**

> Try pasting any news headline or full article text. The model returns a **Real** , **Fake** or **Uncertain** label with a confidence score.

![App Screenshot](assets/screenshot.png)

---

## Key Features

- **Bidirectional LSTM model** — captures context from both directions in a sequence, making it more powerful than a standard LSTM for text classification
- **Kenyan news scraper** — a custom-built scraper targeting [Nation Africa](https://nation.africa), [Standard Media](https://standardmedia.co.ke), and [The Star Kenya](https://the-star.co.ke)
- **Merged multi-source dataset** — combines global Kaggle datasets with locally scraped and historical Kenyan news for broader coverage
- **Firebase Firestore authentication** — persistent, cloud-based user authentication that works reliably on Streamlit Cloud's ephemeral filesystem
- **Dark themed UI** — custom Streamlit CSS with a deep purple gradient palette (`#0f0c29` → `#302b63`) and Syne font for a polished look
- **Real-time prediction** — confidence score output alongside the Real/Fake label
- **Git LFS managed** — large model files (`.keras`, tokenizer) tracked with Git LFS for clean repository management

---

## Architecture & Tech Stack

```
News Article (text input)
        │
        ▼
  Text Preprocessing
  (lowercase → clean → tokenize → pad sequences)
        │
        ▼
  Keras Tokenizer (fitted on training data)
        │
        ▼
  Embedding Layer
        │
        ▼
  Bidirectional LSTM
        │
        ▼
  Dense + Dropout layers
        │
        ▼
  Sigmoid output → Real (< 0.5) / Fake (≥ 0.5)
        │
        ▼
  Streamlit App (with Firebase auth)
```

| Layer | Technology |
|---|---|
| Model | Bidirectional LSTM — TensorFlow/Keras 2.18 |
| Frontend | Streamlit |
| Authentication & Database | Firebase Firestore |
| Language | Python 3.11 |
| Deployment | Streamlit Cloud |
| Data Collection | Custom BeautifulSoup scraper |
| Model Storage | Git LFS (`.keras` + tokenizer pickle) |

---

## Dataset

The model was trained on a unified dataset assembled from four distinct sources:

| Source | Type | Description |
|---|---|---|
| [Kaggle - True News](https://www.kaggle.com/clmentbisaillon/fake-and-real-news-dataset) | Real | Reuters articles, global coverage |
| [Kaggle - Fake News](https://www.kaggle.com/clmentbisaillon/fake-and-real-news-dataset) | Fake | PolitiFact-labelled fake articles |
| Kenya scraped news | Real | Scraped from Nation Africa, Standard Media, The Star |
| Kenya historical news | Real | Archived Kenyan news articles |

**Preprocessing pipeline:**
- Lowercasing and punctuation removal
- Stopword filtering
- Keras `Tokenizer` with a vocabulary cap of 10,000 words
- Sequence padding to a fixed max length
- 80/20 train-validation split

> The Kenyan data was the hardest to source and clean — it's what makes this model meaningfully different from off-the-shelf solutions.

---

## Model Performance

| Metric | Score |
|---|---|
| Accuracy | 99.18% |
| AUC-ROC | 99.96% |
| Average Precision | 99.96% |
|F1 score | 99.18% |


![Training Curves](assets/training_curves.png)

<!-- Add a confusion matrix if available -->
<!-- ![Confusion Matrix](assets/confusion_matrix.png) -->

> **Note on overfitting:** Early stopping and dropout regularization were applied to prevent the model from memorizing training data. Validation accuracy is the metric that matters most here.

---

## Getting Started

### Prerequisites

- Python **3.11** (TensorFlow 2.18 requires this exact version)
- A Firebase project with **Firestore** enabled
- Git LFS installed (`git lfs install`)

### Installation

```bash
# 1. Clone the repository (LFS files will download automatically)
git clone https://github.com/donkshel/Fake_Real_News_Detection_LSTM.git
cd Fake_Real_News_Detection_LSTM

# 2. Install dependencies
pip install -r requirements.txt
```

### Firebase Setup

1. Go to [Firebase Console](https://console.firebase.google.com) → create a project
2. Enable **Firestore Database** in test mode
3. Go to Project Settings → Service Accounts → Generate a new private key
4. Save the JSON as `firebase-credentials.json` in the project root

### Environment Variables

Create a `.streamlit/secrets.toml` file (for local development):

```toml
[firebase]
type = "service_account"
project_id = "your-project-id"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "your-client-id"
```

> For Streamlit Cloud deployment, paste these same values into the **Secrets** section of your app settings.

### Running the App

```bash
streamlit run news_app.py
```

The app will open at `http://localhost:8501`.

---

## Project Structure

```
fake-news-detection/
│
├── news_app.py                  # Main Streamlit application
├── requirements.txt        # Python dependencies
│
├── model/
│   ├── lstm_model.keras     # Trained Keras model (tracked with Git LFS)
│   └── tokenizer.pickle       # Fitted Keras tokenizer (tracked with Git LFS)
│
├── scraper/
│   └── scraper.py   # Web scraper for Kenyan news sites
│
├── data/
│   ├── True.csv 
│   ├── Fake.csv
│   ├── kenya.csv
│   └── news.csv
│
├── notebooks/
│   └── LSTM_Based_Fake_News_Detection.ipynb   # Training, evaluation, and analysis
│
├── assets/
│   ├── demo.gif
│   └── screenshot.png
│
└── .gitattributes          # Git LFS tracking rules
```

---

## Roadmap

- [x] Train Bidirectional LSTM on merged dataset
- [x] Deploy Streamlit app to Streamlit Cloud
- [x] Migrate authentication from SQLite to Firebase Firestore
- [x] Build Kenyan news scraper


---

## Contributing

Contributions are welcome! If you'd like to improve the model, add new data sources, or enhance the UI:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -m "feat: describe your change"`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Open a Pull Request

Please open an **issue** first if you're planning a major change, so we can discuss it.

---

## License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for details.

---

<p align="center">
  Built by <a href="https://github.com/donkshel">Sheldon Vwinah Kenyani</a> · Powered by TensorFlow, Streamlit & Firebase
</p>
