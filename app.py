import streamlit as st
import os
from dotenv import load_dotenv
import google.generativeai as genai
import json
import pycountry
import re
import webbrowser

# Load environment variables
load_dotenv()

# Configure Gemini API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    st.error("Google API Key not found. Please set it in the .env file.")
    st.stop()

genai.configure(api_key=api_key)

# App Configuration
st.set_page_config(page_title="Amazon Maestro Automation", layout="wide")

st.title("Amazon Maestro Pitching Automation")

# --- Helper Functions ---
def clean_json_response(response_text):
    """Cleans the response text to ensure it's valid JSON."""
    # Remove markdown code blocks if present
    text = re.sub(r"```json", "", response_text)
    text = re.sub(r"```", "", text)
    return text.strip()

def validate_isrc(isrc):
    """Validates ISRC format (CC-XXX-YY-NNNNN or similar without hyphens)."""
    if not isrc:
        return False
    # Standard regex (2 alpha, 3 alphanumeric, 2 digit, 5 digit)
    # Removing hyphens for validation
    clean_isrc = isrc.replace("-", "").upper()
    return bool(re.match(r"^[A-Z]{2}[A-Z0-9]{3}[0-9]{7}$", clean_isrc))

def get_country_name(code):
    """Converts ISO A-2 code to full country name."""
    try:
        country = pycountry.countries.get(alpha_2=code.upper())
        return country.name if country else None
    except:
        return None

def apply_business_logic(data):
    """Applies specific mapping rules and defaults."""
    
    # Defaults
    data["label"] = "ONErpm"
    data["latin_audience"] = "Yes"
    
    # Genre Mapping
    genre = data.get("genre", "")
    genre_map = {
        "Popular": "Regional Mexican",
        "trapmambo": "Urbano",
        "Electrónica": "Electronic",
        "Cumbia": "Tropical"
    }
    # Case-insensitive check for keys could be better, but staying simple for now
    data["genre"] = genre_map.get(genre, genre)

    # Release Type Mapping
    rtype = data.get("release_type", "").strip()
    # Normalize to avoid case issues
    rtype_lower = rtype.lower()
    
    if "single + video" in rtype_lower:
        data["release_type"] = "New Single"
    elif "album + video" in rtype_lower:
        data["release_type"] = "New Album" 
    elif "ep + video" in rtype_lower:
        data["release_type"] = "New EP"
    elif not rtype:
         data["release_type"] = "New Single"

    # Country Validation/Fix
    cc = data.get("country_code", "")
    if cc:
        # If it's a full name, try to find code, else if code, get name
        if len(cc) == 2:
             full_name = get_country_name(cc)
             # If valid code, keep it (or store name if needed? 
             # Requirement says "convert ISO A-2 codes... into full country names")
             if full_name:
                 data["country_name"] = full_name
             else:
                 data["country_name"] = "" # Invalid code
        else:
             # Maybe LLM returned full name?
             try:
                 c = pycountry.countries.search_fuzzy(cc)
                 if c:
                     data["country_name"] = c[0].name
                     data["country_code"] = c[0].alpha_2
             except:
                 data["country_name"] = ""

    return data

# --- Main App Logic ---

# 1. Input Section
st.subheader("1. Paste Release Data")
raw_text = st.text_area("Paste unstructured text here:", height=200)

if "parsed_data" not in st.session_state:
    st.session_state.parsed_data = {}

def parse_release_data(text):
    """
    Parses unstructured text using Gemini to extract release information.
    """
    prompt = f"""
    You are an expert music data assistant. Your task is to extract structured music release data from the following unstructured text.
    
    Target Fields:
    1. Primary Artist
    2. Title (Release Title)
    3. UPC (Barcode)
    4. ISRC (International Standard Recording Code)
    5. Release Date (YYYY-MM-DD format)
    6. Country Code (ISO 3166-1 alpha-2 code, e.g., US, GB, CO. If a full name is given, convert it).
    7. Description (Release description/pitch).
    8. Genre (Map 'Popular'->'Regional Mexican', 'trapmambo'->'Urbano', 'Electrónica'->'Electronic', 'Cumbia'->'Tropical'. Default to original if no match).
    9. Release Type (Map 'Single + Video'->'New Single', 'Album + Video'->'New Album', 'EP + Video'->'New EP'. Default to 'New Single' if ambiguous).

    Rules:
    - If ISRC is not found or ambiguous, return null (None). DO NOT GUESS.
    - If Country is not found, return null.
    - Output MUST be valid JSON.
    
    Unstructured Text:
    {text}
    
    JSON Output:
    """
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        response = model.generate_content(prompt)
        json_text = clean_json_response(response.text)
        data = json.loads(json_text)
        
        # Apply strict mappings and defaults here if LLM misses them
        # (Though we asked LLM to do it, we can reinforce in Python later)
        data = apply_business_logic(data)
        return data
    except Exception as e:
        st.error(f"Error parsing data: {e}")
        return None

