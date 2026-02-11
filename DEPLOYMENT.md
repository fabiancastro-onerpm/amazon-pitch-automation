# Process to Deploy to Streamlit Community Cloud

Since your code is already on GitHub, deploying is very easy!

1.  **Sign Up / Login**: Go to [share.streamlit.io](https://share.streamlit.io/) and sign in with your GitHub account.
2.  **New App**: Click the "New app" button.
3.  **Select Repository**:
    *   Repository: `fabiancastro-onerpm/amazon-pitch-automation`
    *   Branch: `main`
    *   Main file path: `app.py`
4.  **Configure Secrets (CRITICAL)**:
    *   Before clicking Deploy, click **"Advanced settings"**.
    *   Go to the **"Secrets"** tab.
    *   **Get your Key**: Go to [Google AI Studio](https://aistudio.google.com/app/apikey) and click "Create API key".
    *   Paste your API key in the following format:
        ```toml
        GOOGLE_API_KEY = "your-actual-api-key-here"
        ```
    *   *Note: Do not use quotes if the UI asks for key-value pairs differently, but usually TOML format is expected.*
5.  **Deploy**: Click "Deploy!".

Streamlit will install the libraries from your `requirements.txt` and launch the app. It usually takes 1-2 minutes.
