# JARVIS

JARVIS is a modular AI assistant combining a React-based futuristic dashboard, a FastAPI backend, and local AI capabilities powered by LM Studio and OpenRouter.

## Installation

### Prerequisites
- Node.js (v18+)
- Python (3.10+)
- Git

### Windows
1. **Clone the repository:**
   ```bash
   git clone https://github.com/mohd-shariq-osmani/JARVIS.git
   cd JARVIS
   ```

2. **Setup the Backend:**
   ```bash
   cd backend
   python -m venv venv
   .\venv\Scripts\activate
   pip install -r requirements.txt
   ```
   *Note: Ensure all dependencies like `chromadb` for memory are installed within this virtual environment.*

3. **Setup the Frontend:**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Run the Application:**
   Start the backend:
   ```bash
   cd backend
   .\venv\Scripts\uvicorn main:app --reload --port 8000
   ```
   In a separate terminal, start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

### macOS
1. **Clone the repository:**
   ```bash
   git clone https://github.com/mohd-shariq-osmani/JARVIS.git
   cd JARVIS
   ```

2. **Setup the Backend:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Setup the Frontend:**
   ```bash
   cd ../frontend
   npm install
   ```

4. **Run the Application:**
   Start the backend:
   ```bash
   cd backend
   venv/bin/uvicorn main:app --reload --port 8000
   ```
   In a separate terminal, start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

## Configuring AI Providers

JARVIS supports both local and cloud-based AI models. You can configure these in the **Settings** tab of the JARVIS UI.

### LM Studio (Local AI)
1. Download and install [LM Studio](https://lmstudio.ai/).
2. Download a model of your choice (e.g., `gemma-4-e4b` or any compatible GGUF).
3. In LM Studio, navigate to the **Local Server** tab and click **Start Server**.
4. Ensure the server is running on port `1234` (the default).
5. In the JARVIS **Settings** tab, select **LM Studio** as your provider. The default local URL `http://localhost:1234/v1` will be used automatically.

### OpenRouter (Cloud AI)
1. Create an account at [OpenRouter](https://openrouter.ai/) and generate an API Key.
2. In the JARVIS **Settings** tab, select **OpenRouter** as your provider.
3. Paste your API Key into the **API Key** input field and save your settings.