if st.button("Parse Data"):
    if not raw_text:
        st.warning("Please paste some text first.")
    else:
        with st.spinner("Analyzing text with Gemini..."):
            parsed = parse_release_data(raw_text)
            if parsed:
                st.session_state.parsed_data = parsed
                st.success("Parsing complete!")


# 2. Review Section
if st.session_state.parsed_data:
    st.subheader("2. Review & Validate")
    
    with st.form("review_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            artist = st.text_input("Primary Artist", value=st.session_state.parsed_data.get("primary_artist", ""))
            title = st.text_input("Release Title", value=st.session_state.parsed_data.get("title", ""))
            upc = st.text_input("UPC", value=st.session_state.parsed_data.get("upc", ""))
            
            # ISRC Validation in UI
            isrc_val = st.session_state.parsed_data.get("isrc", "")
            if isrc_val is None:
                isrc_val = ""
            isrc = st.text_input("ISRC", value=isrc_val, help="Required 12-character alphanumeric code.")
            
            isrc_valid = True
            if not isrc:
                st.error("ISRC is MISSING. Please enter it manually.")
                isrc_valid = False
            elif not validate_isrc(isrc):
                st.error("Invalid ISRC format. Must be 12 alphanumeric characters.")
                isrc_valid = False
            
            label = st.text_input("Label", value=st.session_state.parsed_data.get("label", "ONErpm"))

        with col2:
            release_date = st.text_input("Release Date (YYYY-MM-DD)", value=st.session_state.parsed_data.get("release_date", ""))
            
            # Country Display
            c_code = st.session_state.parsed_data.get("country_code", "")
            c_name = st.session_state.parsed_data.get("country_name", "")
            country_display = f"{c_name} ({c_code})" if c_name else c_code
            country_input = st.text_input("Country (Name or Code)", value=country_display)
            
            description = st.text_area("Description", value=st.session_state.parsed_data.get("description", ""))
            genre = st.text_input("Genre", value=st.session_state.parsed_data.get("genre", ""))
            rtype = st.text_input("Release Type", value=st.session_state.parsed_data.get("release_type", ""))
            latin_audience = st.text_input("Latin Audience", value=st.session_state.parsed_data.get("latin_audience", "Yes"))

        submitted = st.form_submit_button("Generate Script", disabled=not isrc_valid)
        
        if submitted:
            # Update session state with edited values
            st.session_state.parsed_data.update({
                "primary_artist": artist,
                "title": title,
                "upc": upc,
                "isrc": isrc,
                "label": label,
                "release_date": release_date,
                "country_code": country_input, # simplified for now
                "description": description,
                "genre": genre,
                "release_type": rtype,
                "latin_audience": latin_audience
            })
            
            # Generate JS Script
            # Heuristic selector strategy: try to find by Name, then ID, then Label text
            
            js_script = f"""
            (function() {{
                function setVal(selector, value) {{
                    let el = document.querySelector(selector);
                    if (el) {{
                        el.value = value;
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        console.log('Set ' + selector + ' to ' + value);
                    }} else {{
                        console.warn('Could not find element for ' + selector);
                    }}
                }}

                // Mappings based on best guesses for Salesforce/Webforms
                setVal('input[name="Primary_Artist"]', {json.dumps(artist)});
                setVal('input[name="Title"]', {json.dumps(title)});
                setVal('input[name="UPC"]', {json.dumps(upc)});
                setVal('input[name="ISRC"]', {json.dumps(isrc)});
                setVal('input[name="Release_Date"]', {json.dumps(release_date)});
                setVal('textarea[name="Description"]', {json.dumps(description)});
                setVal('input[name="Label"]', {json.dumps(label)});
                
                // Specific handling for Country might be needed if it's a dropdown
                // For now assuming text input or autocomplete
                setVal('input[name="Territory"]', {json.dumps(country_input)});
                
                if (confirm("Data filled. Do you want to submit the form now?")) {{
                    let submitBtn = document.querySelector('button[type="submit"], input[type="submit"]');
                    if (submitBtn) {{
                        submitBtn.click();
                    }} else {{
                        alert("Could not find a submit button. Please submit manually.");
                    }}
                }}
            }})();
            """
            
            st.session_state.generated_script = js_script
            
            # Auto-open the portal
            webbrowser.open_new_tab("https://labelportal.amazonmusic.com/s/project-flow-frontline")
            st.toast("Amazon Portal opened in a new tab!", icon="🚀")

# 3. Output Section
if "generated_script" in st.session_state:
    st.subheader("3. Copy Script")
    st.code(st.session_state.generated_script, language="javascript")
    st.info("Copy the code above and paste it into the browser console (F12 -> Console) on the Amazon label portal.")
    
    # Optional: Link to open the portal
    st.link_button("Open Amazon Label Portal", "https://labelportal.amazonmusic.com/s/project-flow-frontline")
    
