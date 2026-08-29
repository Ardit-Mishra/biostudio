# =============================================================================
# ARDIT BIOSTUDIO - MAIN STREAMLIT APPLICATION
# =============================================================================
# This is the main entry point for the Ardit BioStudio web application.
# It provides an interactive interface for pharmaceutical AI/ML predictions.
#
# ARCHITECTURE:
# - Frontend: Streamlit web framework with custom CSS styling
# - Backend: Python modules for prediction (utils/, models/, data/)
# - Caching: @st.cache_resource for model persistence
#
# MODULES:
# - Home: Welcome page with platform overview
# - Molecule Studio: Basic molecular property analysis
# - ADME Navigator: Absorption, Distribution, Metabolism, Excretion predictions
# - Toxicity Radar: Safety assessment (hepatotox, hERG, mutagenicity, carcinogenicity)
# - Drug-Likeness Deck: Lipinski, Veber, QED, SA score evaluation
# - Target Prediction: Kinase, GPCR, ion channel, enzyme prediction
# - Protein & Biologic Studio: Peptide/protein analysis
# - Explainability Canvas: ML model interpretability (feature importance)
# - Knowledge Graph: Drug-target-disease network explorer
# - Lead Lab: Batch screening and prioritization
# - Case Study: Kinase inhibitor lead ranking demonstration
# - About: Platform information and credits
#
# DEVELOPER: Ardit Mishra
# LICENSE: MIT Open Source
# REPOSITORY: github.com/ardit-mishra/ardit-biocore
# =============================================================================

# Import Streamlit framework for building the web interface
# Streamlit converts Python scripts into interactive web apps
import streamlit as st

# Import pandas for data manipulation and display
# Used for creating and displaying DataFrames in the UI
import pandas as pd

# Import numpy for numerical array operations
# Used for molecular descriptor calculations
import numpy as np

# Import RDKit core chemistry module for molecular operations
from rdkit import Chem
# Import AllChem for fingerprints and DataStructs for similarity calculations
from rdkit.Chem import AllChem, DataStructs

# Import sys and os for path manipulation
# Needed to import modules from sibling directories
import sys
import os

# Import io for in-memory file operations (CSV downloads)
import io

# Add current directory to Python path
# This allows importing from utils/, models/, data/ directories
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import core molecular processing utilities
# MolecularProcessor: SMILES validation, property calculation, fingerprints
from utils.molecular_utils import MolecularProcessor

# Import drug-likeness calculator
# DrugLikenessCalculator: Lipinski, Veber, QED, SA score
from utils.drug_likeness import DrugLikenessCalculator

# Import knowledge graph for drug-target-disease relationships
from utils.knowledge_graph import BiomedicalKnowledgeGraph

# Import visualization utilities for molecular images and charts
from utils.visualization_utils import MolecularVisualizer, ClusteringVisualizer

# Import ADME prediction module (Absorption, Distribution, Metabolism, Excretion)
from models.adme_predictors import ADMEPredictor

# Import toxicity prediction module (hepatotox, hERG, mutagenicity, carcinogenicity)
from models.toxicity_predictors import ToxicityPredictor

# Import target class prediction module (kinase, GPCR, ion channel, enzyme)
from models.target_predictors import TargetClassPredictor

# Import real, held-out-validated ADMET models (XGBoost trained on public TDC
# datasets with scaffold splits) — replaces the previous random-weight "neural
# network" toxicity demo.
from models.real_admet import RealADMETPredictor

# Import case study data (kinase inhibitor candidates)
from data.kinase_inhibitors import get_case_study_data, get_approved_kinase_drugs

# Import protein analysis utilities
from features.protein_utils import ProteinAnalyzer

# Import input type detector (SMILES vs sequence)
from features.input_detector import InputDetector

# Import example molecule data (peptides and proteins)
from data.example_molecules import get_all_peptide_names, get_all_protein_names, get_peptide, get_protein

# Import the shared design-system glyph set (generated — see design-system/icons.json).
# icon() returns a bare <svg> string, section_header() a full heading block, inline()
# a glyph+text run for chips/legends. All three return HTML for st.markdown(..., unsafe_allow_html=True).
from utils.icons import icon, section_header, inline

# =============================================================================
# STREAMLIT PAGE CONFIGURATION
# =============================================================================
# Configure the Streamlit app with page title, icon, layout settings
# Must be called first before any other Streamlit commands
st.set_page_config(
    # Browser tab title
    page_title="Ardit BioStudio — ADMET property prediction",
    # Browser tab icon (DNA emoji)
    page_icon="🧬",
    # Use wide layout to maximize screen space
    layout="wide",
    # Keep sidebar expanded by default for navigation
    initial_sidebar_state="expanded"
)

