# Walkthrough - Amazon Maestro Automation

## Setup
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
2.  **Configure API Key**:
    -   Open `.env.example`, rename it to `.env` (or create a new `.env` file).
    -   Add your Google Gemini API Key:
        ```
        GOOGLE_API_KEY=your_actual_api_key_here
        ```

## Running the App
1.  Run the Streamlit app:
    ```bash
    streamlit run app.py
    ```

## Usage Guide
1.  **Paste Data**: Copy your unstructured music release info and paste it into the text area.
2.  **Parse**: Click "Parse Data". Gemini will extract the fields.
3.  **Review**:
    -   Check the "Review & Validate" section.
    -   **ISRC**: Must be a valid 12-character alphanumeric code. If invalid, you will see an error and cannot proceed.
    -   **Country**: Verify the country name/code is correct.
    -   **Label**: Defaults to "ONErpm" but can be changed.
    -   **Release Type**: Mapped to "New Single", "New Album", or "New EP" based on keywords (e.g., "Album + Video").
4.  **Generate Script**: Once verified, click "Generate Script".
    -   **Auto-Open**: The Amazon Label Portal will automatically open in a new tab.
5.  **Automate**:
    -   Copy the JavaScript code from the app.
    -   Go to the opened Amazon tab.
    -   Open the Browser Console (F12).
    -   Paste and hit Enter.
    -   **Submit**: The script will fill the data and ask for confirmation to click the "Submit" button automatically.

## Notes
-   The JavaScript uses generic selectors (`name="Primary_Artist"`, etc.). If Amazon changes their form or uses different IDs, the script might need adjustment.
