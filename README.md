# Social Media Moderation Analytics

## Project Overview

This project is a Python-based social media moderation analytics system designed to process, analyse and visualise moderation-related data.

The system combines data preprocessing, statistical analysis, data visualisation, JSON persistence and an interactive Tkinter interface to explore patterns in social media moderation activity.

The project demonstrates an end-to-end Python workflow from raw data processing to interactive analytical outputs.

## Project Objectives

- Clean and integrate social media datasets
- Transform raw data into analysis-ready structures
- Analyse patterns in content moderation and user reports
- Explore relationships between moderation levels and reporting behaviour
- Generate statistical summaries and visualisations
- Store processed data using JSON
- Provide an interactive desktop interface using Tkinter
- Maintain an audit log of user interactions
- Consider responsible and transparent use of automated moderation analytics

## Key Features

- Data loading and preprocessing with Pandas
- Data cleaning and dataset integration
- Statistical and categorical analysis
- Correlation analysis
- Data visualisation with Matplotlib
- JSON data persistence
- Interactive Tkinter GUI
- Event-driven user interactions
- Audit logging
- Modular Python implementation

## Analysis Results

The analytics pipeline generates several visualisations to explore posting behaviour, moderation patterns and user reporting activity.

### Posting Activity by Hour and Topic

This heatmap shows how posting activity varies across topics throughout the day.

<img src="outputs/posting_pivot.png" alt="Posting Activity by Hour and Topic" width="700">

### Report Rate by Moderation Level

Report rates were compared across low, medium and high moderation levels. The observed correlation was approximately **-0.15**, indicating only a weak negative relationship in this dataset.

<img src="outputs/report_correlation.png" alt="Report Rate by Moderation Level" width="600">

### Report Counts by Topic and Moderation Level

This heatmap highlights differences in report volumes across topics and moderation levels.

<img src="outputs/report_heatmap.png" alt="Report Counts by Topic and Moderation Level" width="600">

### Media Presence, Category and Moderation Level

Posts were also compared by media presence, content category and moderation level.

<img src="outputs/categorical_analysis.png" alt="Post Count by Media Presence, Category and Moderation Level" width="700">

## Technologies & Skills

- Python
- Pandas
- NumPy
- Matplotlib
- Tkinter
- JSON
- Data Cleaning
- Data Transformation
- Statistical Analysis
- Data Visualisation
- Event-Driven Programming
- GUI Development
- Audit Logging
- Responsible Data Analytics

## Disclaimer

This repository is a portfolio project demonstrating Python programming, data analytics and software development concepts using a social media moderation scenario.

The system is intended for portfolio demonstration purposes and should not be used as an automated moderation or decision-making system in real-world environments.