# =============================================================================
# CUSTOM CSS STYLING
# =============================================================================
# Inject custom CSS to create the futuristic dark theme with cyan/pink accents
# This overrides Streamlit's default styling for a professional pharma look
st.markdown("""
<style>
  /* ---------------------------------------------------------------------
     "Laboratory Instrument" — shared with GenomeSight and PeptideMHC.

     Replaces a neon cyan/pink scheme on near-black that carried a grid
     background, glowing text shadows, gradient buttons and a scale-on-hover.
     That reads as a sci-fi console; this app reports ADMET properties with
     stated held-out scores, and should look like the instrument it is.

     Accent (blue) marks measurement and interaction. Risk is carried by a
     SEPARATE semantic scale (safe / caution / critical) so a property being
     dangerous is never confused with a control being active.
     --------------------------------------------------------------------- */
  @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,400;12..96,500;12..96,600;12..96,700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

  :root {
    --bg-main: #11161D;        /* cool slate, not pure black */
    --bg-panel: #171E27;
    --text-main: #E7ECF3;
    --text-dim: #8D9AAA;
    --border: #232C36;
    --accent: #6E9BFF;         /* AlphaFold high-confidence pLDDT blue */
    --safe: #5FBF8F;
    --caution: #D9A44F;
    --critical: #E06C75;
    --font-ui: 'Bricolage Grotesque', 'Helvetica Neue', Arial, sans-serif;
    --font-mono: 'IBM Plex Mono', ui-monospace, Consolas, Menlo, monospace;
  }

  /* Flat ground. The 40px grid overlay was decoration with no referent. */
  .stApp {
    background: var(--bg-main);
    color: var(--text-main);
  }

  /* Streamlit sets its own face on inner elements, so a rule on .stApp alone
     loses to it. Claim the UI face broadly, then hand the data back to mono.
     stIconMaterial is excluded -- it's Streamlit's Material Symbols glyph
     span (expander arrows, the sidebar collapse chevron, etc.); catching it
     in the broad `span` selector above used to render those as literal
     ligature text ("keyboard_arrow_right") instead of an icon. */
  html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"],
  h1, h2, h3, h4, h5, h6, p, div, label, button, input, select, textarea,
  span:not([data-testid="stIconMaterial"]) {
    font-family: var(--font-ui) !important;
  }

  code, pre, .stCode, [data-testid="stDataFrame"],
  [data-testid="stMetricValue"], [data-testid="stMetricLabel"], .risk-pill {
    font-family: var(--font-mono) !important;
  }

  /* Belt-and-suspenders: re-assert the icon font explicitly in case a more
     specific Streamlit rule ever stops winning on its own. */
  [data-testid="stIconMaterial"] {
    font-family: "Material Symbols Rounded" !important;
  }

  [data-testid="stSidebar"] {
    background: var(--bg-panel);
    border-right: 1px solid var(--border);
  }
  [data-testid="stSidebar"] * { color: var(--text-main); }

  /* Left-aligned and unlit. A glowing centred title is a poster, not a tool. */
  /* Streamlit's own h1 rule sets ~44px and wins on specificity, hence the
     !important — without it the "restrained header" silently stays huge. */
  .main-header {
    font-family: var(--font-ui) !important;
    font-size: 1.6rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.02em;
    color: var(--text-main);
    text-align: left;
    padding: 0 !important;
  }

  .subtitle {
    color: var(--text-dim);
    text-align: left;
    font-size: 0.95rem;
  }

  /* Hairline panel. Elevation is a border, not a 25px coloured glow. */
  .metric-card {
    background: var(--bg-panel);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 1.15rem 1.25rem;
  }

  /* Every measured number is monospace and tabular so columns of results
     line up and digits do not shift width as values change. */
  [data-testid="stMetricValue"] {
    font-family: var(--font-mono);
    font-variant-numeric: tabular-nums;
    letter-spacing: -0.02em;
  }
  [data-testid="stMetricLabel"] {
    font-family: var(--font-mono);
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-dim);
  }

  /* Callouts: a 2px rail, matching the caveat treatment in PeptideMHC. */
  .success-box {
    background: rgba(95,191,143,0.10);
    border-left: 2px solid var(--safe);
    padding: 0.75rem 1rem;
    border-radius: 0 6px 6px 0;
  }
  .danger-box {
    background: rgba(224,108,117,0.10);
    border-left: 2px solid var(--critical);
    padding: 0.75rem 1rem;
    border-radius: 0 6px 6px 0;
  }

  /* Risk pills read as status, not as brand colour. */
  .risk-pill {
    font-family: var(--font-mono);
    padding: 0.15rem 0.6rem;
    border-radius: 4px;
    font-size: 0.7rem;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    border: 1px solid currentColor;
  }
  .safe-zone     { color: var(--safe); }
  .caution-zone  { color: var(--caution); }
  .critical-zone { color: var(--critical); }

  /* Flat control. Was a cyan->pink gradient pill with a 18px glow that grew
     6% on hover; a button on an instrument does not inflate when approached. */
  .stButton > button {
    background: var(--accent);
    color: #11161D;
    border: 1px solid var(--accent);
    border-radius: 6px;
    padding: 0.5rem 1.1rem;
    font-family: var(--font-ui);
    font-weight: 600;
    box-shadow: none;
    transition: filter .15s ease, border-color .15s ease;
  }
  .stButton > button:hover {
    filter: brightness(1.08);
    transform: none;
  }
  .stButton > button:focus-visible {
    outline: 2px solid var(--accent);
    outline-offset: 2px;
  }

  /* Streamlit paints st.info/success/warning as a full accent-tinted block with
     accent-coloured body text, so a single long callout turned a whole screen
     blue and drowned the numbers it sat next to. Alerts are now a neutral panel
     with one 2px status rail — the same treatment as a stated limitation — so
     the accent stays reserved for measurement and interaction. */
  [data-testid="stAlert"] {
    background: var(--bg-panel) !important;
    border: 1px solid var(--border) !important;
    border-left: 2px solid var(--accent) !important;
    border-radius: 0 6px 6px 0 !important;
    color: var(--text-main) !important;
    box-shadow: none !important;
  }
  [data-testid="stAlert"] * { color: var(--text-main) !important; }
  [data-testid="stAlert"] a { color: var(--accent) !important; }
  [data-testid="stAlertContentSuccess"] { border-left-color: var(--safe) !important; }
  [data-testid="stAlertContentWarning"] { border-left-color: var(--caution) !important; }
  [data-testid="stAlertContentError"]   { border-left-color: var(--critical) !important; }

  /* Prose is read, not scanned: cap the measure so long callouts do not run the
     full width of a 1440px screen. */
  [data-testid="stAlert"] p, [data-testid="stCaptionContainer"] p {
    max-width: 78ch;
  }

  /* SMILES, formulae and identifiers are read character by character. */
  code, .stCode, [data-testid="stDataFrame"] {
    font-family: var(--font-mono);
  }

  @media (prefers-reduced-motion: reduce) {
    * { transition-duration: .01ms !important; animation-duration: .01ms !important; }
  }

  /* Custom icon nav (replaces st.radio, which cannot render HTML options).
     Each row is an icon column + a real st.button — flatten the button back to
     a left-aligned list row instead of the pill treatment used for action
     buttons elsewhere, and vertically centre the icon against the label.
     Scoped to the sidebar's own horizontal-block/button wrappers (real
     Streamlit containers) rather than a hand-written div, since an
     st.markdown("<div>") does not actually wrap sibling widgets in the DOM. */
  [data-testid="stSidebar"] [data-testid="stHorizontalBlock"] {
    align-items: center;
    margin-bottom: 0.15rem;
  }
  [data-testid="stSidebar"] .stButton > button[kind="secondary"] {
    background: transparent;
    border: 1px solid transparent;
    color: var(--text-dim);
    font-weight: 500;
    padding: 0.4rem 0.6rem;
    text-align: left;
    justify-content: flex-start;
    box-shadow: none;
  }
  [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
    background: rgba(110,155,255,0.08);
    color: var(--text-main);
    border-color: var(--border);
    filter: none;
  }
  [data-testid="stSidebar"] .stButton > button[kind="primary"] {
    background: rgba(110,155,255,0.14);
    color: var(--text-main);
    border: 1px solid var(--accent);
    box-shadow: none;
    font-weight: 600;
    padding: 0.4rem 0.6rem;
    text-align: left;
    justify-content: flex-start;
  }
  [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {
    filter: none;
    background: rgba(110,155,255,0.2);
  }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# MODEL INITIALIZATION WITH CACHING
# =============================================================================
@st.cache_data
def _admet_endpoint_names() -> list:
    """
    Endpoint names read from the manifest the app actually serves.

    The sidebar used to hardcode "8"; the manifest holds seven. Deriving the
    count means the UI cannot drift from the shipped artifacts again.
    """
    import json
    from models.real_admet import _default_model_dir

    path = os.path.join(_default_model_dir(), "admet_models_manifest.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return list(json.load(fh).keys())
    except (OSError, ValueError):
        return []


# Use @st.cache_resource to load models only once and reuse across sessions
# This significantly improves performance by avoiding repeated initialization
@st.cache_resource
def load_models():
    """
    Load and cache all prediction models and utilities.
    
    This function is decorated with @st.cache_resource, which means it only
    runs once per application session. All subsequent calls return the cached
    objects, avoiding expensive re-initialization.
    
    Returns:
        Tuple of initialized model instances:
        - mol_processor: SMILES validation and property calculation
        - drug_likeness: Lipinski, Veber, QED, SA score calculators
        - adme_predictor: ADME/PK predictions
        - toxicity_predictor: Heuristic (rule-based) toxicity predictions
        - real_admet_predictor: Real, held-out-validated XGBoost ADMET/toxicity models
        - target_predictor: Target class predictions
        - kg: Biomedical knowledge graph
        - visualizer: Molecular visualization utilities
        - protein_analyzer: Protein/peptide analysis
        - input_detector: Input type detection
    """
    # Initialize molecular processing utilities
    mol_processor = MolecularProcessor()
    # Initialize drug-likeness calculator (Lipinski, Veber, QED, SA)
    drug_likeness = DrugLikenessCalculator()
    # Initialize ADME/PK predictor
    adme_predictor = ADMEPredictor()
    # Initialize heuristic (rule-based) toxicity predictor
    toxicity_predictor = ToxicityPredictor()
    # Initialize real ADMET predictor (held-out-validated XGBoost models)
    real_admet_predictor = RealADMETPredictor()
    # Initialize target class predictor (kinase, GPCR, ion channel, enzyme)
    target_predictor = TargetClassPredictor()
    # Initialize biomedical knowledge graph with 70+ drugs
    kg = BiomedicalKnowledgeGraph()
    # Initialize molecular visualization utilities
    visualizer = MolecularVisualizer()
    # Initialize protein/peptide analyzer
    protein_analyzer = ProteinAnalyzer()
    # Initialize input type detector
    input_detector = InputDetector()

    # Return all initialized objects as a tuple
    return (mol_processor, drug_likeness, adme_predictor, toxicity_predictor, real_admet_predictor,
            target_predictor, kg, visualizer, protein_analyzer, input_detector)


# Load all models and unpack into individual variables
# This call either loads fresh models (first run) or returns cached ones
(mol_processor, drug_likeness, adme_predictor, toxicity_predictor, real_admet_predictor,
 target_predictor, kg, visualizer, protein_analyzer, input_detector) = load_models()


# =============================================================================
# HEADER AND TITLE SECTION
# =============================================================================
# Display the main application header with glowing effect
st.markdown('<div class="main-header">Ardit BioStudio</div>', unsafe_allow_html=True)
# Decorative gold underline (empty div for styling)
st.markdown('<div class="gold-underline"></div>', unsafe_allow_html=True)
# Subtitle describing the platform
st.markdown('<div class="subtitle">ADMET property prediction from molecular structure &middot; seven XGBoost models, scaffold-split, held-out scores shown per prediction</div>', unsafe_allow_html=True)

# Important disclaimer about the educational nature of predictions
# This is crucial for setting user expectations about prediction accuracy
# This note contradicted the app. It said "current predictors use heuristic
# scoring functions ... for demonstration purposes" while the table directly
# beneath it correctly advertised seven held-out-validated XGBoost models — the
# text was left over from before the real models shipped and now UNDERSOLD the
# work while confusing which parts are trained and which are rule-based.
# Both facts are true of different modules, so the note now separates them.
st.caption(
    "Research and educational use — not for clinical or regulatory decisions. "
    "**ADMET endpoints are trained models**: XGBoost on ECFP4 fingerprints plus RDKit "
    "descriptors, fit on Therapeutics Data Commons benchmarks under a Bemis–Murcko "
    "scaffold split, each reported from a single held-out evaluation with its "
    "benchmark's own metric. **Drug-likeness, structural-alert toxicity and target-class "
    "modules are rule-based heuristics**, not trained models, and are labelled as such "
    "where they appear."
)

# =============================================================================
# SIDEBAR NAVIGATION
# =============================================================================
# Create sidebar for page navigation and platform information
with st.sidebar:
    # Navigation header
    st.markdown("### BioStudio Navigation")

    # Each module's nav row carries its domain glyph. st.radio cannot render HTML
    # inside its options, so navigation is built from real st.button widgets — one
    # per module, an icon column beside each — instead of fighting Streamlit's
    # internal radio markup with brittle CSS. Selection lives in session_state and
    # a rerun swaps the page, exactly like the radio group it replaces.
    # `None` means no glyph in the 22-icon set genuinely marks this page's concept
    # (Home is the app itself; About is platform info) — per the design system's
    # own rule, no icon beats a wrong one.
    NAV_ITEMS = [
        ("Home", "benzene"),
        ("Molecule Studio", "molecule"),
        ("ADME Navigator", "membrane"),
        ("Toxicity Radar", "hazard"),
        ("Drug-Likeness Deck", "ruler"),
        ("Target Prediction", "receptor"),
        ("Protein & Biologic Studio", "peptide"),
        ("Explainability Canvas", "calibration"),
        ("Knowledge Graph", "graph"),
        ("Lead Lab", "plate"),
        ("Case Study", "flask"),
        ("About", None),
    ]

    if "biostudio_page" not in st.session_state:
        st.session_state.biostudio_page = "Home"

    for _label, _glyph in NAV_ITEMS:
        _active = st.session_state.biostudio_page == _label
        _icon_col, _btn_col = st.columns([1, 6], gap="small")
        with _icon_col:
            if _glyph:
                st.markdown(
                    icon(_glyph, 17, "var(--accent)" if _active else "var(--text-dim)"),
                    unsafe_allow_html=True,
                )
        with _btn_col:
            if st.button(
                _label,
                key=f"nav_{_label}",
                use_container_width=True,
                type="primary" if _active else "secondary",
            ):
                st.session_state.biostudio_page = _label
                st.rerun()
    page = st.session_state.biostudio_page

    # Visual separator
    st.markdown("---")
    
    # Facts about the shipped models, read from the manifest they are served
    # from. This block previously showed "Models Deployed 8" (there are seven),
    # "Predictions Today 0" (never tracked) and "Success Rate 95%" — a figure
    # with no definition and no measurement behind it. A predictor does not have
    # a success rate; it has a held-out score per endpoint, which is shown on
    # each prediction card.
    st.markdown("### Models")
    _endpoints = _admet_endpoint_names()
    st.metric("ADMET endpoints", str(len(_endpoints)) if _endpoints else "—")
    st.markdown(
        f"""<div style="font-family: var(--font-mono); font-size: 0.68rem; letter-spacing: 0.12em;
                        text-transform: uppercase; color: var(--text-dim); margin-top: 0.75rem;">Split</div>
            <div style="margin-top:.2rem">{inline('split', 'Bemis&ndash;Murcko scaffold', size=16)}</div>""",
        unsafe_allow_html=True,
    )
    st.caption(
        "Each endpoint is one XGBoost model with a single held-out evaluation, "
        "scored with the metric its benchmark specifies. Per-endpoint numbers "
        "appear with each prediction."
    )
    
    # Visual separator
    st.markdown("---")
    
    # Platform capabilities summary — each module paired with the glyph that
    # marks it elsewhere in the app, so the sidebar doubles as a legend.
    st.markdown(
        '<div style="font-size:.68rem;letter-spacing:.1em;text-transform:uppercase;'
        'color:var(--text-dim);margin-bottom:.5rem">Platform Modules</div>'
        '<div style="display:flex;flex-direction:column;gap:.5rem">'
        + inline("membrane", "ADME/PK prediction")
        + inline("hazard", "Toxicity risk assessment")
        + inline("ruler", "Drug-likeness scoring")
        + inline("receptor", "Target class prediction")
        + inline("calibration", "Rule-based explainability")
        + inline("graph", "Knowledge graph explorer")
        + '</div>',
        unsafe_allow_html=True,
    )


# =============================================================================
# HOME PAGE
# =============================================================================
# Welcome page with platform overview and beginner's guide
if page == "Home":
    # Section header
    st.markdown(section_header("benzene", "Welcome to Ardit BioStudio"),
                unsafe_allow_html=True)
    
    # Expandable beginner's guide
    with st.expander("New to drug discovery? Start here", expanded=False):
        st.markdown("""
        ### What is Ardit BioStudio?
        
        **Ardit BioStudio** is an educational platform that helps you analyze potential drug molecules using
        a mix of real, held-out-validated machine-learning models and rule-based chemistry heuristics.

        **Think of it as:** An assistant that can tell you if a molecule would make a good medicine before you spend time and money making it in a lab — and that tells you plainly which of its answers come from a trained model versus a formula.

        ### What Can You Do Here?

        1. **Check if a molecule is drug-like** - Will it work as a medicine?
        2. **Predict absorption** - Can your body absorb it?
        3. **Assess safety** - Is it toxic?
        4. **Identify targets** - What does it interact with in the body?
        5. **Understand predictions** - Why does each tool give the result it does?
        
        ### Key Terms Explained (Beginner's Glossary)
        
        **SMILES**: A simple text code that represents a molecule's structure
        - Example: `CC(=O)Oc1ccccc1C(=O)O` = Aspirin
        - Think of it like: A ZIP code for molecules
        
        **ADME**: How a drug behaves in your body
        - **A**bsorption - Does it get into your bloodstream?
        - **D**istribution - Where does it go in your body?
        - **M**etabolism - How does your body break it down?
        - **E**xcretion - How does it leave your body?
        
        **LogP**: How "fatty" vs "water-loving" a molecule is
        - **Positive LogP** (like 3): Fatty, can cross cell membranes easily
        - **Negative LogP** (like -1): Water-loving, stays in blood
        - **Sweet spot**: 0-3 for most drugs
        
        **Toxicity**: Potential for harm
        - **hERG**: Heart rhythm issues
        - **Hepatotoxicity**: Liver damage
        - **Mutagenicity**: DNA damage
        - **Carcinogenicity**: Cancer risk
        
        **QED Score** (0-1): Overall "drug-likeness"
        - **0.7-1.0**: Excellent drug candidate
        - **0.5-0.7**: Good, needs optimization
        - **< 0.5**: Needs significant improvement
        
        ### How to Get Started
        
        1. **Try an example first**: Use the pre-filled molecules (like Aspirin or Ibuprofen)
        2. **Start with Molecule Studio**: See basic properties
        3. **Move to ADME Navigator**: Check absorption
        4. **Check Drug-Likeness Deck**: Overall assessment
        5. **Review Toxicity Radar**: Safety check
        
        **No chemistry knowledge needed!** Each tool explains what it does and what the results mean.
        """)
    
    # Platform capabilities section — a glyph-led grid rather than a plain
    # table, so each module's icon does double duty as a legend for the
    # sidebar nav and every other page carrying that same glyph.
    st.markdown(section_header("split", "Platform Capabilities"), unsafe_allow_html=True)

    _capability_rows = [
        ("membrane", "ADME/PK", "LogP, Caco-2, BBB, CYP450, Clearance", "Heuristic"),
        ("split", "ADMET Models", "XGBoost, 7 endpoints — held-out validated on TDC", "Trained"),
        ("hazard", "Toxicity", "Hepatotox, hERG, Ames, Carcinogenicity (structural alerts)", "Heuristic"),
        ("ruler", "Drug-likeness", "Lipinski, Veber, QED, SA Score", "Heuristic"),
        ("receptor", "Target Prediction", "Kinase, GPCR, Ion Channel, Enzyme", "Heuristic"),
        ("graph", "Knowledge Graph", "Drug-Target-Disease Relationships", "Reference data"),
    ]
    _cap_cols = st.columns(3, gap="medium")
    for _i, (_glyph, _mod, _cap, _kind) in enumerate(_capability_rows):
        _pill_class = "safe-zone" if _kind == "Trained" else "caution-zone" if _kind == "Heuristic" else "safe-zone"
        with _cap_cols[_i % 3]:
            st.markdown(
                f'<div style="border:1px solid var(--border);border-radius:6px;'
                f'padding:.9rem 1rem;margin-bottom:1rem;min-height:9.5rem">'
                f'<div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.5rem">'
                f'{icon(_glyph, 19, "var(--accent)")}'
                f'<span style="font-weight:600;color:var(--text-main)">{_mod}</span></div>'
                f'<div style="font-size:.82rem;color:var(--text-dim);margin-bottom:.6rem">{_cap}</div>'
                f'<span class="risk-pill {_pill_class}">{_kind}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    st.caption(
        "“Trained” = fit on labelled data with a held-out score. “Heuristic” = a fixed "
        "formula or structural-alert rule, not learned from data. See About for the full breakdown."
    )

    # Industry alignment section
    st.markdown('<div class="sub-header">Industry Alignment</div>', unsafe_allow_html=True)
    st.info("""
    This platform mirrors pharmaceutical industry best practices used in modern drug discovery:

    - **ML Techniques**: Gradient-boosted models (XGBoost) trained on public Therapeutics Data
      Commons (TDC) datasets with scaffold splits, for ADMET property prediction
    - **ADME/PK Focus**: Critical for small molecule development pipelines
    - **Target Class Prediction**: Kinase inhibitors central to oncology drug discovery
    - **Rule-Based Screening**: Structural-alert and descriptor-threshold heuristics for
      toxicity and drug-likeness (Lipinski, Veber, QED)
    - **Knowledge Graphs**: Drug-target-disease relationships for precision medicine
    """)


# =============================================================================
# MOLECULE STUDIO PAGE
# =============================================================================
# Basic molecular property analysis - the starting point for new molecules
elif page == "Molecule Studio":
    # Section header
    st.markdown(
        section_header("molecule", "Molecule Studio", "Structure input, 2D rendering and a quick drug-likeness read"),
        unsafe_allow_html=True,
    )
    
    # Help expander explaining what the module does
    with st.expander("**What does Molecule Studio do?**"):
        st.markdown("""
        ### Purpose
        **Molecule Studio** lets you analyze the basic properties of any molecule. It's like getting a molecule's ID card with all its important characteristics.
        
        ### What You'll Learn
        - **Molecular Weight (MW)**: How heavy the molecule is (measured in Daltons)
          - *Good range for drugs*: 150-500 Da (lighter molecules are easier for the body to process)
        
        - **LogP**: Measures if the molecule is fatty or water-loving
          - *Good range*: 0-3 (balanced between water and fat)
          - *Too high* (>5): Won't dissolve in blood
          - *Too low* (<-2): Can't enter cells
        
        - **TPSA** (Polar Surface Area): How "sticky" the molecule is to water
          - *Good range*: 20-140 Ų for oral drugs
          - *Lower*: Can cross cell membranes easily
          - *Higher*: Stays in bloodstream
        
        - **H-Bond Donors/Acceptors**: How many connections it can make with water
          - *Donors*: Groups like -OH, -NH that give hydrogen
          - *Acceptors*: Groups like =O, -N that receive hydrogen
          - *Why it matters*: Too many makes absorption difficult
        
        - **Rotatable Bonds**: How flexible the molecule is
          - *Good range*: < 10 bonds
          - *More flexible*: Harder to bind to targets
        
        - **Aromatic Rings**: Flat ring structures (like in benzene)
          - *Common in drugs*: Most drugs have 1-4 aromatic rings
        
        ### How to Use
        1. **Enter a SMILES code** (or use the example Ibuprofen)
        2. **Click "Validate & Analyze"**
        3. **Review the 2D structure** (visual representation)
        4. **Check the properties table** (all the numbers explained above)
        5. **See the quick drug-likeness check** (Pass/Fail indicators)
        
        ### Try These Examples
        - **Aspirin**: `CC(=O)Oc1ccccc1C(=O)O`
        - **Caffeine**: `CN1C=NC2=C1C(=O)N(C(=O)N2C)C`
        - **Ibuprofen**: `CC(C)Cc1ccc(cc1)C(C)C(=O)O` (pre-filled)
        """)

    st.markdown(
        inline("ruler", "Validating a structure returns its 2D rendering, MW/LogP/TPSA table, "
                         "and Lipinski/Veber/QED pass-fail in one pass."),
        unsafe_allow_html=True,
    )

    # Input method selection (currently only SMILES implemented)
    input_method = st.radio("Input Method", ["SMILES String", "Draw Structure (Coming Soon)", "Upload File"], horizontal=True)
    
    # SMILES input section
    if input_method == "SMILES String":
        # Text input for SMILES with Ibuprofen as default
        smiles_input = st.text_input("Enter SMILES String", "CC(C)Cc1ccc(cc1)C(C)C(=O)O")
        # Optional molecule name input
        molecule_name = st.text_input("Molecule Name (Optional)", "Ibuprofen")
        
        # Analysis button
        if st.button("Validate & Analyze", type="primary"):
            # Validate the SMILES input
            is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)
            
            if is_valid:
                # Show success message with canonical SMILES
                st.success(f"Valid SMILES: `{canonical_smiles}`")
                
                # Convert to RDKit molecule object
                mol = mol_processor.smiles_to_mol(canonical_smiles)
                
                # Create two-column layout
                col1, col2 = st.columns([1, 1])
                
                # Left column: 2D structure visualization
                with col1:
                    st.markdown("#### 2D Structure")
                    # Generate molecular image
                    img = visualizer.mol_to_image(mol, size=(400, 400))
                    if img:
                        st.image(img)
                
                # Right column: Property table
                with col2:
                    st.markdown("#### Basic Properties")
                    # Calculate all basic properties
                    props = mol_processor.calculate_basic_properties(mol)
                    
                    # Convert to DataFrame for display
                    props_df = pd.DataFrame([props]).T
                    props_df.columns = ['Value']
                    st.dataframe(props_df, use_container_width=True)
                
                # Drug-likeness quick check section
                st.markdown("#### Drug-Likeness Quick Check")
                # Calculate all drug-likeness metrics
                lipinski = mol_processor.calculate_lipinski_descriptors(mol)
                veber = mol_processor.calculate_veber_descriptors(mol)
                qed = mol_processor.calculate_qed(mol)
                
                # Display metrics in 4 columns
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Lipinski Violations", lipinski['Violations'])
                col2.metric("Veber Pass", "Pass" if veber['Passes'] else "Fail")
                col3.metric("QED Score", "unavailable" if qed is None else f"{qed:.3f}")
                col4.metric("Overall", "Drug-like" if lipinski['Violations'] <= 1 and veber['Passes'] else "Review")
                
            else:
                # Show error for invalid SMILES
                st.error(f"Invalid SMILES: {canonical_smiles}")


# =============================================================================
# ADME NAVIGATOR PAGE
# =============================================================================
# Predicts Absorption, Distribution, Metabolism, Excretion properties
elif page == "ADME Navigator":
    # Section header
    st.markdown(
        section_header("membrane", "ADME Navigator", "Absorption, distribution, metabolism and excretion, from one structure"),
        unsafe_allow_html=True,
    )
    
    # Help expander with detailed ADME explanation
    with st.expander("**Understanding ADME - What Happens to a Drug in Your Body**"):
        st.markdown("""
        ### What is ADME?
        **ADME** predicts what happens to a drug after you take it. Think of it as tracking the drug's journey through your body.
        
        ### The Four Stages
        
        **A - Absorption**
        - *What it means*: Can the drug get from your stomach into your blood?
        - *Tool used*: **Caco-2 Permeability**
          - Measures how well a drug crosses intestinal walls
          - **High (>8)**: Absorbs easily
          - **Moderate (2-8)**: Average absorption
          - **Low (<2)**: Poor absorption
        
        **D - Distribution**
        - *What it means*: Where does the drug go in your body?
        - *Tool used*: **BBB Penetration** (Blood-Brain Barrier)
          - Can it reach your brain?
          - **Yes**: Good for brain diseases (but may cause side effects)
          - **No**: Won't affect the brain (good for most drugs)
        
        **M - Metabolism**
        - *What it means*: How does your liver break down the drug?
        - *Tool used*: **CYP450 Enzymes**
          - Liver enzymes that modify drugs
          - **CYP3A4**: Processes ~50% of all drugs
          - **CYP2D6**: Important for many medications
          - **CYP2C9**: Common pathway
          - *Why it matters*: Drug interactions happen here
        
        **E - Excretion**
        - *What it means*: How fast does the drug leave your body?
        - *Tool used*: **Clearance Rate**
          - **High clearance**: Short-acting (need frequent doses)
          - **Low clearance**: Long-acting (fewer doses needed)
          - **Moderate**: Ideal for most drugs
        
        ### How to Use
        1. **Enter your molecule's SMILES code**
        2. **Click "Run ADME/PK Analysis"**
        3. **Review each tab** (LogP, Caco-2, BBB, CYP450, Clearance)
        4. **Check the color indicators**: 
           - Green = Good
           - Yellow = Moderate/Caution
           - Red = Poor/Risk
        
        ### What Makes a Good Drug?
        - **High absorption** (Caco-2 > 8)
        - **BBB penetration** depends on target (brain drugs need it, others don't)
        - **Moderate metabolism** (not too fast, not too slow)
        - **Balanced clearance** (stays active long enough)
        
        **Note**: These are predictive models for educational purposes. Real drugs need lab testing!
        """)
    
    # Disclaimer about heuristic predictions
    st.info("""**Note:** ADME/PK predictions use heuristic scoring functions based on molecular descriptors (LogP, TPSA, molecular weight, etc.), not trained models.
    For production use, replace with validated QSAR models trained on experimental ADME data.
    Caco-2 Permeability and BBB Penetration also have real, held-out-validated XGBoost models — see **Toxicity Radar → XGBoost (Gradient-Boosted)** for that trained-model alternative on the same two endpoints.
    """)
    
    # SMILES input
    smiles_input = st.text_input("Enter SMILES String", "CC(C)Cc1ccc(cc1)C(C)C(=O)O")
    
    # Analysis button
    if st.button("Run ADME/PK Analysis", type="primary"):
        # Validate SMILES
        is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)
        
        if is_valid:
            # Convert to molecule and run ADME analysis
            mol = mol_processor.smiles_to_mol(canonical_smiles)
            adme_profile = adme_predictor.comprehensive_adme_profile(mol)
            
            # Create tabs for each ADME property
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["LogP", "Caco-2 Permeability", "BBB Penetration", "CYP450 Metabolism", "Clearance"])
            
            # Tab 1: LogP (lipophilicity) — governs membrane crossing
            with tab1:
                st.markdown(inline("membrane", "Permeability endpoint — lipophilicity"), unsafe_allow_html=True)
                data = adme_profile['LogP']
                st.markdown(f"**LogP:** {data['LogP']}")
                st.markdown(f"**Category:** {data['Category']}")
                st.info(data['Interpretation'])

            # Tab 2: Caco-2 permeability (absorption)
            with tab2:
                st.markdown(inline("membrane", "Permeability endpoint — intestinal absorption"), unsafe_allow_html=True)
                data = adme_profile['Caco-2 Permeability']
                st.markdown(f"**Caco-2 Score:** {data['Caco-2 Score']}")
                st.markdown(f"**Category:** {data['Category']}")
                st.info(data['Interpretation'])

            # Tab 3: BBB penetration (distribution)
            with tab3:
                st.markdown(inline("membrane", "Permeability endpoint — blood-brain barrier"), unsafe_allow_html=True)
                data = adme_profile['BBB Penetration']
                st.markdown(f"**BBB Score:** {data['BBB Score']}")
                st.markdown(f"**Probability:** {data['Probability']}")
                st.info(data['Recommendation'])

            # Tab 4: CYP450 metabolism
            with tab4:
                st.markdown(inline("metabolism", "Metabolic endpoint — CYP450 biotransformation"), unsafe_allow_html=True)
                data = adme_profile['CYP450 Metabolism']
                st.markdown(f"**Primary Metabolizer:** {data['Primary Metabolizer']}")
                st.write(f"- CYP3A4: {data['CYP3A4 Substrate Probability']}")
                st.write(f"- CYP2D6: {data['CYP2D6 Substrate Probability']}")
                st.write(f"- CYP2C9: {data['CYP2C9 Substrate Probability']}")
                st.warning(data['Interpretation'])

            # Tab 5: Clearance (excretion)
            with tab5:
                st.markdown(inline("metabolism", "Metabolic endpoint — clearance and half-life"), unsafe_allow_html=True)
                data = adme_profile['Clearance']
                st.markdown(f"**Clearance Score:** {data['Clearance Score']}")
                st.markdown(f"**Category:** {data['Category']}")
                st.markdown(f"**Half-life Estimate:** {data['Half-life Estimate']}")
                st.info(data['Interpretation'])
        else:
            st.error("Invalid SMILES string")


# =============================================================================
# TOXICITY RADAR PAGE
# =============================================================================
# Safety assessment for hepatotoxicity, hERG, mutagenicity, carcinogenicity
elif page == "Toxicity Radar":
    # Section header
    st.markdown(
        section_header("hazard", "Toxicity Radar", "Hepatotoxicity, cardiotoxicity, mutagenicity and carcinogenicity risk"),
        unsafe_allow_html=True,
    )
    
    # Help expander with toxicity explanation
    with st.expander("**Understanding Toxicity - Safety Screening Explained**"):
        st.markdown("""
        ### Why Check Toxicity?
        Before a drug can be used, we need to make sure it's safe. **Toxicity Radar** predicts potential side effects and safety concerns.
        
        ### Four Main Safety Checks
        
        **1. Hepatotoxicity (Liver Damage)**
        - *What it is*: Can the drug harm your liver?
        - *Why it matters*: Your liver processes all drugs - damage here is serious
        - *Risk Levels*:
          - **0-30%**: Low risk (Safe)
          - **30-70%**: Moderate risk (Needs monitoring)
          - **70-100%**: High risk (Concerning)
        
        **2. Cardiotoxicity - hERG Inhibition (Heart Problems)**
        - *What it is*: Can the drug cause irregular heartbeat?
        - *hERG channel*: Electrical pathway in your heart
        - *Measured as IC50* (lower = more dangerous):
          - **>10 μM**: Low risk
          - **1-10 μM**: Moderate risk (caution)
          - **<1 μM**: High risk (dangerous)
        
        **3. Mutagenicity - Ames Test (DNA Damage)**
        - *What it is*: Can the drug damage your DNA?
        - *Why it matters*: DNA damage can lead to mutations
        - *Result*:
          - **Negative**: Safe (no DNA damage expected)
          - **Positive**: Risky (may cause mutations)
        
        **4. Carcinogenicity (Cancer Risk)**
        - *What it is*: Long-term cancer risk
        - *Risk Score*:
          - **0-30%**: Low risk
          - **30-70%**: Moderate risk (needs study)
          - **70-100%**: High risk (concerning)
        
        ### How to Use
        1. **Enter your molecule's SMILES**
        2. **Click "Run Toxicity Analysis"**
        3. **Review all four toxicity types**
        4. **Check the color-coded risk levels**:
           - Green = Safe/Low Risk
           - Yellow = Moderate/Caution
           - Red = High Risk/Dangerous
        
        ### What's Acceptable?
        - **All Low Risk**: Great candidate!
        - **One Moderate**: May still be okay with monitoring
        - **Any High Risk**: Needs redesign or very careful evaluation
        
        **Remember**: These are predictions. Real drugs need extensive lab and clinical testing!
        """)
    
    # Prediction system info
    st.info("""**ADMET toxicity models.** This platform offers two independent toxicity assessments:
    real **gradient-boosted models (XGBoost)** trained on public Therapeutics Data Commons (TDC)
    datasets with scaffold splits — each endpoint shows its held-out test score (AUROC, AUPRC or MAE, per endpoint) — and a
    **Heuristic** (rule-based) screen using structural alerts and descriptor thresholds.
    Educational tool — not a substitute for laboratory assays (Tox21, ToxCast, DILIrank).
    """)

    with st.expander("**Model Selection Benchmark — why XGBoost, not a neural net or a chemical LLM**"):
        st.markdown("""
        Before settling on gradient-boosted trees (XGBoost) for the seven production ADMET endpoints,
        four of them were also benchmarked against two deep-learning approaches on the *same* TDC
        endpoints and the *same* scaffold split, to check whether a heavier model earns its cost on
        this data rather than assuming it would.

        **Compared**: XGBoost (production) vs. **ChemBERTa-77M-MLM** (a chemical language model,
        LoRA fine-tuned) vs. **Chemprop D-MPNN** (a message-passing graph neural network). All three
        trained CPU-only, $0 marginal cost, no GPU.

        | Endpoint | XGBoost (single seed) | ChemBERTa LoRA (3-seed mean ± std) | Chemprop D-MPNN (3-seed mean ± std) |
        |---|---|---|---|
        | BBB_Martins | 0.905 | 0.882 ± 0.007 | 0.846 ± 0.025 |
        | hERG | 0.809 | 0.783 ± 0.008 | 0.699 ± 0.003 |
        | AMES | 0.845 | 0.816 ± 0.005 | 0.818 ± 0.013 |
        | DILI | 0.925 | 0.873 ± 0.022 | 0.860 ± 0.036 |

        All values are AUROC on TDC's default scaffold split. Source: `admet_models_manifest.json`
        (XGBoost), `chemberta_results.json`, `chemprop_results.json` in `ml-training/biostudio/`.

        **Result**: XGBoost scored highest on all four endpoints compared, and its inference is
        near-instant on CPU — it's already what serves every prediction in this app. ChemBERTa
        (a 77M-parameter transformer) and Chemprop (a trained graph neural network) both require
        loading a neural network at inference time, meaningfully heavier for a $0, CPU-only,
        per-request deployment, on top of scoring lower here.

        **Honest caveats, not smoothed over**:
        - The XGBoost column is a **single held-out evaluation** (scaffold seed 1, matching the
          production models); the two deep-learning columns are a **mean ± std over 3 scaffold-split
          seeds**. XGBoost has no reported variance here, so this isn't a perfectly like-for-like
          comparison — a fair XGBoost error bar would need the same 3-seed treatment.
        - This benchmark covers **4 of the 7** production endpoints (BBB_Martins, hERG, AMES, DILI).
          Pgp_Broccatelli, CYP3A4_Veith and Caco2_Wang were not run through the deep-learning tiers.
        - Exact training/inference wall-clock time wasn't instrumented in the training scripts, so
          no specific seconds are claimed here — the cost comparison above is about model size and
          serving complexity (a tree ensemble vs. a loaded neural network), not a timed benchmark.

        The takeaway this supports: deep learning and a chemical language model were **evaluated**
        on this project's own data, not assumed superior by default — and for these four endpoints,
        classical gradient-boosted trees on fingerprint + descriptor features won on both accuracy
        and serving cost.
        """)

    # Prediction method selection
    prediction_method = st.radio(
        "Select Prediction Method",
        ["XGBoost (Gradient-Boosted)", "Heuristic (Rule-Based)", "Both (Comparison)"],
        index=0,
        horizontal=True,
        help="XGBoost models use ECFP4 fingerprints + RDKit descriptors, held-out validated on TDC. Heuristic uses structural alerts."
    )

    # SMILES input
    smiles_input = st.text_input("Enter SMILES String", "CC(C)Cc1ccc(cc1)C(C)C(=O)O")

    # Analysis button
    if st.button("Run Toxicity Analysis", type="primary"):
        # Validate SMILES
        is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)

        if is_valid:
            # Convert to molecule
            mol = mol_processor.smiles_to_mol(canonical_smiles)

            # Real XGBoost ADMET predictions
            if prediction_method == "XGBoost (Gradient-Boosted)":
                st.markdown("### XGBoost Toxicity Predictions")
                st.caption("ECFP4(2048) + 10 RDKit descriptors | held-out validated on TDC | endpoints without a validated model are omitted")

                # Get real ADMET predictions
                admet_profile = real_admet_predictor.comprehensive_toxicity_profile(mol)

                # Only display endpoints with an actual trained model (hide "Unavailable")
                available = {k: v for k, v in admet_profile.items() if v.get('risk_level') != 'Unavailable'}

                # Two-column layout
                col1, col2 = st.columns(2)
                cols = [col1, col2]

                for i, (label, data) in enumerate(available.items()):
                    with cols[i % 2]:
                        st.markdown(f"#### {label}")
                        st.metric("Probability", data['percentage'])
                        st.metric("Risk Level", data['risk_level'])
                        st.caption(f"Model: {data['confidence']}")
                        # A stated limitation belongs beside the number it
                        # qualifies. These regressions were previously
                        # disclosed only in repo markdown that this app never
                        # opens, so nobody using the demo could see them.
                        if data.get('caveat'):
                            st.warning(data['caveat'])

                        # Color-coded risk pill
                        if data['risk_level'] in ('High', 'Positive'):
                            st.markdown('<div class="risk-pill critical-zone">High Risk</div>', unsafe_allow_html=True)
                        elif data['risk_level'] == 'Moderate':
                            st.markdown('<div class="risk-pill caution-zone">Moderate Risk</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="risk-pill safe-zone">Low Risk</div>', unsafe_allow_html=True)

                if not available:
                    st.warning("No held-out-validated model is available for this endpoint set.")

                # comprehensive_toxicity_profile() only covers the four
                # toxicity endpoints. The other three trained models —
                # absorption, distribution and metabolism — had no route into
                # the UI at all, while ADME Navigator told users to come here
                # to find them. That made the cross-reference false and left
                # Caco2_Wang's stated regression with nowhere to appear.
                other = [n for n in ("Caco2_Wang", "BBB_Martins", "Pgp_Broccatelli", "CYP3A4_Veith")
                         if n in real_admet_predictor.models]
                if other:
                    st.markdown("#### Absorption · Distribution · Metabolism")
                    st.caption(
                        "The same XGBoost pipeline, on the remaining trained endpoints. "
                        "These are properties of the compound, not toxicity."
                    )
                    ocols = st.columns(2)
                    for i, name in enumerate(other):
                        res = real_admet_predictor.predict_endpoint(mol, name)
                        with ocols[i % 2]:
                            label = (res or {}).get("app_label") or name
                            st.markdown(f"**{label}**")
                            if res is None:
                                st.caption("Prediction unavailable for this structure.")
                                continue
                            if res["task"] == "regression":
                                st.metric(res.get("metric") or "Value", f"{res['value']:.3f}")
                            else:
                                st.metric("Probability", f"{res['probability'] * 100:.1f}%")
                            st.caption(f"Model: {res['provenance']}")
                            if res.get("caveat"):
                                st.warning(res["caveat"])

            # Heuristic predictions
            elif prediction_method == "Heuristic (Rule-Based)":
                st.markdown("### Heuristic Toxicity Predictions")
                st.caption("Structural alerts + descriptor thresholds")
                
                # Get heuristic predictions
                tox_profile = toxicity_predictor.comprehensive_toxicity_profile(mol)
                
                # Two-column layout
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### Hepatotoxicity")
                    data = tox_profile['Hepatotoxicity']
                    st.metric("Risk Level", data['Hepatotoxicity Risk'])
                    st.markdown(f"**Category:** {data['Category']}")
                    
                    if 'High' in data['Category']:
                        st.markdown(f'<div class="danger-box">{data["Recommendation"]}</div>', unsafe_allow_html=True)
                    elif 'Moderate' in data['Category']:
                        st.markdown(f'<div class="warning-box">{data["Recommendation"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="success-box">{data["Recommendation"]}</div>', unsafe_allow_html=True)
                    
                    st.markdown("#### Mutagenicity (Ames Test)")
                    data = tox_profile['Mutagenicity (Ames)']
                    st.metric("Risk Level", data['Mutagenicity Risk'])
                    st.markdown(f"**Probability:** {data['Ames Positive Probability']}")
                    st.info(data['Recommendation'])
                
                with col2:
                    st.markdown("#### Cardiotoxicity (hERG)")
                    data = tox_profile['Cardiotoxicity (hERG)']
                    st.metric("hERG Inhibition Risk", data['hERG Inhibition Risk'])
                    st.markdown(f"**Category:** {data['Category']}")
                    st.markdown(f"**IC50 Estimate:** {data['IC50 Estimate']}")
                    
                    if 'High' in data['Category']:
                        st.markdown(f'<div class="danger-box">{data["Recommendation"]}</div>', unsafe_allow_html=True)
                    elif 'Moderate' in data['Category']:
                        st.markdown(f'<div class="warning-box">{data["Recommendation"]}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="success-box">{data["Recommendation"]}</div>', unsafe_allow_html=True)
                    
                    st.markdown("#### Carcinogenicity")
                    data = tox_profile['Carcinogenicity']
                    st.metric("Risk Level", data['Carcinogenicity Risk'])
                    st.markdown(f"**Category:** {data['Category']}")
                    st.info(data['Recommendation'])
            
            # Side-by-side comparison
            else:
                st.markdown("### Side-by-Side Comparison")
                st.caption("XGBoost (gradient-boosted) vs Heuristic Methods")

                # Get both prediction types
                admet_profile = real_admet_predictor.comprehensive_toxicity_profile(mol)
                tox_profile = toxicity_predictor.comprehensive_toxicity_profile(mol)

                # Compare each endpoint
                endpoints = ['Hepatotoxicity', 'Cardiotoxicity (hERG)', 'Mutagenicity (Ames)', 'Carcinogenicity']

                for endpoint in endpoints:
                    st.markdown(f"#### {endpoint}")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**XGBoost**")
                        admet_data = admet_profile[endpoint]
                        if admet_data['risk_level'] == 'Unavailable':
                            st.caption("No validated model for this endpoint")
                        else:
                            st.metric("Probability", admet_data['percentage'])
                            st.caption(f"Risk: {admet_data['risk_level']} · {admet_data['confidence']}")
                            if admet_data.get('caveat'):
                                st.warning(admet_data['caveat'])

                    with col2:
                        st.markdown("**Heuristic**")
                        heur_data = tox_profile[endpoint]
                        if endpoint == 'Hepatotoxicity':
                            st.metric("Risk", heur_data['Hepatotoxicity Risk'])
                            st.caption(f"Category: {heur_data['Category']}")
                        elif endpoint == 'Cardiotoxicity (hERG)':
                            st.metric("Risk", heur_data['hERG Inhibition Risk'])
                            st.caption(f"IC50: {heur_data['IC50 Estimate']}")
                        elif endpoint == 'Mutagenicity (Ames)':
                            st.metric("Risk", heur_data['Mutagenicity Risk'])
                            st.caption(f"Prob: {heur_data['Ames Positive Probability']}")
                        else:
                            st.metric("Risk", heur_data['Carcinogenicity Risk'])
                            st.caption(f"Category: {heur_data['Category']}")
                    
                    st.markdown("---")
        else:
            st.error("Invalid SMILES string")


# =============================================================================
# TARGET PREDICTION PAGE
# =============================================================================
# Predicts likely biological target class (kinase, GPCR, ion channel, enzyme)
elif page == "Target Prediction":
    st.markdown(
        section_header("receptor", "Target Class Prediction", "Kinase, GPCR, ion channel and enzyme likelihood — heuristic scoring"),
        unsafe_allow_html=True,
    )
    
    with st.expander("**What Targets Does Your Molecule Hit?**"):
        st.markdown("""
        ### Understanding Biological Targets
        **Targets** are proteins in your body that drugs interact with. Think of them as locks, and drugs as keys.
        
        ### Four Major Target Types
        
        **1. Kinase Inhibitors**
        - *What they are*: Proteins that control cell growth and division
        - *Disease focus*: Cancer (most cancer drugs are kinase inhibitors)
        - *Examples*: Imatinib (leukemia), Gefitinib (lung cancer)
        
        **2. GPCR Ligands**
        - *Full name*: G-Protein Coupled Receptors
        - *What they are*: Cell surface proteins that receive signals
        - *Disease focus*: Heart disease, asthma, allergies, pain
        - *Examples*: Beta-blockers (heart), antihistamines (allergies)
        - *Fun fact*: ~30% of all drugs target GPCRs!
        
        **3. Ion Channel Modulators**
        - *What they are*: Proteins that control electrical signals in cells
        - *Disease focus*: Epilepsy, pain, heart arrhythmias
        - *Examples*: Local anesthetics, anti-epilepsy drugs
        
        **4. Enzyme Inhibitors**
        - *What they are*: Proteins that speed up chemical reactions
        - *Disease focus*: Infections, inflammation, metabolic diseases
        - *Examples*: Aspirin (pain enzyme), statins (cholesterol enzyme)
        
        ### How to Use
        1. **Enter your molecule's SMILES**
        2. **Click "Predict Target Class"**
        3. **See probability for each target type** (0-100%)
        4. **Review the primary prediction** (highest probability)
        
        ### Understanding Results
        - **80-100%**: Highly Likely to hit this target
        - **50-80%**: Likely, worth investigating
        - **20-50%**: Possible, but uncertain
        - **<20%**: Unlikely
        
        **Note**: These are heuristic (rule-based) predictions for education, not a trained model. Real drugs need lab testing to confirm targets!
        """)
    
    st.info("""**Note:** Target class predictions use heuristic scoring based on physicochemical properties typical of each target class.  
    For production use, replace with validated bioactivity models trained on ChEMBL or similar databases.
    """)
    
    # Default SMILES is Imatinib (a kinase inhibitor)
    smiles_input = st.text_input("Enter SMILES String", "Cc1ccc(cc1Nc2nccc(n2)c3cccnc3)NC(=O)c4ccc(cc4)CN5CCN(CC5)C")
    
    if st.button("Predict Target Class", type="primary"):
        is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)
        
        if is_valid:
            mol = mol_processor.smiles_to_mol(canonical_smiles)
            target_profile = target_predictor.comprehensive_target_prediction(mol)
            
            st.markdown("### Primary Target Prediction")
            st.success(f"**Primary Target Class:** {target_profile['Primary Target Class']} (Confidence: {target_profile['Confidence']})")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Kinase Inhibitor")
                data = target_profile['Kinase Inhibitor']
                st.metric("Probability", data['Kinase Inhibitor Probability'])
                st.markdown(f"**Category:** {data['Category']}")
                st.info(data['Interpretation'])
                
                st.markdown("#### GPCR Ligand")
                data = target_profile['GPCR Ligand']
                st.metric("Probability", data['GPCR Ligand Probability'])
                st.markdown(f"**Category:** {data['Category']}")
                st.info(data['Interpretation'])
            
            with col2:
                st.markdown("#### Ion Channel Modulator")
                data = target_profile['Ion Channel Modulator']
                st.metric("Probability", data['Ion Channel Modulator Probability'])
                st.markdown(f"**Category:** {data['Category']}")
                st.info(data['Interpretation'])
                
                st.markdown("#### Enzyme Inhibitor")
                data = target_profile['Enzyme Inhibitor']
                st.metric("Probability", data['Enzyme Inhibitor Probability'])
                st.markdown(f"**Category:** {data['Category']}")
        else:
            st.error("Invalid SMILES string")


# =============================================================================
# PROTEIN & BIOLOGIC STUDIO PAGE
# =============================================================================
# Analysis of proteins, peptides, and biologics (not small molecules)
elif page == "Protein & Biologic Studio":
    st.markdown(
        section_header("peptide", "Protein & Biologic Studio", "Sequence-based developability: solubility, aggregation risk, stability"),
        unsafe_allow_html=True,
    )
    
    with st.expander("**Analyzing Proteins, Peptides & Biologics**"):
        st.markdown("""
        ### What are Biologics?
        **Biologics** are large-molecule drugs made from living cells, including:
        - **Therapeutic proteins** (insulin, growth factors, enzymes)
        - **Monoclonal antibodies** (cancer treatments, autoimmune diseases)
        - **Peptides** (short amino acid chains)
        
        **Difference from small molecules**: SMILES only work for small chemicals. Biologics need **amino acid sequences**.
        
        ### What Can You Analyze?
        
        **1. Peptides (5-60 amino acids)**
        - Examples: Insulin fragments, Semaglutide, Octreotide
        - Used for: Diabetes, hormones, cancer
        
        **2. Proteins (>60 amino acids)**
        - Examples: Antibodies, interferons, growth factors
        - Used for: Cancer, autoimmune diseases, blood disorders
        
        ### Biologic Developability Profile
        
        This tool predicts how "manufacturable" and stable your biologic is:
        
        **Solubility**
        - Can it dissolve in solution?
        - **High**: Easy to formulate
        - **Low**: Difficult manufacturing
        
        **Aggregation Risk**
        - Will it clump together?
        - **Low**: Stable formulation
        - **High**: Shelf-life problems
        
        **Stability**
        - Will it degrade quickly?
        - **Stable** (index < 40): Good shelf life
        - **Unstable** (index > 40): Needs cold storage
        
        ### How to Use
        1. **Select an example** from the dropdown (or enter your own sequence)
        2. **Enter protein sequence** (FASTA format or plain amino acids)
        3. **Click "Analyze Biologic"**
        4. **Review developability profile** (solubility, aggregation, stability)
        
        ### Input Formats Accepted
        
        **Plain sequence**:
        ```
        MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRF
        ```
        
        **FASTA format**:
        ```
        >Insulin B-chain
        MVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRF
        ```
        
        **Note**: These are computational predictions for educational purposes. Real biologics need extensive lab testing!
        """)
    
    st.info("""**Educational Tool**: Biologic developability predictions use sequence-based algorithms (hydrophobicity, charge distribution, composition analysis).  
    For production use, replace with lab-validated assays and protein engineering tools.
    """)
    
    # Example biologic dropdown
    example_biologics = ["Enter your own"] + get_all_peptide_names() + get_all_protein_names()
    selected_example = st.selectbox("Select Example Biologic", example_biologics)
    
    # Set default sequence based on selection
    if selected_example != "Enter your own":
        peptide_data = get_peptide(selected_example)
        protein_data = get_protein(selected_example)
        
        if peptide_data:
            default_seq = peptide_data['sequence']
            st.caption(f"**{selected_example}** - {peptide_data['description']} ({peptide_data['length']} amino acids)")
        elif protein_data:
            default_seq = protein_data['sequence']
            st.caption(f"**{selected_example}** - {protein_data['description']} ({protein_data['length']} amino acids)")
        else:
            default_seq = ""
    else:
        default_seq = ""
    
    # Sequence input
    sequence_input = st.text_area(
        "Enter Protein/Peptide Sequence (FASTA or plain)",
        value=default_seq,
        height=100,
        help="Enter a valid amino acid sequence using single-letter codes"
    )
    
    if st.button("Analyze Biologic", type="primary"):
        is_valid, clean_seq, error = protein_analyzer.validate_fasta(sequence_input)
        
        if is_valid:
            # Run comprehensive biologic analysis
            profile = protein_analyzer.comprehensive_biologic_profile(sequence_input)
            
            st.markdown("### Sequence Information")
            col1, col2, col3 = st.columns(3)
            col1.metric("Length", f"{profile['length']} AA")
            col2.metric("Molecular Weight", f"{profile['molecular_weight']:.2f} Da")
            seq_type = protein_analyzer.detect_sequence_type(clean_seq)
            type_display = {
                'peptide_small': 'Small Peptide',
                'peptide_medium': 'Medium Peptide',
                'protein': 'Protein'
            }
            col3.metric("Type", type_display.get(seq_type, 'Unknown'))
            
            st.markdown("### Biologic Developability Profile")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### Solubility")
                sol_data = profile['solubility']
                st.metric("Solubility Score", f"{sol_data['solubility_score']}/100")
                
                if sol_data['solubility_score'] >= 70:
                    st.markdown('<div class="risk-pill safe-zone">High Solubility</div>', unsafe_allow_html=True)
                elif sol_data['solubility_score'] >= 40:
                    st.markdown('<div class="risk-pill caution-zone">Moderate Solubility</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="risk-pill critical-zone">Low Solubility</div>', unsafe_allow_html=True)
                
                st.info(sol_data['recommendation'])
            
            with col2:
                st.markdown("#### Aggregation Risk")
                agg_data = profile['aggregation_risk']
                st.metric("Aggregation Score", f"{agg_data['aggregation_score']}/100")
                
                if agg_data['aggregation_score'] < 30:
                    st.markdown('<div class="risk-pill safe-zone">Low Risk</div>', unsafe_allow_html=True)
                elif agg_data['aggregation_score'] < 60:
                    st.markdown('<div class="risk-pill caution-zone">Moderate Risk</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="risk-pill critical-zone">High Risk</div>', unsafe_allow_html=True)
                
                st.warning(agg_data['recommendation'])
            
            with col3:
                st.markdown("#### Stability")
                st.metric("Instability Index", f"{profile['instability_index']}")
                st.metric("Category", profile['stability_category'])
                
                if profile['stability_category'] == "Stable":
                    st.markdown('<div class="risk-pill safe-zone">Stable</div>', unsafe_allow_html=True)
                    st.success("Predicted stable (index < 40). Favorable for biologic development.")
                else:
                    st.markdown('<div class="risk-pill critical-zone">Unstable</div>', unsafe_allow_html=True)
                    st.error("Predicted unstable (index > 40). May require formulation optimization.")
            
            st.markdown("### Physicochemical Properties")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Amino Acid Composition")
                comp = profile['amino_acid_composition']
                st.write(f"**Hydrophobic:** {comp['hydrophobic_percent']}%")
                st.write(f"**Polar:** {comp['polar_percent']}%")
                st.write(f"**Charged:** {comp['charged_percent']}%")
                st.write(f"- Positive: {comp['positive_percent']}%")
                st.write(f"- Negative: {comp['negative_percent']}%")
            
            with col2:
                st.markdown("#### Advanced Indices")
                st.metric("Hydrophobicity (GRAVY)", f"{profile['hydrophobicity_index']}")
                st.metric("Aliphatic Index", f"{profile['aliphatic_index']}")
                
                if profile['hydrophobicity_index'] > 0:
                    st.caption("Positive GRAVY = hydrophobic")
                else:
                    st.caption("Negative GRAVY = hydrophilic")
            
            with st.expander("View Full Amino Acid Composition"):
                comp_df = pd.DataFrame([
                    {'Amino Acid': aa, 'Percentage': f"{perc:.2f}%"}
                    for aa, perc in sorted(comp['composition'].items(), key=lambda x: x[1], reverse=True)
                    if perc > 0
                ])
                st.dataframe(comp_df, use_container_width=True, hide_index=True)
        
        else:
            st.error(f"Invalid sequence: {error}")
            st.info("Please enter a valid protein/peptide sequence using single-letter amino acid code (A, C, D, E, F, G, H, I, K, L, M, N, P, Q, R, S, T, V, W, Y)")
    
    # Protein-Ligand Compatibility section — DISABLED
    # This panel was backed by an untrained network (random fixed-seed weights,
    # never fit on any dataset). Its output was noise dressed as a prediction, so
    # the panel is disabled and the module removed, rather than shown with a
    # fabricated score.
    st.markdown("---")
    st.markdown("### Protein-Ligand Compatibility Testing")
    st.warning("""**Temporarily disabled.** This panel previously reported a "binding score" from a
    neural network that was never trained (random, fixed-seed weights) — its output was
    not a meaningful prediction. It's disabled until a version trained on real binding
    data (e.g. PDBbind/BindingDB) is available. No numbers are shown here to avoid
    presenting an untrained model's output as a real assessment.
    """)


# =============================================================================
# DRUG-LIKENESS DECK PAGE
# =============================================================================
# Comprehensive drug-likeness assessment (Lipinski, Veber, QED, SA)
elif page == "Drug-Likeness Deck":
    st.markdown(
        section_header("ruler", "Drug-Likeness Deck", "Lipinski, Veber, QED and synthetic accessibility — published formulas, not fitted models"),
        unsafe_allow_html=True,
    )
    
    with st.expander("**Drug-Likeness Rules - Will This Molecule Make a Good Drug?**"):
        st.markdown("""
        ### What is Drug-Likeness?
        **Drug-Likeness** measures how similar a molecule is to successful drugs. Think of it as a checklist developed from analyzing thousands of approved medicines.
        
        ### Four Industry-Standard Assessments
        
        **1. Lipinski's Rule of 5**
        - *Created by*: Christopher Lipinski (Pfizer scientist, 1997)
        - *Purpose*: Predicts oral bioavailability (can you swallow it as a pill?)
        - *The 5 Rules*:
          - **Molecular Weight ≤ 500**: Not too heavy
          - **LogP ≤ 5**: Not too fatty
          - **H-Bond Donors ≤ 5**: Not too sticky to water
          - **H-Bond Acceptors ≤ 10**: Not too many water connections
        - *Passing*: ≤ 1 violation = Drug-like
        - *Failing*: ≥ 2 violations = Needs improvement
        
        **2. Veber Rules**
        - *Created by*: Daniel Veber (SmithKline Beecham, 2002)
        - *Purpose*: Predicts good absorption
        - *The 2 Rules*:
          - **Rotatable Bonds ≤ 10**: Not too flexible
          - **TPSA ≤ 140 Ų**: Right amount of polarity
        - *Why it matters*: Flexible molecules don't absorb well
        
        **3. QED Score (0-1)**
        - *Stands for*: Quantitative Estimate of Drug-likeness
        - *Think of it as*: A grade from 0-100%
        - *Scoring*:
          - **0.7-1.0**: Excellent (A grade)
          - **0.5-0.7**: Good (B grade)
          - **0.3-0.5**: Fair (C grade)
          - **<0.3**: Poor (needs work)
        - *What it measures*: Overall "drug quality" combining all properties
        
        **4. SA Score (1-10)**
        - *Stands for*: Synthetic Accessibility
        - *Purpose*: How hard is it to make this molecule in a lab?
        - *Scoring*:
          - **1-3**: Easy to synthesize
          - **4-6**: Moderate complexity
          - **7-10**: Very difficult/expensive
        - *Why it matters*: No point designing a drug you can't make!
        
        ### How to Use
        1. **Enter your molecule's SMILES**
        2. **Click "Assess Drug-Likeness"**
        3. **Review all four assessments**
        4. **Check the Risk Pills**:
           - **Safe Zone**: Passes criteria
           - **Caution Zone**: Some violations
           - **Critical Zone**: Major issues
        
        ### What Makes a Great Drug Candidate?
        - **Lipinski**: 0-1 violations
        - **Veber**: Passes both rules
        - **QED**: > 0.5 (preferably > 0.7)
        - **SA Score**: < 6 (preferably < 4)
        
        **Real Example**: Aspirin scores QED = 0.55, SA = 1.0 - Good drug!
        """)
    
    st.info("""**Comprehensive drug-likeness assessment** using validated pharmaceutical criteria: Lipinski Rule of 5, Veber rules, QED score, and Synthetic Accessibility.
    """)
    
    smiles_input = st.text_input("Enter SMILES String", "CC(C)Cc1ccc(cc1)C(C)C(=O)O")
    
    if st.button("Assess Drug-Likeness", type="primary"):
        is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)
        
        if is_valid:
            mol = mol_processor.smiles_to_mol(canonical_smiles)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("#### Lipinski Rule of 5")
                lipinski = mol_processor.calculate_lipinski_descriptors(mol)
                
                for key, value in lipinski.items():
                    if key != 'Passes' and key != 'Violations':
                        st.metric(key, value)
                
                if lipinski['Passes']:
                    st.markdown('<div class="risk-pill safe-zone">Safe Zone — Drug-Like</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="risk-pill caution-zone">Caution Zone — {lipinski["Violations"]} Violations</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown("#### Veber Rules")
                veber = mol_processor.calculate_veber_descriptors(mol)
                
                st.metric("Rotatable Bonds", veber['Rotatable Bonds'])
                st.metric("TPSA", f"{veber['TPSA']} Ų")
                
                if veber['Passes']:
                    st.markdown('<div class="risk-pill safe-zone">Safe Zone — Passes</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="risk-pill caution-zone">Caution Zone — Does Not Pass</div>', unsafe_allow_html=True)
            
            col3, col4 = st.columns(2)
            with col3:
                st.markdown("#### QED Score")
                qed = mol_processor.calculate_qed(mol)
                # A failed QED used to arrive here as 0.0 and fall straight
                # through to the "Critical Zone - Low Drug-Likeness" branch,
                # turning a crashed calculation into a verdict on the molecule.
                if qed is None:
                    st.metric("QED", "unavailable")
                    st.warning(
                        "QED could not be calculated for this structure. "
                        "This is a calculation failure, not a low score."
                    )
                else:
                    st.metric("QED", f"{qed:.3f}")
                    if qed >= 0.7:
                        st.markdown('<div class="risk-pill safe-zone">Safe Zone — High Drug-Likeness</div>', unsafe_allow_html=True)
                    elif qed >= 0.4:
                        st.markdown('<div class="risk-pill caution-zone">Caution Zone — Moderate</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="risk-pill critical-zone">Critical Zone — Low Drug-Likeness</div>', unsafe_allow_html=True)
            
            with col4:
                st.markdown("#### Synthetic Accessibility")
                sa_score = mol_processor.calculate_sa_score(mol)
                st.metric("SA Score", f"{sa_score:.2f}")
                
                if sa_score <= 3:
                    st.markdown('<div class="risk-pill safe-zone">Safe Zone — Easy to Synthesize</div>', unsafe_allow_html=True)
                elif sa_score <= 6:
                    st.markdown('<div class="risk-pill caution-zone">Caution Zone — Moderate Complexity</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="risk-pill critical-zone">Critical Zone — Difficult to Synthesize</div>', unsafe_allow_html=True)
        else:
            st.error("Invalid SMILES string")


# =============================================================================
# EXPLAINABILITY CANVAS PAGE
# =============================================================================
# ML model interpretability with feature importance
elif page == "Explainability Canvas":
    st.markdown(
        section_header("calibration", "Explainability Canvas", "Why the score says that — traced back to the published formula, not a fitted model"),
        unsafe_allow_html=True,
    )
    
    with st.expander("**Understanding This Assessment - Why the Score Says That**"):
        st.markdown("""
        ### What is Explainability?
        **Explainability** shows you WHY a molecule scores the way it does — not a black box,
        but rules you can check by hand.

        ### Rule-Based, Not a Trained Classifier

        This page evaluates drug-likeness using established **formulas**, not a machine-learning
        model trained on data:

        - **Lipinski's Rule of 5** — molecular weight, LogP, H-bond donors/acceptors
        - **Veber Rules** — rotatable bonds, topological polar surface area (TPSA)
        - **QED** (Quantitative Estimate of Drug-likeness) — a weighted composite of 8
          physicochemical properties, published by Bickerton et al. (2012)
        - **Synthetic Accessibility** — a fragment-complexity estimate

        Each of these is a fixed, published formula applied directly to the molecule's RDKit
        descriptors — every number here traces to a documented equation, not a fitted model.

        ### How to Use
        1. **Enter your molecule's SMILES**
        2. **Click "Run Drug-Likeness Analysis"**
        3. **Review each rule's pass/fail and the overall score**

        **Why this matters**: Because these are formulas, not learned models, there is no
        "confidence" or feature-importance chart to show — the calculation itself *is* the
        explanation.
        """)

    smiles_input = st.text_input("Enter SMILES String", "CC(C)Cc1ccc(cc1)C(C)C(=O)O")

    if st.button("Run Drug-Likeness Analysis", type="primary"):
        is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)

        if is_valid:
            mol = mol_processor.smiles_to_mol(canonical_smiles)

            # Rule-based drug-likeness (QED, Lipinski Ro5, Veber) — not a trained classifier
            analysis = drug_likeness.comprehensive_analysis(mol)

            st.markdown("### Rule-Based Drug-Likeness Results")
            st.caption("Lipinski, Veber, QED, Synthetic Accessibility — published formulas, not a trained model")

            col1, col2, col3 = st.columns(3)
            col1.metric("Lipinski Ro5", "Pass" if analysis['Lipinski'].get('Passes') else "Fail",
                        f"{analysis['Lipinski'].get('Violations', '?')} violations")
            col2.metric("Veber", "Pass" if analysis['Veber'].get('Passes') else "Fail")
            col3.metric("QED Score", analysis['QED'].get('QED Score', 'n/a'), analysis['QED'].get('Category', ''))

            st.markdown(f"**Overall Score:** {analysis['Overall Score']} — {analysis['Recommendation']}")

            st.markdown("### Rule Breakdown")
            colA, colB = st.columns(2)
            with colA:
                st.markdown("#### Lipinski's Rule of 5")
                st.write(analysis['Lipinski'])
                st.markdown("#### QED")
                st.write(analysis['QED'])
            with colB:
                st.markdown("#### Veber Rules")
                st.write(analysis['Veber'])
                st.markdown("#### Synthetic Accessibility")
                st.write(analysis['Synthetic Accessibility'])

            st.info("""**Method**: Rule-based (structural formulas applied to RDKit-computed descriptors) —
            not a trained classifier, so there is no cross-validation or feature-importance chart.
            Lipinski/Veber/QED are the same industry-standard rules used elsewhere in this app's
            Drug-Likeness Deck.
            """)
        else:
            st.error("Invalid SMILES string")


# =============================================================================
# KNOWLEDGE GRAPH PAGE
# =============================================================================
# Drug-target-disease relationship explorer with interactive visualization
elif page == "Knowledge Graph":
    st.markdown(
        section_header("graph", "Biomedical Knowledge Graph Explorer", "Drug-target-disease relationships across 70+ FDA-approved compounds"),
        unsafe_allow_html=True,
    )
    
    with st.expander("**How Drugs, Targets, and Diseases Connect**"):
        st.markdown("""
        ### What is a Knowledge Graph?
        A **Knowledge Graph** is like a map showing how drugs, proteins, and diseases are connected. Think of it as a relationship diagram!
        
        ### The Connections
        
        **Drugs → Targets → Diseases**
        
        Example: **Imatinib** → inhibits → **BCR-ABL protein** → treats → **Leukemia**
        
        ### What You Can Explore
        
        **1. Interactive Visualization**
        - See the entire network as a beautiful interactive graph
        - Color-coded nodes (Blue=Drugs, Green=Targets, Red=Diseases, Purple=Pathways)
        - Zoom, pan, and drag nodes to explore connections
        - Hover over nodes to see detailed information
        - Filter by node type to focus on specific relationships
        
        **2. Drug Mechanism**
        - Pick a drug (like Imatinib or Pembrolizumab)
        - See what proteins it targets
        - See what diseases it treats
        - Learn about biological pathways involved
        
        **3. Target Information**
        - Pick a protein target (like EGFR or PD-1)
        - See all drugs that hit this target
        - See diseases linked to this target
        
        **4. Disease Insights**
        - Select a disease (like Melanoma or Breast Cancer)
        - Find approved drugs for treatment
        - Discover associated protein targets
        - Identify involved biological pathways
        
        **5. Drug Repurposing**
        - Graph-based predictions for new disease uses (not a trained model)
        - Based on shared targets and network patterns
        - Discover potential new applications for existing drugs
        
        **6. Network Analytics**
        - Find the most connected nodes (hubs)
        - Discover shortest paths between drugs and diseases
        - Measure node importance with centrality metrics
        
        **7. Export & Share**
        - Download graph data in multiple formats
        - JSON, CSV, or GraphML for analysis in other tools
        - Share findings with colleagues
        
        ### Example Drugs in Our Graph (70+ total)
        - **Cancer**: Imatinib, Pembrolizumab, Trastuzumab, Olaparib
        - **Immunotherapy**: Nivolumab, Atezolizumab, Durvalumab
        - **Arthritis**: Adalimumab, Infliximab, Tofacitinib
        - **And many more!**
        
        ### Key Terms
        - **Target**: The protein the drug interacts with
        - **Pathway**: Chain of biological events (like a domino effect)
        - **Indication**: The disease the drug treats
        - **Mechanism of Action (MOA)**: How the drug works in your body
        - **Centrality**: How important/connected a node is in the network
        - **Repurposing**: Finding new uses for existing drugs
        
        **This shows how drugs work!** Real pharmaceutical researchers use similar graphs with millions of connections.
        """)
    
    st.info("""
    This knowledge graph contains 70+ FDA-approved drugs with their targets, pathways, and disease indications.
    Explore connections visually, discover drug repurposing opportunities, and export data for further analysis.
    """)
    
    # Graph statistics
    stats = kg.get_graph_statistics()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Nodes", stats['Total Nodes'])
    col2.metric("Drugs", stats['Compounds'])
    col3.metric("Targets", stats['Targets'])
    col4.metric("Diseases", stats['Diseases'])
    col5.metric("Pathways", stats['Pathways'])
    
    # Tabbed interface for different features
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Interactive Visualization",
        "Query Graph", 
        "Drug Repurposing",
        "Network Analytics",
        "Export Data"
    ])
    
    # Tab 1: Interactive PyVis visualization
    with tab1:
        st.markdown("### Interactive Network Visualization")
        
        st.info("**Tip**: The visualization may take a few seconds to load. Zoom, pan, and drag nodes to explore!")
        
        filter_options = st.multiselect(
            "Filter by Node Type",
            options=['compound', 'target', 'disease', 'pathway'],
            default=['compound', 'target', 'disease', 'pathway'],
            help="Select which types of nodes to display"
        )
        
        col_viz1, col_viz2 = st.columns([3, 1])
        
        with col_viz2:
            st.markdown("**Legend**")
            st.markdown("**Drugs** (Blue)")
            st.markdown("**Targets** (Green)")
            st.markdown("**Diseases** (Red)")
            st.markdown("**Pathways** (Purple)")
            st.markdown("---")
            st.markdown("**Node Size** = Number of connections")
            st.markdown("**Hover** = See details")
        
        with col_viz1:
            if st.button("Generate Interactive Graph", type="primary"):
                with st.spinner("Creating interactive visualization..."):
                    try:
                        html_file = kg.create_interactive_visualization(
                            filter_types=filter_options if filter_options else None
                        )
                        
                        with open(html_file, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                        
                        st.components.v1.html(html_content, height=700, scrolling=True)
                        st.success("Visualization loaded! Drag nodes to rearrange, scroll to zoom.")
                    except Exception as e:
                        st.error(f"Error generating visualization: {str(e)}")
    
    # Tab 2: Query Graph
    with tab2:
        st.markdown("### Query Knowledge Graph")
        
        query_type = st.selectbox(
            "Query Type", 
            ["Drug Mechanism", "Target Information", "Disease Relationships"]
        )
        
        if query_type == "Drug Mechanism":
            all_drugs = sorted([n for n, d in kg.graph.nodes(data=True) 
                               if d.get('node_type') == 'compound'])
            selected_drug = st.selectbox("Select Drug", all_drugs)
            
            if st.button("Get Mechanism of Action"):
                moa = kg.get_mechanism_of_action(selected_drug)
                
                if 'error' not in moa:
                    st.markdown(f"### {moa['Drug']}")
                    
                    col_moa1, col_moa2 = st.columns(2)
                    with col_moa1:
                        st.markdown("**Targets**")
                        for target in moa['Targets']:
                            st.markdown(f"- {target}")
                    
                    with col_moa2:
                        st.markdown("**Indications**")
                        for indication in moa['Indications']:
                            st.markdown(f"- {indication}")
                    
                    if moa['Pathways']:
                        st.markdown("**Biological Pathways**")
                        for pathway in moa['Pathways']:
                            st.markdown(f"- {pathway}")
                    else:
                        st.info("No pathway information available")
                else:
                    st.warning(moa['error'])
        
        elif query_type == "Target Information":
            all_targets = sorted([n for n, d in kg.graph.nodes(data=True) 
                                 if d.get('node_type') == 'target'])
            selected_target = st.selectbox("Select Target", all_targets)
            
            if st.button("Get Target Information"):
                drugs = kg.find_similar_drugs(selected_target)
                diseases = kg.get_target_diseases(selected_target)
                
                st.markdown(f"### {selected_target}")
                
                col_tgt1, col_tgt2 = st.columns(2)
                with col_tgt1:
                    st.markdown(f"**Drugs Targeting {selected_target}** ({len(drugs)})")
                    if drugs:
                        for drug in drugs:
                            st.markdown(f"- {drug}")
                    else:
                        st.info("No drugs found")
                
                with col_tgt2:
                    st.markdown(f"**Associated Diseases** ({len(diseases)})")
                    if diseases:
                        for disease in diseases:
                            st.markdown(f"- {disease}")
                    else:
                        st.info("No diseases found")
        
        else:
            all_diseases = sorted([n for n, d in kg.graph.nodes(data=True) 
                                  if d.get('node_type') == 'disease'])
            selected_disease = st.selectbox("Select Disease", all_diseases)
            
            if st.button("Get Disease Information"):
                disease_info = kg.get_disease_relationships(selected_disease)
                
                if 'error' not in disease_info:
                    st.markdown(f"### {disease_info['Disease']}")
                    
                    col_dis1, col_dis2, col_dis3 = st.columns(3)
                    
                    with col_dis1:
                        st.metric("Approved Drugs", disease_info['Total_Drugs'])
                        if disease_info['Approved_Drugs']:
                            for drug in disease_info['Approved_Drugs']:
                                st.markdown(f"- {drug}")
                    
                    with col_dis2:
                        st.metric("Associated Targets", disease_info['Total_Targets'])
                        if disease_info['Associated_Targets']:
                            for target in disease_info['Associated_Targets']:
                                st.markdown(f"- {target}")
                    
                    with col_dis3:
                        st.markdown("**Pathways**")
                        if disease_info['Involved_Pathways']:
                            for pathway in disease_info['Involved_Pathways']:
                                st.markdown(f"- {pathway}")
                        else:
                            st.info("No pathways")
                else:
                    st.warning(disease_info['error'])
    
    # Tab 3: Drug Repurposing
    with tab3:
        st.markdown("### Drug Repurposing Predictions")
        st.info("""**Drug repurposing** identifies new therapeutic uses for existing drugs. This is a **graph-based
        heuristic** (shared-target set intersection + network distance over the knowledge graph), not a trained
        model — it uses network patterns and shared targets to surface potential new indications for review.
        """)
        
        all_drugs = sorted([n for n, d in kg.graph.nodes(data=True) 
                           if d.get('node_type') == 'compound'])
        selected_drug_repo = st.selectbox("Select Drug for Repurposing Analysis", all_drugs, key="repo_drug")
        
        num_predictions = st.slider("Number of Predictions", 3, 10, 5)
        
        if st.button("Predict Repurposing Opportunities", type="primary"):
            with st.spinner("Analyzing network patterns..."):
                predictions = kg.predict_drug_repurposing(selected_drug_repo, top_n=num_predictions)
                
                if predictions:
                    st.success(f"Found {len(predictions)} potential repurposing opportunities!")
                    
                    current_uses = kg.get_drug_indications(selected_drug_repo)
                    st.markdown(f"**Current Approved Uses**: {', '.join(current_uses)}")
                    st.markdown("---")
                    
                    for i, pred in enumerate(predictions, 1):
                        with st.expander(f"#{i}: {pred['disease']} (Score: {pred['repurposing_score']:.1f})"):
                            col_repo1, col_repo2 = st.columns(2)
                            
                            with col_repo1:
                                st.markdown(f"**Shared Targets ({pred['num_shared_targets']})**")
                                for target in pred['shared_targets']:
                                    st.markdown(f"- {target}")
                            
                            with col_repo2:
                                st.metric("Network Distance", f"{pred['path_length']} steps")
                                st.metric("Repurposing Score", f"{pred['repurposing_score']:.1f}")
                            
                            st.info(f"**Rationale**: {selected_drug_repo} targets {', '.join(pred['shared_targets'])}, which are also involved in {pred['disease']}.")
                else:
                    st.warning("No repurposing opportunities found. This drug may have limited target overlap with other diseases.")
    
    # Tab 4: Network Analytics
    with tab4:
        st.markdown("### Network Analytics")
        
        analytics_type = st.selectbox(
            "Analysis Type",
            ["Most Connected Nodes (Hubs)", "Shortest Path Finder", "Centrality Rankings"]
        )
        
        if analytics_type == "Most Connected Nodes (Hubs)":
            st.info("Identify the most connected nodes (hubs) in the network. Hubs often represent key drugs, targets, or diseases.")
            
            top_n_hubs = st.slider("Number of Top Nodes", 5, 20, 10)
            
            if st.button("Find Network Hubs"):
                top_nodes = kg.get_top_central_nodes(metric='degree', top_n=top_n_hubs)
                
                st.markdown(f"### Top {top_n_hubs} Most Connected Nodes")
                
                hub_data = []
                for node, centrality in top_nodes:
                    node_type = kg.graph.nodes[node].get('node_type', 'unknown')
                    degree = kg.graph.degree(node)
                    hub_data.append({
                        'Rank': len(hub_data) + 1,
                        'Node': node,
                        'Type': node_type.capitalize(),
                        'Connections': degree,
                        'Centrality': f"{centrality:.3f}"
                    })
                
                hub_df = pd.DataFrame(hub_data)
                st.dataframe(hub_df, use_container_width=True, hide_index=True)
        
        elif analytics_type == "Shortest Path Finder":
            st.info("Find the shortest path between any two nodes in the knowledge graph.")
            
            col_path1, col_path2 = st.columns(2)
            
            all_nodes = sorted(kg.graph.nodes())
            
            with col_path1:
                source_node = st.selectbox("Source Node", all_nodes)
            with col_path2:
                target_node = st.selectbox("Target Node", all_nodes, index=min(10, len(all_nodes)-1))
            
            if st.button("Find Shortest Path"):
                if source_node == target_node:
                    st.warning("Source and target must be different nodes!")
                else:
                    path = kg.find_shortest_path(source_node, target_node)
                    
                    if path:
                        st.success(f"Found path with {len(path)-1} steps!")
                        st.markdown(f"**Path**: {' → '.join(path)}")
                        st.metric("Path Length", len(path)-1)
                    else:
                        st.error("No path found between these nodes.")
        
        else:
            st.info("Rank all nodes by centrality metrics to identify the most important entities.")
            
            metric_type = st.selectbox(
                "Centrality Metric",
                ["Degree (Connections)", "Betweenness (Bridge)", "Closeness (Proximity)"]
            )
            
            metric_map = {
                "Degree (Connections)": "degree",
                "Betweenness (Bridge)": "betweenness",
                "Closeness (Proximity)": "closeness"
            }
            
            selected_metric = metric_map[metric_type]
            top_n_central = st.slider("Number of Top Nodes", 5, 20, 10, key="central_slider")
            
            if st.button("Calculate Centrality Rankings"):
                top_nodes = kg.get_top_central_nodes(metric=selected_metric, top_n=top_n_central)
                
                st.markdown(f"### Top {top_n_central} Nodes by {metric_type}")
                
                central_data = []
                for node, centrality in top_nodes:
                    node_type = kg.graph.nodes[node].get('node_type', 'unknown')
                    central_data.append({
                        'Rank': len(central_data) + 1,
                        'Node': node,
                        'Type': node_type.capitalize(),
                        'Centrality Score': f"{centrality:.4f}"
                    })
                
                central_df = pd.DataFrame(central_data)
                st.dataframe(central_df, use_container_width=True, hide_index=True)
    
    # Tab 5: Export Data
    with tab5:
        st.markdown("### Export Knowledge Graph Data")
        st.info("Download the knowledge graph in various formats for external analysis or sharing.")
        
        col_exp1, col_exp2, col_exp3 = st.columns(3)
        
        with col_exp1:
            st.markdown("#### JSON Format")
            st.markdown("Complete graph with metadata")
            if st.button("Export as JSON"):
                json_data = kg.export_to_json()
                st.download_button(
                    label="Download JSON",
                    data=json_data,
                    file_name="knowledge_graph.json",
                    mime="application/json"
                )
        
        with col_exp2:
            st.markdown("#### CSV Format")
            st.markdown("Separate node & edge tables")
            if st.button("Export as CSV"):
                nodes_df, edges_df = kg.export_to_csv()
                
                nodes_csv = nodes_df.to_csv(index=False)
                edges_csv = edges_df.to_csv(index=False)
                
                col_csv1, col_csv2 = st.columns(2)
                with col_csv1:
                    st.download_button(
                        label="Nodes CSV",
                        data=nodes_csv,
                        file_name="kg_nodes.csv",
                        mime="text/csv"
                    )
                with col_csv2:
                    st.download_button(
                        label="Edges CSV",
                        data=edges_csv,
                        file_name="kg_edges.csv",
                        mime="text/csv"
                    )
        
        with col_exp3:
            st.markdown("#### GraphML Format")
            st.markdown("For Cytoscape, Gephi, etc.")
            if st.button("Export as GraphML"):
                try:
                    graphml_data = kg.export_to_graphml()
                    st.download_button(
                        label="Download GraphML",
                        data=graphml_data,
                        file_name="knowledge_graph.graphml",
                        mime="application/xml"
                    )
                except Exception as e:
                    st.error(f"Error exporting GraphML: {str(e)}")


# =============================================================================
# LEAD LAB PAGE
# =============================================================================
# Batch screening and prioritization of multiple molecules
elif page == "Lead Lab":
    st.markdown(
        section_header("plate", "Lead Lab — Batch Screening & Prioritization", "Many molecules, one ranked pass — drug-likeness scored and sorted together"),
        unsafe_allow_html=True,
    )
    
    with st.expander("**Screening Many Molecules at Once**"):
        st.markdown("""
        ### What is Batch Screening?
        Instead of testing one molecule at a time, **Lead Lab** lets you analyze many molecules together and rank them from best to worst!
        
        ### Think of it like:
        - **Report Card**: Grades multiple students at once
        - **Job Applicants**: Ranks candidates from most to least qualified
        - **Lead Lab**: Ranks molecules from most to least drug-like
        
        ### What It Does
        
        For each molecule in your list, it calculates:
        1. **Molecular Weight** - Is it the right size?
        2. **LogP** - Is it balanced (water vs fat)?
        3. **Lipinski Violations** - Does it pass the drug-likeness rules?
        4. **QED Score** - Overall drug quality (0-1 scale)
        
        Then it **ranks them** from highest to lowest QED Score!
        
        ### How to Use
        
        **Option 1: Example Dataset** (Easiest!)
        1. Click "Run Batch Analysis on Example Set"
        2. See results for 5 common drugs
        3. Download results as CSV
        
        **Option 2: Upload Your Own**
        1. Prepare a CSV file with columns: `name`, `smiles`
        2. Upload the file
        3. Get ranked results instantly!
        
        ### Understanding Results Table
        
        - **Name**: Molecule name
        - **SMILES**: Molecular structure code
        - **MW**: Molecular weight (lighter is often better)
        - **LogP**: Fat-loving measure (0-3 is ideal)
        - **Lipinski Violations**: Fewer is better (0-1 = good)
        - **QED Score**: Overall grade (higher = better drug)
        - **Passes Lipinski**: Yes/No (Yes = drug-like!)
        
        **Top ranked = Best drug candidate!**
        
        ### Example: If you had 100 molecules, this tool:
        1. Tests all 100 automatically
        2. Calculates drug-likeness for each
        3. Ranks them from #1 (best) to #100 (worst)
        4. Saves you weeks of manual work!
        
        **Real pharmaceutical companies screen millions of molecules this way!**
        """)
    
    st.info("""
    Upload a CSV file with SMILES strings or use the example dataset to screen multiple compounds.
    Results will be ranked by drug-likeness and ADME/PK properties.
    """)
    
    input_method = st.radio("Input Method", ["Example Dataset", "Upload CSV"])
    
    if input_method == "Example Dataset":
        if st.button("Run Batch Analysis on Example Set"):
            # Example molecules for demonstration
            example_molecules = [
                ("Ibuprofen", "CC(C)Cc1ccc(cc1)C(C)C(=O)O"),
                ("Aspirin", "CC(=O)Oc1ccccc1C(=O)O"),
                ("Caffeine", "CN1C=NC2=C1C(=O)N(C(=O)N2C)C"),
                ("Paracetamol", "CC(=O)Nc1ccc(cc1)O"),
                ("Atorvastatin", "CC(C)c1c(c(c(c(c1OCC(CC(CC(=O)O)O)O)c2ccc(cc2)F)C(=O)Nc3ccccc3)O)C(C)C")
            ]
            
            results = []
            
            for name, smiles in example_molecules:
                is_valid, canonical_smiles = mol_processor.validate_smiles(smiles)
                
                if is_valid:
                    mol = mol_processor.smiles_to_mol(canonical_smiles)
                    
                    lipinski = drug_likeness.lipinski_rule_of_5(mol)
                    qed = drug_likeness.qed_score(mol)
                    
                    results.append({
                        'Name': name,
                        'SMILES': canonical_smiles,
                        'MW': lipinski['Molecular Weight'],
                        'LogP': lipinski['LogP'],
                        'Lipinski Violations': lipinski['Violations'],
                        'QED Score': qed['QED Score'],
                        'Passes Lipinski': 'Yes' if lipinski['Passes'] else 'No'
                    })
            
            results_df = pd.DataFrame(results)
            results_df = results_df.sort_values('QED Score', ascending=False)
            
            st.markdown("### Batch Analysis Results")
            st.dataframe(results_df, use_container_width=True, hide_index=True)
            
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="Download Results as CSV",
                data=csv,
                file_name="batch_screening_results.csv",
                mime="text/csv"
            )
    
    else:
        uploaded_file = st.file_uploader("Upload CSV (columns: name, smiles)", type=['csv'])
        st.markdown(
            inline("plate", "One row per molecule. A 'smiles' column is required; 'name' is optional."),
            unsafe_allow_html=True,
        )
        # Previously this branch accepted a file and printed "CSV upload
        # functionality ready" without reading it — a stub dressed as a
        # working feature. It now runs the same Lipinski/QED scoring as the
        # example-dataset path above, on whatever rows validate.
        if uploaded_file:
            try:
                upload_df = pd.read_csv(uploaded_file)
            except Exception as e:
                upload_df = None
                st.error(f"Could not read this file as CSV: {e}")

            if upload_df is not None:
                if 'smiles' not in upload_df.columns:
                    st.error("CSV must include a 'smiles' column (column names found: "
                              f"{', '.join(upload_df.columns)}).")
                else:
                    results = []
                    skipped = 0
                    for _, row in upload_df.iterrows():
                        raw_smiles = str(row['smiles'])
                        has_name = 'name' in upload_df.columns and pd.notna(row.get('name'))
                        raw_name = str(row['name']) if has_name else raw_smiles
                        is_valid, canonical_smiles = mol_processor.validate_smiles(raw_smiles)
                        if not is_valid:
                            skipped += 1
                            continue
                        mol = mol_processor.smiles_to_mol(canonical_smiles)
                        lipinski = drug_likeness.lipinski_rule_of_5(mol)
                        qed = drug_likeness.qed_score(mol)
                        results.append({
                            'Name': raw_name,
                            'SMILES': canonical_smiles,
                            'MW': lipinski['Molecular Weight'],
                            'LogP': lipinski['LogP'],
                            'Lipinski Violations': lipinski['Violations'],
                            'QED Score': qed['QED Score'],
                            'Passes Lipinski': 'Yes' if lipinski['Passes'] else 'No'
                        })

                    if not results:
                        st.warning("No valid SMILES were found in the uploaded file.")
                    else:
                        results_df = pd.DataFrame(results).sort_values('QED Score', ascending=False)
                        st.markdown(f"### Batch Analysis Results — {len(results_df)} molecule(s)")
                        if skipped:
                            st.caption(f"{skipped} row(s) skipped — SMILES did not parse.")
                        st.dataframe(results_df, use_container_width=True, hide_index=True)
                        csv_out = results_df.to_csv(index=False)
                        st.download_button(
                            label="Download Results as CSV",
                            data=csv_out,
                            file_name="batch_screening_results.csv",
                            mime="text/csv",
                        )


# =============================================================================
# CASE STUDY PAGE
# =============================================================================
# Demonstration of kinase inhibitor lead ranking workflow
elif page == "Case Study":
    st.markdown(
        section_header("flask", "Case Study: Ranking Kinase Inhibitor Leads", "Five candidates, five criteria, one applied workflow"),
        unsafe_allow_html=True,
    )
    
    with st.expander("**Real-World Example: Finding the Best Cancer Drug Candidate**"):
        st.markdown("""
        ### What is a Case Study?
        A **Case Study** is a real-world example that shows you how all the tools work together in an actual drug discovery project!
        
        ### The Scenario
        
        **Goal**: Find the best kinase inhibitor for cancer treatment
        
        **Challenge**: You have 5 candidate molecules. Which one should you develop into a drug?
        
        ### The Evaluation Process
        
        We test each candidate on **5 criteria**:
        
        1. **Drug-Likeness (Lipinski's Rule)** - Can it be taken as a pill?
           - Score: 20 points for passing
        
        2. **Overall Quality (QED Score)** - Is it a good drug overall?
           - Score: 20 points if QED ≥ 0.5
        
        3. **Kinase Activity** - Does it actually hit kinases?
           - Score: 30 points if predicted as kinase inhibitor
        
        4. **Absorption (ADME)** - Can your body absorb it?
           - Score: 15 points for good absorption
        
        5. **Safety (Toxicity)** - Is it safe for the liver?
           - Score: 15 points for low liver toxicity
        
        **Total possible: 100 points**
        
        ### How to Use
        
        1. **Read the scenario** (already on this page)
        2. **Click "Run Complete Analysis on All Candidates"**
        3. **Review the results table** sorted by total score
        4. **See the recommended lead** (highest scorer)
        5. **Examine charts** showing how candidates compare
        
        ### Understanding Results
        
        **Candidate Scores**:
        - **85-100**: Excellent candidate! Move forward
        - **70-84**: Good candidate, needs minor optimization
        - **50-69**: Moderate, needs significant work
        - **<50**: Poor candidate, consider alternatives
        
        ### What You Learn
        
        This shows the **real pharmaceutical workflow**:
        1. Start with multiple candidates
        2. Test each on multiple criteria
        3. Score and rank them
        4. Pick the winner
        5. Invest resources in the best one
        
        **This is how billion-dollar drugs are discovered!**
        
        Instead of spending millions testing all 5 in the lab, you predict first and test only the winner!
        """)
    
    # Load case study data
    case_study = get_case_study_data()
    
    st.markdown(f"#### {case_study['title']}")
    st.write(case_study['description'])
    
    st.markdown("### Evaluation Criteria")
    for i, criterion in enumerate(case_study['evaluation_criteria'], 1):
        st.write(f"{i}. {criterion}")
    
    if st.button("Run Complete Analysis on All Candidates", type="primary"):
        results = []
        
        for candidate in case_study['molecules']:
            is_valid, canonical_smiles = mol_processor.validate_smiles(candidate['smiles'])
            
            if is_valid:
                mol = mol_processor.smiles_to_mol(canonical_smiles)
                
                # Run all analyses
                lipinski = drug_likeness.lipinski_rule_of_5(mol)
                qed = drug_likeness.qed_score(mol)
                kinase_pred = target_predictor.predict_kinase_inhibitor(mol)
                adme = adme_predictor.predict_caco2_permeability(mol)
                tox = toxicity_predictor.predict_hepatotoxicity(mol)
                
                # Calculate overall score
                score = 0
                if lipinski['Passes']: score += 20
                if qed['QED Score'] >= 0.5: score += 20
                if 'Likely' in kinase_pred['Category']: score += 30
                if 'High' in adme['Category'] or 'Moderate' in adme['Category']: score += 15
                if 'Low' in tox['Category']: score += 15
                
                results.append({
                    'Candidate': candidate['name'],
                    'Lipinski': 'Pass' if lipinski['Passes'] else 'Fail',
                    'QED': qed['QED Score'],
                    'Kinase Prob': kinase_pred['Kinase Inhibitor Probability'],
                    'Permeability': adme['Category'],
                    'Hepatotox Risk': tox['Category'],
                    'Overall Score': score
                })
        
        # Sort by overall score
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('Overall Score', ascending=False)
        results_df['Rank'] = range(1, len(results_df) + 1)
        
        st.markdown("### Lead Ranking Results")
        st.dataframe(results_df[['Rank', 'Candidate', 'Overall Score', 'Lipinski', 'QED', 
                                 'Kinase Prob', 'Permeability', 'Hepatotox Risk']], 
                    use_container_width=True, hide_index=True)
        
        st.success(f"**Recommended Lead:** {results_df.iloc[0]['Candidate']} (Score: {results_df.iloc[0]['Overall Score']}/100)")
        
        st.markdown("### Conclusion")
        st.info("""
        This case study demonstrates a typical pharmaceutical lead prioritization workflow:
        
        1. **Multi-parameter optimization**: Balancing efficacy (kinase inhibition) with safety (toxicity) and PK (permeability)
        2. **Structured decision making**: Using rule-based scoring (Lipinski, QED, and the heuristic kinase/ADME/toxicity predictors — not trained models) to rank candidates before expensive experimental validation
        3. **Risk mitigation**: Identifying potential liabilities early in the discovery process
        
        This mirrors industry-standard approaches to lead optimization in kinase inhibitor drug discovery programs.
        """)


# =============================================================================
# ABOUT PAGE
# =============================================================================
# Platform information and credits
elif page == "About":
    # No glyph in the 22-icon set marks "platform info" without stretching a
    # concept past what it actually means (rule: no icon beats a wrong one) —
    # this header matches section_header's typography without a glyph.
    st.markdown(
        '<div style="margin:2rem 0 .9rem 0"><span style="font-size:1.15rem;font-weight:600;'
        'color:#E7ECF3;letter-spacing:-.01em">About Ardit BioStudio</span></div>',
        unsafe_allow_html=True,
    )
    
    st.markdown("""
    ### Ardit BioStudio — ADMET property prediction
    
    An open-source educational platform demonstrating computational drug discovery workflows using 
    cheminformatics, QSAR modeling, and machine learning techniques used in pharmaceutical research.
    
    #### Key Features
    
    - **Molecular Property Prediction**: ADME/PK, toxicity, drug-likeness
    - **Target Class Prediction**: Kinase, GPCR, ion channel, enzyme inhibitors
    - **ADMET Prediction**: XGBoost (7 endpoints, held-out validated — see
      `models/saved_models/admet_models_manifest.json`)
    - **Rule-Based Scoring**: ADME/PK heuristics, structural-alert toxicity screening,
      target-class heuristics, drug-likeness (Lipinski, Veber, QED)
    - **Knowledge Graph**: Drug-target-disease relationships
    - **Batch Screening**: High-throughput lead prioritization
    - **FastAPI Backend**: REST API for pharmaceutical predictions

    #### Technologies Used

    - **ML/AI**: XGBoost (7 ADMET endpoints trained on public TDC data, scaffold splits)
    - **Cheminformatics**: RDKit, molecular descriptors, fingerprints
    - **Visualization**: Plotly, Matplotlib, Seaborn
    - **Backend**: FastAPI, Uvicorn
    - **Frontend**: Streamlit
    - **Data**: NetworkX (knowledge graphs), UMAP (clustering)

    #### Industry Standard Workflows

    This platform demonstrates workflows and techniques used in pharmaceutical discovery:

    1. **ADME/PK Focus**: Critical for small molecule drug development pipelines
    2. **Kinase Inhibitors**: Important target class in oncology research
    3. **Held-Out Validation**: Every ADMET model's score is a single held-out TDC test
       evaluation — no synthetic data, no fabricated metrics
    4. **Knowledge Graphs**: Used for target identification and validation

    #### References & Industry Practices

    - XGBoost: Standard gradient-boosted model for pharmaceutical QSAR
    - Therapeutics Data Commons (TDC): Public benchmark datasets with scaffold splits
    - Lipinski/Veber rules: Industry-standard drug-likeness filters
    - hERG prediction: Critical safety assessment
    - CYP450 profiling: Standard ADME analysis
    
    See `references.md` for complete scientific citations and methodology documentation.
    
    ---
    
    **Developer**: Ardit Mishra  
    **Tech Stack**: Python, RDKit, scikit-learn, Streamlit, FastAPI  
    **GitHub**: github.com/ardit-mishra
    """)
    
    st.markdown('<div class="sub-header">Contact</div>', unsafe_allow_html=True)
    st.write("For questions about this platform or to discuss pharmaceutical AI/ML applications.")

# =============================================================================
# FOOTER
# =============================================================================
# Display footer with credits and links
st.markdown("""
<div class="biostudio-footer">
    <p>Ardit BioStudio &middot; ADMET property prediction &middot; v1.0 &middot; Ardit Mishra</p>
    <p style="font-size: 0.85rem; margin-top: 0.5rem;">
        Built with RDKit • scikit-learn • XGBoost • Streamlit • FastAPI
    </p>
    <p style="font-size: 0.8rem; margin-top: 0.3rem;">
        <a href="https://github.com/ardit-mishra" style="color: #4A90E2; text-decoration: none;">github.com/ardit-mishra</a>
    </p>
</div>
""", unsafe_allow_html=True)
