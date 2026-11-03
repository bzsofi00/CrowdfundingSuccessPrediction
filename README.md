# Predicting Crowdfunding Campaign Success: A Multimodal Machine Learning Approach

## Overview

This project investigates how machine learning and multimodal data can be used to predict the success of Kickstarter campaigns using **pre-launch information only**.

The study analyses 40,301 Kickstarter campaigns and explores how structured metadata, textual descriptions and visual information contribute to predictive performance. It compares traditional machine learning algorithms, deep learning architectures, multimodal fusion strategies and a large language model (LLM).

Beyond predictive accuracy, the research examines different text representation techniques, investigates the contribution of individual data modalities and applies explainability methods to better understand the factors associated with campaign success.

The project was developed as part of my MSc thesis in Business Administration and Data Science at Copenhagen Business School (CBS).

## Project Documents

- [Full Master's Thesis](report/Masters_Thesis.pdf)
- [Thesis Defence Presentation](presentation/Thesis_Defence_Presentation.pdf)

## Research Questions

The study is guided by the following main research question:

**How can multimodal data and machine learning techniques be used to effectively predict the success of crowdfunding campaigns using only pre-launch information?**

To address this question, the research examines five sub-questions:

1. How well can crowdfunding success be predicted using only structured metadata, and which models perform best in this setting?
2. How does incorporating textual features improve predictive performance compared to metadata-only models?
3. How do multimodal approaches, including visual features, provide additional predictive value beyond textual and metadata-based models in crowdfunding success prediction?
4. Which features are the most important in predicting crowdfunding success, and how can explainability methods improve the understanding of model predictions?
5. How effectively can large language models predict and explain crowdfunding campaign success compared to traditional machine learning and deep learning approaches using text, image, and metadata features?

## Data Collection and Preparation

The initial dataset was obtained from WebRobots.io, which provides publicly collected Kickstarter campaign data. A total of 83 CSV files were consolidated into a single dataset containing 257,873 records and 110 features.

Following initial filtering, duplicate removal and feature selection, the dataset was reduced to 183,709 campaigns and 50 columns.

To enrich the structured data, publicly accessible Kickstarter campaign pages were scraped using Playwright. Campaign stories, risks and rewards were retrieved and processed using BeautifulSoup.

The data preparation pipeline included:

- Cleaning and consolidating the original datasets, including flattening nested JSON structures.
- Removing duplicates, irrelevant records and campaigns with unsuitable states.
- Cleaning HTML content and extracting textual information from campaign descriptions.
- Handling missing values and engineering additional features, including campaign duration, launch date characteristics and funding goals converted to USD.
- Filtering non-English campaigns and applying text-length and funding-goal criteria.
- Preventing temporal information leakage by excluding post-launch variables, such as backer counts, pledged amounts and platform success indicators.
- Removing outcome-revealing expressions from campaign text to ensure that predictions relied on information available before launch.

The final modelling dataset consisted of **40,301 campaigns**, with campaign success represented as a binary classification target.

## Methodology

The modelling approach was designed to compare different feature representations and combinations of data modalities.

### 1. Structured Metadata

Campaign metadata included numerical and categorical characteristics such as funding goals, campaign duration, reward tiers, category, country, currency and media-related attributes.

Preprocessing included missing-value handling, feature engineering, one-hot encoding and scaling of continuous variables.

The following traditional machine learning algorithms were evaluated:

- Logistic Regression
- Support Vector Machine (SVM)
- Decision Tree
- Random Forest
- K-Nearest Neighbours (KNN)
- XGBoost
- LightGBM
- CatBoost

### 2. Textual Features

Campaign descriptions and other textual fields were processed using multiple NLP techniques to compare keyword-based and contextual representations.

The evaluated approaches included:

- **Bag-of-Words (BoW):** Unigram and bigram frequency representations.
- **TF-IDF:** Term frequency–inverse document frequency representations using up to 8,000 features.
- **Sentence-BERT:** Pre-trained sentence embeddings using `all-MiniLM-L6-v2`.
- **Fine-tuned Transformer:** Contextual text representations extracted from a partially fine-tuned pre-trained transformer model.

Two text representation strategies were compared:

- **Unstructured representation:** Combining campaign text fields into a single document.
- **Structured representation:** Processing individual text sections separately to preserve section-specific information.

### 3. Image Features

Visual information was incorporated using campaign title images.

Images were resized to 224 × 224 pixels and processed using a pre-trained ResNet50 model without its classification layer. The resulting 2,048-dimensional embeddings were used as visual feature representations.

### 4. Deep Learning and Multimodal Fusion

Several neural network architectures were developed to investigate how structured metadata and textual representations could be combined.

The evaluated architectures included:

- Simple Concatenation
- Deep Fusion MLP
- Gated Fusion Network
- Cross-Interaction Network
- Multi-Branch Sectional Network
- Residual Multi-Branch Network

Additional tri-modal architectures integrated metadata, text and image embeddings:

- Tri-Modal Residual Multi-Branch Network
- Tri-Modal Gated Fusion Network
- Feature-Level Gated Fusion Network

These approaches explored different ways of combining information, including feature concatenation, gated weighting, cross-modal interactions and multi-branch representations.

### 5. LLM-Based Prediction

Gemini 2.5 Flash was evaluated using a few-shot multimodal prompting approach.

The model received structured campaign information, textual descriptions and campaign title images, together with two labelled examples representing successful and unsuccessful campaigns.

For each evaluated campaign, it generated:
- A binary success prediction.
- A short natural-language explanation of its prediction.

BERTopic was subsequently used to identify recurring themes in the generated explanations and examine how the LLM described successful and unsuccessful campaigns.

### 6. Evaluation and Explainability

The dataset was divided into stratified training, validation and test sets using a 70/15/15 split.

Model performance was evaluated using accuracy, precision, recall, F1 score and ROC-AUC.

Explainability was investigated through:
- **Model coefficients and feature importance:** Examining the features associated with predictions in traditional machine learning models.
- **SHAP:** Analysing feature contributions and their direction of influence on individual predictions.
- **LLM-generated explanations:** Exploring qualitative reasoning and comparing recurring themes with the quantitative findings.

## Results and Key Findings

The experiments demonstrate that structured metadata and textual information provide strong predictive signals for campaign success. The best overall performance was achieved by a relatively simple linear model combining metadata and TF-IDF text features.

### Predictive Performance

| Model configuration | Best ROC-AUC |
|---|---:|
| Metadata-only models (XGBoost / CatBoost) | 0.876 |
| Metadata + TF-IDF (Logistic Regression) | **0.904** |
| Text + metadata deep learning (Residual Multi-Branch) | 0.9002 |
| Tri-modal deep learning (Gated Fusion) | 0.9011 |

The LLM achieved **75.50% accuracy** on the evaluated subset using few-shot multimodal prompting.

### Main Findings

- **Metadata provides a strong baseline:** Structured campaign characteristics alone achieved an ROC-AUC of 0.876, demonstrating substantial predictive value even without textual or visual information.
- **Text significantly improves predictions:** Combining metadata with textual features consistently improved performance. Logistic Regression with TF-IDF achieved the best overall ROC-AUC of 0.904, with an accuracy of approximately 81.6%.
- **TF-IDF outperformed more complex text representations:** TF-IDF generally performed better than Bag-of-Words and the evaluated BERT-based embeddings, showing that keyword-level representations can be highly effective for this prediction task.
- **Model complexity did not guarantee better performance:** Deep learning architectures achieved competitive results, but none outperformed the best Logistic Regression model.
- **Structured text representations benefited neural networks:** Multi-branch architectures demonstrated the value of preserving individual campaign text sections, although the improvements over simpler approaches remained relatively modest.
- **Visual information provided limited additional value:** Multimodal models combining metadata, text and images achieved ROC-AUC scores close to 0.90, but did not surpass the best metadata + text model.
- **SHAP revealed important campaign characteristics:** Funding goal, number of reward tiers, campaign duration, campaign video and media-related features emerged as important predictors.
- **LLMs offered complementary interpretability:** Although Gemini did not match the predictive performance of traditional machine learning models, its natural-language explanations provided an accessible qualitative perspective that was broadly consistent with the quantitative findings.

Overall, the results suggest that effective feature representation and careful feature engineering can be more important than model complexity or the number of modalities incorporated.

## Research Contributions

The study makes several contributions to the analysis of crowdfunding success prediction:

- **Comparative analysis of text representations:** Investigated structured and unstructured text processing strategies and compared traditional keyword-based representations with contextual embeddings.
- **Evaluation of multimodal fusion strategies:** Developed and compared multiple architectures for integrating structured, textual and visual campaign information.
- **LLM-based classification and reasoning:** Explored the use of a large language model for multimodal success prediction while generating human-readable explanations.
- **Explainable predictive modelling:** Combined SHAP analysis and LLM-generated reasoning to provide complementary quantitative and qualitative insights into campaign success factors.
- **Pre-launch prediction framework:** Focused exclusively on information available before campaign launch, avoiding the use of post-launch signals that can artificially inflate predictive performance.

## Limitations and Future Research

- **Visual representations:** Only campaign title images and pre-trained ResNet50 embeddings were used. Future research could incorporate all campaign images and fine-tuned vision models.
- **Generalisation:** The study focuses exclusively on Kickstarter. Applying the framework to other crowdfunding platforms could help assess the generalisability of the findings.
- **Model improvements:** Further work could explore more advanced transformer representations, deep learning explainability and fine-tuned LLM approaches.

## Repository Structure

The repository contains the notebooks and scripts used throughout the research, organised according to the main stages of the project.

| File | Description |
|---|---|
| `001_CleanAndMergeData.ipynb` | Consolidating and cleaning the original datasets |
| `002_RemoveDuplicates.ipynb` | Duplicate removal and initial dataset filtering |
| `003_WebScraping.py` | Scraping publicly accessible Kickstarter campaign pages |
| `004_ScrapeCleaning.ipynb` | Cleaning and processing scraped campaign content |
| `005_5_Examine_nonenglish.ipynb` | Examining and identifying non-English campaigns |
| `005_Preprocessing.ipynb` | Data cleaning and preprocessing |
| `006_EDA.ipynb` | Exploratory data analysis |
| `007_5_Extract_images.ipynb` | Extracting and processing campaign image features |
| `007_Text_preprocessing.ipynb` | Text cleaning and feature preparation |
| `008_DataPreprocessing_splitting.ipynb` | Final feature preparation and train/validation/test splitting |
| `009_Meta_models.ipynb` | Traditional machine learning models and metadata-based experiments |
| `010_Multimodal_models.ipynb` | Deep learning and multimodal modelling experiments |
| `011_LLM.ipynb` | LLM-based predictions and explanation analysis |

Additional project documents are available in the `report/` and `presentation/` folders.

## Technologies and Methods

- **Programming:** Python
- **Data collection:** Playwright, WebRobots.io
- **Data processing:** Pandas, NumPy, BeautifulSoup
- **Machine learning:** Scikit-learn, XGBoost, LightGBM, CatBoost
- **Natural Language Processing:** TF-IDF, Bag-of-Words, spaCy, Sentence-BERT, BERT
- **Deep Learning and Computer Vision:** Neural networks, ResNet50, multimodal fusion
- **Explainable AI:** SHAP
- **Topic Modelling:** BERTopic
- **Large Language Models:** Gemini 2.5 Flash

## Academic Context

**MSc in Business Administration and Data Science**  
Copenhagen Business School (CBS)  
June 2026

**Master's Thesis:** *Predicting Crowdfunding Campaign Success: A Multimodal Machine Learning and Deep Learning Approach*
