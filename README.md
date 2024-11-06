# IT Ticket Reply Automation System

This project automates the process of generating responses for IT helpdesk tickets. By leveraging Natural Language Processing (NLP) models, the system scrapes ticket data, summarizes email threads, and creates AI-generated replies to enhance the efficiency of IT support workflows.

## Features

- **Automated Ticket Scraping and Summarization**: Extracts ticket data and summarizes email threads using a BART model for quick and accurate response generation.
- **AI-Powered Reply Generation**: Utilizes a LLaMA model to craft responses based on the summarized email content and similar past resolutions.
- **Response Similarity Scoring**: Measures the similarity between AI-generated replies and previous resolutions using TF-IDF vectorization and cosine similarity.
- **Interactive User Prompts**: Allows users to accept the AI response, modify it with custom input, or regenerate a response.

## Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/donneypr/it-ticket-reply-automation.git
   cd it-ticket-reply-automation
   ```
