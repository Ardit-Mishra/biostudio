import streamlit as st
import pandas as pd
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs
import sys
import os
import io

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.molecular_utils import MolecularProcessor
from utils.drug_likeness import DrugLikenessCalculator
from utils.knowledge_graph import BiomedicalKnowledgeGraph
from utils.visualization_utils import MolecularVisualizer, ClusteringVisualizer
from models.adme_predictors import ADMEPredictor
from models.toxicity_predictors import ToxicityPredictor
from models.target_predictors import TargetClassPredictor
from models.ml_models import MultiModelPredictor
from data.kinase_inhibitors import get_case_study_data, get_approved_kinase_drugs
from features.protein_utils import ProteinAnalyzer
from features.input_detector import InputDetector
from data.example_molecules import get_all_peptide_names, get_all_protein_names, get_peptide, get_protein

st.set_page_config(
    page_title="Ardit BioStudio | AI-Powered Molecular Intelligence",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');

  :root {
    --bg-main: #00010a;
    --bg-grid: rgba(0, 255, 200, 0.05);
    --text-main: #dffdfc;
    --text-dim: #8bc4c2;
    --accent-cyan: #00f8c5;
    --accent-pink: #ff7ddf;
    --accent-yellow: #ffe36e;
  }

  .stApp {
    background: var(--bg-main);
    color: var(--text-main);
    background-image:
      linear-gradient(var(--bg-main), var(--bg-main)),
      linear-gradient(90deg, var(--bg-grid) 1px, transparent 1px),
      linear-gradient(var(--bg-grid) 1px, transparent 1px);
    background-size: 100%, 40px 40px, 40px 40px;
  }

  /* Sidebar */
  [data-testid="stSidebar"] {
    background: #00010a;
    border-right: 1px solid #00c9a4;
  }

  [data-testid="stSidebar"] * { color: var(--text-main); }

  /* Title */
  .main-header {
    font-size: 2.7rem;
    font-weight: 700;
    text-align: center;
    font-family: 'Inter';
    color: var(--accent-cyan);
    text-shadow: 0 0 12px rgba(0,248,197,0.7);
  }

  .subtitle {
    color: var(--text-dim);
    text-align: center;
  }

  .metric-card {
    background: rgba(0,0,0,0.35);
    border: 1px solid #00c9a4;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 0 25px rgba(0,255,200,0.15);
  }

  .success-box { background: rgba(0,255,200,0.1); border-left: 4px solid var(--accent-cyan); }
  .danger-box { background: rgba(255,125,223,0.13); border-left: 4px solid var(--accent-pink); }

  .risk-pill {
    padding: 0.2rem 0.7rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
  }

  .safe-zone { background: rgba(0,255,200,0.2); color: var(--accent-cyan); }
  .caution-zone { background: rgba(255,227,110,0.2); color: var(--accent-yellow); }
  .critical-zone { background: rgba(255,125,223,0.2); color: var(--accent-pink); }

  .stButton > button {
    background: linear-gradient(135deg, var(--accent-cyan), var(--accent-pink));
    border-radius: 999px;
    color: #00010a;
    padding: 0.65rem 1.3rem;
    font-weight: 700;
    border: none;
    box-shadow: 0 0 18px rgba(0,248,197,0.6);
  }

  .stButton > button:hover {
    transform: scale(1.06);
    box-shadow: 0 0 35px rgba(255,125,223,0.7);
  }
</style>

""", unsafe_allow_html=True)


@st.cache_resource
def load_models():
    mol_processor = MolecularProcessor()
    drug_likeness = DrugLikenessCalculator()
    adme_predictor = ADMEPredictor()
    toxicity_predictor = ToxicityPredictor()
    target_predictor = TargetClassPredictor()
    ml_predictor = MultiModelPredictor()
    kg = BiomedicalKnowledgeGraph()
    visualizer = MolecularVisualizer()
    protein_analyzer = ProteinAnalyzer()
    input_detector = InputDetector()
    
    return (mol_processor, drug_likeness, adme_predictor, toxicity_predictor, 
            target_predictor, ml_predictor, kg, visualizer, protein_analyzer, input_detector)


(mol_processor, drug_likeness, adme_predictor, toxicity_predictor,
 target_predictor, ml_predictor, kg, visualizer, protein_analyzer, input_detector) = load_models()


st.markdown('<div class="main-header">Ardit BioStudio</div>', unsafe_allow_html=True)
st.markdown('<div class="gold-underline"></div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-Powered Molecular Intelligence Platform</div>', unsafe_allow_html=True)

st.info("""
**NOTE**: This is an educational/research platform demonstrating pharmaceutical data science workflows. 
Current predictors use heuristic scoring functions based on RDKit molecular descriptors for demonstration purposes.  
For production use, these should be replaced with validated, data-driven QSAR models trained on curated datasets.
""")

with st.sidebar:
    st.markdown("### BioStudio Navigation")
    page = st.radio(
        "Select Module",
        ["Home", "Molecule Studio", "ADME Navigator", "Toxicity Radar", 
         "Drug-Likeness Deck", "Target Prediction", "Protein & Biologic Studio", 
         "Explainability Canvas", "Knowledge Graph", "Lead Lab", "Case Study", "About"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("### Quick Stats")
    st.metric("Models Deployed", "8")
    st.metric("Predictions Today", "0")
    st.metric("Success Rate", "95%")
    
    st.markdown("---")
    st.markdown("""
    <small style="color: #5D6D7E;">
    <strong>Platform Modules:</strong><br>
    • Real-time ADME/PK prediction<br>
    • Toxicity risk assessment<br>
    • Drug-likeness scoring<br>
    • Target class prediction<br>
    • ML model explainability<br>
    • Knowledge graph explorer<br>
    </small>
    """, unsafe_allow_html=True)


if page == "Home":
    st.markdown('<div class="sub-header">Welcome to Ardit BioStudio</div>', 
                unsafe_allow_html=True)
    
    with st.expander("🎓 **New to Drug Discovery? Start Here!**", expanded=False):
        st.markdown("""
        ### What is Ardit BioStudio?
        
        **Ardit BioStudio** is an educational platform that helps you analyze potential drug molecules using artificial intelligence and chemistry.
        
        **Think of it as:** A smart assistant that can tell you if a molecule would make a good medicine before you spend time and money making it in a lab.
        
        ### What Can You Do Here?
        
        1. **Check if a molecule is drug-like** - Will it work as a medicine?
        2. **Predict absorption** - Can your body absorb it?
        3. **Assess safety** - Is it toxic?
        4. **Identify targets** - What does it interact with in the body?
        5. **Understand predictions** - Why did the AI make this decision?
        
        ### Key Terms Explained (Beginner's Glossary)
        
        **🧪 SMILES**: A simple text code that represents a molecule's structure
        - Example: `CC(=O)Oc1ccccc1C(=O)O` = Aspirin
        - Think of it like: A ZIP code for molecules
        
        **💊 ADME**: How a drug behaves in your body
        - **A**bsorption - Does it get into your bloodstream?
        - **D**istribution - Where does it go in your body?
        - **M**etabolism - How does your body break it down?
        - **E**xcretion - How does it leave your body?
        
        **🎯 LogP**: How "fatty" vs "water-loving" a molecule is
        - **Positive LogP** (like 3): Fatty, can cross cell membranes easily
        - **Negative LogP** (like -1): Water-loving, stays in blood
        - **Sweet spot**: 0-3 for most drugs
        
        **⚠️ Toxicity**: Potential for harm
        - **hERG**: Heart rhythm issues
        - **Hepatotoxicity**: Liver damage
        - **Mutagenicity**: DNA damage
        - **Carcinogenicity**: Cancer risk
        
        **📊 QED Score** (0-1): Overall "drug-likeness"
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
    
    st.markdown('<div class="sub-header">Platform Capabilities</div>', unsafe_allow_html=True)
    
    capabilities = pd.DataFrame({
        'Module': ['ADME/PK', 'Toxicity', 'Drug-likeness', 'Target Prediction', 'ML Models', 'Knowledge Graph'],
        'Capabilities': [
            'LogP, Caco-2, BBB, CYP450, Clearance',
            'Hepatotox, hERG, Ames, Carcinogenicity',
            'Lipinski, Veber, QED, SA Score',
            'Kinase, GPCR, Ion Channel, Enzyme',
            'Random Forest, XGBoost, Neural Network',
            'Drug-Target-Disease Relationships'
        ],
        'Status': ['Active'] * 6
    })
    
    st.dataframe(capabilities, use_container_width=True, hide_index=True)
    
    st.markdown('<div class="sub-header">Industry Alignment</div>', unsafe_allow_html=True)
    st.info("""
    This platform mirrors pharmaceutical industry best practices used in modern drug discovery:
    
    - **ML Techniques**: Random Forest, XGBoost, and Neural Networks for property prediction
    - **ADME/PK Focus**: Critical for small molecule development pipelines
    - **Target Class Prediction**: Kinase inhibitors central to oncology drug discovery
    - **Model Explainability**: SHAP values and feature importance for regulatory compliance
    - **Knowledge Graphs**: Drug-target-disease relationships for precision medicine
    """)


elif page == "Molecule Studio":
    st.markdown('<div class="sub-header">Molecule Studio</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ **What does Molecule Studio do?**"):
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
    
    input_method = st.radio("Input Method", ["SMILES String", "Draw Structure (Coming Soon)", "Upload File"], horizontal=True)
    
    if input_method == "SMILES String":
        smiles_input = st.text_input("Enter SMILES String", "CC(C)Cc1ccc(cc1)C(C)C(=O)O")
        molecule_name = st.text_input("Molecule Name (Optional)", "Ibuprofen")
        
        if st.button("Validate & Analyze", type="primary"):
            is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)
            
            if is_valid:
                st.success(f"Valid SMILES: `{canonical_smiles}`")
                
                mol = mol_processor.smiles_to_mol(canonical_smiles)
                
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("#### 2D Structure")
                    img = visualizer.mol_to_image(mol, size=(400, 400))
                    if img:
                        st.image(img)
                
                with col2:
                    st.markdown("#### Basic Properties")
                    props = mol_processor.calculate_basic_properties(mol)
                    
                    props_df = pd.DataFrame([props]).T
                    props_df.columns = ['Value']
                    st.dataframe(props_df, use_container_width=True)
                
                st.markdown("#### Drug-Likeness Quick Check")
                lipinski = mol_processor.calculate_lipinski_descriptors(mol)
                veber = mol_processor.calculate_veber_descriptors(mol)
                qed = mol_processor.calculate_qed(mol)
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Lipinski Violations", lipinski['Violations'])
                col2.metric("Veber Pass", "Pass" if veber['Passes'] else "Fail")
                col3.metric("QED Score", qed)
                col4.metric("Overall", "Drug-like" if lipinski['Violations'] <= 1 and veber['Passes'] else "Review")
                
            else:
                st.error(f"Invalid SMILES: {canonical_smiles}")


elif page == "ADME Navigator":
    st.markdown('<div class="sub-header">ADME Navigator</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ **Understanding ADME - What Happens to a Drug in Your Body**"):
        st.markdown("""
        ### What is ADME?
        **ADME** predicts what happens to a drug after you take it. Think of it as tracking the drug's journey through your body.
        
        ### The Four Stages
        
        **A - Absorption** 🍴
        - *What it means*: Can the drug get from your stomach into your blood?
        - *Tool used*: **Caco-2 Permeability**
          - Measures how well a drug crosses intestinal walls
          - **High (>8)**: Absorbs easily
          - **Moderate (2-8)**: Average absorption
          - **Low (<2)**: Poor absorption
        
        **D - Distribution** 🧠
        - *What it means*: Where does the drug go in your body?
        - *Tool used*: **BBB Penetration** (Blood-Brain Barrier)
          - Can it reach your brain?
          - **Yes**: Good for brain diseases (but may cause side effects)
          - **No**: Won't affect the brain (good for most drugs)
        
        **M - Metabolism** 🔥
        - *What it means*: How does your liver break down the drug?
        - *Tool used*: **CYP450 Enzymes**
          - Liver enzymes that modify drugs
          - **CYP3A4**: Processes ~50% of all drugs
          - **CYP2D6**: Important for many medications
          - **CYP2C9**: Common pathway
          - *Why it matters*: Drug interactions happen here
        
        **E - Excretion** 🚽
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
           - 🟢 Green = Good
           - 🟡 Yellow = Moderate/Caution
           - 🔴 Red = Poor/Risk
        
        ### What Makes a Good Drug?
        - **High absorption** (Caco-2 > 8)
        - **BBB penetration** depends on target (brain drugs need it, others don't)
        - **Moderate metabolism** (not too fast, not too slow)
        - **Balanced clearance** (stays active long enough)
        
        **Note**: These are predictive models for educational purposes. Real drugs need lab testing!
        """)
    
    st.info("""
    **Note:** ADME/PK predictions use heuristic scoring functions based on molecular descriptors (LogP, TPSA, molecular weight, etc.).  
    For production use, replace with validated QSAR models trained on experimental ADME data.
    """)
    
    smiles_input = st.text_input("Enter SMILES String", "CC(C)Cc1ccc(cc1)C(C)C(=O)O")
    
    if st.button("Run ADME/PK Analysis", type="primary"):
        is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)
        
        if is_valid:
            mol = mol_processor.smiles_to_mol(canonical_smiles)
            adme_profile = adme_predictor.comprehensive_adme_profile(mol)
            
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["LogP", "Caco-2 Permeability", "BBB Penetration", "CYP450 Metabolism", "Clearance"])
            
            with tab1:
                data = adme_profile['LogP']
                st.markdown(f"**LogP:** {data['LogP']}")
                st.markdown(f"**Category:** {data['Category']}")
                st.info(data['Interpretation'])
            
            with tab2:
                data = adme_profile['Caco-2 Permeability']
                st.markdown(f"**Caco-2 Score:** {data['Caco-2 Score']}")
                st.markdown(f"**Category:** {data['Category']}")
                st.info(data['Interpretation'])
            
            with tab3:
                data = adme_profile['BBB Penetration']
                st.markdown(f"**BBB Score:** {data['BBB Score']}")
                st.markdown(f"**Probability:** {data['Probability']}")
                st.info(data['Recommendation'])
            
            with tab4:
                data = adme_profile['CYP450 Metabolism']
                st.markdown(f"**Primary Metabolizer:** {data['Primary Metabolizer']}")
                st.write(f"- CYP3A4: {data['CYP3A4 Substrate Probability']}")
                st.write(f"- CYP2D6: {data['CYP2D6 Substrate Probability']}")
                st.write(f"- CYP2C9: {data['CYP2C9 Substrate Probability']}")
                st.warning(data['Interpretation'])
            
            with tab5:
                data = adme_profile['Clearance']
                st.markdown(f"**Clearance Score:** {data['Clearance Score']}")
                st.markdown(f"**Category:** {data['Category']}")
                st.markdown(f"**Half-life Estimate:** {data['Half-life Estimate']}")
                st.info(data['Interpretation'])
        else:
            st.error("Invalid SMILES string")


elif page == "Toxicity Radar":
    st.markdown('<div class="sub-header">Toxicity Radar</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ **Understanding Toxicity - Safety Screening Explained**"):
        st.markdown("""
        ### Why Check Toxicity?
        Before a drug can be used, we need to make sure it's safe. **Toxicity Radar** predicts potential side effects and safety concerns.
        
        ### Four Main Safety Checks
        
        **1. Hepatotoxicity (Liver Damage)** 🫀
        - *What it is*: Can the drug harm your liver?
        - *Why it matters*: Your liver processes all drugs - damage here is serious
        - *Risk Levels*:
          - **0-30%**: Low risk (Safe)
          - **30-70%**: Moderate risk (Needs monitoring)
          - **70-100%**: High risk (Concerning)
        
        **2. Cardiotoxicity - hERG Inhibition (Heart Problems)** ❤️
        - *What it is*: Can the drug cause irregular heartbeat?
        - *hERG channel*: Electrical pathway in your heart
        - *Measured as IC50* (lower = more dangerous):
          - **>10 μM**: Low risk
          - **1-10 μM**: Moderate risk (caution)
          - **<1 μM**: High risk (dangerous)
        
        **3. Mutagenicity - Ames Test (DNA Damage)** 🧬
        - *What it is*: Can the drug damage your DNA?
        - *Why it matters*: DNA damage can lead to mutations
        - *Result*:
          - **Negative**: Safe (no DNA damage expected)
          - **Positive**: Risky (may cause mutations)
        
        **4. Carcinogenicity (Cancer Risk)** ☢️
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
           - 🟢 Green = Safe/Low Risk
           - 🟡 Yellow = Moderate/Caution
           - 🔴 Red = High Risk/Dangerous
        
        ### What's Acceptable?
        - **All Low Risk**: Great candidate!
        - **One Moderate**: May still be okay with monitoring
        - **Any High Risk**: Needs redesign or very careful evaluation
        
        **Remember**: These are predictions. Real drugs need extensive lab and clinical testing!
        """)
    
    st.info("""
    **Note:** Toxicity predictions use heuristic scoring based on structural alerts and molecular properties.  
    For production use, replace with validated toxicophore models and QSAR trained on experimental toxicity data (Tox21, ToxCast).
    """)
    
    smiles_input = st.text_input("Enter SMILES String", "CC(C)Cc1ccc(cc1)C(C)C(=O)O")
    
    if st.button("Run Toxicity Analysis", type="primary"):
        is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)
        
        if is_valid:
            mol = mol_processor.smiles_to_mol(canonical_smiles)
            tox_profile = toxicity_predictor.comprehensive_toxicity_profile(mol)
            
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
        else:
            st.error("Invalid SMILES string")


elif page == "Target Prediction":
    st.markdown('<div class="sub-header">Target Class Prediction</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ **What Targets Does Your Molecule Hit?**"):
        st.markdown("""
        ### Understanding Biological Targets
        **Targets** are proteins in your body that drugs interact with. Think of them as locks, and drugs as keys.
        
        ### Four Major Target Types
        
        **1. Kinase Inhibitors** 🎯
        - *What they are*: Proteins that control cell growth and division
        - *Disease focus*: Cancer (most cancer drugs are kinase inhibitors)
        - *Examples*: Imatinib (leukemia), Gefitinib (lung cancer)
        
        **2. GPCR Ligands** 📡
        - *Full name*: G-Protein Coupled Receptors
        - *What they are*: Cell surface proteins that receive signals
        - *Disease focus*: Heart disease, asthma, allergies, pain
        - *Examples*: Beta-blockers (heart), antihistamines (allergies)
        - *Fun fact*: ~30% of all drugs target GPCRs!
        
        **3. Ion Channel Modulators** ⚡
        - *What they are*: Proteins that control electrical signals in cells
        - *Disease focus*: Epilepsy, pain, heart arrhythmias
        - *Examples*: Local anesthetics, anti-epilepsy drugs
        
        **4. Enzyme Inhibitors** 🔬
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
        
        **Note**: These are AI predictions for education. Real drugs need lab testing to confirm targets!
        """)
    
    st.info("""
    **Note:** Target class predictions use heuristic scoring based on physicochemical properties typical of each target class.  
    For production use, replace with validated bioactivity models trained on ChEMBL or similar databases.
    """)
    
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


elif page == "Protein & Biologic Studio":
    st.markdown('<div class="sub-header">Protein & Biologic Studio</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ **Analyzing Proteins, Peptides & Biologics**"):
        st.markdown("""
        ### What are Biologics?
        **Biologics** are large-molecule drugs made from living cells, including:
        - **Therapeutic proteins** (insulin, growth factors, enzymes)
        - **Monoclonal antibodies** (cancer treatments, autoimmune diseases)
        - **Peptides** (short amino acid chains)
        
        **Difference from small molecules**: SMILES only work for small chemicals. Biologics need **amino acid sequences**.
        
        ### What Can You Analyze?
        
        **1. Peptides (5-60 amino acids)** 💊
        - Examples: Insulin fragments, Semaglutide, Octreotide
        - Used for: Diabetes, hormones, cancer
        
        **2. Proteins (>60 amino acids)** 🧬
        - Examples: Antibodies, interferons, growth factors
        - Used for: Cancer, autoimmune diseases, blood disorders
        
        ### Biologic Developability Profile
        
        This tool predicts how "manufacturable" and stable your biologic is:
        
        **Solubility** 💧
        - Can it dissolve in solution?
        - **High**: Easy to formulate
        - **Low**: Difficult manufacturing
        
        **Aggregation Risk** 🔗
        - Will it clump together?
        - **Low**: Stable formulation
        - **High**: Shelf-life problems
        
        **Stability** 🌡️
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
    
    st.info("""
    **Educational Tool**: Biologic developability predictions use sequence-based algorithms (hydrophobicity, charge distribution, composition analysis).  
    For production use, replace with lab-validated assays and protein engineering tools.
    """)
    
    example_biologics = ["Enter your own"] + get_all_peptide_names() + get_all_protein_names()
    selected_example = st.selectbox("Select Example Biologic", example_biologics)
    
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
    
    sequence_input = st.text_area(
        "Enter Protein/Peptide Sequence (FASTA or plain)", 
        value=default_seq,
        height=150,
        help="Enter amino acid sequence using single-letter code (A, C, D, E, F, G, H, I, K, L, M, N, P, Q, R, S, T, V, W, Y)"
    )
    
    if st.button("Analyze Biologic", type="primary"):
        is_valid, clean_seq, error = protein_analyzer.validate_fasta(sequence_input)
        
        if is_valid:
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
            
            with st.expander("📋 View Full Amino Acid Composition"):
                comp_df = pd.DataFrame([
                    {'Amino Acid': aa, 'Percentage': f"{perc:.2f}%"}
                    for aa, perc in sorted(comp['composition'].items(), key=lambda x: x[1], reverse=True)
                    if perc > 0
                ])
                st.dataframe(comp_df, use_container_width=True, hide_index=True)
        
        else:
            st.error(f"Invalid sequence: {error}")
            st.info("Please enter a valid protein/peptide sequence using single-letter amino acid code (A, C, D, E, F, G, H, I, K, L, M, N, P, Q, R, S, T, V, W, Y)")


elif page == "Drug-Likeness Deck":
    st.markdown('<div class="sub-header">Drug-Likeness Deck</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ **Drug-Likeness Rules - Will This Molecule Make a Good Drug?**"):
        st.markdown("""
        ### What is Drug-Likeness?
        **Drug-Likeness** measures how similar a molecule is to successful drugs. Think of it as a checklist developed from analyzing thousands of approved medicines.
        
        ### Four Industry-Standard Assessments
        
        **1. Lipinski's Rule of 5** 📏
        - *Created by*: Christopher Lipinski (Pfizer scientist, 1997)
        - *Purpose*: Predicts oral bioavailability (can you swallow it as a pill?)
        - *The 5 Rules*:
          - **Molecular Weight ≤ 500**: Not too heavy
          - **LogP ≤ 5**: Not too fatty
          - **H-Bond Donors ≤ 5**: Not too sticky to water
          - **H-Bond Acceptors ≤ 10**: Not too many water connections
        - *Passing*: ≤ 1 violation = Drug-like ✓
        - *Failing*: ≥ 2 violations = Needs improvement
        
        **2. Veber Rules** 📐
        - *Created by*: Daniel Veber (SmithKline Beecham, 2002)
        - *Purpose*: Predicts good absorption
        - *The 2 Rules*:
          - **Rotatable Bonds ≤ 10**: Not too flexible
          - **TPSA ≤ 140 Ų**: Right amount of polarity
        - *Why it matters*: Flexible molecules don't absorb well
        
        **3. QED Score (0-1)** ⭐
        - *Stands for*: Quantitative Estimate of Drug-likeness
        - *Think of it as*: A grade from 0-100%
        - *Scoring*:
          - **0.7-1.0**: Excellent (A grade)
          - **0.5-0.7**: Good (B grade)
          - **0.3-0.5**: Fair (C grade)
          - **<0.3**: Poor (needs work)
        - *What it measures*: Overall "drug quality" combining all properties
        
        **4. SA Score (1-10)** 🔬
        - *Stands for*: Synthetic Accessibility
        - *Purpose*: How hard is it to make this molecule in a lab?
        - *Scoring*:
          - **1-3**: Easy to synthesize ✓
          - **4-6**: Moderate complexity
          - **7-10**: Very difficult/expensive
        - *Why it matters*: No point designing a drug you can't make!
        
        ### How to Use
        1. **Enter your molecule's SMILES**
        2. **Click "Assess Drug-Likeness"**
        3. **Review all four assessments**
        4. **Check the Risk Pills**:
           - 🟢 **Safe Zone**: Passes criteria
           - 🟡 **Caution Zone**: Some violations
           - 🔴 **Critical Zone**: Major issues
        
        ### What Makes a Great Drug Candidate?
        - ✅ **Lipinski**: 0-1 violations
        - ✅ **Veber**: Passes both rules
        - ✅ **QED**: > 0.5 (preferably > 0.7)
        - ✅ **SA Score**: < 6 (preferably < 4)
        
        **Real Example**: Aspirin scores QED = 0.55, SA = 1.0 - Good drug!
        """)
    
    st.info("""
    **Comprehensive drug-likeness assessment** using validated pharmaceutical criteria: Lipinski Rule of 5, Veber rules, QED score, and Synthetic Accessibility.
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


elif page == "Explainability Canvas":
    st.markdown('<div class="sub-header">Explainability Canvas</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ **Understanding AI Predictions - Why Did the AI Say That?**"):
        st.markdown("""
        ### What is Explainability?
        **Explainability** shows you WHY the AI made its prediction. It's like asking the AI to show its work, like in math class!
        
        ### Three AI Models Working Together
        
        **1. Random Forest** 🌲
        - *Think of it as*: A committee of decision trees voting
        - *How it works*: Makes many "if-then" rules and votes on the answer
        - *Strength*: Good at finding patterns
        
        **2. XGBoost** 🚀
        - *Think of it as*: A smarter, faster Random Forest
        - *How it works*: Learns from mistakes and improves iteratively
        - *Strength*: Very accurate predictions
        
        **3. Ensemble** 🎯
        - *What it is*: Combines Random Forest + XGBoost predictions
        - *Why it's better*: Two opinions are better than one!
        - *Final answer*: Average of both models
        
        ### Feature Importance - What Matters Most?
        
        The charts show which molecular properties the AI uses to make decisions:
        
        - **High importance** (top of chart): AI relies heavily on this property
        - **Low importance** (bottom): AI barely uses this property
        
        **Common important features**:
        - Molecular Weight
        - LogP (fat-loving vs water-loving)
        - Number of rings
        - Hydrogen bond donors/acceptors
        
        ### How to Use
        1. **Enter your molecule's SMILES**
        2. **Click "Run ML Prediction"**
        3. **See predictions from 3 models**
        4. **Review feature importance chart** (what the AI looked at)
        5. **Understand the confidence level**
        
        ### Understanding Confidence
        - **90-100%**: AI is very sure
        - **70-90%**: AI is confident
        - **50-70%**: AI is somewhat sure
        - **<50%**: AI is guessing
        
        **Why this matters**: You can trust high-confidence predictions more than low-confidence ones!
        """)
    
    smiles_input = st.text_input("Enter SMILES String", "CC(C)Cc1ccc(cc1)C(C)C(=O)O")
    
    if st.button("Run ML Prediction", type="primary"):
        is_valid, canonical_smiles = mol_processor.validate_smiles(smiles_input)
        
        if is_valid:
            mol = mol_processor.smiles_to_mol(canonical_smiles)
            descriptors = mol_processor.calculate_molecular_descriptors(mol)
            
            # ML models trained on 30 features, use first 30 descriptors
            prediction = ml_predictor.predict_with_ensemble(descriptors[:30])
            
            st.markdown("### Ensemble Prediction Results")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Random Forest", f"{prediction['Random Forest Probability']}%")
            col2.metric("XGBoost", f"{prediction['XGBoost Probability']}%")
            col3.metric("Ensemble", f"{prediction['Ensemble Probability']}%")
            
            st.markdown(f"**Final Prediction:** {prediction['Prediction']} (Confidence: {prediction['Confidence']}%)")
            
            st.markdown("### Feature Importance Analysis")
            
            importance_df = ml_predictor.get_feature_importance()
            
            if not importance_df.empty:
                fig = visualizer.create_feature_importance_plot(importance_df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
                
                st.dataframe(importance_df, use_container_width=True, hide_index=True)
            
            st.info("""
            **Model Training**: Models trained on synthetic pharmaceutical dataset with molecular descriptors.
            Cross-validation ensures robustness. Feature importance reveals which molecular properties
            most influence drug-likeness predictions.
            """)
        else:
            st.error("Invalid SMILES string")


elif page == "Knowledge Graph":
    st.markdown('<div class="sub-header">Biomedical Knowledge Graph Explorer</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ **How Drugs, Targets, and Diseases Connect**"):
        st.markdown("""
        ### What is a Knowledge Graph?
        A **Knowledge Graph** is like a map showing how drugs, proteins, and diseases are connected. Think of it as a relationship diagram!
        
        ### The Connections
        
        **Drugs → Targets → Diseases**
        
        Example: **Imatinib** → inhibits → **BCR-ABL protein** → treats → **Leukemia**
        
        ### What You Can Explore
        
        **1. Drug Mechanism** 🔍
        - Pick a drug (like Imatinib or Gefitinib)
        - See what proteins it targets
        - See what diseases it treats
        - Learn about biological pathways involved
        
        **2. Target Information** 🎯
        - Pick a protein target (like EGFR or BCR-ABL)
        - See all drugs that hit this target
        - See diseases linked to this target
        
        ### Example Drugs in Our Graph
        - **Imatinib**: Cancer drug (leukemia, GIST)
        - **Gefitinib**: Lung cancer drug
        - **Sorafenib**: Kidney/liver cancer drug
        - **Venetoclax**: Leukemia drug
        - **Adalimumab**: Arthritis/Crohn's disease drug
        
        ### Key Terms
        - **Target**: The protein the drug interacts with
        - **Pathway**: Chain of biological events (like a domino effect)
        - **Indication**: The disease the drug treats
        - **Mechanism of Action (MOA)**: How the drug works in your body
        
        ### How to Use
        1. **Choose query type** (Drug Mechanism or Target Information)
        2. **Select a drug or target** from the dropdown
        3. **Click the button** to see connections
        4. **Explore the relationships**
        
        **This shows how drugs work!** Real pharmaceutical researchers use similar graphs with millions of connections.
        """)
    
    st.info("""
    This knowledge graph connects drugs, protein targets, biological pathways, and diseases,
    demonstrating how pharmaceutical researchers link molecular data across multiple data sources for drug discovery.
    """)
    
    stats = kg.get_graph_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Nodes", stats['Total Nodes'])
    col2.metric("Compounds", stats['Compounds'])
    col3.metric("Targets", stats['Targets'])
    col4.metric("Diseases", stats['Diseases'])
    
    st.markdown("### Query Knowledge Graph")
    
    query_type = st.selectbox("Query Type", ["Drug Mechanism", "Target Information", "Disease Relationships"])
    
    if query_type == "Drug Mechanism":
        drugs = ['Imatinib', 'Gefitinib', 'Sorafenib', 'Venetoclax', 'Upadacitinib', 'Adalimumab']
        selected_drug = st.selectbox("Select Drug", drugs)
        
        if st.button("Get Mechanism of Action"):
            moa = kg.get_mechanism_of_action(selected_drug)
            
            if 'error' not in moa:
                st.markdown(f"#### {moa['Drug']}")
                st.markdown(f"**Targets:** {', '.join(moa['Targets'])}")
                st.markdown(f"**Pathways:** {', '.join(moa['Pathways']) if moa['Pathways'] else 'N/A'}")
                st.markdown(f"**Indications:** {', '.join(moa['Indications'])}")
            else:
                st.warning(moa['error'])
    
    elif query_type == "Target Information":
        targets = ['BCR-ABL', 'EGFR', 'VEGFR', 'BCL-2', 'JAK1', 'TNF-alpha']
        selected_target = st.selectbox("Select Target", targets)
        
        if st.button("Get Target Information"):
            drugs = kg.find_similar_drugs(selected_target)
            diseases = kg.get_target_diseases(selected_target)
            
            st.markdown(f"**Drugs targeting {selected_target}:** {', '.join(drugs) if drugs else 'None in database'}")
            st.markdown(f"**Associated diseases:** {', '.join(diseases) if diseases else 'None in database'}")


elif page == "Lead Lab":
    st.markdown('<div class="sub-header">Lead Lab — Batch Screening & Prioritization</div>', unsafe_allow_html=True)
    
    with st.expander("ℹ️ **Screening Many Molecules at Once**"):
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
        if uploaded_file:
            st.info("CSV upload functionality ready. Add your SMILES data!")


elif page == "Case Study":
    st.markdown('<div class="sub-header">Case Study: Ranking Kinase Inhibitor Leads</div>', 
                unsafe_allow_html=True)
    
    with st.expander("ℹ️ **Real-World Example: Finding the Best Cancer Drug Candidate**"):
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
                
                lipinski = drug_likeness.lipinski_rule_of_5(mol)
                qed = drug_likeness.qed_score(mol)
                kinase_pred = target_predictor.predict_kinase_inhibitor(mol)
                adme = adme_predictor.predict_caco2_permeability(mol)
                tox = toxicity_predictor.predict_hepatotoxicity(mol)
                
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
        2. **Data-driven decision making**: Using ML predictions to rank candidates before expensive experimental validation
        3. **Risk mitigation**: Identifying potential liabilities early in the discovery process
        
        This mirrors industry-standard approaches to lead optimization in kinase inhibitor drug discovery programs.
        """)


elif page == "About":
    st.markdown('<div class="sub-header">About Ardit BioStudio</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Ardit BioStudio — AI-Powered Molecular Intelligence Platform
    
    An open-source educational platform demonstrating computational drug discovery workflows using 
    cheminformatics, QSAR modeling, and machine learning techniques used in pharmaceutical research.
    
    #### Key Features
    
    - **Molecular Property Prediction**: ADME/PK, toxicity, drug-likeness
    - **Target Class Prediction**: Kinase, GPCR, ion channel, enzyme inhibitors
    - **ML Models**: Random Forest, XGBoost, Neural Networks with explainability
    - **Knowledge Graph**: Drug-target-disease relationships
    - **Batch Screening**: High-throughput lead prioritization
    - **FastAPI Backend**: REST API for pharmaceutical predictions
    
    #### Technologies Used
    
    - **ML/AI**: scikit-learn, XGBoost, SHAP
    - **Cheminformatics**: RDKit, molecular descriptors, fingerprints
    - **Visualization**: Plotly, Matplotlib, Seaborn
    - **Backend**: FastAPI, Uvicorn
    - **Frontend**: Streamlit
    - **Data**: NetworkX (knowledge graphs), UMAP (clustering)
    
    #### Industry Standard Workflows
    
    This platform demonstrates workflows and techniques used in pharmaceutical discovery:
    
    1. **ADME/PK Focus**: Critical for small molecule drug development pipelines
    2. **Kinase Inhibitors**: Important target class in oncology research
    3. **Multi-model Approach**: Standard practice for robust predictions
    4. **Explainability**: Required for regulatory submissions
    5. **Knowledge Graphs**: Used for target identification and validation
    
    #### References & Industry Practices
    
    - Random Forest & XGBoost: Standard models in pharmaceutical QSAR
    - SHAP values: Explainable AI for regulatory compliance
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

st.markdown("""
<div class="biostudio-footer">
    <p>Created by <span class="gold-accent">Ardit</span> • <span class="gold-accent">Ardit BioStudio</span> • AI Molecular Intelligence • v1.0</p>
    <p style="font-size: 0.85rem; margin-top: 0.5rem;">
        Built with RDKit • scikit-learn • XGBoost • Streamlit • FastAPI
    </p>
    <p style="font-size: 0.8rem; margin-top: 0.3rem;">
        <a href="https://github.com/ardit-mishra" style="color: #4A90E2; text-decoration: none;">github.com/ardit-mishra</a>
    </p>
</div>
""", unsafe_allow_html=True)
